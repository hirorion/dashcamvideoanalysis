# -*- coding: utf-8 -*-
"""
  Common parameters
"""

# Rabbit MQ info
import os

from config.settings import BASE_DIR

# JSON DOCKERから接続してほしいこのサーバーのIPを記述  # TODO ポート番号を自動的にしないと大変かも
AI_URL_HOST_ADDRESS_FROM_DOCKER = "172.20.0.101:8000"

RABBIT_SERVER_NAME = 'localhost'
RABBIT_PORT = 5672
RABBIT_ADMIN_NAME = 'admin'
RABBIT_ADMIN_PASSWORD = 'admin'
RABBIT_QUEUE_NAME = 'dashcam-ai-data'
# API from backend to web
API_RABBIT_QUEUE_NAME = 'dashcam-ai-api'
# API from web to backend
API_FS_RABBIT_QUEUE_NAME = 'dashcam-ai-api-fs'

# dockerで動かす場合は、マウントした/mnt
AI_WORKER_BUILD_DIR = "/data/docker_irric"
# ホストのdockerから利用されるのでホストにディレクトリ
AI_DOCKER_BUILD_DIR = "/data/docker_irric"

# 各種処理を実行するバッチスクリプト
TRACKING_BAT_PATH = "tracking_no_sudo.sh"

# DOCKER USER (このスクリプトの起動ユーザーとdocker buildしたときに指定したuserと合わせないとだめ）
DOCKER_USER = "mitsui"
# CONTAINER NAMES
CONTAINER_NAMES = "dashcam/ai:1.0-dev"

# LOGファイルのパス
LOGGING_PATH = os.path.join(BASE_DIR, "logs")

# 環境切り替え
try:
    from development import *
except ImportError:
    pass
