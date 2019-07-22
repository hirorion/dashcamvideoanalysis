# -*- coding: utf-8 -*-
"""
    歩道を横切って駐車場など（路外）に侵入する際の手前で不停止 検出クラス
"""
import json
import logging
from math import pi, cos, sin

from django.db.models import Q

from app_ai.models import AiFrameInfo, AiFrameObjectTags, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class StopHodouViolationClass(Detections, ViolationWorkerClass):
    """
    歩道を横切って駐車場など（路外）に侵入する際の手前で不停止
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    PREV_PLAY_BACK_METER = 10.0  # TODO 逆上るフレームの距離が10mになっている
    SEARCH_MIN_STOP = 2.0  # 停止しているかを2秒のフレーム中で探す
    PLAY_BACK_END_PLUS_MIN = 3.0  # 抽出映像最後に付け加える秒数
    FIND_FRAMES_BY_SECONDS = MOVIE_FPS * 1.0  # 1秒単位に指定の事象があるかを見つける

    def __init__(self):
        super().__init__()
        self.start_fno = 0
        self.last_fno = 0
        self.checked_objects = dict()
        self.safety_flag = True
        self.violations = list()

    def get_violations(self):
        output = {
            "group": "一時停止",
            "category": "歩道を横切って駐車場等に進入する際の手前での不停止",
            "violations": self.violations
        }
        return output

    def violation_detections(self, movie_id, obj_fno, obj_tags):
        if "hyoshikireg-stop" in obj_tags and obj_tags["hyoshikireg-stop"]["score"] > 0.9:
            logger.info("found check tag: hyoshikireg-stop, fno: %d" % obj_fno)
            self.set_checked_objects("hyoshikireg-stop", obj_fno)

        if "hyoji-stop" in obj_tags and obj_tags["hyoji-stop"]["score"] > 0.9:
            logger.info("found check tag: hyoji-stop, fno: %d" % obj_fno)
            self.set_checked_objects("hyoji-stop", obj_fno)

        if "hyoji-stop_line" in obj_tags and obj_tags["hyoji-stop_line"]["score"] > 0.5:
            # 判定前にあるべき条件をチェック
            if "hyoshikireg-stop" not in self.checked_objects or "hyoji-stop" not in self.checked_objects:
                logger.warning("---- condition fault! was not found hyoshikireg-stop or hyoji-stop")
                return

            # このオブジェクトを見つるたびに違反運転を判定して更新する
            logger.info("found tag: %s, fno: %d", "hyoji-stop_line", obj_fno)
            # スタートフレーム番号をセット
            self.set_start_fno(obj_fno)

            # 終了フレーム番号をセット
            self.set_last_fno(obj_fno)
            logger.info("last fno = %d" % self.get_last_fno())

            check_frames = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=self.get_start_fno(), fno__lte=self.get_last_fno()).order_by("fno")
            speed = 1
            for f in check_frames:
                logger.debug("speed = %d" % f.speed)
                if f.speed == 0:
                    logger.info("stopped car!")
                    self.safety_flag = True

            logger.info("[Fault] over run stop line")
            self.safety_flag = False

    def get_cross_hodou_by_turn_left(self, movie_id):
        """
        歩道へ入るフレームをすべて抜き出す
        :param movie_id:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'curb-lr' and score >= 0.700000 and ((data->'pose3'->>0)::float > 0 and (data->'pose3'->>0)::float < 5.5 and (data->'pose3'->>1)::float > -1 and (data->'pose3'->>1)::float <= 0 and degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) > 40.0)) ) and speed >= 0 and movie_id=%d order by movie_id, fno" % movie_id

        obj_list = AiFrameObject.objects.raw(sql)

        return obj_list

    def get_cross_hodou_by_turn_right(self, movie_id):
        """
        歩道へ入るフレームをすべて抜き出す
        :param movie_id:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'curb-rl' and score >= 0.800000 and ((data->'pose2'->>0)::float > 0 and (data->'pose2'->>0)::float < 5.5 and (data->'pose2'->>1)::float > -3 and (data->'pose2'->>1)::float < 1 and degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < 20.0 )) ) and speed >= 0 and movie_id=%d order by movie_id, fno" % movie_id

        obj_list = AiFrameObject.objects.raw(sql)

        return obj_list

    def violation_detections(self, movie_id, obj_list, turn_left_right_flag):
        """
        1秒間でチェックして入り口と出口を見つけて、角度をチェックして速度を見て判定している
        :param movie_id:
        :param obj_list:
        :param turn_left_right_flag: left/right
        :return:
        """
        check_arr = {}
        for fm in obj_list:
            check_arr[fm.fno] = True

        if len(obj_list) > 0:
            ai = AiFrameInfo.objects.filter(movie_id=movie_id).order_by("fno")
            org_start_fno = ai[0].fno
            fno_count = ai.count() + org_start_fno

            is_start = True
            for obj_fno in range(org_start_fno, fno_count, int(self.FIND_FRAMES_BY_SECONDS)):

                start_fno = obj_fno
                end_fno = start_fno + int(self.FIND_FRAMES_BY_SECONDS)

                if is_start:
                    # 入り口を見つける
                    start = self.check_object_appears_more_than_once(check_arr, start_fno, end_fno)
                    if start >= 0:
                        # スタートのチェックポイントを見つけた
                        # 5m手前のフレームを計算  TODO 逆上るフレームの距離が10m(PREV_PLAY_BACK_METER)になっている, 5秒前からその距離を見つけようとしている
                        prev_fno = self.get_prev_positon_by_meter(movie_id, 10, start_fno - self.MOVIE_FPS * 5, start_fno)
                        if prev_fno < 0:
                            # うまく計算できない場合は1秒前から
                            prev_fno = self.MOVIE_FPS * 1
                        self.set_start_fno(prev_fno - org_start_fno)
                        is_start = False
                else:
                    # そこから出口を見つける
                    end = self.check_object_not_appear(check_arr, start_fno, end_fno)
                    if end >= 0:
                        # 次のチェックポイントを見つけさせる
                        is_start = True

                        # 見つけた歩道入り口で先に左にまがっているか判断 TODO 前後2秒前から2秒後までで判断している
                        degree = self.get_changed_degrees(movie_id, start_fno - self.MOVIE_FPS * 2, end_fno + self.MOVIE_FPS * 2)
                        if turn_left_right_flag == "left" and degree > 15 or turn_left_right_flag == "right" and degree < -15:  # 左はプラス # 右はマイナス

                            # 見つけたスタートフレームから2秒戻って1秒間停止しているかチェック
                            logger.debug("start_fno = %d, end_fno = %d" % (start_fno, end_fno))
                            chk_start_fno = start_fno - self.MOVIE_FPS * self.SEARCH_MIN_STOP
                            if chk_start_fno < 0:
                                # 2秒なかったらやめる
                                continue
                            check_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=chk_start_fno, fno__lt=start_fno).order_by("fno")
                            speed = []
                            [speed.append(f.speed) for f in check_frms]
                            check_flag = False
                            for i in range(0, self.MOVIE_FPS):
                                s = 0
                                for j in range(i, i + self.MOVIE_FPS):
                                    #logger.debug("j = %d, speed = %d" % (j, speed[j]))
                                    s = s + speed[j]
                                # TODO 停止スピードを1秒間の平均にしている
                                stop_speed = s / self.MOVIE_FPS
                                #logger.debug("==== check speed = %f" % stop_speed)
                                if stop_speed < 1:
                                    check_flag = True
                                    break
                            # 不停止
                            if check_flag is False:
                                self.safety_flag = False
                                self.set_last_fno(end_fno + self.MOVIE_FPS * self.PLAY_BACK_END_PLUS_MIN - org_start_fno)  # TODO 見せるために3秒追加

                            self.fix()

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行
        check_frame_count = int(self.FIND_FRAMES_BY_SECONDS)

        # 路側帯との距離が0のフレームを抜き出す
        obj_list = self.get_cross_hodou_by_turn_left(movie_id)
        self.violation_detections(movie_id, obj_list, "left")

        # 路側帯との距離が0のフレームを抜き出す
        obj_list = self.get_cross_hodou_by_turn_right(movie_id)
        self.violation_detections(movie_id, obj_list, "right")

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

