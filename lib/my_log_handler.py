# -*- coding: UTF-8 -*-
import logging
import logging.handlers
import os


class GroupWriteRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    グループ書き込み権限付きログローテート
    """
    def _open(self):
        prevumask = os.umask(0o002)
        #os.fdopen(os.open('/path/to/file', os.O_WRONLY, 0600))
        rtv = logging.handlers.TimedRotatingFileHandler._open(self)
        os.umask(prevumask)
        return rtv
