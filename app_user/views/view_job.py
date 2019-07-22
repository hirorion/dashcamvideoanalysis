# -*- coding: UTF-8 -*-
"""
    apps.dashboard.view_job

    @author: $Author$
    @version: $Id: api.py bb216bf874cd 2013/11/11 11:28:58 jxtreme $

"""
import datetime
import hashlib
import json
import logging
import random
import subprocess

import pika
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View

from accounts.models import Users
from app_admin.models.movie_models import UserMovieProgress, UserMovie, UserMovieStatusLog
from config.settings import RABBIT_ID, RABBIT_PASSWORD, RABBIT_CONNECTION_HOST, RABBIT_QUEUE_NAME, RABBIT_QUEUE_NAME_API_FS, URL_HOST_ADDRESS_FROM_DOCKER, MEDIA_ROOT
from lib.mixin import LoginRequiredMixin

logger = logging.getLogger(__name__)


class NotAllowGetMethodMixin(object):
    """
    GETが指定されたエラーにする
    """

    def dispatch(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        if self.request.method == "POST":
            return super().dispatch(*args, **kwargs)

        raise PermissionDenied("Invalid requests.")


class _SetUserMixin(object):
    """
    user_idがurlで指定される、ユーザー情報がクラス変数およびセッションとして保存される
    user_idの指定がない場合は、セッションからユーザー情報がクラス変数にセットされる
    """

    def dispatch(self, *args, **kwargs):
        """
        管理者、もしくはirricユーザーのみ許される
        :param args:
        :param kwargs:
        :return:
        """
        user = self.request.user
        # システム管理者およびIRRICユーザーのみ処理される
        if self.request.user.user_group.id <= 3:  # TODO 別で定義した方がいい
            user_id = self.kwargs.get('user_id', None)
            if user_id is None:
                user = self.request.session.get("selected_user", None)
                if user is None:
                    raise PermissionDenied("Invalid requests.")
            else:
                try:
                    user = Users.objects.get(id=user_id, is_inactive=False, is_delete=False)
                    self.request.session["selected_user"] = user

                except Users.DoesNotExist as e:
                    raise PermissionDenied("Invalid requests.")

        # クラスインスタンス変数に入れる
        self.user = user

        return super().dispatch(*args, **kwargs)


class SetUserMixin(_SetUserMixin):
    """
    指定ユーザーなりすまし機能
    違うユーザーでログインしているが指定したユーザーとして動作させる場合に利用する
    ユーザー情報はcontextにセットされる
    """

    def get_context_data(self, **kwargs):
        """
        そのユーザーをテンプレートにセットする
        :param kwargs:
        :return:
        """
        context = super().get_context_data(**kwargs)

        if not self.request.is_ajax() and self.request.user.user_group.id <= 3:  # TODO 別で定義した方がいい
            context.update({"selected_user": self.user})

        return context


class SetUserMixinForDataTable(_SetUserMixin):
    """
    dataTable用の指定ユーザーなりすまし機能
    違うユーザーでログインしているが指定したユーザーとして動作させる場合に利用する
    contextにはuserをセットしない
    """
    def get_context_data(self, **kwargs):
        """
        何もしない
        :param kwargs:
        :return:
        """
        context = super().get_context_data(**kwargs)
        return context


class MoviePermissionMixin(object):
    """
    リクエストしたユーザーが動画を処理できるかどうかチェック
    """

    def dispatch(self, *args, **kwargs):
        self.movie_id = self.kwargs.get("movie_id", None)
        if self.movie_id is None:
            logger.error("movie_id was not specified.")
            return HttpResponseBadRequest()

        request_user = self.user  # ユーザー置換の値
        if request_user.contract_company is not None and request_user.contract_company_user is None:
            # 契約会社ユーザーだった場合、ドライバ一覧を作成
            driver_objs = Users.objects.filter(contract_company_user__isnull=False, contract_company_id=request_user.contract_company.id)
            ids = [d.id for d in driver_objs]  # TODO idがない場合の処理
            # 指定動画が自社のドライバーの動画かどうかチェック
            if not UserMovie.objects.filter(id=self.movie_id, user_id__in=ids).exists():
                raise PermissionDenied('Permission denied.')
        else:
            # ドライバーだった
            # 指定動画が自分の動画かどうかチェック
            if not UserMovie.objects.filter(id=self.movie_id, user=request_user.id).exists():
                raise PermissionDenied('Permission denied.')

        return super().dispatch(*args, **kwargs)

        '''
        self.user_movie = UserMovie.objects.get(id=movie_id, is_delete=False)
        movie_driver_user = self.user_movie.user

        # このムービーが自分が閲覧できるかどうかチェック
        check = False
        request_user = Users.objects.get(id=self.request.user.id, is_inactive=False, is_delete=False)
        if request_user.contract_company is not None:
            # 契約会社だった
            # このドライバーが自分の会社のドライバーかチェック
            if movie_driver_user.contract_company is not None and movie_driver_user.contract_company.id == request_user.contract_company.id:
                # 自分の会社のドライバーだった
                check = True
            else:
                raise PermissionDenied('Permission denied.')

        elif request_user.id == movie_driver_user.id:
            # ドライバー自身だった
            check = True

        elif request_user.irric_user_id is not None:
            # irricユーザーだった
            if request_user.user_group.id == 1:  # TODO これの定義が必要
                # IRRICシステム管理者だった
                check = True

            elif UserContractCompanyRelated.objects.filter(
                    # この動画のドライバーの会社はirric担当コンサルタントかどうか
                    contract_company_id=movie_driver_user.contract_company.id,
                    irric_user_id=request_user.id).exist():
                # そうだった
                check = True

        elif request_user.user_group.id == 0:  # TODO これの定義が必要
            # システム管理者だった
            check = True

        logger.info("check is %d" % check)

        if not check:
            raise PermissionDenied('Permission denied.')
        '''


def get_ai_activation_key(unique_filename):
    """
    時限付きactivation keyを作成

    :param unique_filename:
    :return: activation_key, expire seconds
    """
    salt = hashlib.sha256(str(random.random()).encode('utf-8')).hexdigest()[:5]
    activation_key = hashlib.sha256((salt + unique_filename).encode('utf-8')).hexdigest()
    key_expires = datetime.datetime.today() + datetime.timedelta(1) - datetime.datetime.today()  # timeout 1 day
    return activation_key, key_expires.total_seconds()


class SubmitJob(LoginRequiredMixin, SetUserMixin, MoviePermissionMixin, View):
    """
    各アクション（コンパイル、削除）が実行可能かチェックし、ステータスをスタートにする
    パラメータ: movie_id
    戻り値はJSON文字列。正常/エラーでJSON文字列が違う
    TODO JSONResponseMixinを削除したが不要なのかを調べる
    """

    @transaction.non_atomic_requests  # TODO トランザクション確認
    def post(self, request, *args, **kwargs):

        # ジョブスタート
        transaction.set_autocommit(False)
        try:
            # MoviePermissionMixinで権限を確認しているのでuser_idの指定は不要
            user_movie = UserMovie.objects.get(id=self.movie_id)

            if user_movie.status == 1 or user_movie.status == 10:
                result = dict(result="PROCESSING")
                return JsonResponse(result)

            # 時限付きactivation keyを作成
            activation_key, expire = get_ai_activation_key(user_movie.unique_filename)
            # キャッシュにセット
            cache.set(activation_key, True, timeout=expire)

            # TODO モデルとパラメータの指定未実装
            # sanity check
            #if user_movie.user_model is None:
            #    transaction.rollback()
            #    logger.error("Already deleted the model(%s)" % user_movie.user_model_name)
            #    data = dict(result="NG", errormsg='このモデルは削除されているため、書き起こしが実行できません')
            #    return JsonResponse(data)

            #if user_movie.parameter is None:
            #    transaction.rollback()
            #    logger.error("Already deleted the parameter(%s)" % user_movie.user_parameter_name)
            #    data = dict(result="NG", errormsg='このパラメータは削除されているため、書き起こしが実行できません')
            #    return JsonResponse(data)

            http = "http"
            if request.is_secure():
                http += "s"

            download_url = http + "://" + URL_HOST_ADDRESS_FROM_DOCKER + reverse('api_movie_download_data')
            upload_url = http + "://" + URL_HOST_ADDRESS_FROM_DOCKER + reverse('api_movie_upload_data', args=[user_movie.id])
            status_url = http + "://" + URL_HOST_ADDRESS_FROM_DOCKER + reverse('api_movie_update_job_status', args=[user_movie.id])

            request_str = {
                "web_activation_key": activation_key,
                "server_media_root": MEDIA_ROOT,
                "movie_download_url": download_url,
                "movie_upload_url": upload_url,
                "movie_status_url": status_url,
                "user_id": user_movie.user.username, "movie_id": user_movie.id,
                "unique_filename": user_movie.unique_filename, "media_type": user_movie.media_type, "filename": user_movie.filename,
                "meta_data": user_movie.meta_data, "parameters": user_movie.parameter,  # parameterはjson文字列
                "select_model": {
                }
            }

            # ログはサーバー側にあるので使っていない
            # 古いログファイル削除
            #ppath = os.path.join(MEDIA_ROOT, user_movie.user.username)
            #unique_id, ext = os.path.splitext(user_movie.path)
            # 実際のパス
            #path = os.path.join(ppath, unique_id + ".log")
            #if os.path.exists(path):
            #    os.remove(path)

            credentials = pika.PlainCredentials(RABBIT_ID, RABBIT_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_CONNECTION_HOST, credentials=credentials))
            channel = connection.channel()
            # 永続化を指示
            channel.queue_declare(queue=RABBIT_QUEUE_NAME, durable=True)
            channel.basic_publish(exchange='', routing_key=RABBIT_QUEUE_NAME,
                                  body=json.dumps(request_str, sort_keys=False, ensure_ascii=False, indent=2),
                                  properties=pika.BasicProperties(delivery_mode=2))  # make message persistent
            connection.close()

            #
            # voice dataのステータスとか変更
            #
            user_movie.status = 1  # creating
            user_movie.save()

            #
            # progressをリセット（TODO 未実装）
            #
            progress = UserMovieProgress.objects.filter(user_movie_id=user_movie.id).first()
            if progress is None:
                progress = UserMovieProgress()
                progress.user_movie_id = user_movie.id
                progress.created_at = timezone.now()

            progress.progress = 0
            progress.created_json_flag = False
            progress.updated_at = timezone.now()
            progress.save()

            data = dict(result="OK")
            return JsonResponse(data)

        except UserMovie.DoesNotExist as e:
            transaction.rollback()
            logger.exception("movie was not found. %s" % str(self.movie_id))
            result = dict(result="NG", errormsg="movie was not found.")
            return JsonResponse(result)

        except Exception as e:
            transaction.rollback()
            logger.exception("error occurred.(%s)" % e)
            data = dict(result="NG", errormsg='Job error')
            return JsonResponse(data)

        finally:
            transaction.commit()
            transaction.set_autocommit(True)


class StopJob(LoginRequiredMixin, SetUserMixin, MoviePermissionMixin, View):
    """
    各アクション（コンパイル、削除）が実行可能かチェックし、ステータスをスタートにする
    パラメータ: movie_id
    戻り値はJSON文字列。正常/エラーでJSON文字列が違う
    """

    @transaction.non_atomic_requests
    def post(self, request, *args, **kwargs):

        transaction.set_autocommit(False)
        try:
            user_movie = UserMovie.objects.get(id=self.movie_id)

            # 停止の指示
            request_str = {
                "id": user_movie.id,
                "cmd": "stop"
            }

            credentials = pika.PlainCredentials(RABBIT_ID, RABBIT_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_CONNECTION_HOST, credentials=credentials))
            channel = connection.channel()
            # 永続化を指示
            channel.queue_declare(queue=RABBIT_QUEUE_NAME_API_FS, durable=True)
            channel.basic_publish(exchange='', routing_key=RABBIT_QUEUE_NAME_API_FS,
                                  body=json.dumps(request_str, sort_keys=False, ensure_ascii=False, indent=2),
                                  properties=pika.BasicProperties(delivery_mode=2))  # make message persistent
            connection.close()

            data = dict(result="OK")
            return JsonResponse(data)

        except UserMovie.DoesNotExist as e:
            transaction.rollback()
            logger.exception("movie was not found. %s" % str(self.movie_id))
            result = dict(result="NG", errormsg="movie was not found.")
            return JsonResponse(result)

        except Exception as e:
            transaction.rollback()
            logger.exception("error occurred.(%s)" % e)
            data = dict(result="NG", errormsg='Job error')
            return JsonResponse(data)

        finally:
            transaction.commit()
            transaction.set_autocommit(True)


class GetJobStatus(LoginRequiredMixin, SetUserMixin, MoviePermissionMixin, View):
    """JOBの状態を取得する
       詳細ページからの確認用
       パラメータ: movie_id
       戻り値はJSON文字列。正常/エラーでJSON文字列が違う
    """

    def post(self, request, *args, **kwargs):

        user_movie = get_object_or_404(UserMovie, id=self.movie_id)

        ret_dict = dict()
        if user_movie.status != 1:
            status_message = ""
            if user_movie.status_message is not None:
                status_message = user_movie.status_message
            log = ""
            user_status_log = get_object_or_404(UserMovieStatusLog, user_movie_id=self.movie_id)
            if user_status_log.log is not None:
                log = user_status_log.log

            ret_dict.update({
                user_movie.id: {
                    "status": user_movie.status, "status_message": status_message, "log": log
                }
            })
        else:
            # TODO サーバー側に確認に行くものを作らないとだめ
            #ppath = os.path.join(MEDIA_ROOT, user_movie.user.username)
            #unique_id, ext = os.path.splitext(user_movie.path)
            # 実際のパス
            #path = os.path.join(ppath, unique_id + ".log")

            #self._progress(user_movie.id, path)

            progress_data = get_object_or_404(UserMovieProgress, user_movie_id=user_movie.id)
            ret_dict.update({
                user_movie.id: {
                    "status": user_movie.status, "progress": progress_data.progress
                }
            })

        return JsonResponse(ret_dict)

    def _progress(self, vid, path):
        """
        ログファイルから進捗をチェック
        :param vid:
        :return:
        """
        try:
            proc = subprocess.Popen('tail -n 10000 %s | grep PROGRESS | tail -n 1' % path,
                                    shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
            output = proc.communicate()[0]
            if output:
                output = output.decode('utf-8')
                if "PROGRESS:" in output:
                    t = output.replace("DETECTION ", "").replace("VISUALIZATION ", "").replace("PROGRESS: ", "").replace("% COMPLETE", "").strip()
                    progress = int(t)
                    if "DETECTION PROGRESS:" in output:
                        progress = int(progress / 2)
                    elif "VISUALIZATION PROGRESS:" in output:
                        progress = 50 + int(progress / 2)
                    logger.info("progress = %d" % progress)

                    # localなのでそのままDBに書き込みにした
                    c = UserMovieProgress.objects.filter(user_movie_id=vid).count()
                    if c != 0:
                        p = UserMovieProgress.objects.get(user_movie_id=vid)
                        p.progress = progress
                        p.save()
            else:
                logger.info("not log = %s" % output.decode('utf-8'))

        except Exception as e:
            logger.exception(e)


class GetJobAllStatus(GetJobStatus):
    """ユーザーのすべてのJOBの状態を取得する
       一覧からの確認用
       戻り値はJSON文字列。正常/エラーでJSON文字列が違う
       TODO リクエストしたユーザーの動画リストの実装
       TODO 管理者のユーザー置換の実装
    """

    def get(self, request, *args, **kwargs):

        try:
            ret_dict = dict()

            request_user = self.user
            if request_user.contract_company is not None and request_user.contract_company_user is None:
                # 契約会社ユーザーだった場合、ドライバー一覧を作成
                driver_objs = Users.objects.filter(contract_company_user__isnull=False, contract_company_id=request_user.contract_company.id)
                ids = [d.id for d in driver_objs]
                movies = UserMovie.objects.filter(user_id__in=ids)
            else:
                # ドライバーだった
                movies = UserMovie.objects.filter(user=self.user)

            for movie in movies:

                if movie.status == 1:
                    # TODO サーバー側に確認に行くものを作らないとだめ
                    #ppath = os.path.join(MEDIA_ROOT, movie.user.username)
                    #unique_id, ext = os.path.splitext(movie.path)
                    # 実際のパス
                    #path = os.path.join(ppath, unique_id + ".log")
                    #self._progress(movie.id, path)
                    pass

                ret_dict.update({
                    movie.id: {
                        "status": movie.status,
                    }
                })
                progress_data = UserMovieProgress.objects.filter(user_movie_id=movie.id).first()
                if progress_data:
                    ret_dict[movie.id].update({
                        "progress": progress_data.progress
                    })

            return JsonResponse(ret_dict)

        except Exception as e:
            logger.exception("error occurred.(%s)" % e)
            data = dict(result="NG", errormsg='Job error')
            return JsonResponse(data)

