# -*- coding: utf-8 -*-
"""
    判定ロジック集クラス
"""
import logging
from math import pi, cos, sin
import numpy as np
from django.db.models import Sum, Count

from app_ai.models import AiFrameInfo, AiFrameObject

logger = logging.getLogger(__name__)


class Detections(object):
    """
    判定ロジック集
    """

    def calc_last_fno(self, movie_id, fno, check_objs, use_pose, fps):
        """
        そのフレームにある複数の対象オブジェクト（人や自転車たち）で自車から一番遠いオブジェクトを通過するフレーム数を計算
        TODO 過去の認識結果の距離の差分を使って計算する
        :param movie_id:
        :param fno:
        :param check_objs: QuerySet
        :param use_pose: どのposeを使うか
        :return:
        """
        dist_max = 0
        for obj in check_objs:
            distance = float(obj.data[use_pose][0])  # 単位はm
            if distance > dist_max:
                dist_max = distance
        # フレーム数計算
        # 現在の速度 (1秒前からの平均速度を使っている）
        speed_sum = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=fno - int(fps/2.0), fno__lte=fno).aggregate(Sum('speed'))['speed__sum']
        speed = speed_sum / fps
        logger.debug("** speed = %d", speed)
        logger.debug("** dist_max = %d", dist_max)
        s = ((float(dist_max) / 1000.0) / float(speed)) * float(3600.0)  # 距離km * 時速km/h
        logger.debug("** cross second = %f", s)
        fnum = int(s * float(fps))
        logger.debug("** cross add frame = %d", fnum)

        return fnum

    def get_changed_degrees(self, movie_id, start_fno, end_fno):
        """
        指定フレームの角度変化を抽出
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return:
        """
        check_frames = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gt=start_fno, fno__lt=end_fno).order_by("fno")
        degrees = []
        [degrees.append(float(f.meta["camera_pose"][2][0])) for f in check_frames]
        ndegrees = np.array(degrees)

        diff = np.diff(ndegrees, n=1)
        return np.sum(diff)

        #prev_c = float(check_frames[0].meta["camera_pose"][2][0])
        #degree = 0.0
        #for c in check_frames:
        #    degree = degree + (float(c.meta["camera_pose"][2][0]) - prev_c)
        #    prev_c = float(c.meta["camera_pose"][2][0])

        return degree

    def get_intersection(self, movie_id, score=0.6, curb_degrees=15.0, left_except_x=0.4, right_except_x=0.6):
        """
        交差点のフレームをすべて抜き出す
        :param movie_id:
        :param score:
        :param curb_degrees: 縁石の角度
        :param left_except_x: 左除外位置
        :param right_except_x: 右除外位置
        :return: RawQuerySet
        """
        INCLUDE_TAG_IN_FRAME_SQL = "bool_or(data->'tags' ? '%s' and score >= %f %s)"

        # フレームでループ
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'curb-lr' and score >= %f and (degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < %f and (data->>'x2')::float > %f)) or bool_or(data->'tags' ? 'curb-rl' and score >= %f and (degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < %f and  (data->>'x1')::float < %f)) ) and speed >= 0 and movie_id=%d order by movie_id, fno" % (score, curb_degrees, right_except_x, score, curb_degrees, left_except_x, movie_id)

        is_list = AiFrameObject.objects.raw(sql)

        return is_list

    def get_intersection_start_with_stop_or_hodou(self, movie_id, score=0.6, curb_degrees=15.0, left_except_x=0.4, right_except_x=0.6):
        """
        止まれ、停止線もしくは歩道がある交差点入り口のフレームをすべて抜き出す
        :param movie_id:
        :param score:
        :param curb_degrees: 縁石の角度
        :param left_except_x: 左除外位置
        :param right_except_x: 右除外位置
        :return: RawQuerySet
        """
        include_tags = ["hyoshikireg-stop", "hyoji-stop", "hyoji-stop_line", "hyoji-hodou"]
        INCLUDE_TAG_IN_FRAME_SQL = "bool_or(data->'tags' ? '%s' and score >= %f)"

        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having (bool_or(data->'tags' ? 'curb-lr' and score >= %f and (degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < %f and (data->>'x2')::float > %f)) or bool_or(data->'tags' ? 'curb-rl' and score >= %f and (degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < %f and  (data->>'x1')::float < %f)) ) and (%s)) and speed >= 0 and movie_id=%d order by movie_id, fno"

        add_sql = []
        for tag in include_tags:
            add_sql.append(INCLUDE_TAG_IN_FRAME_SQL % (tag, 0.800000))

        sql = sql % (score, curb_degrees, right_except_x, score, curb_degrees, left_except_x, " or ".join(add_sql), movie_id)

        is_list = AiFrameObject.objects.raw(sql)

        return is_list

    def get_intersection_with_traffic_light(self, movie_id):
        """
        信号がある交差点フレームをすべて抜き出す
        :param movie_id:
        :return: RawQuerySet
        """
        include_tags = ["trafficlight-black", "trafficlight-blue", "trafficlight-red",]
        INCLUDE_TAG_IN_FRAME_SQL = "bool_or(data->'tags' ? '%s' and score >= %f)"

        # フレームでループ
        sql = "select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having (bool_or(data->'tags' ? 'curb-lr' and score >= 0.600000 and (degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < 15.0 and (data->>'x2')::float > 0.6)) or bool_or(data->'tags' ? 'curb-rl' and score >= 0.600000 and (degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < 15.0 and  (data->>'x1')::float < 0.4))) and (%s)) and speed >= 0 and movie_id=%d order by movie_id, fno"

        add_sql = []
        for tag in include_tags:
            add_sql.append(INCLUDE_TAG_IN_FRAME_SQL % (tag, 0.700000))

        sql = sql % (" or ".join(add_sql), movie_id)

        is_list = AiFrameObject.objects.raw(sql)

        return is_list

    def get_intersection_area(self, intersection_after_check_seconds_frames, movie_id, frm_list):
        """
        交差点に入って出る部分を抜き出した配列を返す
        :param intersection_after_check_seconds_frames:
        :param movie_id:
        :param frm_list: 交差点リスト
        :return:  [{"start": 1, "end": 20},...]
        """
        # sanity check
        if frm_list is None:
            raise TypeError("Intersection data list must be need!")
        if intersection_after_check_seconds_frames is None:
            raise TypeError("intersection_after_check_seconds class variable not found in class!")

        check_arr = {}
        for fm in frm_list:
            check_arr[fm.fno] = True

        check_frame_count = int(intersection_after_check_seconds_frames)
        result = []
        item = None
        start_checking = False
        fno_count = AiFrameInfo.objects.filter(movie_id=movie_id).count()
        for obj_fno in range(1, fno_count, check_frame_count):
            start_fno = obj_fno
            end_fno = start_fno + check_frame_count

            check_flag = 0
            for fno in range(start_fno, end_fno):
                if fno in check_arr:
                    check_flag = check_flag + 1

            if check_flag < 1:
                if start_checking:
                    # 出口見つけた
                    item.update({"end": end_fno})
                    result.append(item)
                    item = None
                    # 次のチェックポイントを見つけさせる
                    start_checking = False
            else:
                if start_checking is False:
                    # 次のチェックポイントを見つけた
                    start_checking = True
                    item = {"start": start_fno}

        return result

    def check_object_appears_more_than_once(self, check_arr, sfno, efno, count=1):
        """
        指定フレーム間で指定された配列にオブジェクトが2回以上あったらを見つける
        :param check_arr:
        :param sfno:
        :param efno:
        :param count: 現れた回数（以上）
        :return: 見つけた: fno / 見つけられない: -1
        """
        start_check_flag = 0
        check_start_fno = []
        for fno in range(sfno, efno):
            if fno in check_arr:
                start_check_flag = start_check_flag + 1
                check_start_fno.append(fno)

        if start_check_flag > count:
            # スタートのチェックポイントを見つけた
            return check_start_fno[0]  # 最初に見つけた位置
        return -1

    def check_object_not_appear(self, check_arr, sfno, efno):
        """
        指定フレーム間で指定された配列にオブジェクトが0回だったらを見つける
        :param check_arr:
        :param sfno:
        :param efno:
        :return: 見つけた: fno/ 見つけられない: -1
        """
        end_check_flag = 0
        for fno in range(sfno, efno):
            if fno in check_arr:
                end_check_flag = end_check_flag + 1

        if end_check_flag == 0:
            # 出口見つけた
            # 次のチェックポイントを見つけさせる
            return efno
        return -1

    def get_past_positon_by_meter(self, movie_id, check_distance, start_fno, end_fno):
        """
        指定メータ先のフレームを抜き出す
        :param movie_id:
        :param check_distance:
        :param start_fno: 現在の位置
        :param end_fno: どこまでも先のフレームまで検索するか
        :return: 見つけたらそのフレーム番号、見つけられなかったら-1
        """

        distance_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno).order_by("fno")
        distance = 0
        past_fno = -1
        for d_frm in distance_frms:
            speed = float(d_frm.speed)
            t = 1.0 / float(self.MOVIE_FPS)
            distance = distance + ((speed * (t / 3600.0)) * 1000.0)
            logger.debug("============== distance = %f" % distance)
            if distance > check_distance:
                past_fno = d_frm.fno
                break

        return past_fno

    def get_past_positon_by_meter_old(self, movie_id, check_distance, start_fno, end_fno):
        """
        指定メータ先のフレームを抜き出す
        :param movie_id:
        :param check_distance:
        :param start_fno: 現在の位置
        :param end_fno: どこまでも先のフレームまで検索するか
        :return: 見つけたらそのフレーム番号、見つけられなかったら-1
        """

        distance_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno).order_by("fno")
        distance = 0
        past_fno = -1
        for d_frm in distance_frms:
            speed = d_frm.meta["camera_pose"][0][0] * float(self.MOVIE_FPS) * 3.6
            angle = d_frm.meta["camera_pose"][2][0]

            radians = angle * pi / 180  # 度をラジアンに変換
            vx = cos(radians) * speed
            vy = sin(radians) * speed

            x = vx
            y = vy

            a = np.array([0, 0])
            b = np.array([x, y])
            distance = distance + np.linalg.norm(b - a)
            logger.debug("============== distance = %f" % distance)
            if distance > check_distance:
                past_fno = d_frm.fno
                break

        return past_fno

    def get_prev_positon_by_meter(self, movie_id, check_distance, start_fno, end_fno):
        """
        指定メータ手前のフレームを抜き出す
        :param movie_id:
        :param check_distance:
        :param start_fno: どこまでもどったフレームまで検索するか
        :param end_fno: 現在の位置
        :return: 見つけたらそのフレーム番号、見つけられなかったら-1
        """

        distance_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno).order_by("-fno")
        distance = 0
        prev_fno = -1
        for d_frm in distance_frms:
            speed = float(d_frm.speed)
            t = 1.0 / float(self.MOVIE_FPS)
            distance = distance + ((speed * (t/3600.0)) * 1000.0)
            logger.debug("============== distance = %f" % distance)
            if distance > check_distance:
                prev_fno = d_frm.fno
                break

        return prev_fno

    def get_prev_positon_by_meter_old(self, movie_id, check_distance, start_fno, end_fno):
        """
        指定メータ手前のフレームを抜き出す
        :param movie_id:
        :param check_distance:
        :param start_fno: どこまでもどったフレームまで検索するか
        :param end_fno: 現在の位置
        :return: 見つけたらそのフレーム番号、見つけられなかったら-1
        """

        distance_frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno).order_by("-fno")
        distance = 0
        prev_fno = -1
        prev_x = 0
        prev_y = 0
        for d_frm in distance_frms:
            speed = float(d_frm.meta["camera_pose"][0][0]) * float(self.MOVIE_FPS) * 3.6
            angle = float(d_frm.meta["camera_pose"][2][0])

            radians = angle * pi / 180  # 度をラジアンに変換
            vx = cos(radians) * speed
            vy = sin(radians) * speed

            x = vx
            y = vy

            a = np.array([prev_x, prev_y])
            b = np.array([x, y])
            prev_x = x
            prev_y = y
            distance = distance + np.linalg.norm(b - a)
            logger.debug("============== distance = %f" % distance)
            if distance > check_distance:
                prev_fno = d_frm.fno
                break

        return prev_fno

    def get_maximum_frequency_speed(self, movie_id, start_fno, end_fno):
        """
        指定範囲から速度標識、標示を探して、あればその時の速度を見つける
        :param movie_id:
        :param start_fno:
        :param end_fno:
        :return: 速度/-1
        """
        # 速度標示、速度標識があるか
        # TODO 速度更新位置は見えたところにしている
        # TODO 過ぎるところで間違える傾向があるんで1秒間で一番多いもの（GROUP byして大きい順にして一番最初を使っている）
        # speed_list = AiFrameObject.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno, tag__contains="max_speed", score__gte=0.9).order_by("fno")
        speed_list = AiFrameObject.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lt=end_fno, tag__contains="max_speed", score__gte=0.7).values('tag').annotate(
            count=Count('tag')).order_by('-count')
        if speed_list is not None and len(speed_list) > 0:
            sp = speed_list[0]["tag"]
            s = sp.split("max_speed_")
            check_speed = int(s[1])
            logger.debug("=== update start sfno= %d, efno = %d, speed = %d" % (start_fno, end_fno, check_speed))
            return check_speed

        return -1

