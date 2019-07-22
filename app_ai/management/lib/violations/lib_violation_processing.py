# -*- coding: utf-8 -*-
"""
    Processing video
    Called from rabbit receiver
"""

import json
import os
import signal
import subprocess
import tempfile
from time import sleep

import math
import requests

from app_ai.management.config.define_violations import VIOLATION_WORKER_BUILD_DIR
from app_ai.management.lib.lib_recev_api_from_mq import recv_api_action_stop
from app_ai.models import AiMovie
from app_ai.worker.high_speed_on_a_narrow_road_violation import HighSpeedOnNarrowRoadViolationClass
from app_ai.worker.jammed_distance_violation import JammedDistanceViolationClass
from app_ai.worker.no_parking_or_stopping_violation import NoParkingOrStoppingViolationClass
from app_ai.worker.no_parking_violation import NoParkingViolationClass
from app_ai.worker.overspeed_violation import OverSpeedViolationClass
from app_ai.worker.speed_side_of_person_bicycle_violation import SpeedSideOfPersonAndBicycleViolationClass
from app_ai.worker.steep_steering_the_turning_right_or_left_at_the_intersection import SteepSteeringWhenTurningRightOrLeftAtTheIntersectionViolationClass
from app_ai.worker.stop_hodou_violation import StopHodouViolationClass
from app_ai.worker.stopline_violation import StopLineViolationClass
from app_ai.worker.sudden_acceleration_before_turning import SuddenAccelerationBeforeTurningViolationClass
from app_ai.worker.sudden_deceleration_before_turning import SuddenDecelerationBeforeTurningViolationClass
from app_ai.worker.test_intersection import TestInterSectionClass
from app_ai.worker.test_turn_intersection import TestTurnInterSectionClass


class ViolationProcessingClass(object):
    """
    動画の解析
    """
    def __init__(self, logger):
        self.logger = logger
        self.results = []
        # クラスインスタンス化
        self.stop_violation_cls = StopLineViolationClass()
        self.speed_sidewalk_violation_cls = SpeedSideOfPersonAndBicycleViolationClass()
        self.jammped_distance_violation_cls = JammedDistanceViolationClass()
        self.steep_steering_violation_cls = SteepSteeringWhenTurningRightOrLeftAtTheIntersectionViolationClass()
        self.test_intersection_cls = TestInterSectionClass()
        self.test_turn_intersection_cls = TestTurnInterSectionClass()
        self.sudden_deceleration_cls = SuddenDecelerationBeforeTurningViolationClass()
        self.sudden_acceleration_cls = SuddenAccelerationBeforeTurningViolationClass()
        self.overspeed_cls = OverSpeedViolationClass()
        self.narrow_road_cls = HighSpeedOnNarrowRoadViolationClass()
        self.stop_hodou_cls = StopHodouViolationClass()
        self.no_parking_cls = NoParkingViolationClass()
        self.no_parking_or_stopping_cls = NoParkingOrStoppingViolationClass()
        self.stop_line_test_cls = StopLineViolationClass()

    def analysis(self, movie_id):
        # メインスレッド（フレームオブジェクトを見て、各のworkerを動作させる)
        movies = AiMovie.objects.filter(user_movie_id=movie_id)
        if not movies.exists():
            raise Exception("This json data in DB does not exist.")

        for mv in movies:  # TODO 1動画1jsonのはず

            # 処理を開始する
            self.stop_violation_cls.worker(mv.id)
            self.results.append(self.stop_violation_cls.get_violations())

            #self.speed_sidewalk_violation_cls.worker(mv.id)
            #self.results.append(self.speed_sidewalk_violation_cls.get_violations())

            #self.jammped_distance_violation_cls.worker(mv.id)
            #self.results.append(self.jammped_distance_violation_cls.get_violations())

            #self.steep_steering_violation_cls.worker(mv.id)
            #self.results.append(self.steep_steering_violation_cls.get_violations())

            #self.test_intersection_cls.worker(mv.id)
            #self.results.append(self.test_intersection_cls.get_violations())

            #self.test_turn_intersection_cls.worker(mv.id)
            #self.results.append(self.test_turn_intersection_cls.get_violations())

            #self.sudden_deceleration_cls.worker(mv.id)
            #self.results.append(self.sudden_deceleration_cls.get_violations())

            #self.sudden_acceleration_cls.worker(mv.id)
            #self.results.append(self.sudden_acceleration_cls.get_violations())

            #self.overspeed_cls.worker(mv.id)
            #self.results.append(self.overspeed_cls.get_violations())

            #self.narrow_road_cls.worker(mv.id)
            #self.results.append(self.narrow_road_cls.get_violations())

            #self.stop_hodou_cls.worker(mv.id)
            #self.results.append(self.stop_hodou_cls.get_violations())

            #self.no_parking_cls.worker(mv.id)
            #self.results.append(self.no_parking_cls.get_violations())

            #self.no_parking_or_stopping_cls.worker(mv.id)
            #self.results.append(self.no_parking_or_stopping_cls.get_violations())

            #self.stop_line_test_cls.worker(mv.id)
            #self.results.append(self.stop_line_test_cls.get_violations())
