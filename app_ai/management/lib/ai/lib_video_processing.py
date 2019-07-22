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

import requests
from requests import Timeout

from app_ai.management.config.define_ai import TRACKING_BAT_PATH, DOCKER_USER, AI_DOCKER_BUILD_DIR, CONTAINER_NAMES
from app_ai.management.lib.lib_recev_api_from_mq import recv_api_action_stop
from config.settings import BASE_DIR


def video_func(logger, activation_key,
               server_media_root,
               movie_download_url, movie_upload_url, build_dir, movie_id, user_dir,
               movie_filename, movie_unique_filename, meta_data, parameters_json, select_model, thread_ctrl):
    """
    Processing video
    :param logger:
    :param activation_key:
    :param server_media_root:
    :param movie_download_url:
    :param movie_upload_url:
    :param build_dir:
    :param movie_id:
    :param user_dir:
    :param movie_filename:
    :param movie_unique_filename:
    :param meta_data:
    :param parameters_json:
    :param select_model:
    :param thread_ctrl:
    :return: true/false true 停止
    """

    # Download data from S3 or HOST
    logger.info("Downloading from %s" % movie_download_url)
    input_movie_prefix, ext = os.path.splitext(movie_unique_filename)
    input_movie_filename = movie_unique_filename
    input_movie_path = os.path.join(build_dir, movie_unique_filename)
    # remote host
    try:
        payload = {
            'activation_key': activation_key,
            "path": os.path.join(server_media_root, user_dir),
            "filename": input_movie_filename}
        r = requests.get(movie_download_url, params=payload)
    except Timeout:
        logger.error("Download timeout.")
        return False

    with open(input_movie_path, "wb") as fd:
        fd.write(r.content)

    # is stop?
    if recv_api_action_stop(thread_ctrl, movie_id):
        return False

    # 実行しているtrackingがある場合は停止
    try:
        pid_path = os.path.join(build_dir, ".tracking.pid")
        if os.path.exists(pid_path):
            with open(pid_path, "r") as f:
                ppid = f.read()
            os.kill(int(ppid), signal.SIGTERM)
            os.remove(pid_path)
    except:
        logger.warn("passed kill process")
        pass

    # hostのdockerを起動して実行
    # ex) docker run --rm -e CUR_USER_NAME=edw -e USER_DIR='xxxx' -e MOVIE_PREFIX='movie2' -e MOVIE_FILENAME='movie2.mov' -e CAMERA_TYPE='KENWOOD_DRV-830_1920x1080_27fps' -e CAMERA_HEIGHT='1.0' -e START_FNO=0 -e END_FNO=10000000 -v /data/docker_irric/:/mnt/ --runtime=nvidia  dashcam-ai-dev:1.0,
    cmd = "%s %s \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" %d  %d %s \"%s\""
    cmd = cmd % (
        os.path.join(BASE_DIR, "app_ai", "management", "sub_sh", TRACKING_BAT_PATH),
        DOCKER_USER,
        user_dir,
        input_movie_prefix,
        input_movie_filename,
        parameters_json['camera_type'],
        parameters_json['camera_height'],
        parameters_json['start_fno'],
        parameters_json['end_fno'],
        AI_DOCKER_BUILD_DIR,
        CONTAINER_NAMES
    )
    logger.info("Performing tracking and speed estimation and writing out final movie: %s" % cmd)

    fd, tmp_filename = tempfile.mkstemp()
    with open(tmp_filename, 'w') as tmpf:
        proc = subprocess.Popen(cmd, shell=True, stdout=tmpf, stderr=subprocess.STDOUT)
        ppid = proc.pid
        # あとでこのプロセスを強制的に殺せるようにppidを保存する
        pid_path = os.path.join(build_dir, ".tracking.pid")
        with open(pid_path, "w") as f:
            f.write(str(ppid))

        ret = proc.poll()
        while ret is None:
            logger.debug("poll")
            sleep(0.5)
            ret = proc.poll()
            if ret is not None:
                tmpf.close()
                os.close(fd)
                break
            logger.debug("===== poll done")

            # is stop?
            if recv_api_action_stop(thread_ctrl, movie_id):
                logger.info("------- tracking.sh was killed!!")
                os.kill(int(ppid), signal.SIGTERM)
                os.remove(pid_path)
                return False

    with open(tmp_filename, 'r') as tmpf:
        log_contents = tmpf.read()
        logger.info(log_contents)

    os.remove(pid_path)

    # check error
    logger.info("====== shell ret = %d" % ret)
    if ret != 0:
        raise Exception("Exit shell script on error!")

    logger.info("...done.")

    # is stop?
    if recv_api_action_stop(thread_ctrl, movie_id):
        return False

    logger.info("...done.")

    # upload annotated video to remote host
    logger.info("upload labeled.mp4 to remote host")
    output_filename = input_movie_prefix + "_labeled.mp4"
    output_movie_name = os.path.join(build_dir, output_filename)
    data = {'activation_key': activation_key, "filename": output_filename}
    file = {'datafile': open(output_movie_name, 'rb')}
    try:
        ret = requests.post(movie_upload_url, data=data, files=file)
        logger.info("ret = %d, %s" % (ret.status_code, ret.text))
        if r.status_code != 200:
            logger.error("Failed to upload movie.")
            return False
    except Timeout:
        logger.error("Movie upload timeout")
        return False
    r = json.loads(ret.text)
    if "result" in r and r['result'] == "NG":
        logger.error("ret = NG")
        return False
    if "movie_id" in r and r['movie_id'] != str(movie_id):
        logger.error("movie_id is different. %s: %s" % (r['movie_id'], str(movie_id)))
        return False

    logger.info("...done.")

    # is stop?
    if recv_api_action_stop(thread_ctrl, movie_id):
        return False

    return True
