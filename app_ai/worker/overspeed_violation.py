# -*- coding: utf-8 -*-
"""
    速度超過 検出クラス
"""
import json
import logging

from django.db.models import Count, Avg

from app_ai.models import AiFrameInfo, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class OverSpeedViolationClass(Detections, ViolationWorkerClass):
    """
    速度超過
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
            "group": "速度",
            "category": "速度超過",
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

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        # 一般道の基準速度
        check_speed = 60.0

        # 動画開始から1秒単位で速度チェック
        check_frames = []
        ai = AiFrameInfo.objects.filter(movie_id=movie_id).order_by("fno")
        org_start_fno = ai[0].fno
        logger.debug("start fno = %d" % org_start_fno)
        fno_count = ai.count() + org_start_fno
        for obj_fno in range(org_start_fno, fno_count, self.MOVIE_FPS):
            start_fno = obj_fno
            end_fno = start_fno + self.MOVIE_FPS

            # 曲がってたら無視する TODO 前後1秒でチェック
            degree = abs(self.get_changed_degrees(movie_id, start_fno - self.MOVIE_FPS, end_fno + self.MOVIE_FPS))
            if degree > 14:
                logger.debug("==== found turning car!! %d, start_fno = %d, end_fno = %d" % (degree, start_fno, end_fno))
                continue

            # 速度標示、速度標識があるか
            sp = self.get_maximum_frequency_speed(movie_id, start_fno, end_fno)
            if sp > 0:
                check_speed = sp

            ck_speed = check_speed + 10.0

            c = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno, speed__gt=0).aggregate(Avg('speed'))['speed__avg']
            # 1秒間全部速度オーバーをチェック
            if c is not None and c >= ck_speed:
                logger.debug("[Fault] over speed %d, start_fno = %d, end_fno = %d" % (ck_speed, start_fno, end_fno))
                # 速度オーバー映像をセット(1秒間)
                check_frames.append(start_fno)

        # フレームがつながっているものをつなげた違反動画を作成
        prev_fno = 0
        for start_fno in check_frames:
            if prev_fno == start_fno - self.MOVIE_FPS:
                self.set_last_fno(start_fno + self.MOVIE_FPS)
            else:
                if prev_fno != 0:
                    self.safety_flag = False
                    self.set_start_fno(self.get_start_fno() - self.MOVIE_FPS)
                    self.set_last_fno(self.get_last_fno() + self.MOVIE_FPS)
                    self.fix()
                self.set_start_fno(start_fno)
                self.set_last_fno(start_fno + self.MOVIE_FPS)
            prev_fno = start_fno
        # 最後の分を更新
        if prev_fno != 0:
            self.safety_flag = False
            self.set_start_fno(self.get_start_fno() - self.MOVIE_FPS)
            self.set_last_fno(self.get_last_fno() + self.MOVIE_FPS)
            self.fix()

        for vio in self.violations:
            vio["start_fno"] = vio["start_fno"] - org_start_fno
            vio["last_fno"] = vio["last_fno"] - org_start_fno

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))
