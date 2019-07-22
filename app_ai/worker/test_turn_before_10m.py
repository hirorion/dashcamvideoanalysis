# -*- coding: utf-8 -*-
"""
    交差点右左折 検出クラス
"""
import json
import logging

from app_ai.models import AiFrameInfo
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class TestTurnInterSectionClass(Detections, ViolationWorkerClass):
    """
     交差点右左折（信号なし）
     TODO 映像が交差点手前で終わっているパターンで交差点抽出
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    # TODO 曲がり終わりの判定に1.5秒にしている
    INTERSECTION_AFTER_CHECK_SECONDS = MOVIE_FPS * 1.0
    CHECK_DEGREE = 40  # TODO 右左折の定義を知りたい 今は60度にしている

    def __init__(self):
        super().__init__()
        self.check_flag = None
        self.start_checking = None

    def get_violations(self):
        output = {
            "group": "右左折判定",
            "category": "交差点右左折",
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
        if self.check_flag < 1:  # 交差点を決めるオブジェクトが現れたフレーム数
            if self.start_checking:
                # 交差点出口見つけた
                logger.debug("# found intersection start= %d, end = %d" % (self.get_start_fno(), end_fno))

                # 右左折しているかチェック
                degree = abs(self.get_changed_degrees(movie_id, self.get_start_fno(), end_fno))
                logger.debug("# degree = %f" % degree)
                if abs(degree) >= self.CHECK_DEGREE:
                    logger.info("[TEST 右左折した!: start: %d, end: %d" % (self.get_start_fno(), end_fno))

                    # curb-lr, curb-rl検索


                    self.safety_flag = False
                    self.set_last_fno(end_fno)

                self.fix()
                # 次の交差点入り口へ
                self.start_checking = False
        else:
            if self.start_checking is False:
                # 交差点入り口
                self.start_checking = True
                self.set_start_fno(start_fno)

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        check_frame_count = int(self.INTERSECTION_AFTER_CHECK_SECONDS)

        # 信号なし交差点
        ic_list = self.get_intersection(movie_id, 0.7, 20.0, 0.4, 0.6)

        check_arr = {}
        for fm in ic_list:
            check_arr[fm.fno] = True

        self.start_checking = False
        fno_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        # check_frame_countごとに交差点が続いているかチェックしている
        for obj_fno in range(1, fno_count, check_frame_count):

            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            self.check_flag = 0
            check_start_fno = start_fno
            for fno in range(start_fno, end_fno):
                if fno in check_arr:
                    self.check_flag = self.check_flag + 1
                    check_start_fno = fno

            self.violation_detections(movie_id, start_fno=check_start_fno, end_fno=end_fno)

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

