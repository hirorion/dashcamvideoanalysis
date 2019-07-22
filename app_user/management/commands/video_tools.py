# -*- coding: utf-8 -*-
"""
    deployment.management.commands

    @author: $Author$
    @version: $Id$

"""
import json
import logging
import os
import subprocess

import pika
from django.core.management.base import BaseCommand

from app_admin.models.movie_models import UserMovie
from config.settings import RABBIT_ID, RABBIT_PASSWORD, RABBIT_CONNECTION_HOST, RABBIT_QUEUE_NAME_API, MEDIA_ROOT, FFMPEG, TILE_IMAGE_CMD, FFPROBE, RABBIT_PORT

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "RabbitMQからのVIDEOに対する変換を処理するワーカー"

    def handle(self, *args, **options):

        self.output_transaction = True

        try:
            credentials = pika.PlainCredentials(RABBIT_ID, RABBIT_PASSWORD)
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                RABBIT_CONNECTION_HOST,
                RABBIT_PORT,
                '/',
                credentials,
                heartbeat=60,
                blocked_connection_timeout=3000
            ))
            channel = connection.channel()

            # 永続化
            channel.queue_declare(queue=RABBIT_QUEUE_NAME_API, durable=True)

            logger.info(' [*] Waiting for messages. To exit press CTRL+C')

            # 一つのワーカーに一度に複数のメッセージを与えないよう、RabbitMQに指示
            channel.basic_qos(prefetch_count=1)
            # キューのメッセージは自分でコントロール
            # no_ack=True
            channel.basic_consume(RABBIT_QUEUE_NAME_API, callback)
            try:
                channel.start_consuming()
            except KeyboardInterrupt as e:
                print("Catch KeyboardInterrupt.")
                logger.debug("Catch KeyboardInterrupt.")

            channel.stop_consuming()
            channel.close()

        except Exception as e:
            logger.exception(e)


def callback(ch, method, properties, body):
    logger.info("API worker Received %r" % (body,))

    try:
        command = json.loads(body.decode('utf-8'))
        if command['cmd'] == "create_preview_and_change_avi":
            mv_id = command['movie_id']
            user_id = command['user_id']
            create_thumbnail_image(mv_id, user_id)
            create_low_rate_video_for_view(mv_id, user_id)
            if 'avi' in command:
                change_avi_to_mp4_thread(mv_id, user_id)

        # 処理が終わったのでキュー削除を指示して次のキューへ
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.exception(e)


def change_avi_to_mp4_thread(movie_id, user_id):
    """
    AVIファイルをMP4に変換スレッド
    :param movie_id:
    :param user_id:
    :return:
    """
    logger.info("### AVI to MP4 task: Start")
    tmp_mp4_path = None
    mp4_path = None
    try:
        user_movie = UserMovie.objects.get(id=movie_id, user_id=user_id)
        ppath = os.path.join(MEDIA_ROOT, user_movie.user.username)
        unique_id, ext = os.path.splitext(user_movie.unique_filename)
        # 実際のパス
        avi_path = os.path.join(ppath, unique_id + ".avi")
        tmp_new_filename = "_" + unique_id + ".mp4"
        new_filename = unique_id + ".mp4"
        tmp_mp4_path = os.path.join(ppath, tmp_new_filename)
        mp4_path = os.path.join(ppath, new_filename)

        # acodec(オーディオ）は不要かも、元のAVIがドラレコの場合は)
        proc = subprocess.Popen(FFMPEG + ' -i %s -vcodec copy -acodec copy %s' % (avi_path, tmp_mp4_path),
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        output, error = proc.communicate()
        logger.info("### AVI to MP4 ret = %d" % proc.returncode)
        if proc.returncode != 0:
            logger.error(error.decode('utf-8'))
            if tmp_mp4_path is not None and os.path.exists(tmp_mp4_path):
                os.remove(tmp_mp4_path)
            return

        # rename
        os.rename(tmp_mp4_path, mp4_path)

        logger.info("### AVI to MP4 task: End")

    except Exception as e:
        logger.exception(e)
        if tmp_mp4_path is not None and os.path.exists(tmp_mp4_path):
            os.remove(tmp_mp4_path)
        if mp4_path is not None and os.path.exists(mp4_path):
            os.remove(mp4_path)


def create_thumbnail_image(movie_id, user_id):
    """
    動画からタイルのサムネイル画像を作成するスレッド
    :param movie_id:
    :param user_id:
    :return:
    """
    logger.info("### Create thumbnail task: Start")
    out_path = None
    try:
        user_movie = UserMovie.objects.get(id=movie_id, user_id=user_id)
        ppath = os.path.join(MEDIA_ROOT, user_movie.user.username)
        unique_id, ext = os.path.splitext(user_movie.unique_filename)
        new_filename = unique_id + ".jpg"
        # 実際のパス
        img_path = os.path.join(ppath, user_movie.unique_filename)
        out_path = os.path.join(ppath, new_filename)

        # 30コマのタイルイメージを作成
        cmd = TILE_IMAGE_CMD + ' %s %s %s 100 30 1 %s' % (FFPROBE, FFMPEG, img_path, out_path)
        logger.info("CMD = " + cmd)
        proc = subprocess.Popen(cmd,
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        output, error = proc.communicate()
        logger.info("### Create thumbnail ret = %d" % proc.returncode)
        if proc.returncode != 0:
            logger.error(error.decode('utf-8'))
            if out_path is not None and os.path.exists(out_path):
                os.remove(out_path)
            return

        logger.info("### Create thumbnail task: End")

    except Exception as e:
        logger.exception(e)
        if out_path is not None and os.path.exists(out_path):
            os.remove(out_path)


def create_low_rate_video_for_view(movie_id, user_id):
    """
    TODO 低解像度に変換する（ストリーミングにするまでの間)
    :param movie_id:
    :param user_id:
    :return:
    """
    logger.info("### RESIZE movie task: Start")
    tmp_mp4_path = None
    mp4_path = None
    try:
        user_movie = UserMovie.objects.get(id=movie_id, user_id=user_id)
        ppath = os.path.join(MEDIA_ROOT, user_movie.user.username)
        unique_id, ext = os.path.splitext(user_movie.unique_filename)
        # 実際のパス
        in_path = os.path.join(ppath, user_movie.unique_filename)
        tmp_new_filename = "_" + unique_id + "_pv.mp4"
        new_filename = unique_id + "_pv.mp4"
        tmp_mp4_path = os.path.join(ppath, tmp_new_filename)
        mp4_path = os.path.join(ppath, new_filename)

        # acodec(オーディオ）は不要かも、元のAVIがドラレコの場合は)
        proc = subprocess.Popen(FFMPEG + ' -i %s -preset ultrafast -vf scale=1280:-1 %s' % (in_path, tmp_mp4_path),
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        output, error = proc.communicate()
        logger.info("### RESIZE movie ret = %d" % proc.returncode)
        if proc.returncode != 0:
            logger.error(error.decode('utf-8'))
            if tmp_mp4_path is not None and os.path.exists(tmp_mp4_path):
                os.remove(tmp_mp4_path)
            return

        # rename
        os.rename(tmp_mp4_path, mp4_path)

        logger.info("### RESIZE movie task: End")

    except Exception as e:
        logger.exception(e)
        if tmp_mp4_path is not None and os.path.exists(tmp_mp4_path):
            os.remove(tmp_mp4_path)
        if mp4_path is not None and os.path.exists(mp4_path):
            os.remove(mp4_path)
