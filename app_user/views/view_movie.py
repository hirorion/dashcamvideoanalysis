# -*- coding: UTF-8 -*-
import json
import logging
import mimetypes
import os

# Create your views here.
import re
from wsgiref.util import FileWrapper

from django.http import HttpResponseServerError, JsonResponse, HttpResponse, Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from accounts.models import Users
from app_admin.models.movie_models import UserMovie, UserMovieAnalysisResult
from app_ai.models import AiMovie
from app_ai.worker.high_speed_on_a_narrow_road_violation import HighSpeedOnNarrowRoadViolationClass
from app_ai.worker.jammed_distance_violation import JammedDistanceViolationClass
from app_ai.worker.no_parking_or_stopping_violation import NoParkingOrStoppingViolationClass
from app_ai.worker.no_parking_violation import NoParkingViolationClass
from app_ai.worker.overspeed_violation import OverSpeedViolationClass
from app_ai.worker.speed_side_of_person_bicycle_violation import SpeedSideOfPersonAndBicycleViolationClass
from app_ai.worker.steep_steering_the_turning_right_or_left_at_the_intersection import SteepSteeringWhenTurningRightOrLeftAtTheIntersectionViolationClass
from app_ai.worker.stop_hodou_violation import StopHodouViolationClass
from app_ai.worker.stopline_violation import StopLineViolationClass
from app_ai.worker.sudden_acceleration_before_turning import SuddenAccelerationBeforeTurningViolationClass
from app_ai.worker.sudden_deceleration_before_turning import SuddenDecelerationBeforeTurningViolationClass
from app_ai.worker.test_intersection import TestInterSectionClass
from app_ai.worker.test_turn_intersection import TestTurnInterSectionClass
from app_user.forms import UserMovieSearchForm
from app_user.upload_mixin import UploadMovieDataMixin, detecting_format_name
from app_user.views.view_job import SetUserMixin, MoviePermissionMixin
from config.settings import MEDIA_ROOT, USE_CONVERT_AVI
from lib.mixin import LoginRequiredMixin, NeverCacheMixin

logger = logging.getLogger(__name__)


class UserMovieView(LoginRequiredMixin, SetUserMixin, FormView):
    """
    動画管理画面
    """
    template_name = 'user/movie/movie.html'
    form_class = UserMovieSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ドライバーリスト作成
        if self.user.contract_company is not None and self.user.contract_company_user is None:
            # 契約会社ユーザーだった場合、ドライバ一覧を作成
            driver_objs = Users.objects.filter(contract_company_user__isnull=False, contract_company_id=self.user.contract_company.id)
            drivers = [{"id": d.id, "username": d.username} for d in driver_objs]
            context.update({"drivers": drivers})
        else:
            drivers = [{"id": self.user.id, "username": self.user.username}]
            context.update({"drivers": drivers})

        return context

    #def get_initial(self):
    #    initial = super().get_initial()
    #    initial["search_name"] = None
    #    initial["search_text"] = "aa"
    #    return initial

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(form=form))


class UserMovieUpload(LoginRequiredMixin, UploadMovieDataMixin, SetUserMixin, View):
    """
    動画のアップロード
    TODO アップロードできるファイルのチェックの対応（FPSがないとか）
    """

    def post(self, request, *args, **kwargs):
        """
        動画アップロード
        付属情報、動画のメタ情報(今はない）、動画ファイルがポストされる
        :param request:
        :param args:
        :param kwargs:
        :return: JSON
        """
        result = {}
        try:
            driver_id = self.request.POST.get("movie_driver_id", None)
            user = Users.objects.get(id=driver_id)
            unique_ids = self.save_upload_files_and_save_db(user)  # TODO ログインユーザーでしか登録していない、ドライバーIDで登録すべき
            if unique_ids is None or len(unique_ids) == 0:
                logger.error("Failed to upload file: parameter error.")
                return HttpResponseServerError()

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError()

        return JsonResponse(result)

    def save_to_db(self, user, path, filename, length=0, driving_date=timezone.now, media_type='video', meta_data=""):
        """
        DBに情報を保存
        :param user:
        :param path:
        :param filename:
        :param length:
        :param driving_date:
        :param media_type:
        :param meta_data:
        :return:
        """

        data = UserMovie.objects.create(
            user=user, media_type=media_type, unique_filename=path,
            filename=filename, length=length, driving_day=driving_date, meta_data=meta_data,
            contract_company_id=user.contract_company_id
        )

        return data.id


class UserMovieDelete(LoginRequiredMixin, UploadMovieDataMixin, SetUserMixin, MoviePermissionMixin, View):
    """
    動画の削除
    """
    def post(self, request, *args, **kwargs):
        result = {}
        try:
            movie = get_object_or_404(UserMovie, id=self.movie_id)
            # TODO 保存フラグなどの処理を追加（削除しないでファイル名の前に_を付けて移動するとかする）
            # 関連ファイルを削除
            self.delete_temp_file(movie.user, movie.unique_filename)
            movie.is_delete = True
            movie.save()

            result = {
                "result": 0,
            }
        except Exception as e:
            logger.exception(e)
            result = {
                "result": -1
            }

        return JsonResponse(result)


class UserMovieGetThumbnailVideo(NeverCacheMixin, LoginRequiredMixin, SetUserMixin, MoviePermissionMixin, View):
    """ ユーザーの動画データから生成したタイルサムネイルイメージを取得する
    """

    def get(self, request, *args, **kwargs):

        user_id = self.kwargs.get("uid", None)
        if user_id is None:
            raise Exception("Parameter user_id invalid.")

        filename = self.kwargs.get("fn", None)
        if filename is None:
            raise Exception("Parameter filename invalid.")

        filename = filename + ".jpg"
        path = os.path.join(MEDIA_ROOT, user_id, filename)
        if not os.path.exists(path):
            raise Http404("thumbnail image was not found.")

        try:
            with open(path, 'rb') as f:
                data = f.read()

            response = HttpResponse(data, content_type='application/octet-stream')
            response['Expires'] = 0
            response['Cache-Control'] = "no-cache"
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            response['Accept-Ranges'] = 'bytes'  # for chrome
            response['Content-Length'] = len(data)

            return response

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError(e)


class RangeFileWrapper(object):
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data


range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)


class UserMovieGetVideoData(NeverCacheMixin, LoginRequiredMixin, SetUserMixin, MoviePermissionMixin, View):
    """ ユーザーの動画データを取得する
    """

    def get(self, request, *args, **kwargs):

        file_type = self.kwargs.get("type", None)
        if file_type is None:
            raise Exception("Parameter type invalid.")

        movie = get_object_or_404(UserMovie, id=self.movie_id)

        try:
            hfname = ''
            path = os.path.join(MEDIA_ROOT, movie.user.username)
            unique_id, ext = os.path.splitext(movie.unique_filename)
            if file_type == 'org':
                # 実際の動画のパス
                # AVIファイルのチェック
                format_name = detecting_format_name(json.loads(movie.meta_data))
                if USE_CONVERT_AVI and "avi" in format_name:
                    mp4 = movie.unique_filename.replace("avi", "mp4")
                    mpath = os.path.join(path, mp4)
                    if not os.path.exists(mpath):
                        path = os.path.join(MEDIA_ROOT, "waiting.mp4")
                    else:
                        path = mpath
                else:
                    path = os.path.join(path, movie.unique_filename)
                # ダウンロードファイル名 (TODO ダウンロードは別のクラスで)
                hfname = movie.filename

            elif file_type == 'org_pv':
                # 実際の動画のプレビュー版のパス
                unique_id, ext = os.path.splitext(movie.unique_filename)
                mpath = os.path.join(path, unique_id + "_pv.mp4")
                if not os.path.exists(mpath):
                    mpath = os.path.join(path, movie.unique_filename)

                if not os.path.exists(mpath):
                    mpath = os.path.join(MEDIA_ROOT, "waiting.mp4")
                path = mpath
                # ダウンロードファイル名(TODO ダウンロードは別のクラスで)
                hfname = movie.filename

            elif file_type == "labeled":
                # アノテーションの動画のパス
                path = os.path.join(path, unique_id + "_labeled.mp4")
                fn, ext = os.path.splitext(movie.filename)
                # ダウンロードファイル名(TODO ダウンロードは別のクラスで)
                hfname = fn + "_labeled.mp4"

            elif file_type == "json":
                # 実際のパス
                path = os.path.join(path, unique_id + ".json")
                # ダウンロードファイル名
                hfname = movie.filename + ".json"

            elif file_type == "csv":
                # 実際のパス
                path = os.path.join(path, unique_id + ".csv")
                # ダウンロードファイル名
                hfname = movie.filename + ".csv"

            range_header = request.META.get('HTTP_RANGE', '').strip()
            range_match = range_re.match(range_header)
            size = os.path.getsize(path)
            content_type, encoding = mimetypes.guess_type(path)
            content_type = content_type or 'application/octet-stream'
            if range_match:
                first_byte, last_byte = range_match.groups()
                first_byte = int(first_byte) if first_byte else 0
                last_byte = int(last_byte) if last_byte else size - 1
                if last_byte >= size:
                    last_byte = size - 1
                length = last_byte - first_byte + 1
                resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'), offset=first_byte, length=length), status=206, content_type=content_type)
                resp['Content-Length'] = str(length)
                resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
            else:
                resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
                resp['Content-Length'] = str(size)
            resp['Accept-Ranges'] = 'bytes'
            return resp

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError(e)


class UserMovieAnalysisView(LoginRequiredMixin, UploadMovieDataMixin, SetUserMixin, MoviePermissionMixin, View):
    """
    動画の解析 (TODO これはテンポラリ。本当はSubmitJobを読んでその中で解析する
    """
    def post(self, request, *args, **kwargs):
        result = {}
        movie = None
        try:
            movie = get_object_or_404(UserMovie, id=self.movie_id)

            # メインスレッド（フレームオブジェクトを見て、各のworkerを動作させる)
            movies = AiMovie.objects.filter(user_movie_id=movie.id)
            if not movies.exists():
                raise Http404("this movie file does not exist.")

            # クラスインスタンス化
            stop_violation_cls = StopLineViolationClass()
            speed_sidewalk_violation_cls = SpeedSideOfPersonAndBicycleViolationClass()
            jammped_distance_violation_cls = JammedDistanceViolationClass()
            steep_steering_violation_cls = SteepSteeringWhenTurningRightOrLeftAtTheIntersectionViolationClass()
            test_intersection_cls = TestInterSectionClass()
            test_turn_intersection_cls = TestTurnInterSectionClass()
            sudden_deceleration_cls = SuddenDecelerationBeforeTurningViolationClass()
            sudden_acceleration_cls = SuddenAccelerationBeforeTurningViolationClass()
            overspeed_cls = OverSpeedViolationClass()
            narrow_road_cls = HighSpeedOnNarrowRoadViolationClass()
            stop_hodou_cls = StopHodouViolationClass()
            no_parking_cls = NoParkingViolationClass()
            no_parking_or_stopping_cls = NoParkingOrStoppingViolationClass()
            stop_line_test_cls = StopLineViolationClass()

            ret_analy = []
            for mv in movies:  # TODO 1動画1jsonのはず
                # 処理を開始する
                #stop_violation_cls.worker(mv.id)
                #ret_analy.append(stop_violation_cls.get_violations())

                speed_sidewalk_violation_cls.worker(mv.id)
                ret_analy.append(speed_sidewalk_violation_cls.get_violations())

                #jammped_distance_violation_cls.worker(mv.id)
                #ret_analy.append(jammped_distance_violation_cls.get_violations())

                #steep_steering_violation_cls.worker(mv.id)
                #ret_analy.append(steep_steering_violation_cls.get_violations())

                #test_intersection_cls.worker(mv.id)
                #ret_analy.append(test_intersection_cls.get_violations())

                #test_turn_intersection_cls.worker(mv.id)
                #ret_analy.append(test_turn_intersection_cls.get_violations())

                #sudden_deceleration_cls.worker(mv.id)
                #ret_analy.append(sudden_deceleration_cls.get_violations())

                #sudden_acceleration_cls.worker(mv.id)
                #ret_analy.append(sudden_acceleration_cls.get_violations())

                #overspeed_cls.worker(mv.id)
                #ret_analy.append(overspeed_cls.get_violations())

                narrow_road_cls.worker(mv.id)
                ret_analy.append(narrow_road_cls.get_violations())

                #stop_hodou_cls.worker(mv.id)
                #ret_analy.append(stop_hodou_cls.get_violations())

                #no_parking_cls.worker(mv.id)
                #ret_analy.append(no_parking_cls.get_violations())

                #no_parking_or_stopping_cls.worker(mv.id)
                #ret_analy.append(no_parking_or_stopping_cls.get_violations())

                #stop_line_test_cls.worker(mv.id)
                #ret_analy.append(stop_line_test_cls.get_violations())

            if len(ret_analy) > 0:
                um = UserMovieAnalysisResult.objects.filter(user_movie_id=movie.id)
                if not um.exists():
                    um = UserMovieAnalysisResult()
                    um.data = ret_analy
                    um.user_movie_id = movie.id
                    um.save()
                else:
                    analy = um[0].data
                    analy = analy + ret_analy
                    um.update(data=analy, user_movie_id=movie.id)

                movie.status = 2
                movie.save()

            result = {
                "result": 0,
            }

        except Exception as e:
            if movie is not None:
                movie.status = -1
                movie.save()

            logger.exception(e)
            result = {
                "result": -1
            }

        return JsonResponse(result)
