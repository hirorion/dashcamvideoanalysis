# -*- coding: UTF-8 -*-

# Create your views here.
import base64
import logging
from math import degrees, atan, sqrt

from django.db.models import Count, Max
from django.http import HttpResponse, HttpResponseServerError, JsonResponse
from django.views import View
from django.views.generic import TemplateView, ListView
from pure_pagination import PaginationMixin

from app_ai.models import AiFrameInfo, AiFrameObject, AiMovie
from lib.raw_base_datatable_view import RawBaseDatatableView
from lib.mixin import AdminLoginRequiredMixin

logger = logging.getLogger(__name__)

INCLUDE_TAG_IN_FRAME_SQL = "bool_or(data->'tags' ? '%s' and score >= %f %s)"
SEARCH_TAG_IN_FRAME_SQL = "(data->'tags' ? '%s' and score >= %f %s)"
# 指定オブジェクトを含むフレームを検索するSQL
FRAME_SQL = "select movie_id, fno from ai_frame_objects group by movie_id, fno having %s"
SPEED_SQL = "speed >= 0"
# 見つけたフレームの情報を検索するSQL
SEARCH_FRAME_SQL = "select * from ai_frame_info where (movie_id, fno) in (%s) and %s order by movie_id, fno"
# 見つけたフレームすべてから指定オブジェクトを検索するSQL
SEARCH_OBJECTS_IN_ALL_FRAME_SQL = "select * from ai_frame_objects a where (movie_id, fno) in (%s) and (%s) order by movie_id, fno"
# 見つけた１つのフレームからオブジェクトを検索するSQL
SEARCH_OBJECTS_IN_THE_FRAME_SQL = "select * from ai_frame_objects a where movie_id=%d and fno=%d and (%s) order by movie_id, fno"
SCORE = 0.9


def pose_condition(cond):
    ret_cond = ""
    if cond != "":
        ret_cond = "and ("
        cond = cond.replace("x1", "(data->>'x1')::float")
        cond = cond.replace("y1", "(data->>'y1')::float")
        cond = cond.replace("x2", "(data->>'x2')::float")
        cond = cond.replace("y2", "(data->>'y2')::float")
        for i in range(4):
            for j in range(4):
                cond = cond.replace("pose%d_%d" % (i, j), "(data->'pose%d'->>%d)::float" % (i, j))
        ret_cond = ret_cond + cond + ")"

    return ret_cond


def condition_not_string(cond):
    if cond == "not":
        return " = false"
    else:
        return ""


class AiMovieSearchView(AdminLoginRequiredMixin, PaginationMixin, ListView):
    """
    AI管理、検索動画表示
    """
    model = AiFrameInfo
    template_name = 'ai/list.html'
    paginate_by = 10

    object_sqls = None

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_queryset(self):

        if self.request.method == "POST":
            movie = self.request.POST.get("movie", None)
            condition_not = self.request.POST.getlist("condition_not[]")
            bracket_open = self.request.POST.getlist("bracket_open[]")
            bracket_close = self.request.POST.getlist("bracket_close[]")
            objects = self.request.POST.getlist("object[]")
            scores = self.request.POST.getlist("score[]")
            poses = self.request.POST.getlist("pose[]")
            and_or = self.request.POST.getlist("and_or[]")
            score = self.request.POST.get("score", None)
            speed = self.request.POST.get("speed", None)
            search_frame_sql = self.request.POST.get("search_frame_sql", None)
            search_objects_sql = self.request.POST.get("search_objects_sql", None)
            search_sql = self.request.POST.get("search_sql", None)

            # 数字変換
            if score is not None and score != "":
                score = float(score)

            self.request.session["ai_search_movie"] = movie
            self.request.session["ai_search_condition_not"] = condition_not
            self.request.session["ai_search_bracket_open"] = bracket_open
            self.request.session["ai_search_bracket_close"] = bracket_close
            self.request.session["ai_search_objects"] = objects
            self.request.session["ai_search_scores"] = scores
            self.request.session["ai_search_pose"] = poses
            self.request.session["ai_search_and_or"] = and_or
            self.request.session["ai_search_score"] = score
            self.request.session["ai_search_speed"] = speed
            self.request.session["ai_search_frame_sql"] = search_frame_sql
            self.request.session["ai_search_objects_sql"] = search_objects_sql
            self.request.session["ai_search_sql"] = search_sql

        else:  #if self.request.method == "GET":
            movie = self.request.session.get("ai_search_movie", None)
            condition_not = self.request.session.get("ai_search_condition_not", None)
            bracket_open = self.request.session.get("ai_search_bracket_open", None)
            bracket_close = self.request.session.get("ai_search_bracket_close", None)
            objects = self.request.session.get("ai_search_objects", None)
            scores = self.request.session.get("ai_search_scores", None)
            poses = self.request.session.get("ai_search_pose", None)
            and_or = self.request.session.get("ai_search_and_or", None)
            score = self.request.session.get("ai_search_score", None)
            speed = self.request.session.get("ai_search_speed", None)
            search_frame_sql = self.request.session.get("ai_search_frame_sql", None)
            search_objects_sql = self.request.session.get("ai_search_objects_sql", None)
            search_sql = self.request.session.get("ai_search_sql", None)

            if objects is None:
                return self.model.objects.filter(movie_id=0)

        if search_sql is not None and search_sql != "" and search_sql != "None":
            return self.model.objects.raw(search_sql)

        # フレームにあるオブジェクトを検索するためのSQLを作成
        frame_sqls = []
        for i in range(len(objects)):
            if objects[i] != "":
                tmp = INCLUDE_TAG_IN_FRAME_SQL % (objects[i], float(scores[i]), pose_condition(poses[i]))
                frame_sqls.append("%s" % tmp)
        if len(frame_sqls) == 0:
            return self.model.objects.filter(movie_id=0)

        # 検索条件組み立て
        frame_sql = ""
        for i in range(len(frame_sqls)):
            tmp = bracket_open[i] + frame_sqls[i] + condition_not_string(condition_not[i]) + bracket_close[i]
            try:
                tmp = tmp + " " + and_or[i]
            except IndexError as e:
                pass
            frame_sql = frame_sql + " " + tmp

        # 動画、フレームの検索（ページングのため）
        search_frame_sql = search_frame_sql % frame_sql
        add_sql = speed
        if movie is not None and movie != "":
            add_sql = add_sql + " and movie_id=" + movie
        sql = SEARCH_FRAME_SQL % (search_frame_sql, add_sql)

        self.kwargs.update({"find_frame_sql": sql})

        return self.model.objects.raw(sql)

    def get_context_data(self, **kwargs):
        context = {}
        error = False
        try:
            context = super().get_context_data(**kwargs)
        except Exception as e:
            logger.exception(e)
            error = True

        sample_data_list = {
            "movie": [
                {
                  "id": 1,
                  "fno": [
                      {
                        "id": 1,
                        "speed": 29,
                        "camera_pose": [[1,2,3,4],[5,6,7,8],[9,10,11,12]],
                        "object_sql": "select...",
                        "objs": [
                            {
                                "name": "aaa",
                                "score": 1223,
                                "pose0": 0.44,
                            },
                            {
                                "name": "bbb",
                                "score": 12
                            }
                        ]
                      }
                  ]
                },
            ]
        }

        data_list = {"movie": []}
        if not error:

            # 動画、フレームのみの検索結果を取得
            frame_list = context['object_list']
            if len(frame_list) > 0:
                condition_not = self.request.session.get("ai_search_condition_not")
                objects = self.request.session.get("ai_search_objects")
                scores = self.request.session.get("ai_search_scores")
                poses = self.request.session.get("ai_search_pose")

                # 検索するオブジェクトをセット
                object_sqls = []
                for i in range(len(objects)):
                    if objects[i] != "":
                        if "not" not in condition_not[i]:
                            tmp = SEARCH_TAG_IN_FRAME_SQL % (objects[i], float(scores[i]), pose_condition(poses[i]))
                            object_sqls.append("%s" % tmp)

                # 画面に表示させる配列を作成
                prev_movie_id = -1
                prev_fno_id = -1
                mv_arr = None
                frm_arr = None
                for obj in frame_list:
                    if prev_movie_id != obj.movie_id:
                        mv_arr = {"id": obj.movie_id, "fno": []}
                        data_list["movie"].append(mv_arr)
                        prev_movie_id = obj.movie_id
                    if prev_fno_id != obj.fno:
                        frm_arr = {"id": obj.fno, "speed": obj.speed, "camera_pose": obj.meta['camera_pose'], "objs": []}
                        mv_arr["fno"].append(frm_arr)
                        prev_fno_id = obj.fno

                    # そのフレームにある指定されたオブジェクトをすべて検索
                    sql = SEARCH_OBJECTS_IN_THE_FRAME_SQL % (obj.movie_id, obj.fno, " or ".join(object_sqls))
                    ai = AiFrameObject.objects.raw(sql)
                    frm_arr.update({"object_sql": sql})

                    for a in ai:
                        obj_arr = {}
                        frm_arr["objs"].append(obj_arr)
                        obj_arr["name"] = a.data['tags'][0]
                        obj_arr["score"] = a.data['score']
                        obj_arr["center"] = a.pose_ground_center
                        obj_arr["pose0"] = a.data['pose0']
                        obj_arr["pose1"] = a.data['pose1']
                        obj_arr["pose2"] = a.data['pose2']
                        obj_arr["pose3"] = a.data['pose3']
                        obj_arr["x1p"] = float(a.data['x1']) * 1920.0
                        obj_arr["y1p"] = float(a.data['y1']) * 1080.0
                        obj_arr["x2p"] = float(a.data['x2']) * 1920.0
                        obj_arr["y2p"] = float(a.data['y2']) * 1080.0
                        obj_arr["x1"] = a.data['x1']
                        obj_arr["y1"] = a.data['y1']
                        obj_arr["x2"] = a.data['x2']
                        obj_arr["y2"] = a.data['y2']
                        obj_arr["y2y1"] = float(a.data['y2']) - float(a.data['y1'])
                        obj_arr["h_degrees"] = degrees(atan((float(a.data['y2']) - float(a.data['y1'])) / (float(a.data['x2']) - float(a.data['x1']))))
                        obj_arr["length"] = sqrt((float(a.data['y2']) - float(a.data['y1']))**2 + (float(a.data['x2']) - float(a.data['x1']))**2)
                        obj_arr["lengthp"] = sqrt( (((float(a.data['y2']) - float(a.data['y1'])) * 1080.0) ** 2) + (((float(a.data['x2']) - float(a.data['x1'])) * 1920.0) ** 2) )

        # すべてのオブジェクト名を抽出(プルダウン用)
        objects = AiFrameObject.objects.values('tag').order_by('tag').annotate(count=Count('tag'))

        # movieリスト
        movie_list = AiMovie.objects.all()

        context.update({
            "error": error,
            "movie_list": movie_list,
            "score": SCORE,
            "speed": SPEED_SQL,
            "object_sql": "",
            "data_list": data_list,
            "OBJECTS": objects,
            "FRAME_SQL": FRAME_SQL,
            "OBJECT_SQL": SEARCH_OBJECTS_IN_THE_FRAME_SQL,
            "SEARCH_SQL": self.request.session.get("ai_search_sql", ""),
            "FIND_FRAME_SQL": self.kwargs.get("find_frame_sql", None)
        })

        return context


class AiMovieSearchCustomView(AdminLoginRequiredMixin, TemplateView):
    """
    AI管理、検索動画表示
    """
    template_name = 'ai/list_custom.html'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        movie = self.request.POST.get("movie", None)

        frame_list = AiFrameObject.objects.raw("select * from ai_frame_info where (movie_id, fno) in (select movie_id, fno from ai_frame_objects group by movie_id, fno having  bool_or(data->'tags' ? 'lane-white-lr' and score >= 0.900000 and ( (data->>'x1')::float < 0.375 and (data->>'y2')::float > 0.5 and sqrt( power((data->>'y2')::float - (data->>'y1')::float, 2.0) + power((data->>'x2')::float - (data->>'x1')::float, 2.0) ) < 0.19 and degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < 45.0)) and bool_or(data->'tags' ? 'lane-white-rl' and score >= 0.900000 and ( (data->>'x2')::float < 0.625 and (data->>'y2')::float > 0.5 and sqrt( power((data->>'y2')::float - (data->>'y1')::float, 2.0) + power((data->>'x2')::float - (data->>'x1')::float, 2.0) ) < 0.19  and degrees( atan( ((data->>'y2')::float - (data->>'y1')::float) /  ((data->>'x2')::float - (data->>'x1')::float) ) ) < 45.0)) ) and speed > 0 and fno>585 and movie_id=5 order by movie_id, fno")

        data_list = {"movie": []}

        # 画面に表示させる配列を作成
        prev_movie_id = -1
        prev_fno_id = -1
        mv_arr = None
        frm_arr = None
        for obj in frame_list:
            if prev_movie_id != obj.movie_id:
                mv_arr = {"id": obj.movie_id, "fno": []}
                data_list["movie"].append(mv_arr)
                prev_movie_id = obj.movie_id
            if prev_fno_id != obj.fno:
                frm_arr = {"id": obj.fno, "speed": obj.speed, "camera_pose": obj.meta['camera_pose'], "objs": []}
                mv_arr["fno"].append(frm_arr)
                prev_fno_id = obj.fno

            # そのフレームにある指定されたオブジェクトをすべて検索
            '''
            sql = SEARCH_OBJECTS_IN_THE_FRAME_SQL % (obj.movie_id, obj.fno, " or ".join(object_sqls))
            ai = AiFrameObject.objects.raw(sql)
            frm_arr.update({"object_sql": sql})

            for a in ai:
                obj_arr = {}
                frm_arr["objs"].append(obj_arr)
                obj_arr["name"] = a.data['tags'][0]
                obj_arr["score"] = a.data['score']
                obj_arr["center"] = a.pose_ground_center
                obj_arr["pose0"] = a.data['pose0']
                obj_arr["pose1"] = a.data['pose1']
                obj_arr["pose2"] = a.data['pose2']
                obj_arr["pose3"] = a.data['pose3']
                obj_arr["x1p"] = a.data['x1'] * 1920.0
                obj_arr["y1p"] = a.data['y1'] * 1080.0
                obj_arr["x2p"] = a.data['x2'] * 1920.0
                obj_arr["y2p"] = a.data['y2'] * 1080.0
                obj_arr["x1"] = a.data['x1']
                obj_arr["y1"] = a.data['y1']
                obj_arr["x2"] = a.data['x2']
                obj_arr["y2"] = a.data['y2']
                obj_arr["y2y1"] = float(a.data['y2']) - float(a.data['y1'])
                obj_arr["h_degrees"] = degrees(atan((a.data['y2'] - a.data['y1']) / (a.data['x2'] - a.data['x1'])))
                obj_arr["length"] = sqrt((a.data['y2'] - a.data['y1'])**2 + (a.data['x2'] - a.data['x1'])**2)
                obj_arr["lengthp"] = sqrt(   (((a.data['y2'] - a.data['y1']) * 1080.0) ** 2) + (((a.data['x2'] - a.data['x1']) * 1920.0) ** 2) )
            '''

        # movieリスト
        movie_list = AiMovie.objects.all()

        context.update({
            "movie_list": movie_list,
            "data_list": data_list,
        })

        return context


class AiMovieSearchListView(AdminLoginRequiredMixin, RawBaseDatatableView):
    """
    未使用
    パスワード変更のユーザーリストのJSONを返す
    """

    # The model we're going to show
    model = AiFrameObject

    columns = ['']

    order_columns = ['id', 'movie_id', 'fno', "tag", "score"]

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        objects = self.request.POST.getlist("object[]")
        search_frame_sql = self.request.POST.get("search_frame_sql", None)
        search_objects_sql = self.request.POST.get("search_objects_sql", None)

        frame_sqls = []
        object_sqls = []
        for obj in objects:
            if obj != "":
                tmp = INCLUDE_TAG_IN_FRAME_SQL % obj
                tmp2 = SEARCH_TAG_IN_FRAME_SQL % obj
                frame_sqls.append("%s" % tmp)
                object_sqls.append("%s" % tmp2)

        if len(frame_sqls) == 0:
            return self.model.objects.filter(movie_id=0)

        search_frame_sql = search_frame_sql % " and ".join(frame_sqls)
        sql = search_objects_sql % (search_frame_sql, " or ".join(object_sqls))

        sobj = self.model.objects.raw(sql)

        return sobj

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            json_data.append({
                "dataId": "row_%d" % item.id,
                "movie_id": item.movie_id,
                "fno": item.fno,
                "tag": item.tag,
                "score": item.data["score"],
                "data": str(item.data)
                })
        return json_data


class AiMovieGetImageAjaxView(AdminLoginRequiredMixin, View):
    """
    該当フレームの画像を取得
    """

    def get(self, request, *args, **kwargs):

        movie_id = self.kwargs.get("movie_id", None)
        if movie_id is None:
            raise Exception("Parameter movie_id invalid.")

        fno = self.kwargs.get("fno", None)
        if fno is None:
            raise Exception("Parameter fno invalid.")

        ai = AiFrameInfo.objects.get(movie_id=movie_id, fno=fno)
        jpeg64 = ai.meta['jpeg_annotated']
        data = base64.b64decode(jpeg64.encode())
        filename = movie_id + "_" + fno + ".jpg"

        try:
            response = HttpResponse(data, content_type='application/octet-stream')
            response['Expires'] = 0
            response['Cache-Control'] = "no-cache"
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['Accept-Ranges'] = 'bytes'  # for chrome
            response['Content-Length'] = len(data)

            return response

        except Exception as e:
            return HttpResponseServerError(e)


class AiMovieDrawFrameView(AdminLoginRequiredMixin, TemplateView):
    """
    AI管理、指定フレームの自車の動きを描画させる画面
    """
    template_name = 'ai/vehicle_position.html'

    def get_context_data(self, **kwargs):
        mv = AiMovie.objects.all()
        context = super().get_context_data(**kwargs)

        context.update({
            "movie_list": mv,
        })
        return context


class AiMovieDrawFrameGetDataView(AdminLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        movie_id = self.kwargs.get("movie_id", 1)
        start_fno = self.kwargs.get("start_fno", 0)
        end_fno = self.kwargs.get("end_fno", None)

        if end_fno is None:
            max = AiFrameInfo.objects.filter(movie_id=movie_id).aggregate(Max('fno'))
            end_fno = max['fno__max']

        frms = AiFrameInfo.objects.filter(movie_id=movie_id, fno__gte=start_fno, fno__lte=end_fno)
        json_data = { "result": "OK", "end_fno": end_fno, "data": []}
        for frm in frms:
            data = [frm.meta["camera_pose"][0][0], frm.meta["camera_pose"][2][0]]
            json_data["data"].append(data)

        return JsonResponse(json_data)


