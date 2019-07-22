# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    違反判定をしてDBに書き込みをする

"""
import json
import logging
import os
import signal
import threading
from logging import Formatter, INFO
from logging.handlers import TimedRotatingFileHandler
import io

import pika
import requests
from django.core.management.base import BaseCommand
from requests import Timeout

from app_ai.management.config.define_violations import VIOLATION_WORKER_BUILD_DIR, RABBIT_ADMIN_NAME, RABBIT_ADMIN_PASSWORD, RABBIT_SERVER_NAME, \
    RABBIT_PORT, API_FS_RABBIT_VIOLATION_QUEUE_NAME, VIOLATION_LOGGING_PATH, RABBIT_VIOLATION_QUEUE_NAME
from app_ai.management.lib.lib_common import send_response
from app_ai.management.lib.violations.lib_jsontodb import LibDbJsonClass

from app_ai.management.lib.violations.lib_violation_processing import ViolationProcessingClass


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
        web_activation_key = None
        status_url = None

        mlogger.info(" [x] Received %s" % body.decode("utf-8"))
        json_data = json.loads(body.decode("utf-8"))
        try:
            # check parameter
            if 'movie_id' not in json_data:
                mlogger.error("[ERROR] id parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            movie_id = json_data['movie_id']

            if 'web_activation_key' not in json_data:
                mlogger.error("[ERROR] web_activation_key parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            web_activation_key = json_data['web_activation_key']

            if 'ai_activation_key' not in json_data:
                mlogger.error("[ERROR] ai_activation_key parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            ai_activation_key = json_data['ai_activation_key']

            if 'movie_status_url' not in json_data:
                mlogger.error("[ERROR] movie_status_url parameter is missing. the queue was deleted.\n")
                ch.basic_ack(method_frame.delivery_tag)
                return
            status_url = json_data['movie_status_url']

            # check parameter
            if 'server_media_root' not in json_data\
                    or 'json_download_url' not in json_data\
                    or 'json_upload_url' not in json_data\
                    or 'user_id' not in json_data\
                    or 'fps' not in json_data\
                    or 'movie_filename' not in json_data\
                    or 'movie_unique_filename' not in json_data:
                mlogger.error("[ERROR] parameter error.")
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data = {'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'violations', 'status_message': 'Parameter Error', 'log': 'Parameter Error'}
                )

                ch.basic_ack(method_frame.delivery_tag)
                return

            server_media_root = json_data['server_media_root']  # AIサーバー
            json_download_url = json_data['json_download_url']  # AIサーバー
            json_upload_url = json_data['json_upload_url']  # WEBサーバー
            user_id = json_data['user_id']
            movie_id = json_data['movie_id']
            fps = json_data['fps']
            movie_filename = json_data['movie_filename']
            movie_unique_filename = json_data['movie_unique_filename']

            unique_id, ext = os.path.splitext(movie_unique_filename)
            user_dir = user_id
            json_dir = os.path.join(VIOLATION_WORKER_BUILD_DIR, "users", user_dir)
            json_filename = unique_id + ".json.final"
            json_path = os.path.join(json_dir, json_filename)

            # ===============================
            # JSONファイルをダウンロードする
            # ===============================
            mlogger.info("Downloading from %s" % json_download_url)
            try:
                payload = {
                    'activation_key': ai_activation_key,
                    "path": os.path.join(server_media_root, "users", user_dir),
                    "filename": json_filename,
                    "delete_activation_key": True
                }
                r = requests.get(json_download_url, params=payload)
                if r.status_code != 200:
                    mlogger.error("JSON file failed to download.")
                    send_response(
                        mlogger, status_url,
                        status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'violations', 'status_message': 'File Error', 'log': 'Failed to download JSON'}
                    )
                    ch.basic_ack(method_frame.delivery_tag)
                    return

            except Timeout:
                mlogger.error("Download json timeout.")
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'violations', 'status_message': 'File Error', 'log': 'Download json timeout.'}
                )

                ch.basic_ack(method_frame.delivery_tag)
                return

            with open(json_path, "wb") as fd:
                fd.write(r.content)

            # ===============================
            # stopかどうか、それ以外はすでに処理をしているのでエラーで返す
            # ===============================
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
                        mlogger, status_url,
                        status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'stop', 'status_type': 'violations', 'status_message': 'stopped', 'log': ''}
                    )

                    # return
                    ch.basic_ack(method_frame.delivery_tag)
                    return

                raise Exception("Already running this media process!")

            # idに初期値をセット
            threadCtrl[movie_id] = {"cmd": "none"}

            # ===============================
            # jsontodb
            # ===============================
            mlogger.info("Jsontodb...")
            rarr = {
                "user_movie_id": movie_id,
                "movie_filename": movie_filename,
                "movie_unique_filename": movie_unique_filename,
                "s_fno": 0,
                "e_fno": 1000000000000,  # 最後まで。ここまではフレームがないだろう
            }
            rarray = [rarr]
            libdb_cls = LibDbJsonClass()
            if libdb_cls.set_json_to_db_frames(fps, json_path, rarray, movie_id, threadCtrl) is False:
                # 停止が指示された
                mlogger.info("Processing was stopped.")
                # 削除
                del threadCtrl[movie_id]
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'stop', 'status_type': 'violations', 'status_message': 'stopped', 'log': ''}
                )

                # return
                ch.basic_ack(method_frame.delivery_tag)
                return

            # ===============================
            # 不安全運転解析
            # ===============================
            mlogger.info("Create violations...")
            violation_cls = ViolationProcessingClass(mlogger)
            violation_cls.analysis(movie_id)

            # ===============================
            # upload analysis json to web remote host
            # ===============================
            mlogger.info("upload result json to remote")

            unique_id, ext = os.path.splitext(movie_unique_filename)
            out_json_filename = unique_id + "_violations.json"
            buf = io.StringIO()
            buf.write(json.dumps(violation_cls.results, ensure_ascii=False))
            buf.seek(0)
            data = {'activation_key': web_activation_key, "filename": out_json_filename}
            file = {'datafile': buf}
            try:
                ret = requests.post(json_upload_url, data=data, files=file)
                mlogger.info("ret = %d, %s" % (ret.status_code, ret.text))
                if r.status_code != 200:
                    mlogger.error("Failed to upload violations json.")
                    send_response(
                        mlogger, status_url,
                        status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'violations', 'status_message': 'File Error', 'log': 'Failed to upload violations json'}
                    )
                    ch.basic_ack(method_frame.delivery_tag)
                    return
            except Timeout:
                mlogger.error("Download json timeout.")
                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'violations', 'status_message': 'File Error', 'log': 'Upload violations json timeout.'}
                )

                ch.basic_ack(method_frame.delivery_tag)
                return

            # 削除
            if movie_id in threadCtrl:
                del threadCtrl[movie_id]

            mlogger.info("Processing was successful.")
            # status and log
            send_response(
                mlogger, status_url,
                status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'success', 'status_type': 'violations', 'status_message': 'completed', 'log': ''}
            )

            # return
            ch.basic_ack(method_frame.delivery_tag)

        except Exception as e:
            mlogger.exception(e)
            mlogger.error("Exception: %s" % e)
            if movie_id is not None and status_url is not None:
                if movie_id in threadCtrl and status_url is not None and web_activation_key is not None:
                    # 削除
                    del threadCtrl[movie_id]

                # status and log
                send_response(
                    mlogger, status_url,
                    status_data={'activation_key': web_activation_key, 'movie_id': movie_id, 'status': 'failed', 'status_type': 'violations', 'status_message': 'failed', 'log': str(e)}
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
    api_consume_channel.queue_declare(queue=API_FS_RABBIT_VIOLATION_QUEUE_NAME, durable=True)
    api_consume_channel.basic_qos(prefetch_count=1)

    api_consume_channel.basic_consume(on_message_api, API_FS_RABBIT_VIOLATION_QUEUE_NAME)
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
mlogger = logging.getLogger("rabbit_receive_violations")
# mlogger.propagate = False

# create thread control array
threadCtrl = {}


class Command(BaseCommand):
    help = "違反判定をしてDBに書き込みをする"

    def handle(self, *args, **options):
        formatter = Formatter('%(levelname)s | %(asctime)s | %(message)s ')
        mlogger.setLevel(INFO)

        # file出力
        file_handler = TimedRotatingFileHandler(filename=os.path.join(VIOLATION_LOGGING_PATH, "rabbit_receive_violations.log"), when="D", interval=1, backupCount=10)
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
        consume_channel.queue_declare(queue=RABBIT_VIOLATION_QUEUE_NAME, durable=True)
        consume_channel.basic_qos(prefetch_count=1)
        consume_channel.basic_consume(on_message, RABBIT_VIOLATION_QUEUE_NAME)
        try:
            consume_channel.start_consuming()
        except KeyboardInterrupt as e:
            mlogger.info("Catch KeyboardInterrupt.")

        consume_channel.stop_consuming()
        consume_channel.close()
        os.kill(os.getpid(), signal.SIGKILL)
