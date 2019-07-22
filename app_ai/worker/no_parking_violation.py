# -*- coding: utf-8 -*-
"""
    駐車禁止場所での駐車 検出クラス
"""
import json
import logging

import numpy as np
from django.db.models import Sum

from app_ai.models import AiFrameInfo, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class NoParkingViolationClass(Detections, ViolationWorkerClass):
    """
    駐車禁止場所での駐車
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    # TODO 交差点の判定を1.0秒間隔にしている
    CHECK_FRAME_SECOND = MOVIE_FPS * 1  # 1秒
    PREV_PLAY_BACK_METER = 5.0  # TODO 逆上るフレームの距離が5mになっている

    def __init__(self):
        super().__init__()
        self.start_fno = 0
        self.last_fno = 0
        self.checked_objects = dict()
        self.safety_flag = True
        self.violations = list()

    def get_violations(self):
        output = {
            "group": "その他",
            "category": "駐車禁止場所での駐車",
            "violations": self.violations
        }
        return output

    def get_no_parking_hyoushiki(self, movie_id, start_fno, end_fno):
        """
        駐車禁止の標識のフレームをすべて抜き出す
        fnoは大きい順になっている
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'hyoshikireg-no_parking' and score >= 0.700000) and speed >=0 and movie_id=%d and fno >= %d and fno < %d order by movie_id, fno" % (movie_id, start_fno, end_fno)

        return AiFrameObject.objects.raw(sql)

    def get_no_parking_hyouji(self, movie_id, start_fno, end_fno):
        """
        駐車禁止の標示(lr)のフレームをすべて抜き出す
        fnoは大きい順になっている
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'curb-yellow_dashed-lr' and score >= 0.700000 and ((data->'pose3'->>0)::float < 5.5)) ) and  speed >=0 and movie_id=%d and fno >= %d and fno < %d order by movie_id, fno" % (movie_id, start_fno, end_fno)

        return AiFrameObject.objects.raw(sql)

    def get_speed_zero_frames(self, movie_id, second):
        """
        second以上停車しているフレームをすべて抜き出す
        :param movie_id:
        :param second:
        :return: RawQuerySet
        """
        frms = []
        max_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        obj_list = AiFrameInfo.objects.filter(movie_id=movie_id, speed__lt=3, speed__gte=0).order_by("fno")
        next_fno = -1
        for obj in obj_list:
            logger.debug("fno = %d" % obj.fno)
            if obj.fno > next_fno:
                start_fno = obj.fno
                end_fno = obj.fno + self.MOVIE_FPS * second
                # 最初の0スピードフレームからsecond秒間のフレームを抜き出して速度チェック
                speed_sum = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, speed__gte=0).aggregate(Sum('speed'))['speed__sum']
                if speed_sum is None:
                    continue
                # TODO 停止スピードを指定秒間の平均にしている
                stop_speed = speed_sum / (self.MOVIE_FPS * second)
                logger.debug("==== check speed = %f" % stop_speed)
                if stop_speed < 3:
                    # second秒間停車している
                    # どこまで停止しているかを1秒単位でチェックする
                    ck_end_fno = end_fno
                    for fno in range(end_fno, max_count, self.MOVIE_FPS):
                        ck_start_fno = fno
                        ck_end_fno = fno + self.MOVIE_FPS
                        speed_sum = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=ck_start_fno, fno__lt=ck_end_fno, speed__gte=0).aggregate(Sum('speed'))['speed__sum']
                        if speed_sum is None:
                            continue
                        stop_speed = speed_sum / self.MOVIE_FPS
                        # TODO 停止スピードを1秒間の平均にしている
                        logger.debug("==== next check speed = %f" % stop_speed)
                        if stop_speed > 3:
                            break

                    frm = {
                        "start": start_fno,
                        "end": ck_end_fno
                    }
                    frms.append(frm)
                    next_fno = ck_end_fno

        return frms

    def find_nearest_greater_than(self, input_data, value):
        if float(value) > input_data[- 1]:
            return 10000000  # 範囲外は最後まで
        diff = input_data - float(value)
        diff[diff < 0] = np.inf
        idx = diff.argmin()
        return input_data[idx]

    def find_nearest_less_than(self, input_data, value):
        if float(value) < input_data[0]:
            return 0  # 範囲外は0を返す
        diff = input_data - float(value)
        diff[diff > 0] = -np.inf
        idx = diff.argmax()
        return input_data[idx]

    def get_intersection_start_frames(self, movie_id):
        """
        交差点入り口のフレームを配列で取得
        :param movie_id:
        :return:
        """
        check_frame_count = int(self.CHECK_FRAME_SECOND)

        # 交差点スタート
        start_list = self.get_intersection_start_with_stop_or_hodou(movie_id, 0.7, 20.0, 0.4, 0.6)
        # 交差点オブジェクト
        ic_obj_list = self.get_intersection(movie_id, 0.7, 20.0, 0.4, 0.6)

        check_arr = {}
        for fm in start_list:
            check_arr[fm.fno] = True

        end_check_arr = {}
        for fm in ic_obj_list:
            end_check_arr[fm.fno] = True

        frms = []
        is_start = False
        fno_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        for obj_fno in range(1, fno_count, check_frame_count):
            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            if is_start:
                # 入り口を見つける
                start = self.check_object_appears_more_than_once(check_arr, start_fno, end_fno)
                if start >= 0:
                    # スタートのチェックポイントを見つけた
                    frms.append(float(start))
                    is_start = False
            else:
                is_start = True

        return frms

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        # 5分以上停止しているフレームリスト
        stop_frames = self.get_speed_zero_frames(movie_id, 60 * 5)
        if len(stop_frames) > 0:
            # 交差点のフレーム
            isec_nparr = np.array(self.get_intersection_start_frames(movie_id))
            if len(isec_nparr):
                for sfrm in stop_frames:
                    start_fno = sfrm["start"]
                    end_fno = sfrm["end"]
                    # 最初の交差点まで戻って駐車禁止標識を見つける
                    isec_end_fno = self.find_nearest_less_than(isec_nparr, start_fno)
                    # その間に駐車禁止標識があるかどうか
                    obj_list = self.get_no_parking_hyoushiki(movie_id, isec_end_fno, start_fno)
                    if len(obj_list) > 0:  # TODO 標識が一つでもあればOK
                        # 標識があったら危険運転
                        self.safety_flag = False
                        self.set_start_fno(start_fno)
                        self.set_last_fno(end_fno)
                        self.fix()
                        continue
                    # 先の交差点まで進んで駐車禁止標識を見つける
                    isec_end_fno = self.find_nearest_greater_than(isec_nparr, end_fno)
                    # その間に駐車禁止標識があるかどうか
                    obj_list = self.get_no_parking_hyoushiki(movie_id, start_fno, isec_end_fno)
                    if len(obj_list) > 0:  # TODO 標識が一つでもあればOK
                        # 標識があったら危険運転
                        self.safety_flag = False
                        self.set_start_fno(start_fno)
                        self.set_last_fno(end_fno)
                        self.fix()
                        continue

                    # 駐車禁止標示（歩道に）をチェック
                    # 2m手前のフレームから停止位置まで  TODO 逆上るフレームの距離が5mになっている, 5秒前からその距離を見つけようとしている
                    prev_start_fno = self.get_prev_positon_by_meter(movie_id, self.PREV_PLAY_BACK_METER, start_fno - self.MOVIE_FPS * 5, start_fno)
                    obj_list = self.get_no_parking_hyouji(movie_id, prev_start_fno, start_fno)
                    if len(obj_list) > 0:  # TODO 標示が一つでもあればOK
                        # 標識があったら危険運転
                        self.safety_flag = False
                        self.set_start_fno(start_fno)
                        self.set_last_fno(end_fno)
                        self.fix()
                        continue

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

