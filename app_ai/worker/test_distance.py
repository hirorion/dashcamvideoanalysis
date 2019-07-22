# -*- coding: utf-8 -*-
"""
    自車の走行距離 テストクラス
"""
import json
import logging
from math import pi, cos, sin

import numpy as np

from app_ai.models import AiFrameInfo
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class TestDistanceClass(Detections, ViolationWorkerClass):
    """
    自車の走行距離テスト
    特に何もアウトプットしない（ログを確認するだけ）
    """
    MOVIE_FPS = 27

    def __init__(self):
        super().__init__()

    def get_violations(self):
        output = {
            "group": "走行距離",
            "category": "自車の走行距離",
            "violations": self.violations
        }
        return output

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        # フレームでループ
        obj_list = AiFrameInfo.objects.filter(movie_id=movie_id)
        x = 0
        y = 0
        prev_x = 0
        prev_y = 0
        l = 0
        for obj in obj_list:
            speed = obj.meta["camera_pose"][0][0] * float(self.MOVIE_FPS) * 3.6
            angle = obj.meta["camera_pose"][2][0]

            radians = angle * pi / 180 # 度をラジアンに変換
            vx = cos(radians) * speed
            vy = sin(radians) * speed

            x = x + vx
            y = y + vy

            a = np.array([prev_x, prev_y])
            b = np.array([x, y])
            l = l + np.linalg.norm(b - a)

            prev_x = x
            prev_y = y

            logger.debug(l)

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

