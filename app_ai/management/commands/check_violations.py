# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    一時停止違反を見つけるテストコマンド
"""
import logging

from django.core.management.base import BaseCommand

from app_ai.models import AiMovie
from app_ai.worker.test_distance import TestDistanceClass
from app_ai.worker.test_intersection import TestInterSectionClass

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "一時停止違反を見つけるテストコマンド"

    def add_arguments(self, parser):
        parser.add_argument('movie_id')

    def handle(self, *args, **options):
        movie_id = int(options['movie_id'])

        # クラスインスタンス化
        #stop_violation_cls = StopLineViolationClassViolation()
        #speed_sidewalg_violation_cls = SpeedSideOfPersonAndBicycleViolationClassViolation()
        #test_cls = TestInterSectionClass()

        # メインスレッド（フレームオブジェクトを見て、各所のworkerを動作させる)
        movies = AiMovie.objects.filter()
        for movie in movies:
            #stop_violation_cls.worker(8)
            #speed_sidewalg_violation_cls.worker(2)
            #arr = test_cls.get_intersection_area(movie.id, 27, 1, fm_list)
            pass

