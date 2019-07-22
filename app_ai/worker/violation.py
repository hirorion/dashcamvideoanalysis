# -*- coding: utf-8 -*-
"""
    危険運転を検出クラスのベース
"""
import logging
import sys
from abc import abstractmethod

logger = logging.getLogger(__name__)


class ViolationWorkerClass(object):

    def __init__(self):
        self.start_fno = 0
        self.last_fno = 0
        self.checked_objects = dict()
        self.safety_flag = True
        self.violations = list()

    def fix(self):
        logger.info("##### fixed and reset status")

        if self.safety_flag is False:
            dat = {
                "start_fno": self.get_start_fno(),
                "last_fno": self.get_last_fno()
            }
            self.violations.append(dat)

        self.start_fno = 0
        self.last_fno = 0
        self.checked_objects = dict()
        self.safety_flag = True

    def get_checked_objects(self):
        return self.checked_objects

    def set_checked_objects(self, status_tag, fno):
        if status_tag not in self.checked_objects:
            arr = [fno]
            self.checked_objects[status_tag] = arr
        else:
            arr = self.checked_objects[status_tag]
            arr.append(fno)

    def get_start_fno(self):
        return self.start_fno

    def get_last_fno(self):
        return self.last_fno

    def set_start_fno(self, fno):
        self.start_fno = fno

    def set_last_fno(self, fno):
        # 通過点を推測する
        # TODO 過去の認識結果の距離の差分を使って計算する
        self.last_fno = fno

    @abstractmethod
    def get_violations(self):
        raise NotImplementedError(sys._getframe().f_code.co_name)

    @abstractmethod
    def worker(self, movie_id):
        raise NotImplementedError(sys._getframe().f_code.co_name)
