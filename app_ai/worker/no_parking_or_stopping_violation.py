# -*- coding: utf-8 -*-
"""
    駐停車禁止場所での駐車 検出クラス
"""
import json
import logging

import numpy as np
from django.db.models import Sum

from app_ai.models import AiFrameInfo, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.no_parking_violation import NoParkingViolationClass
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class NoParkingOrStoppingViolationClass(NoParkingViolationClass):
    """
    駐停車禁止場所での駐車での駐車
    """

    def __init__(self):
        super().__init__()

    def get_violations(self):
        output = {
            "group": "その他",
            "category": "駐停車禁止場所での駐車",
            "violations": self.violations
        }
        return output

    def get_no_parking_hyoushiki(self, movie_id, start_fno, end_fno):
        """
        指定範囲の駐停車禁止の標識のフレームを抜き出す
        fnoは大きい順になっている
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'hyoshikireg-no_stopping' and score >= 0.700000) and speed >=0 and movie_id=%d and fno >= %d and fno < %d order by movie_id, fno" % (movie_id, start_fno, end_fno)

        return AiFrameObject.objects.raw(sql)

    def get_no_parking_hyouji(self, movie_id, start_fno, end_fno):
        """
        指定範囲の駐停車禁止の標示(lr)のフレームを抜き出す(5.5m以内)
        fnoは大きい順になっている
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'curb-yellow_solid-lr' and score >= 0.700000 and ((data->'pose3'->>0)::float < 5.5)) ) and speed >=0 and movie_id=%d and fno >= %d and fno < %d order by movie_id, fno" % (movie_id, start_fno, end_fno)

        return AiFrameObject.objects.raw(sql)

    def get_oudan_hodou_under_5m(self, movie_id, start_fno, end_fno):
        """
        指定範囲の距離が5m以内の横断歩道を抜き出す
        fnoは大きい順になっている
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'hyoji-hodou' and score >= 0.700000 and ((data->'pose3'->>0)::float <= 5.0)) ) and speed >=0 and movie_id=%d and fno >= %d and fno < %d order by movie_id, fno" % (movie_id, start_fno, end_fno)

        return AiFrameObject.objects.raw(sql)

    def get_stop_line_under_5m(self, movie_id, start_fno, end_fno):
        """
        指定範囲の距離が5m以内の停止線を抜き出す
        fnoは大きい順になっている
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'hyoji-stop_line' and score >= 0.700000 and ((data->'pose3'->>0)::float <= 5.0)) ) and speed >=0 and movie_id=%d and fno >= %d and fno < %d order by movie_id, fno" % (movie_id, start_fno, end_fno)

        return AiFrameObject.objects.raw(sql)


    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行
        ai = AiFrameInfo.objects.filter(movie_id=movie_id).order_by("fno")
        org_start_fno = ai[0].fno

        # 10秒以上停止しているフレームリスト
        stop_frames = self.get_speed_zero_frames(movie_id, 10)
        if len(stop_frames) > 0:
            for sfrm in stop_frames:
                start_fno = sfrm["start"]
                end_fno = sfrm["end"]
                self.set_start_fno(start_fno)
                self.set_last_fno(end_fno)
                self.safety_flag = False
                self.fix()

            '''
            # 交差点のフレーム
            isec_nparr = np.array(self.get_intersection_start_frames(movie_id))
            if len(isec_nparr):
                is_no_paking_or_stopping = False
                for sfrm in stop_frames:
                    start_fno = sfrm["start"] + org_start_fno
                    end_fno = sfrm["end"] + org_start_fno

                    # 最初の交差点まで戻って駐停車禁止標識を見つける
                    isec_end_fno = self.find_nearest_less_than(isec_nparr, start_fno)
                    # その間に駐停車禁止標識があるかどうか
                    obj_list = self.get_no_parking_hyoushiki(movie_id, isec_end_fno, start_fno)
                    if len(obj_list) > 0:  # TODO 標識が一つでもあればOK
                        # 標識があった
                        is_no_paking_or_stopping = True

                    else:
                        # 先の交差点まで進んで駐車禁止標識を見つける
                        isec_end_fno = self.find_nearest_greater_than(isec_nparr, end_fno)
                        # その間に駐停車禁止標識があるかどうか
                        obj_list = self.get_no_parking_hyoushiki(movie_id, start_fno, isec_end_fno)
                        if len(obj_list) > 0:  # TODO 標識が一つでもあればOK
                            # 標識があった
                            is_no_paking_or_stopping = True

                    if is_no_paking_or_stopping is False:
                        # 駐停車禁止標示をチェック
                        # 2m手前のフレームから停止位置まで  TODO 逆上るフレームの距離が5mになっている, 5秒前からその距離を見つけようとしている
                        prev_start_fno = self.get_prev_positon_by_meter(movie_id, self.PREV_PLAY_BACK_METER, start_fno - self.MOVIE_FPS * 5, start_fno)
                        obj_list = self.get_no_parking_hyouji(movie_id, prev_start_fno, start_fno)
                        if len(obj_list) > 0:  # TODO 標示が一つでもあればOK
                            # 標識があった
                            is_no_paking_or_stopping = True

                    if is_no_paking_or_stopping:
                        # 距離が5m以下の横断歩道探す
                        obj_list = self.get_oudan_hodou_under_5m(movie_id, start_fno, end_fno)
                        if obj_list.count() > 0:
                             break
            '''

        # フレームがつながっているものをつなげた違反動画を作成
        new_vio = []
        vio_arr = {
            "start_fno": self.violations[0]["start_fno"],
            "last_fno": self.violations[0]["last_fno"]
        }
        for vio in self.violations[1:]:
            if vio_arr["last_fno"] == vio["start_fno"] - 1:
                vio_arr["last_fno"] = vio["last_fno"]
            else:
                new_vio.append(vio_arr)
                vio_arr = {
                    "start_fno": vio["start_fno"],
                    "last_fno": vio["last_fno"]
                }

        # 最後の分を更新
        new_vio.append(vio_arr)

        self.violations = new_vio

        for vio in self.violations:
            vio["start_fno"] = vio["start_fno"] - org_start_fno
            vio["last_fno"] = vio["last_fno"] - org_start_fno

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

