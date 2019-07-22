# -*- coding: utf-8 -*-
"""
    交差点右左折時の急ハンドル 検出クラス
"""
import json
import logging

from app_ai.models import AiFrameInfo
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class SteepSteeringWhenTurningRightOrLeftAtTheIntersectionViolationClass(Detections, ViolationWorkerClass):
    """
    交差点右左折時の急ハンドル（信号あり）
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    CHECK_FRAME_SECOND = MOVIE_FPS * 1  # 1秒
    THREE_SECONDS_FRAMES = MOVIE_FPS * 3  # 3秒のフレーム数
    CHECK_DEGREE = 40

    def __init__(self):
        super().__init__()
        self.is_start = None
        self.check_arr = None
        self.end_check_arr = None

    def get_violations(self):
        output = {
            "group": "急ハンドル",
            "category": "交差点右左折時の急ハンドル",
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
                self.set_start_fno(start)  # 最初に見つけた位置
                self.is_start = False
        else:
            # そこから出口を見つける  TODO 交差点を見つけてる最中に動画が終了したどうする？
            end = self.check_object_not_appear(self.end_check_arr, start_fno, end_fno)
            if end >= 0:
                # 交差点出口見つけた
                # 3秒でフレームを分割
                logger.debug("# found intersection start= %d, end = %d" % (self.get_start_fno(), end_fno))
                for fno in range(self.get_start_fno(), end_fno, self.THREE_SECONDS_FRAMES):
                    ck_start_fno = fno
                    ck_end_fno = fno + self.THREE_SECONDS_FRAMES
                    if ck_end_fno >= end_fno:  # 3秒未満の場合
                        ck_end_fno = end_fno

                    # このフレーム間で90度曲がっているかチェック TODO 90度だとうまく行かないので40度ぐらいにしている
                    degree = abs(self.get_changed_degrees(movie_id, ck_start_fno, ck_end_fno))
                    logger.debug("# num frm = %d, degree = %f" % (ck_end_fno - ck_start_fno, degree))
                    if abs(degree) >= self.CHECK_DEGREE:
                        logger.info("[Fault] Steep steering!: start: %d, end: %d" % (self.get_start_fno(), end_fno))
                        self.safety_flag = False
                        self.set_last_fno(end_fno)

                    self.fix()
                    # 次の交差点入り口へ
                    self.is_start = True

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        check_frame_count = int(self.CHECK_FRAME_SECOND)

        # 交差点スタート TODO 信号を入れていない
        start_list = self.get_intersection_start_with_stop_or_hodou(movie_id, 0.7, 20.0, 0.4, 0.6)
        # 交差点オブジェクト
        ic_obj_list = self.get_intersection(movie_id, 0.7, 20.0, 0.4, 0.6)

        self.check_arr = {}
        for fm in start_list:
            self.check_arr[fm.fno] = True

        self.end_check_arr = {}
        for fm in ic_obj_list:
            self.end_check_arr[fm.fno] = True

        self.is_start = False
        fno_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        for obj_fno in range(1, fno_count, check_frame_count):

            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            self.violation_detections(movie_id, start_fno=start_fno, end_fno=end_fno)

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

