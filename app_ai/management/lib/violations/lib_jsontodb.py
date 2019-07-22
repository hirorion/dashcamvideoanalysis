# -*- coding: utf-8 -*-
"""
    app_ai.management.commands

    書き起こしで作成されたJSONをDBに登録するコマンド

"""
import io
import json
import logging
import os

from django.db import connections
from django.utils import timezone

from app_ai.management.lib.lib_recev_api_from_mq import recv_api_action_stop
from app_ai.models import AiMovie, AiFrameInfo, AiFrameObject, AiFrameObjectTags

logger = logging.getLogger(__name__)


class LibDbJsonClass(object):

    FLUSH_COUNT = 1000
    READ_JSON_BYTE = 1024 * 1000
    FRM_OBJ_STR = "%d\t%d\t%s\t%s\t%f\t%f"
    FRM_INFO_STR = "%d\t%f\t%s\t%d"

    def __init__(self):
        self.thread_ctrl = None
        self.json_path = None
        self.fps = 0.0
        self.cur = connections['ai'].cursor()
        self.copy_cache_frame_obj = io.StringIO()
        self.copy_cache_frame_info = io.StringIO()
        self.frame_obj_lines_arr = []
        self.frame_info_lines_arr = []
        self.save_frame_count = 0

    def save_info_and_reset_data(self, user_movie_id, movie_filename, movie_unique_filename):
        """
        動画情報をDBに保存する
        その際、データの洗い替えを行う
        :param movie_filename: 動画ファイル名
        :param movie_unique_filename: 動画システムファイル名
        :return: movie_id
        """

        logger.debug("save movie_filename = %s", movie_filename)

        try:
            if movie_unique_filename == "":
                mv = AiMovie.objects.get(name=movie_filename)
            else:
                mv = AiMovie.objects.get(unique_name=movie_unique_filename)
        except AiMovie.DoesNotExist as e:
            mv = AiMovie()
        mv.name = movie_filename
        mv.unique_name = movie_unique_filename
        mv.json_path = self.json_path
        mv.updated_at = timezone.now()
        mv.user_movie_id = user_movie_id
        mv.save()

        # 古いものをすべて削除する
        fi = AiFrameObjectTags.objects.filter(movie_id=mv.id)
        if fi.exists():
            AiFrameObjectTags.objects.filter(movie_id=mv.id).delete()
        fi = AiFrameObject.objects.filter(movie_id=mv.id)
        if fi.exists():
            AiFrameObject.objects.filter(movie_id=mv.id).delete()
        fi = AiFrameInfo.objects.filter(movie_id=mv.id)
        if fi.exists():
            AiFrameInfo.objects.filter(movie_id=mv.id).delete()

        return mv.id

    def save_db(self):
        """
        溜まった配列をDBに書き出す
        :return:
        """
        logger.debug("save db: %d", self.save_frame_count)

        # DB保存
        self.copy_cache_frame_obj.write('\n'.join(self.frame_obj_lines_arr))
        self.copy_cache_frame_info.write('\n'.join(self.frame_info_lines_arr))
        self.copy_cache_frame_obj.seek(0)
        self.copy_cache_frame_info.seek(0)

        self.cur.copy_from(self.copy_cache_frame_obj, 'ai_frame_objects', sep='\t', null='\\N', columns=('fno', 'movie_id', 'data', 'tag', 'score', 'pose_ground_center'))
        self.cur.copy_from(self.copy_cache_frame_info, 'ai_frame_info', sep='\t', null='\\N', columns=('fno', 'speed', 'meta', 'movie_id'))

        # reset
        self.copy_cache_frame_obj = io.StringIO()
        self.copy_cache_frame_info = io.StringIO()
        self.frame_obj_lines_arr = []
        self.frame_info_lines_arr = []

        self.save_frame_count = 0

    def get_fno(self, rarr):
        """
        指定されてフレーム情報から保存するJSONファイルとその情報を返す
        :param rarr:
        :return: mv_id, start_fno, end_fno
        """

        if len(rarr) == 0:
            return -1, 0, 0  # これで処理終了

        rarr = rarr.pop(0)  # 配列の先頭を取り出す

        mv_id = self.save_info_and_reset_data(rarr["user_movie_id"], rarr["movie_filename"], rarr["movie_unique_filename"])

        return mv_id, rarr["s_fno"], rarr["e_fno"]

    def create_copy_db(self, json_obj, rarray, mv_id, start_fno, end_fno):
        """
        複数あるJSONオブジェクトを使って指定フレームまで進んだらDBに保存するCOPY文が配列にセットされる
        :param json_obj:
        :param rarray:
        :param mv_id:
        :param start_fno:
        :param end_fno:
        :return: 次の情報を返す mv_id, start_fno, end_fno
        """

        for frm in json_obj:
            fno = frm["frame_id"]

            if fno > end_fno:
                # 次のポイントを返す
                mv_id, start_fno, end_fno = self.get_fno(rarray)
                if mv_id == -1:
                    return -1, 0, 0  # これで処理終了

            if fno >= start_fno:
                # オブジェクト毎の情報を登録
                objects = frm['objects']
                if objects is not None:
                    for obj in objects:
                        # tagを別JSONBカラムに登録及び追加
                        tags = obj['tags']
                        score = obj['score']
                        pose2 = obj['pose2']
                        pose3 = obj['pose3']
                        # フレームのオブジェクトJSONを全部登録

                        # frame_obj = AiFrameObject()
                        # frame_obj.fno = fno
                        # frame_obj.movie_id = mv_id
                        # frame_obj.data = obj
                        # frame_obj.tag = tags[0]
                        # frame_obj.score = float(score)
                        # グランドオブジェクトのセンタ位置をセット
                        # frame_obj.pose_ground_center = ((float(pose3[1]) - float(pose2[1])) / 2.0) + float(pose2[1])
                        # frame_obj.save(force_insert=True)

                        pose_ground_center = ((float(pose3[1]) - float(pose2[1])) / 2.0) + float(pose2[1])

                        #line_arr.append(fno)
                        #line_arr.append(mv_id)
                        #line_arr.append(json.dumps(obj, ensure_ascii=False))
                        #line_arr.append(str(tags[0]))
                        #line_arr.append(float(score))
                        #line_arr.append(pose_ground_center)
                        lstr = self.FRM_OBJ_STR % (fno, mv_id, json.dumps(obj, ensure_ascii=False), tags[0], score, pose_ground_center)

                        # 検証用のフレーム内のタグリストを登録
                        # tag_obj = AiFrameObjectTags.objects.filter(movie_id=mv_id, fno=fno)
                        # if tag_obj.exists():
                        #    tag_obj = tag_obj[0]
                        #    t = tag_obj.tag
                        #    t.append(tags[0])
                        #    tag_obj.save()
                        # else:
                        #    tag_obj = AiFrameObjectTags()
                        #    tag_obj.fno = fno
                        #    tag_obj.movie_id = mv_id
                        #    tag_obj.tag = tags
                        #    tag_obj.save(force_insert=True)
                        #lstr = '\t'.join(line_arr)
                        self.frame_obj_lines_arr.append(lstr)

                    del frm['objects']

                    # フレーム情報を登録
                    # events = AiFrameInfo()
                    # events.fno = frm['frame_id']
                    # events.speed = frm['speed']
                    # events.meta = frm
                    # events.movie_id = mv_id
                    # events.save(force_insert=True)
                    #line_arr = [frm['frame_id'], frm['speed'], json.dumps(frm, ensure_ascii=False), mv_id]
                    #lstr = '\t'.join(line_arr)
                    # old
                    #speed = frm["camera_pose"][0][1] * self.fps * 3.6
                    # new
                    speed = frm["camera_pose"][0][0] * self.fps * 3.6
                    lstr = self.FRM_INFO_STR % (frm['frame_id'], speed, json.dumps(frm, ensure_ascii=False), mv_id)
                    self.frame_info_lines_arr.append(lstr)

                    # DBにフラッシュ
                    self.save_frame_count = self.save_frame_count + 1
                    if self.save_frame_count >= self.FLUSH_COUNT:
                        self.save_db()

            return mv_id, start_fno, end_fno

    def set_json_to_db_frames(self, fps, json_path, rarray, movie_id, thread_ctrl):
        """
        指定されたJSONを使って、指定フレーム毎に指定保存名を使って保存する
        :param fps: 動画のfps
        :param json_path: 全体のフレームJSON
        :param rarray: 個別フレーム配列
        :paran movie_id: ユーザーの動画ID
        :param thread_ctrl: スレッドコントロール
        :return:
        """
        self.thread_ctrl = thread_ctrl
        self.json_path = json_path
        self.fps = float(fps)  # 速度計算に使っている(float)

        with open(json_path, encoding="utf-8") as f:
            print("json filename = %s" % json_path)
            siz = os.path.getsize(json_path)

            mv_id = -1
            start_fno = -1
            end_fno = -1
            json_str = '[{"camera_pose":'
            for i in range(0, siz, self.READ_JSON_BYTE):

                # is stop?
                if recv_api_action_stop(thread_ctrl, movie_id):
                    return False

                data = f.read(self.READ_JSON_BYTE)
                t = data.split('{"camera_pose":')
                if len(t) == 1:
                    # camera_poseが現れなかったらそのまま追加
                    json_str = json_str + t[0]
                else:
                    # camera_poseが2回以上現れた場合
                    if t[0] == "":
                        # 先頭にcamera_poseが現れた場合、追加してクローズ
                        json_str = json_str[:-1] + "]"
                    else:
                        # そうでない場合はその前までを追加してクローズ
                        json_str = json_str + t[0][:-1] + "]"

                    # JSONオブジェクトに変換して保存
                    try:
                        j = json.loads(json_str)
                        mv_id, start_fno, end_fno = self.create_copy_db(j, rarray, mv_id, start_fno, end_fno)
                        if mv_id == -1:
                            break

                    except Exception as e:
                        logger.exception(e)

                    # 最初と最後以外のcamera_poseが現れた場合はそれぞれのJSONを作成して保存
                    is_finish = False
                    for ts in t[1:-1]:
                        ajson = '[{"camera_pose":' + ts[:-1] + "]"
                        try:
                            j = json.loads(ajson)
                            mv_id, start_fno, end_fno = self.create_copy_db(j, rarray, mv_id, start_fno, end_fno)
                            if mv_id == -1:
                                is_finish = True
                                break

                        except Exception as e:
                            logger.exception(e)

                    if is_finish:
                        break

                    # 次のjsonのための開始をセット
                    json_str = '[{"camera_pose":' + t[len(t) - 1]

        # 残りをフラッシュ
        if self.save_frame_count > 0:
            self.save_db()
        logger.debug("finished")

        return True

