# -*- coding: utf-8 -*-
"""
    右左折後の急加速 検出クラス
"""
import json
import logging

from app_ai.models import AiFrameInfo
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class SuddenAccelerationBeforeTurningViolationClass(Detections, ViolationWorkerClass):
    """
    右左折後の急加速での急減速（信号なし）
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27
    # TODO 交差点の判定を1.0秒間隔にしている
    CHECK_FRAME_SECOND = MOVIE_FPS * 1  # 1秒
    # TODO 3秒前から(これは停止もしくは歩道からの距離に変更）
    THREE_SECONDS_FRAMES = MOVIE_FPS * 3  # 3秒のフレーム数
    FIVE_SECONDS_FRAMES = MOVIE_FPS * 5  # 5秒のフレーム数
    CHECK_DEGREE = 40  # TODO 右左折の定義を知りたい 今は40度にしている

    def __init__(self):
        super().__init__()
        self.is_start = None
        self.check_arr = None
        self.end_check_arr = None

    def get_violations(self):
        output = {
            "group": "急加減速2",
            "category": "右左折直後の急加速",
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
                logger.debug("# found intersection start= %d, end = %d" % (self.get_start_fno(), end))

                # 右左折しているかチェック TODO 前後1秒でチェック
                degree = abs(self.get_changed_degrees(movie_id, self.get_start_fno() - self.MOVIE_FPS, end + self.MOVIE_FPS))
                logger.debug("# degree = %f" % degree)
                if abs(degree) >= self.CHECK_DEGREE:
                    logger.info("[TEST 右左折した!: start: %d, end: %d" % (self.get_start_fno(), end))
                    # 10m先まで急加速(0.2G [1秒で7kmの差])しているか判定 (TODO 3秒間先まで1秒0.2Gで判定している, 本当は10m先まで行ったところから）
                    after_three_frames = end_fno + self.THREE_SECONDS_FRAMES
                    check_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=end, fno__lte=after_three_frames)
                    speed = []
                    for f in check_frms:
                        sp = f.speed
                        if sp >= 0.0:
                            speed.append(f.speed)
                        else:
                            speed.append(0.0)

                    # 3秒のフレームがない場合を考慮して、少ない方でチェック
                    check_max = self.THREE_SECONDS_FRAMES
                    if len(speed) < check_max:
                        check_max = len(speed)

                    # 1秒未満は処理しない
                    if check_max > self.MOVIE_FPS:
                        for fno in range(0, check_max):
                            try:  # TODO エラーになるので修正必要
                                logger.debug("speed = %d - %d" % (speed[fno + self.MOVIE_FPS], speed[fno]))
                                diff = speed[fno + self.MOVIE_FPS] - speed[fno]  # 一秒後のスピード
                                if diff >= 7.0:
                                    logger.info("[Fault] Sudden acceleration! 0.2G: %d" % diff)
                                    self.safety_flag = False
                                    self.set_last_fno(after_three_frames)
                                    break
                            except:
                                pass

                    # 5秒間で30km以上になったか判定
                    after_fire_frames = end_fno + self.FIVE_SECONDS_FRAMES
                    check_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=end_fno, fno__lte=after_fire_frames)
                    speed = []
                    for f in check_frms:
                        sp = f.speed
                        if sp >= 0.0:
                            speed.append(f.speed)
                        else:
                            speed.append(0.0)

                    for s in speed:
                        logger.debug("speed = %d - %d" % (s, speed[0]))
                        diff = s - speed[0]  # 最初のスピードから上昇をチェック
                        if diff >= 30.0:
                            logger.info("[Fault] Sudden acceleration!(5 seconds over 30km): %d" % diff)
                            self.safety_flag = False
                            self.set_last_fno(after_fire_frames)
                            break

                self.fix()
                # 次の交差点入り口へ
                self.is_start = True

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        check_frame_count = int(self.CHECK_FRAME_SECOND)

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

        self.is_start = False

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

