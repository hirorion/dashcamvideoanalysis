# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    動画解析をする

"""
import json
import logging
import os
import shutil
import signal
import threading
from logging import Formatter, INFO
from logging.handlers import TimedRotatingFileHandler

import math
import pika
from django.core.cache import cache
from django.core.management import BaseCommand
from django.urls import reverse

from app_ai.management.config.define_ai import AI_WORKER_BUILD_DIR, RABBIT_ADMIN_NAME, RABBIT_ADMIN_PASSWORD, RABBIT_SERVER_NAME, RABBIT_PORT, \
    API_FS_RABBIT_QUEUE_NAME, LOGGING_PATH, RABBIT_QUEUE_NAME, AI_URL_HOST_ADDRESS_FROM_DOCKER
from app_ai.management.config.define_violations import RABBIT_VIOLATION_QUEUE_NAME
from app_ai.management.lib.ai.lib_video_processing import video_func
from app_ai.management.lib.lib_common import send_response
from app_user.views.view_job import get_ai_activation_key


def thread_func(ch, method_frame, body):
    """
    スレッドメソッド
    :param ch:
    :param method_frame:
    :param body:
    :return:
    """
    if method_frame:
        movie_id = None
        activation_key = None
        status_url = None

        mlogger.info(" [x] Received %s" % body.decode("utf-8"))
        json_data = json.loads(body.decode("utf-8"))
        try:
            # check
            if 'movie_id' not in json_data:
                mlogger.error("[ERROR] movie_id parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            movie_id = json_data['movie_id']

            if 'web_activation_key' not in json_data:
                mlogger.error("[ERROR] web_activation_key parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            activation_key = json_data['web_activation_key']

            if 'movie_status_url' not in json_data:
                mlogger.error("[ERROR] movie_status_url parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            status_url = json_data['movie_status_url']

            if 'server_media_root' not in json_data\
                    or 'movie_download_url' not in json_data\
                    or 'movie_upload_url' not in json_data \
                    or 'unique_filename' not in json_data\
                    or 'user_id' not in json_data\
                    or 'media_type' not in json_data or 'filename' not in json_data\
                    or 'meta_data' not in json_data or "parameters" not in json_data \
                    or 'select_model' not in json_data:
                mlogger.error("[ERROR] parameter error.")
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'movie_analysis', 'status_message': 'Parameter Error', 'log': 'Parameter Error'}
                )

                ch.basic_ack(method_frame.delivery_tag)
                return

            # ファイルを置く場所を確認
            if not os.path.exists(AI_WORKER_BUILD_DIR):
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'movie_analysis', 'status_message': 'File Error', 'log': 'Data temporary directly is missing'}
                )

                ch.basic_ack(method_frame.delivery_tag)
                return

            # get parameter data
            server_media_root = json_data['server_media_root']
            movie_download_url = json_data['movie_download_url']
            movie_upload_url = json_data['movie_upload_url']
            movie_unique_filename = json_data['unique_filename']
            user_id = json_data['user_id']
            media_type = json_data['media_type']
            movie_filename = json_data['filename']
            meta_data = json_data['meta_data']
            parameters = json.loads(json_data['parameters'])
            select_model = json_data['select_model']

            # 動画のmetaデータから情報取得する
            frame_rate_float = None
            meta_json = json.loads(meta_data)
            if 'streams' in meta_json:
                # commonly stream 0 is the video
                for s in meta_json['streams']:
                    if s['codec_type'] == 'video':
                        if 'r_frame_rate' in s:
                            # 25/1となっている
                            rs = s['r_frame_rate'].split("/")
                            rf = float(rs[0]) / float(rs[1])
                            frame_rate_float = math.ceil(rf)
                        if 'width' in s:
                            original_movie_width = s['width']
                        if 'height' in s:
                            original_movie_height = s['height']

            # リモートのコンテンツを同期させるディレクトリを作成(なければ作成)
            user_dir = user_id
            build_dir = os.path.join(AI_WORKER_BUILD_DIR, "users", user_id)
            if not os.path.exists(build_dir):
                os.mkdir(build_dir)

            # stopかどうか、それ以外はすでに処理をしているのでエラーで返す
            if movie_id in threadCtrl:
                ctrl = threadCtrl[movie_id]
                cmd = ctrl["cmd"]
                if cmd == "stop":
                    mlogger.info("Thread %d stopping." % movie_id)
                    # 停止が指示された
                    mlogger.info("Processing was stopped.")
                    # 削除
                    del threadCtrl[movie_id]
                    # status and log
                    send_response(
                        mlogger,
                        status_data={'activation_key': activation_key, 'movie_id': movie_id, 'status': 'stop', 'status_type': 'movie_analysis', 'status_message': 'stopped', 'log': ''}
                    )

                    # remove build directory
                    shutil.rmtree(build_dir)

                    # return
                    ch.basic_ack(method_frame.delivery_tag)
                    return

                raise Exception("Already running this media process!")

            # idに初期値をセット
            threadCtrl[movie_id] = {"cmd": "none"}

            if video_func(mlogger, activation_key,
                          server_media_root,
                          movie_download_url, movie_upload_url,
                          build_dir, movie_id, user_dir, movie_filename, movie_unique_filename,
                          meta_data, parameters, select_model, threadCtrl) is False:
                # 停止が指示された
                mlogger.info("Processing was stopped.")
                # 削除
                del threadCtrl[movie_id]
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': activation_key, 'movie_id': movie_id, 'status': 'stop', 'status_type': 'movie_analysis', 'status_message': 'stopped', 'log': ''}
                )

                # remove build directory
                shutil.rmtree(build_dir)

                # return
                ch.basic_ack(method_frame.delivery_tag)
                return

            # ==================================
            # 次の処理(JSON解析)へ
            # ==================================
            # JSONファイルをダウンロードさせるURLを作成
            http = "http"
            if "https" in movie_download_url:
                http += "s"
            json_download_url = http + "://" + AI_URL_HOST_ADDRESS_FROM_DOCKER + reverse('api_movie_download_data')

            # AIサーバーでの時限付きactivation keyを作成
            ai_activation_key, expire = get_ai_activation_key(movie_unique_filename)
            # キャッシュにセット
            cache.set(ai_activation_key, True, timeout=expire)

            request_str = {
                "movie_id": movie_id,
                "server_media_root": AI_WORKER_BUILD_DIR,
                "web_activation_key": activation_key,
                "ai_activation_key": ai_activation_key,
                "json_download_url": json_download_url,
                "json_upload_url": movie_upload_url,
                "movie_status_url": status_url,
                "user_id": user_id,
                'fps': frame_rate_float,
                'movie_filename': movie_filename,
                'movie_unique_filename': movie_unique_filename
            }

            credentials = pika.PlainCredentials(RABBIT_ADMIN_NAME, RABBIT_ADMIN_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_SERVER_NAME, credentials=credentials))
            channel = connection.channel()
            # 永続化を指示
            channel.queue_declare(queue=RABBIT_VIOLATION_QUEUE_NAME, durable=True)
            channel.basic_publish(exchange='', routing_key=RABBIT_VIOLATION_QUEUE_NAME,
                                  body=json.dumps(request_str, sort_keys=False, ensure_ascii=False, indent=2),
                                  properties=pika.BasicProperties(delivery_mode=2))  # make message persistent
            connection.close()

            # 削除
            if movie_id in threadCtrl:
                del threadCtrl[movie_id]

            # status and log
            send_response(
                mlogger, status_url,
                status_data={'activation_key': activation_key, 'movie_id': movie_id, 'status': 'next', 'status_type': 'movie_analysis', 'status_message': 'completed', 'log': 'Processing violations'}
            )
            mlogger.info("Processing was successful.")

            # return
            ch.basic_ack(method_frame.delivery_tag)

        except Exception as e:
            mlogger.exception(e)
            mlogger.error("Exception: %s" % e)
            if movie_id is not None and status_url is not None:
                if movie_id in threadCtrl:
                    # 削除
                    del threadCtrl[movie_id]

                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'movie_analysis', 'status_message': 'failed', 'log': str(e)}
                )

            ch.basic_ack(method_frame.delivery_tag)

    else:
        mlogger.info("Channel Empty.")


def thread_api_func(ch, method_frame, body):
    """
    スレッドAPIメソッド
    :param ch:
    :param method_frame:
    :param body:
    :return:
    """
    if method_frame:
        mlogger.info(" [x] API Received %s" % body.decode("utf-8"))
        json_data = json.loads(body.decode("utf-8"))
        try:
            if "cmd" in json_data:
                if "stop" == json_data['cmd']:
                    #
                    # 停止指示
                    # movie_idが渡される
                    #
                    # check
                    if 'id' not in json_data:
                        mlogger.error("[ERROR][" + json_data['cmd'] + "] id parameter is missing. the queue was deleted.\n")
                        ch.basic_ack(method_frame.delivery_tag)
                        return

                    movie_id = json_data['id']
                    mlogger.error("API Received cmd is stop. (movie_id: %s)" % id)
                    threadCtrl[movie_id] = {"cmd": "stop"}  # thread停止命令発行
                    return

            else:
                mlogger.info("API cmd is not own.")

            mlogger.info("API was successful.")

        except Exception as e:
            mlogger.exception(e)
            mlogger.error("Exception: %s" % e)

        finally:
            ch.basic_ack(method_frame.delivery_tag)

    else:
        mlogger.info("API Channel Empty.")


def on_message(ch, method, properties, body):
    """
    Rabbit on message callback function
    :param ch:
    :param method:
    :param properties:
    :param body:
    :return:
    """
    threading.Thread(target=thread_func, args=(ch, method, body)).start()


def on_message_api(ch, method, properties, body):
    """
    Rabbit on message api callback function
    :param ch:
    :param method:
    :param properties:
    :param body:
    :return:
    """
    threading.Thread(target=thread_api_func, args=(ch, method, body)).start()


def api_from_server_queue_start():
    mlogger.info("Connected api queue.")

    api_credentials = pika.PlainCredentials(RABBIT_ADMIN_NAME, RABBIT_ADMIN_PASSWORD)
    api_consume_connection = pika.BlockingConnection(pika.ConnectionParameters(
        RABBIT_SERVER_NAME,
        RABBIT_PORT,
        '/',
        api_credentials,
        heartbeat_interval=60,
        blocked_connection_timeout=300
    ))

    api_consume_channel = api_consume_connection.channel()
    api_consume_channel.queue_declare(queue=API_FS_RABBIT_QUEUE_NAME, durable=True)
    api_consume_channel.basic_qos(prefetch_count=1)

    api_consume_channel.basic_consume(on_message_api, API_FS_RABBIT_QUEUE_NAME)
    try:
        api_consume_channel.start_consuming()
    except KeyboardInterrupt:
        api_consume_channel.stop_consuming()

    api_consume_channel.close()


class LoggerWriter(object):
    def __init__(self, writer):
        self._writer = writer
        self._msg = ''

    def write(self, message):
        self._msg = self._msg + message
        while '\n' in self._msg:
            pos = self._msg.find('\n')
            self._writer(self._msg[:pos])
            self._msg = self._msg[pos+1:]

    def flush(self):
        if self._msg != '':
            self._writer(self._msg)
            self._msg = ''


# --------------------------------------------------
# main
# --------------------------------------------------
# rabbitmqのログを設定
mlogger = logging.getLogger("rabbit_receive")

# create thread control array
threadCtrl = {}


class Command(BaseCommand):
    help = "動画解析をする"

    def handle(self, *args, **options):
        formatter = Formatter('%(levelname)s | %(asctime)s | %(message)s ')
        mlogger.setLevel(INFO)

        # supervisorでwifi offでなぜかエラーになるのでやめた
        # stdout出力
        #sys.stdout = LoggerWriter(mlogger.info)
        # stderr出力
        #sys.stderr = LoggerWriter(mlogger.error)

        # file出力
        file_handler = TimedRotatingFileHandler(filename=os.path.join(LOGGING_PATH, "rabbit_receive_ai.log"), when="D", interval=1, backupCount=10)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(INFO)
        mlogger.addHandler(file_handler)

        credentials = pika.PlainCredentials(RABBIT_ADMIN_NAME, RABBIT_ADMIN_PASSWORD)
        consume_connection = pika.BlockingConnection(pika.ConnectionParameters(
            RABBIT_SERVER_NAME,
            RABBIT_PORT,
            '/',
            credentials,
            heartbeat_interval=60,
            blocked_connection_timeout=300
        ))

        mlogger.info("Connected queue.")

        api_thread = threading.Thread(target=api_from_server_queue_start)
        api_thread.start()

        consume_channel = consume_connection.channel()
        consume_channel.queue_declare(queue=RABBIT_QUEUE_NAME, durable=True)
        consume_channel.basic_qos(prefetch_count=1)
        consume_channel.basic_consume(on_message, RABBIT_QUEUE_NAME)
        try:
            consume_channel.start_consuming()
        except KeyboardInterrupt as e:
            mlogger.info("Catch KeyboardInterrupt.")

        consume_channel.stop_consuming()
        consume_channel.close()
        os.kill(os.getpid(), signal.SIGKILL)
