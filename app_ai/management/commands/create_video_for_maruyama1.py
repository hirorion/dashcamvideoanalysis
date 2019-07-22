# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    丸山さんビデオをCSVに従って分割して、JSONも分割して登録コマンド

"""
import csv
import logging
import subprocess

from django.core.management import BaseCommand

from app_ai.management.lib.lib_jsontodb import LibDbJsonClass
from config.settings import FFMPEG

logger = logging.getLogger(__name__)


def set_data(fps, movie_path, json_path, csv_path, save_movie):

    try:
        with open(csv_path) as f:
            reader = csv.reader(f)
            c = 0
            rarray = []
            for row in reader:
                if row[0] == "01.mov":
                    mid = c
                    if len(row) == 13:  # 指定id
                        mid = int(row[12])

                    title = row[5]
                    t = row[6].split(":")
                    s_sec = int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])
                    s_fno = s_sec * 27
                    t = row[7].split(":")
                    e_sec = int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])
                    e_fno = e_sec * 27
                    print("s, e = %d, %d" % (s_sec, e_sec))
                    rarr = {
                        "movie_filename": "%s_%03d.mp4" % (title, mid),
                        "movie_unique_filename": "",
                        "s_fno": s_fno,
                        "e_fno": e_fno
                    }

                    if save_movie:
                        proc = subprocess.Popen(FFMPEG + ' -y -i \"%s\" -ss %d -t %d -preset ultrafast -vf scale=1280:-1 -metadata title=\"%s_%03d.mp4\" /tmp/%s_%03d.mp4' % (movie_path, s_sec, e_sec - s_sec, title, mid, title, mid),
                                                shell=True,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE
                                                )
                        output, error = proc.communicate()
                        logger.info("### slice movie ret = %d" % proc.returncode)
                        if proc.returncode != 0:
                            logger.error(error.decode('utf-8'))
                            break
                    c = c + 1
                    rarray.append(rarr)

            libdb_cls = LibDbJsonClass()
            libdb_cls.set_json_to_db_frames(fps, json_path, rarray)

    except Exception as e:
        logger.exception(e)
        print("%s" % e)


class Command(BaseCommand):
    help = "AIからのJSONをDBにフレームごとに保存する"

    def add_arguments(self, parser):
        parser.add_argument('fps')
        parser.add_argument('input_movie_path')
        parser.add_argument('json_path')
        parser.add_argument('csv_path')
        parser.add_argument('save_movie_flag')

    def handle(self, *args, **options):
        fps = options['fps']
        movie_path = options['input_movie_path']
        json_path = options['json_path']
        csv_path = options['csv_path']
        save_movie_flag = options['save_movie_flag']

        if str(save_movie_flag) == "1":
            save_movie_flag = True
        else:
            save_movie_flag = False

        set_data(fps, movie_path, json_path, csv_path, save_movie_flag)
