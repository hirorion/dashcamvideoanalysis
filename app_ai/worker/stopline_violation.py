# -*- coding: utf-8 -*-
"""
    一時停止違反を見つける検出クラス
"""
import json
import logging

from django.db.models import Max

from app_ai.models import AiFrameInfo, AiFrameObjectTags, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class StopLineViolationClass(Detections, ViolationWorkerClass):
    """
    一時停止違反を見つける
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27.0
    CHECK_SCORE = 0.9
    # 実際の車線通過位置を見つけるために今は1.5秒のフレームを追加してチェックしている
    AFTER_CHECK_FRAMES = 40

    def __init__(self):
        super().__init__()

    def get_violations(self):
        output = {
            "group": "一時停止",
            "category": "一時停止手前での不停止",
            "violations": self.violations
        }
        return output

    def get_stop_hyoujiki_or_stop_hyouji(self, movie_id):
        """
        止まれ標識、止まれ標示があることが前提のフレームをすべて抜き出す(TODO 0.9じゃないと難しい）
        :param movie_id:
        :return: RawQuerySet
        """
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'hyoji-stop' and score >= 0.900000 ) or bool_or(data->'tags' ? 'hyoshikireg-stop' and score >= 0.900000 ) ) and speed >= 0 and movie_id=%d order by movie_id, fno" % movie_id

        obj_list = AiFrameInfo.objects.raw(sql)

        return obj_list

    def get_stop_line(self, movie_id, start_fno, end_fno):
        """
        指定範囲の停止線のフレームをすべて抜き出す
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet
        """
        obj_list = AiFrameObject.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, tag="hyoji-stop_line", score__gte=0.9).order_by("fno")

        return obj_list

    def get_last_fno_stop_line(self, movie_id, start_fno, end_fno):
        """
        指定範囲の停止線のフレームの一番最後を抜き出す
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: RawQuerySet / ない場合はNone
        """
        max_fno = AiFrameObject.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, tag="hyoji-stop_line", score__gte=0.9).aggregate(Max('fno'))

        return max_fno["fno__max"]

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        # 止まれ標示、とまれ標識のフレームを抜き出す
        obj_list = self.get_stop_hyoujiki_or_stop_hyouji(movie_id)

        check_arr = {}
        for fm in obj_list:
            check_arr[fm.fno] = True

        is_start = True
        fno_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        start_fno = 0
        for obj_fno in range(1, fno_count):

            if is_start:
                # 入り口を見つける
                start = self.check_object_appears_more_than_once(check_arr, obj_fno, obj_fno + 3)
                if start >= 0:
                    is_start = False
                    start_fno = obj_fno
            else:
                # 開始位置から出口を見つける  TODO 見つけてる最中に動画が終了したどうする？
                # TODO 1秒間見つけられなかったら出口にしている
                end_fno = self.check_object_not_appear(check_arr, obj_fno, obj_fno + 27)
                if end_fno >= 0:
                    is_start = True

                    # このフレーム間に停止線があるかどうかチェック
                    #stop_frames = self.get_stop_line(movie_id, start_fno, end_fno)
                    #if len(stop_frames) == 0:
                        # 停止線がないのでべつものを停止線に設定
                    #    pass
                    #else:

                    # 一番遠いオブジェクトを通過するフレームを検出
                    #fnum = self.calc_last_fno(movie_id, end_fno, stop_frames, "pose3", self.MOVIE_FPS)
                    #logger.debug("#### fnum = %d" % fnum)

                    max_fno = self.get_last_fno_stop_line(movie_id, start_fno, end_fno)
                    if max_fno is None:
                        # TODO 停止線がないのでべつものを停止線に設定
                        continue
                    fnum = self.get_past_positon_by_meter(movie_id, 5, max_fno, max_fno + self.MOVIE_FPS * 3)

                    self.safety_flag = False
                    self.set_start_fno(start_fno)
                    self.set_last_fno(fnum)
                    self.fix()

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))
