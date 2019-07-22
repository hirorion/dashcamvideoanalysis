# -*- coding: utf-8 -*-
"""
    詰まった車間距離 検出クラス
"""
import json
import logging

from django.db.models import Avg

from app_ai.models import AiFrameInfo, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class JammedDistanceViolationClass(Detections, ViolationWorkerClass):
    """
    詰まった車間距離
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27.0
    THREE_SECONDS_FRAMES = MOVIE_FPS * 3
    CHECK_SPEED = 20.0
    CHECK_DEGREE = 15.0
    CHECK_SCORE = 0.9
    CHECK_CENTER_POS_LTE = 0.5
    CHECK_CENTER_POS_GTE = -0.5

    def __init__(self):
        super().__init__()

    def get_violations(self):
        output = {
            "group": "運転のくせ",
            "category": "詰まった車間距離",
            "violations": self.violations
        }
        return output

    def violation_detections(self, movie_id, **kwargs):
        """
        TODO 車の大きさや取り付け位置による調整が必要
        前方の車を判断して車間距離が3秒以上続いたものを違反
        TODO ゴミフレーム（全体を捜査して対象オブジェクトが写っていないフレームを飛ばす処理）
        :param movie_id:
        :param kwargs:
        :return:
        """

        # 3秒をチェック
        start_fno = kwargs.get("start_fno")
        end_fno = kwargs.get("end_fno")
        check_frames = kwargs.get("check_frames")

        # 判定前にあるべき条件をチェック
        # 自車の速度が3秒間20km以上のフレームを見つける
        speed = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, speed__gt=0).aggregate(Avg('speed'))['speed__avg']
        if speed is not None and speed <= 20.0:
            logger.debug("######### 20km以下だよ")
            return

        # 大きく曲がっていたらそれは無視する
        # 速度による車間ででセンターにある車を抽出

        # 自車が曲がっているかどうか判断
        degree = self.get_changed_degrees(movie_id, start_fno, end_fno)
        if abs(degree) > self.CHECK_DEGREE:
            logger.debug("#####################  degree = %f" % degree)
            return

        # pose2_0 <= 10.0 and pose_ground_center <= 0.5 and pose_ground_center >= -0.5
        # 20km以上のフレームのなかで3秒間、車が前にいたフレームを抽出（TODO 全フレームに車はいないけどいいのかな？）
        check_objects = AiFrameObject.objects.filter(movie_id=movie_id, fno__gt=start_fno, fno__lt=end_fno, tag="vehicle-car-ground", score__gte=self.CHECK_SCORE, pose_ground_center__lte=self.CHECK_CENTER_POS_LTE, pose_ground_center__gte=self.CHECK_CENTER_POS_GTE).order_by("fno")
        if len(check_objects) < 2:
            # 3回ぐらい車が現れていないならやならい
            return

        # 3秒間のフレームにあった対象オブジェクトの距離を確認
        checked_count = 0
        for obj in check_objects:
            distance = float(obj.data["pose3"][0])
            if distance <= 0:  # 距離がおかしいのは無視
                continue

            # 時速別安全車間距離 TODO 計算方法
            # TODO 53の場合は55に寄せる　は、厳しい方を取るという意味で、55km
            sp = AiFrameInfo.objects.get(movie_id=movie_id, fno=obj.fno)
            speed = sp.speed
            check_distance = (speed / 3600.0) * 1000.0  # 秒速をmで
            if distance < check_distance:
                logger.info("[Fault] jammed distance!: fno: %d, speed: %d, check_distance: %s, distance: %d" % (obj.fno, speed, check_distance, distance))
                checked_count += 1

        # 3秒で見つけたフレーム全部だったら違反
        if checked_count >= len(check_objects):
            check_frames.append(start_fno)

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        # フレームでループ
        check_frames = []
        three_seconds_frames = int(self.THREE_SECONDS_FRAMES)
        fno_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        for obj_fno in range(1, fno_count, three_seconds_frames):

            start_fno = obj_fno
            end_fno = start_fno + three_seconds_frames

            self.violation_detections(movie_id, start_fno=start_fno, end_fno=end_fno, check_frames=check_frames)

        # フレームがつながっているものをつなげた違反動画を作成
        prev_fno = 0
        for start_fno in check_frames:
            if prev_fno == start_fno - three_seconds_frames:
                self.set_last_fno(start_fno + three_seconds_frames)
            else:
                if prev_fno != 0:
                    self.safety_flag = False
                    self.set_start_fno(self.get_start_fno() - three_seconds_frames)
                    self.set_last_fno(self.get_last_fno() + three_seconds_frames)
                    self.fix()
                self.set_start_fno(start_fno)
                self.set_last_fno(start_fno + three_seconds_frames)
            prev_fno = start_fno
        # 最後の分を更新
        if prev_fno != 0:
            self.safety_flag = False
            self.set_start_fno(self.get_start_fno() - three_seconds_frames)
            self.set_last_fno(self.get_last_fno() + three_seconds_frames)
            self.fix()

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

