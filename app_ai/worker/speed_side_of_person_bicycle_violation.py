# -*- coding: utf-8 -*-
"""
    歩行者・自転車の側方通過時の速度 検出クラス
"""
import json
import logging

from django.db.models import Count, Avg, Q, Max, Min

from app_ai.models import AiFrameInfo, AiFrameObject
from app_ai.worker.detections import Detections
from app_ai.worker.violation import ViolationWorkerClass

logger = logging.getLogger(__name__)


class SpeedSideOfPersonAndBicycleViolationClass(Detections, ViolationWorkerClass):
    """
    歩行者・自転車の側方通過時の速度
    # TODO bicycleをまだ追加していない
    """

    # TODO 27fpsをどこからもってこないといけない
    MOVIE_FPS = 27.0
    CHECK_SCORE = 0.9
    # 対象オブジェクトは、5m以内で、側方5mの場合
    CHECK_DISTANCE = 5
    CHECK_SIDE_DISTANCE = 5
    # TODO 判定を1.0秒間隔にしている
    CHECK_FRAME_SECOND = MOVIE_FPS * 1  # 1秒

    def __init__(self):
        super().__init__()
        self.is_start = None
        self.check_arr = None

    def get_violations(self):
        output = {
            "group": "速度",
            "category": "歩行者、自転車の側方通過時の速度",
            "violations": self.violations
        }
        return output

    def get_curb(self, movie_id, start_fno, end_fno):
        # 1秒間の左右の縁石をチェック
        # 左からlrを検索して、rlが初めて見つかったところの2つの幅
        cond = Q(tag__contains="curb-")
        cur_lr_obj = None
        cur_rl_obj = None
        cur_lr = 0
        cur_rl = 0
        n_list = AiFrameObject.objects.filter(cond, movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, score__gte=0.7).order_by("data__x1")

        for n in n_list:
            if "curb-" in n.tag and "-lr" in n.tag and n.data["x1"] < 0.5:  # TODO 路側帯の検索に0.5を使っている
                # 一番内側
                cur_lr = n.data["pose3"][1]
                cur_lr_obj = n

        for n in n_list:
            if cur_rl == 0 and "curb-" in n.tag and "-rl" in n.tag and n.data["x2"] > 0.5:
                # 最初に見つけたら終わり（一番内側）
                cur_rl = n.data["pose2"][1]
                cur_rl_obj = n
                break

        return cur_lr_obj, cur_rl_obj

    def check_violation(self, movie_id, check_arr, sfno, efno):
        """
        指定フレーム間で歩道外の人で30km/h以上を見つける
        :param check_arr:
        :param movie_id:
        :param sfno:
        :param efno:
        :return: 見つけた: fno / 見つけられない: -1
        """

        # 1秒間の平均速度が30km以下はチェックしない TODO 1秒間隔でチェックしない場合はここを調整する
        #speed_max = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=sfno, fno__lt=sfno + self.MOVIE_FPS, speed__gte=0).aggregate(Max('speed'))['speed__max']
        #speed_min = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=sfno, fno__lt=sfno + self.MOVIE_FPS, speed__gte=0).aggregate(Min('speed'))['speed__min']
        #logger.debug("########### sfno = %d" % sfno)
        # 速度は0以上としているから全部マイナスだとNoneになる
        #if speed_max is None or speed_min is None or speed_max - speed_min < 7:
            # 7kmの差がなければすべての平均を追加
        speed = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=sfno, fno__lt=sfno + self.MOVIE_FPS, speed__gt=0).aggregate(Avg('speed'))['speed__avg']
        if speed is not None and speed < 30.0:
            logger.debug("######### 30km以下だよ")
            return -1

        curb_lr, curb_rl = self.get_curb(movie_id, sfno, efno)

        start_check_flag = 0
        check_start_fno = []
        for fno in range(sfno, efno):
            if fno in check_arr:
                # 前後のフレームすべてに対象オブジェクトが写っていること
                c_start_fno = fno - 1
                c_end_fno = fno + 1
                # group byで写っている対象オブジェクトが0以上のレコードを抽出して、その数をチェックしている
                check_list = AiFrameObject.objects.filter(movie_id=movie_id, fno__gte=c_start_fno, fno__lte=c_end_fno, tag="person-ground", score__gte=self.CHECK_SCORE).values('tag', 'fno').annotate(count=Count('tag')).filter(count__gt=0)
                check_count = check_list.count()
                if check_count == 3:
                    # 歩道内かどうか判断
                    obj = check_arr[fno]
                    obj_pose_l = obj.data["pose3"][1]
                    obj_pose_r = obj.data["pose2"][1]
                    if curb_lr is not None and curb_lr.data["x1"] < 0.5:
                        lr_pose = curb_lr.data["pose2"][1]
                        if obj_pose_l > lr_pose:
                            logger.debug("########### 左歩道のなか %d, %d" % (obj_pose_l, lr_pose))
                            continue
                    if curb_rl is not None and curb_rl.data["x1"] > 0.5:
                        rl_pose = curb_rl.data["pose3"][1]
                        if obj_pose_r < rl_pose:
                            logger.debug("########### 右歩道のなか %d, %d" % (obj_pose_r, rl_pose))
                            continue

                    distance = float(obj.data['pose2'][0])
                    side_distance = float(abs(obj.data['pose2'][1]))  # 右はマイナス

                    # TODO 対象オブジェクトは、10m以内で、側方5mの場合
                    if 0 < distance < self.CHECK_DISTANCE and side_distance < self.CHECK_SIDE_DISTANCE:
                        logger.info("---- distance %d > %d" % (self.CHECK_DISTANCE, distance))
                        logger.info('---- side_distance %d > %d' % (self.CHECK_SIDE_DISTANCE, side_distance))
                        start_check_flag = start_check_flag + 1
                        check_start_fno.append(fno)

        if start_check_flag > 2:
            # スタートのチェックポイントを見つけた
            return check_start_fno[0]  # 最初に見つけた位置
        return -1

    '''
    def calc_pass_fno(self, movie_id, fno, check_obj, use_pose, fps):
        """
        そのオブジェクトを通過するフレーム数を計算
        :param movie_id:
        :param fno:
        :param check_obj: QuerySet
        :param use_pose: どのposeを使うか
        :return:
        """
        distance = float(check_obj.data[use_pose][0])  # 単位はm
        # 5m手前なので通過させるため更に3mを追加
        distance = distance + 3  # m
        # フレーム数計算
        # 現在の速度 (0.5秒前からの平均速度を使っている）
        speed = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=fno - int(fps/2.0), fno__lte=fno, speed__gte=0).aggregate(Avg('speed'))['speed__avg']
        if speed is None or speed == 0.0:
            # スピードがすべて0以下だったら0.5秒を返す
            fnum = int(fps / 2.0)
            return fnum

        logger.debug("** speed = %f", speed)
        logger.debug("** distance = %d", distance)
        s = ((float(distance) / 1000.0) / float(speed)) * float(3600.0)  # 距離km * 時速km/h
        logger.debug("** cross second = %f", s)
        fnum = int(s * float(fps))
        logger.debug("** cross add frame = %d", fnum)

        return fnum
    '''

    def violation_detections(self, movie_id, start_fno, end_fno):
        """
        TODO 車の大きさや取り付け位置による調整が必要
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return:
        """
        if self.is_start:
            # 入り口を見つける
            start = self.check_violation(movie_id, self.check_arr, start_fno, end_fno)
            if start >= 0:
                # スタートのチェックポイントを見つけた
                self.set_start_fno(start)  # 最初に見つけた位置
                self.is_start = False
        else:
            # 違反を見つけた
            self.set_start_fno(self.get_start_fno() - (self.MOVIE_FPS * 2.0))
            self.set_last_fno(self.get_start_fno() + (self.MOVIE_FPS * 3.0))
            self.safety_flag = False
            self.fix()
            # 次の入り口へ
            self.is_start = True
            return

            '''
            # 次の1秒後に出口を見つける  TODO 見つけてる最中に動画が終了したどうする？
            end = self.check_end(movie_id, self.check_arr, start_fno, end_fno)
            if end >= 0:
                # 出口見つけた
                logger.debug("# found start= %d, end = %d" % (self.get_start_fno(), end))

                # 見つけた範囲で側方通過をチェック
                # 複数の人がいるのでそのフレーム間で一番最後の人まで
                start_first_fno = 0
                last_end_fno = 0
                for fno in range(self.get_start_fno(), end_fno):
                    if fno in self.check_arr:  # 人がいるフレーム
                        obj = self.check_arr[fno]
                        distance = float(obj.data['pose2'][0])
                        side_distance = float(abs(obj.data['pose2'][1]))  # 右はマイナス
                        # TODO 対象オブジェクトは、10m以内で、側方5mの場合
                        if 0 < distance < self.CHECK_DISTANCE and side_distance < self.CHECK_SIDE_DISTANCE:
                            logger.info("---- distance %d > %d" % (self.CHECK_DISTANCE, distance))
                            logger.info('---- side_distance %d > %d' % (self.CHECK_SIDE_DISTANCE, side_distance))

                            if start_first_fno == 0:
                                start_first_fno = fno
                                self.set_start_fno(fno)

                            # そのオブジェクトを通過するフレーム数を計算
                            fnum = self.calc_pass_fno(movie_id, fno, obj, "pose2", self.MOVIE_FPS)
                            past_fno = fno + fnum
                            # 最初に見つけた対象オブジェクトから通過ポイントまでのフレームをチェック
                            check_frames = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=fno, fno__lt=past_fno).order_by("fno")
                            for f in check_frames:
                                if f.speed > 30:
                                    logger.info("[Fault] speed over pass side of person!: speed= %d, fno = %d" % (f.speed, f.fno))
                                    self.safety_flag = False
                                    last_end_fno = past_fno  # 通過したところまで

                # 最大値の終了フレーム番号をセット
                if last_end_fno > 0:
                    self.set_last_fno(last_end_fno)
                    logger.debug("last fno = %d" % self.get_last_fno())

                self.fix()
                # 次の入り口へ
                self.is_start = True
                '''

    def get_person_line(self, movie_id):
        """
        指定範囲の人のフレームをすべて抜き出す
        :param movie_id:
        :return: RawQuerySet
        """
        obj_list = AiFrameObject.objects.filter(movie_id=movie_id, tag="person-ground", score__gte=0.9).order_by("fno")

        return obj_list

    def worker(self, movie_id):
        # TODO 将来はスレッドで同時進行

        check_frame_count = int(self.CHECK_FRAME_SECOND)

        # 人のフレームを抜き出す
        obj_list = self.get_person_line(movie_id)

        self.check_arr = {}
        for fm in obj_list:
            self.check_arr[fm.fno] = fm

        self.is_start = True
        ai = AiFrameInfo.objects.filter(movie_id=movie_id).order_by("fno")
        org_start_fno = ai[0].fno
        fno_count = ai.count() + org_start_fno
        for obj_fno in range(org_start_fno, fno_count, check_frame_count):
            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            self.violation_detections(movie_id, start_fno=start_fno, end_fno=end_fno)

        for vio in self.violations:
            vio["start_fno"] = vio["start_fno"] - org_start_fno
            vio["last_fno"] = vio["last_fno"] - org_start_fno

        logger.info("results: %s" % json.dumps(self.get_violations(), sort_keys=True, indent=4, ensure_ascii=False))

