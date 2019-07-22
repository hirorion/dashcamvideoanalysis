# -*- coding: utf-8 -*-
"""
    交差点
"""
import json
import logging

from app_ai.models import AiFrameInfo
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class TestInterSectionClass(Detections, ViolationWorkerClass):
    """
    交差点
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    # TODO 曲がり終わりの判定に1.0秒にしている
    FIND_FRAMES_BY_SECONDS = MOVIE_FPS * 1.0  # 1秒単位に指定の事象があるかを見つける

    def __init__(self):
        super().__init__()
        self.is_start = None
        self.check_arr = None
        self.end_check_arr = None

    def get_violations(self):
        output = {
            "group": "交差点(信号なし)判定",
            "category": "交差点通過",
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
        if self.is_start:
            # 入り口を見つける
            start = self.check_object_appears_more_than_once(self.check_arr, start_fno, end_fno)
            if start >= 0:
                # スタートのチェックポイントを見つけた
                s = start
                if s < 0:
                    s = 0
                self.set_start_fno(s)  # 最初に見つけた位置
                self.is_start = False
        else:
            # そこから出口を見つける
            end = self.check_object_not_appear(self.end_check_arr, start_fno, end_fno)
            if end >= 0:
                # 出口見つけた
                self.safety_flag = False
                self.set_last_fno(end)
                self.fix()
                # 次のチェックポイントを見つけさせる
                self.is_start = True

    def worker(self, movie_id):
        check_frame_count = int(self.FIND_FRAMES_BY_SECONDS)

        # 交差点スタート
        start_list = self.get_intersection_start_with_stop_or_hodou(movie_id, 0.7, 20.0, 0.4, 0.6)
        # 交差点オブジェクト
        ic_obj_list = self.get_intersection(movie_id, 0.7, 20.0, 0.4, 0.6)

        self.check_arr = {}
        for fm in start_list:
            self.check_arr[fm.fno] = True

        self.end_check_arr = {}
        for fm in ic_obj_list:
            self.end_check_arr[fm.fno] = True

        self.is_start = True
        ai = AiFrameInfo.objects.filter(movie_id=movie_id).order_by("fno")
        org_start_fno = ai[0].fno
        fno_count = ai.count() + org_start_fno
        for obj_fno in range(org_start_fno, fno_count, check_frame_count):

            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            self.violation_detections(movie_id, start_fno=start_fno, end_fno=end_fno)

        for vio in self.violations:
            vio["start_fno"] = vio["start_fno"] - org_start_fno
            vio["last_fno"] = vio["last_fno"] - org_start_fno

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))



