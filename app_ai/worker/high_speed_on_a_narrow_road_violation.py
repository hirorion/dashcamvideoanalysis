# -*- coding: utf-8 -*-
"""
    狭路での高速度運転 検出クラス
"""
import heapq
import json
import logging
from collections import Counter

import numpy as np

from django.db.models import Count, Q, Avg

from app_ai.models import AiFrameInfo, AiFrameObjectTags, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class HighSpeedOnNarrowRoadViolationClass(Detections, ViolationWorkerClass):
    """
    狭路での高速度運転
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    # TODO 交差点終わりの判定に1.0秒にしている
    INTERSECTION_AFTER_CHECK_SECONDS = MOVIE_FPS * 1.0
    CHECK_DEGREE = 40  # TODO 右左折の定義を知りたい 今は40度にしている

    def __init__(self):
        super().__init__()
        self.is_start = None
        self.check_arr = None
        self.end_check_arr = None

    def get_violations(self):
        output = {
            "group": "速度2",
            "category": "狭路での高速度運転",
            "violations": self.violations
        }
        return output

    def violation_detections(self, movie_id, start_fno, end_fno):
        """
        TODO 車の大きさや取り付け位置による調整が必要
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return:
        """
        if self.is_start is False:
            # 入り口を見つける
            self.is_start = self.check_object_appears_more_than_once(start_fno, end_fno)
        else:
            # そこから出口を見つける
            self.is_start = self.check_object_not_appear(start_fno, end_fno)

    def is_check_narrow_road(self, movie_id, start_fno, end_fno):
        # 3秒間の左右の縁石の幅をチェック
        # 左からlrを検索して、rlが初めて見つかったところの2つの幅
        # TODO laneはどうする？
        cond = Q(tag__contains="curb-") | Q(tag__contains="lane-")
        n_list = AiFrameObject.objects.filter(cond, movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, score__gte=0.8).order_by("data__x1")
        cur_lr = []
        cur_rl = []
        lane_rl = []
        for n in n_list:
            if "curb-" in n.tag and "-lr" in n.tag and n.data["x1"] < 0.5 and n.data["y2"] > 0.7:  # TODO 路側帯の検索に0.5を使っている
                arr = [n.data["pose3"][1], n.data["pose2"][1]]
                cur_lr.append(max(arr))

        n_list = AiFrameObject.objects.filter(cond, movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, score__gte=0.8).order_by("data__x2")
        for n in n_list:
            if "curb-" in n.tag and "-rl" in n.tag and n.data["x2"] > 0.5 and n.data["y2"] > 0.7:
                arr = [n.data["pose2"][1], n.data["pose2"][1]]
                cur_rl.append(max(arr))
            elif "lane-" in n.tag and "-rl" in n.tag and n.data["x2"] > 0.5 and n.data["y2"] > 0.7:
                arr = [n.data["pose2"][1], n.data["pose2"][1]]
                lane_rl.append(max(arr))

        new_cur_lr = 0
        if len(cur_lr) > 0:
            np_cur_lr = np.array(cur_lr)
            logger.debug(cur_lr)
            h_cur_lr, bins_cur_lr = np.histogram(np_cur_lr, bins=5)
            #logger.debug(h_cur_lr.tolist())
            #logger.debug(bins_cur_lr.tolist())
            b_cur_lr = bins_cur_lr.tolist()
            max_i = np.argmax(h_cur_lr)
            new_cur_lr = b_cur_lr[max_i]

        new_cur_rl = 0
        if len(cur_rl) > 0:
            np_cur_rl = np.array(cur_rl)
            h_cur_rl, bins_cur_rl = np.histogram(np_cur_rl, bins=5)
            #logger.debug(h_cur_rl.tolist())
            #logger.debug(bins_cur_rl.tolist())
            b_cur_rl = bins_cur_rl.tolist()
            max_i = np.argmax(h_cur_rl)
            new_cur_rl = b_cur_rl[max_i]

            '''
            if len(lane_rl) > 0:
                new_lane_rl = 0
                np_lane_rl = np.array(lane_rl)
                h_lane_rl, bins_lane_rl = np.histogram(np_lane_rl, bins=5)
                #logger.debug(h_lane_rl.tolist())
                #logger.debug(bins_lane_rl.tolist())
                last_3 = heapq.nlargest(3, range(len(h_lane_rl)), h_lane_rl.take)
                b_lane_rl = bins_lane_rl.tolist()
                for last in last_3:
                    new_lane_rl = b_lane_rl[last]
                    if abs(new_lane_rl - new_cur_rl) > 0.3:
                        new_cur_rl = 0
                        break
            '''

        logger.debug("#### cur_lr = %f, cur_rl = %f" % (new_cur_lr, new_cur_rl))
        if new_cur_lr != 0.0 and new_cur_rl != 0.0:
            l_len = abs(new_cur_lr - new_cur_rl)
            logger.debug("start_fno = %d, end_fno = %d" % (start_fno, end_fno))
            logger.debug("==== lane width = %f" % l_len)
            return l_len

        # 最大値
        #if len(lane_width) > 0:
        #    #sl = sum(lane_width) / len(lane_width)
        #    sl = max(lane_width)
        #    logger.debug("==== lane width = %f" % sl)
        #    return sl

        return 100000

    def check_overspeed_by_1min(self, movie_id, start_fno, end_fno, check_speed, check_frames):
        c = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, speed__gt=0).aggregate(Avg('speed'))['speed__avg']
        # 1秒間全部速度オーバーをチェック
        if c is not None and c >= check_speed:
            # 速度オーバー映像をセット(1秒間)
            logger.debug("=== found over speed 30")
            return True
        return False

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        # 狭路の基準速度
        check_speed = 30.0 + 10.0

        # チェックフレーム数
        check_frame_count = int(self.MOVIE_FPS * 3.0)

        # 標識ない場合の速度
        road_speed = 60.0

        # 動画開始から1秒単位で速度チェック
        ai = AiFrameInfo.objects.filter(movie_id=movie_id).order_by("fno")
        org_start_fno = ai[0].fno
        fno_count = ai.count() + org_start_fno
        check_frames = []
        for obj_fno in range(org_start_fno, fno_count, check_frame_count):
            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            # 曲がってたら無視する
            degree = abs(self.get_changed_degrees(movie_id, start_fno, end_fno))
            if degree > 15.0:
                continue

            # 速度標示、速度標識があるか
            sp = self.get_maximum_frequency_speed(movie_id, start_fno, end_fno)
            if sp > 0:
                road_speed = sp

            # ソーン30の標示、標識があるか
            # TODO ゾーン30のtag名が分からない

            # 狭路であるか(3秒間)
            lane_width = self.is_check_narrow_road(movie_id, start_fno, end_fno)
            if lane_width < 4.0 and road_speed == 30:
                # 30km/hオーバーしているかチェックして、check_framesにそのstart_fnoが保存される
                for fno in range(start_fno, end_fno, self.MOVIE_FPS):  # 1秒間隔でチェック
                    sfno = fno
                    efno = fno + self.MOVIE_FPS
                    ret = self.check_overspeed_by_1min(movie_id, sfno, efno, check_speed, check_frames)
                    if ret is True:
                        check_frames.append(start_fno)
                        break

        # フレームがつながっているものをつなげた違反動画を作成
        for start_fno in check_frames:
            if self.get_last_fno() == start_fno:
                self.set_last_fno(start_fno + check_frame_count)
            else:
                if self.get_last_fno() != 0:
                    self.safety_flag = False
                    self.fix()
                self.set_start_fno(start_fno)
                self.set_last_fno(start_fno + check_frame_count)
        # 最後の分を更新
        if self.get_last_fno() != 0:
            self.safety_flag = False
            self.fix()

        for vio in self.violations:
            vio["start_fno"] = vio["start_fno"] - org_start_fno
            vio["last_fno"] = vio["last_fno"] - org_start_fno

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))
