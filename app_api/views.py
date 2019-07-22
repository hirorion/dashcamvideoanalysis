# -*- coding: utf-8 -*-
"""
    apps.api.api

    @author: $Author$
    @version: $Id: api.py bb216bf874cd 2013/11/11 11:28:58 jxtreme $

"""
# Create your views here.
import json
import logging
import os

from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from app_admin.models.movie_models import UserMovie, UserMovieStatusLog, UserMovieAnalysisResult
from app_ai.management.config.define_ai import AI_WORKER_BUILD_DIR
from config import settings
from lib.mixin import CsrfExemptMixin, NeverCacheMixin, AuthMixinActivateKey

logger = logging.getLogger(__name__)


class APIMovieUpdateJobStatus(CsrfExemptMixin, AuthMixinActivateKey, View):
    """
    JOBの状態を更新するAPI。
    戻り値はJSON文字列。正常/エラーでJSON文字列が違う
    logもセットで受けるけるように修正
    パラメータ: username, password, movie_id, status, status_message
    """

    def post(self, request, *args, **kwargs):

        # 認証
        data = self.auth(request)
        if data["result"] != "OK":
            return JsonResponse(data)

        movie_id = self.kwargs.get("movie_id", None)
        if movie_id is None:
            logger.error("movie_id was not specified.")
            data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                        errormsg="movie_id was not specified.")
            return JsonResponse(data)

        log = request.POST.get('log', None)
        if log is None:
            logger.error("log was not specified.")
            data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                        errormsg="log was not specified.")
            return JsonResponse(data)

        try:
            # ログを更新
            c = UserMovieStatusLog.objects.filter(user_movie_id=movie_id).count()
            if c == 0:
                status_log = UserMovieStatusLog()
                status_log.user_movie_id = movie_id
            else:
                status_log = UserMovieStatusLog.objects.get(user_movie_id=movie_id)

            status_log.log = log
            status_log.save()

            # statusの更新
            movie_data = UserMovie.objects.get(id=movie_id)

            status = request.POST.get('status', None)
            if status is None:
                logger.error("status was not specified.")
                data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                            errormsg="status was not specified.")
                return JsonResponse(data)

            # サーバーからステータスを自由に変更できる
            if status == "success":  # Compiled
                logger.debug("Success status for id:%s" % movie_id)
                status_id = 2
                # 認証キーの削除
                cache.delete(data["activation_key"])

                # 受け取った解析結果をDBに入れる
                try:
                    movie_data = UserMovie.objects.get(id=int(movie_id))
                    unique_id, ext = os.path.splitext(movie_data.unique_filename)
                    path = os.path.join(settings.MEDIA_ROOT, movie_data.user.username, unique_id + "_violations.json")
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            json_str = f.read()

                        # データ洗い替え
                        um = UserMovieAnalysisResult.objects.filter(user_movie_id=int(movie_id))
                        if not um.exists():
                            um = UserMovieAnalysisResult()
                        else:
                            um = um.first()
                        um.data = json.loads(json_str)
                        um.user_movie_id = movie_id
                        um.save()
                except Exception as e:
                    logger.error(e)
                    request.POST.set('status_message', "Failed to register JSON to DB")
                    status_id = -1

            elif status.startswith("failed"):
                logger.debug("Failed status for id:%s" % movie_id)
                status_id = -1
                # 認証キーの削除
                cache.delete(data["activation_key"])

            elif status.startswith("stop"):
                logger.debug("Stop status for id:%s" % movie_id)
                status_id = 3
                # 認証キーの削除
                cache.delete(data["activation_key"])

            else:
                logger.debug("Set any status for id:%s" % movie_id)
                # 途中経過を表示させるためのany status
                status_id = 10

            status_message = request.POST.get('status_message', None)

            # ステータスを更新
            movie_data.status = status_id
            movie_data.status_message = status_message
            movie_data.save()

            data = dict(id=movie_id, status=status_id)
            return JsonResponse(data)

        except UserMovie.DoesNotExist as e:
            logger.exception("movie was not found. %s" % str(movie_id))
            result = dict(result="NG", id=movie_id, errorcode="400", errortitle="Invalid parameter",
                          errormsg="movie was not found.")
            return JsonResponse(result)

        except Exception as e:
            logger.exception("Failed to update status.(%s)" % e)
            data = dict(result="OK", id=movie_id, errorcode="501", errortitle="Db Error", errormsg='Failed to update status.')
            return JsonResponse(data)


class APIMovieUpdateLog(CsrfExemptMixin, AuthMixinActivateKey, View):
    """
    未使用
    ログを更新するAPI。
    戻り値はJSON文字列。正常/エラーでJSON文字列が違う
    POST
    パラメータ: username, password, movie_id, log
    """

    def post(self, request, *args, **kwargs):

        # ユーザー認証
        data = self.auth(request)
        if data["result"] != "OK":
            return JsonResponse(data)

        movie_id = self.kwargs.get("movie_id", None)
        if movie_id is None:
            logger.error("movie_id was not specified.")
            data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                        errormsg="movie_id was not specified.")
            return JsonResponse(data)

        log = request.POST.get('log', None)
        if log is None:
            logger.error("log was not specified.")
            data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                        errormsg="log was not specified.")
            return JsonResponse(data)

        # ログを更新
        try:
            c = UserMovieStatusLog.objects.filter(user_movie_id=movie_id).count()
            if c == 0:
                status_log = UserMovieStatusLog()
                status_log.user_movie_id = movie_id
            else:
                status_log = UserMovieStatusLog.objects.get(user_movie_id=movie_id)

            status_log.log = log
            status_log.save()

        except UserMovie.DoesNotExist as e:
            logger.exception("movie was not found. %s" % str(movie_id))
            result = dict(result="NG", id=movie_id, errorcode="400", errortitle="Invalid parameter",
                          errormsg="movie was not found.")
            return JsonResponse(result)

        except Exception as e:
            logger.exception("Failed to update project log.(%s)" % e)
            data = dict(result="OK", id=movie_id, errorcode="501", errortitle="Db Error",
                        errormsg='Failed to set status log.')
            return JsonResponse(data)

        data = dict(id=movie_id)
        return JsonResponse(data)


class APIDownloadData(CsrfExemptMixin, NeverCacheMixin, AuthMixinActivateKey, View):
    """
    サーバーにあるユーザーのデータを取得する
    """

    def get(self, request, *args, **kwargs):
        # 認証
        data = self.auth(request)
        if data["result"] != "OK":
            raise PermissionDenied("Authenticate failed")

        return self.download(data)

    def download(self, auth_data):

        filename = self.request.GET.get("filename", None)
        if filename is None:
            logger.error("filename was not specified.")
            raise

        path = self.request.GET.get("path", None)
        if path is None:
            logger.error("path was not specified.")
            raise ImproperlyConfigured("Parameter Error: path was not specified.")

        delete_activation_key = self.request.GET.get("delete_activation_key", None)

        try:
            path = os.path.join(path, filename)
            with open(path, 'rb') as f:
                data = f.read()
                f.close()
            response = HttpResponse(data, content_type='application/octet-stream')
            response['Content-Disposition'] = 'filename=%s' % filename
            response['Content-Length'] = len(data)

            return response

        except Exception as e:
            logger.exception(e)
            raise Exception("Cannot download data file.")

        finally:
            if delete_activation_key is not None:
                logger.debug("delete activation key: %s" % auth_data["activation_key"])
                cache.delete(auth_data["activation_key"])


class APIMovieUploadData(CsrfExemptMixin, AuthMixinActivateKey, View):
    """
    データアップロード
    WEBサーバーにアップロードされることが前提なので、アップロード先はWEBサーバー内
    アップロードファイルはひとつのみ
    パラメータ: movie_id, datafile(file)
    """

    def post(self, request, *args, **kwargs):

        # 認証
        data = self.auth(request)
        if data["result"] != "OK":
            return JsonResponse(data)

        movie_id = self.kwargs.get("movie_id", None)
        if movie_id is None:
            logger.error("movie_id was not specified.")
            data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                        errormsg="movie_id was not specified.")
            return JsonResponse(data)

        filename = self.request.POST.get("filename", None)
        if filename is None:
            logger.error("filename was not specified.")
            data = dict(result="NG", id=movie_id, errorcode="400", errortitle="Parameter Error",
                        errormsg="filename was not specified.")
            return JsonResponse(data)

        upload_file = self.request.FILES.get('datafile', None)
        # エラーチェック
        if upload_file is None:
            logger.error("datafile was not specified.")
            data = dict(result="NG", id=movie_id, errorcode="400", errortitle="Parameter Error",
                        errormsg="datafile was not specified.")
            return JsonResponse(data)

        try:
            movie_data = UserMovie.objects.get(id=int(movie_id))
            path = os.path.join(settings.MEDIA_ROOT, movie_data.user.username, filename)

            # アップロードされたデータを分割して読み込んで保存する
            with open(path, 'wb+') as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)

            result = dict(result="OK", id=movie_id)
            return JsonResponse(result)

        except UserMovie.DoesNotExist as e:
            logger.exception("movie was not found. %s" % str(movie_id))
            result = dict(result="NG", id=movie_id, errorcode="400", errortitle="Invalid parameter",
                          errormsg="movie was not found.")
            return JsonResponse(result)

        except Exception as e:
            logger.exception("API Data upload error occurred.(%s)" % e)
            data = dict(result="NG", id='', errorcode="500", errortitle="Internal Error",
                        errormsg="Internal error was occurred.")
            return JsonResponse(data)


class APIMovieGetStatus(CsrfExemptMixin, AuthMixinActivateKey, View):
    """
    JOBの状態を取得するAPI
    戻り値はJSON文字列。正常/エラーでJSON文字列が違う
    パラメータ: movie_id, datafile(file)
    """

    def post(self, request, *args, **kwargs):

        # ユーザー認証
        data = self.auth(request)
        if data["result"] != "OK":
            return JsonResponse(data)

        movie_id = self.kwargs.get("movie_id", None)
        if movie_id is None:
            logger.error("movie_id was not specified.")
            data = dict(result="NG", id='', errorcode="400", errortitle="Parameter Error",
                        errormsg="movie_id was not specified.")
            return JsonResponse(data)

        try:
            movie_data = UserMovie.objects.get(id=movie_id)

            ret_dict = dict()
            status = ""
            if movie_data.status is not None:
                status = movie_data.status
            status_message = ""
            if movie_data.status_message is not None:
                status_message = movie_data.status_message

            ret_dict.update({
                "result": "OK", "id": movie_id, "status": status, "status_message": status_message
            })
            return JsonResponse(ret_dict)

        except UserMovie.DoesNotExist as e:
            logger.exception("movie was not found. %s" % str(movie_id))
            result = dict(result="NG", id=movie_id, errorcode="400", errortitle="Invalid parameter",
                          errormsg="movie was not found.")
            return JsonResponse(result)

        except Exception as e:
            logger.exception("API Get status error occurred.(%s)" % e)
            data = dict(result="NG", id='', errorcode="500", errortitle="Internal Error",
                        errormsg="Internal error was occurred.")
            return JsonResponse(data)


class APIAuthCheck(CsrfExemptMixin, AuthMixinActivateKey, View):
    """
    認証のみチェック
    upload param is username, password or password2
    """

    def post(self, request, *args, **kwargs):
        # 認証
        data = self.auth(request)
        if data["result"] != "OK":
            return JsonResponse(data)

        result = dict(result="OK")
        return JsonResponse(result)
