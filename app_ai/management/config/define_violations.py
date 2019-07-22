# -*- coding: utf-8 -*-
"""
  Common parameters
"""

# Rabbit MQ info
import os

from config.settings import BASE_DIR

RABBIT_SERVER_NAME = 'localhost'
RABBIT_PORT = 5672
RABBIT_ADMIN_NAME = 'admin'
RABBIT_ADMIN_PASSWORD = 'admin'
# API from backend to web
API_RABBIT_VIOLATION_QUEUE_NAME = 'dashcam-worker-violation-api'
# API from web to backend
API_FS_RABBIT_VIOLATION_QUEUE_NAME = 'dashcam-worker-violation-api-fs'
RABBIT_VIOLATION_QUEUE_NAME = 'dashcam-worker-violation-data'

# dockerで動かす場合は、マウントした/mnt
VIOLATION_WORKER_BUILD_DIR = "/data/docker_irric"

# LOGファイルのパス
VIOLATION_LOGGING_PATH = os.path.join(BASE_DIR, "logs")

# 環境切り替え
try:
    from development import *
except ImportError:
    pass
