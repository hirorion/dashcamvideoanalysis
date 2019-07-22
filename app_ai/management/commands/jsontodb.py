# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    書き起こしで作成されたJSONをDBに登録するコマンド

"""
import glob
import logging
import os

from django.core.management.base import BaseCommand

from app_ai.management.lib.lib_jsontodb import LibDbJsonClass

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "AIからのJSONをDBにフレームごとに保存する"

    def add_arguments(self, parser):
        parser.add_argument('fps')
        parser.add_argument('path')
        parser.add_argument('movie_filename')
        parser.add_argument('movie_unique_filename')

    def handle(self, *args, **options):
        path = options['path']
        fps = options['fps']
        movie_filename = options['movie_filename']
        movie_unique_filename = options['movie_unique_filename']

        file_list = glob.glob(path)
        for json_path in file_list:
            if movie_filename is None or movie_filename == "":
                movie_filename = os.path.basename(json_path)
            rarr = {
                "movie_filename": movie_filename,  # TODO 今は連携していない
                "movie_unique_filename": movie_unique_filename,  # TODO 今は連携していない
                "s_fno": 0,
                "e_fno": 1000000000000,   # 最後まで。ここまではフレームがないだろう
            }
            rarray = [rarr]
            libdb_cls = LibDbJsonClass()
            libdb_cls.set_json_to_db_frames(fps, json_path, rarray)
