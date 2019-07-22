# -*- coding: utf-8 -*-
"""
    apps.bashboard.upload_mixin

    @author: $Author$
    @version: $Id: api.py bb216bf874cd 2013/11/11 11:28:58 jxtreme $

"""
import glob
import json
import logging
import os
import subprocess
import threading
import unicodedata
import uuid
from datetime import datetime

import pika
import pytz
from django.shortcuts import get_object_or_404
from pika.exceptions import AMQPConnectionError

from app_admin.models.movie_models import UserMovie
from config.settings import FFPROBE, USE_CONVERT_AVI, FFMPEG, MEDIA_ROOT, RABBIT_ID, RABBIT_PASSWORD, RABBIT_CONNECTION_HOST, RABBIT_QUEUE_NAME_API

logger = logging.getLogger(__name__)


#
# Command line use of 'ffprobe':
#
# ffprobe -loglevel quiet -print_format json \
#         -show_format    -show_streams \
#         video-file-name.mp4
#
# man ffprobe # for more information about ffprobe
#


def probe(vid_file_path):
    """ Give a json from ffprobe command line

    @vid_file_path : The absolute (full) path of the video file, string.
    """
    if type(vid_file_path) != str:
        raise Exception('Give ffprobe a full file path of the video')

    command = [FFPROBE,
            "-loglevel",  "quiet",
            "-print_format", "json",
             "-show_format",
             "-show_streams",
             vid_file_path
             ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    return json.loads(out.decode('utf-8'))


def get_meta_data(vid_file_path):
    """
    メタ情報を取得
    :param vid_file_path:
    :return: json
    """
    _json = probe(vid_file_path)
    return _json


def mv_creation_time(_json):
    """
    Video's or Audio's duration in seconds, return a float number
    :param _json:
    :return: datetime object
    """
    try:
        if 'format' in _json:
            if 'tags' in _json['format']:
                if 'creation_time' in _json['format']['tags']:
                    creation_time = _json['format']['tags']['creation_time']
                    dt = datetime.strptime(creation_time, '%Y-%m-%dT%H:%M:%S.%fZ')
                    dt = pytz.utc.localize(dt).astimezone(pytz.timezone("Asia/Tokyo"))
                    return dt

        # if everything didn't happen,
        # we got here because no single 'return' in the above happen.
        return None

    except Exception as e:
        return None


def duration(_json):
    """
    Video's or Audio's duration in seconds, return a float number
    :param _json:
    :return: a float number
    """
    try:
        if 'format' in _json:
            if 'duration' in _json['format']:
                return float(_json['format']['duration'])

        if 'streams' in _json:
            # commonly stream 0 is the video
            for s in _json['streams']:
                if 'duration' in s:
                    return float(s['duration'])

        # if everything didn't happen,
        # we got here because no single 'return' in the above happen.
        return 0

    except Exception as e:
        # if everything didn't happen,
        # we got here because no single 'return' in the above happen.
        return 0


def detecting_type(_json):
    """
    アップロードされたメディアのタイプを取得
    :param _json:
    :return: audio/video
    """
    """ detecting if media is video
    """
    if 'streams' in _json:
        # commonly stream 0 is the video
        for s in _json['streams']:
            if 'codec_type' in s:
                if s['codec_type'] == 'video':
                    return 'video'
    return 'audio'


def detecting_fps(_json):
    """
    動画のFPSを取得
    :param _json:
    :return: fps
    """
    if 'streams' in _json:
        # commonly stream 0 is the video
        for s in _json['streams']:
            if 'codec_type' in s:
                if s['codec_type'] == 'video' and 'r_frame_rate' in s:
                    return s['r_frame_rate']

    # if everything didn't happen,
    # we got here because no single 'return' in the above happen.
    return "1/27"
    #raise Exception('No found fps')


def detecting_video_size(_json):
    """
    動画のサイズを取得
    :param _json:
    :return: width, height
    """
    if 'streams' in _json:
        # commonly stream 0 is the video
        for s in _json['streams']:
            if s['codec_type'] == 'video' and 'width' in s and 'height' in s:
                return s['width'], s['height']

    # if everything didn't happen,
    # we got here because no single 'return' in the above happen.
    raise Exception('No found video size')


def detecting_format_name(_json):
    """
    アップロードされたメディアのフォーマットを取得
    :param _json:
    :return: audio/video
    """
    """ detecting if media is video
    """
    if 'format' in _json:
        if 'format_name' in _json['format']:
            return _json['format']['format_name']

    raise Exception('No found format name')


class UploadDataMixin(object):
    """
    アップロードされた音声データ管理
    """

    def _savedir(self, user):
        """ 保存する先のディレクトリを取得 """
        return '/'.join([MEDIA_ROOT, user.username])

    def _create_unique_id(self, user):
        """
        ユニークなIDを生成する
        :param user:
        :return: 重複しないユニークID
        """
        while 1:
            path = uuid.uuid4().hex
            if UserMovie.objects.filter(user=user, unique_filename=path).count() > 0:
                continue
            break
        return path

    def get_save_path(self, user, ext):
        """
        保存ファイル名をパス付きと無しで取得
        :param user:
        :param ext:
        :return: 保存パス
        """
        unique_id = self._create_unique_id(user)
        return self._savedir(user) + '/' + unique_id + ext, unique_id

    def get_ext(self, filename):
        """
        拡張子を取得
        :param filename:
        :return: ファイル名, 拡張子
        """
        fn, ext = os.path.splitext(filename)
        return fn, ext

    def delete_temp_file(self, user, path):
        """
        保存ファイルを削除
        :param user:
        :param path:
        :return: なし
        """
        fn, ext = self.get_ext(path)
        path = os.path.join(self._savedir(user), fn) + "*"
        path_list = glob.glob(path)
        for p in path_list:
            if p and os.path.exists(p):
                os.remove(p)


class UploadMovieDataMixin(UploadDataMixin):

    def save_upload_files_and_save_db(self, user):
        """
        POSTされたメタ情報をDBに保存し、必要な情報を返す
        *主にWEBからのアップロードに使われる
        :param user:
        :return:
        """

        # 保存先のチェック
        if not os.path.isdir(self._savedir(user)):
            os.makedirs(self._savedir(user))

        save_filename = None
        try:
            # メタ情報はまだ未実装
            # notes = self.request.POST.get('notes', None)
            upload_file = self.request.FILES.get('datafile', None)

            # エラーチェック
            if upload_file is None:
                return None

            # MACのファイル名濁点を解決
            upload_filename = unicodedata.normalize("NFC", upload_file.name)

            # 拡張子取得
            fn, ext = self.get_ext(upload_filename)

            # アップロードされたデータを置くためのファイル名を作成
            save_path, unique_id = self.get_save_path(user, ext)
            save_filename = unique_id + ext
            # アップロードされたデータを分割して読み込んで保存する
            with open(save_path, 'wb+') as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)

            # ffprobeの情報を取得
            try:
                json_meta_data = get_meta_data(save_path)
            except Exception as e:
                logger.exception(e)
                raise Exception("file is invalid")

            if json_meta_data is None:
                raise Exception("json is None: %s" % save_path)
            logger.debug("save_path = %s, ffprobe json = %s" % (save_path, json_meta_data))

            # データの長さを取得
            len_secs = duration(json_meta_data)
            length = int(len_secs)  # str(datetime.timedelta(seconds=len_secs))

            # 撮影日
            driving_date = mv_creation_time(json_meta_data)

            # videoかどうか取得
            media_type = detecting_type(json_meta_data)
            if media_type != "video":
                raise Exception("media type is not Video!")

            # dbに情報を登録
            movie_id = self.save_to_db(user, path=save_filename, filename=upload_filename, length=length, driving_date=driving_date, media_type=media_type, meta_data=json.dumps(json_meta_data))

            request_str = {
                "cmd": "create_preview_and_change_avi",
                "movie_id": movie_id,
                "user_id": user.id,
            }

            # AVIファイルの場合は変換する
            format_name = detecting_format_name(json_meta_data)
            if USE_CONVERT_AVI and "avi" in format_name:
                request_str.update({
                    "avi": 1
                })

            # サムネイルとAVIの変換をワーカーに依頼する
            try:
                credentials = pika.PlainCredentials(RABBIT_ID, RABBIT_PASSWORD)
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=RABBIT_CONNECTION_HOST, credentials=credentials))
                channel = connection.channel()
                # 永続化を指示
                channel.queue_declare(queue=RABBIT_QUEUE_NAME_API, durable=True)
                channel.basic_publish(exchange='', routing_key=RABBIT_QUEUE_NAME_API,
                                      body=json.dumps(request_str, sort_keys=False, ensure_ascii=False, indent=2),
                                      properties=pika.BasicProperties(delivery_mode=2))  # make message persistent
                connection.close()
            except AMQPConnectionError as e:
                logger.warning(e)

            return unique_id

        except Exception as e:
            # エラーの場合ファイルを削除する add by mitsui 2018.6.28
            if save_filename is not None:
                self.delete_temp_file(user, save_filename)
            logger.exception(e)
            return None
