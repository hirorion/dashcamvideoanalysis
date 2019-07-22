# -*- coding: UTF-8 -*-
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.six import wraps
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import PermissionDenied

from config.settings import LOGIN_URL


def ajax_login_required(view_func):
    """
    Ajax session timeout decorator
    :param view_func:
    :return:
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.is_ajax() and not request.user.is_authenticated:
            response = HttpResponse()
            response['ajax_session_timeout'] = LOGIN_URL
            return response

        return view_func(request, *args, **kwargs)

    return wrapper


class LoginRequiredMixin(object):
    """
    A mixin that provides a way to restrict anonymous access
    """
    @method_decorator(ajax_login_required)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class AdminLoginRequiredMixin(object):
    """
    A mixin that provides a way to restrict anonymous access
    """
    @method_decorator(ajax_login_required)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.user_group_id > 3:  # TODO ユーザーグループを定義した方がいい
            raise PermissionDenied('Permission denied.')

        return super().dispatch(*args, **kwargs)


class NeverCacheMixin(object):
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class CsrfExemptMixin(object):
    """
    A mixin that provides a way to exempt view class out of CSRF validation
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class UserAuthMixin(object):
    """
    Djangoユーザーの認証を行うローカルメソッド。passwordもしくはpassword2を指定する
    self.userに認証したユーザーオブジェクトが入る
    認証OK: None
    認証エラー: Json
    """
    def get_param(self, request):
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
        except KeyError:
            data = dict(result="NG", id='', errorcode="401", errortitle="Authentication Error",
                        errormsg="username, password parameter was not specified.")
            return data
        return dict(result="OK", username=username, password=password)

    def user_auth(self, request):
        data = self.get_param(request)
        if data["result"] != "OK":
            return data

        username = data["username"]
        password = data["password"]

        # 認証したユーザーで処理を進めることもあるので、ここで保存
        self.user = authenticate(username=username, password=password)

        if self.user is not None:
            if not self.user.is_active:
                data = dict(result="NG", id='', errorcode="401", errortitle="Authentication Error",
                            errormsg="Your account has been disabled!")
                return data
        else:
            data = dict(result="NG", id='', errorcode="401", errortitle="Authentication Error",
                        errormsg="Your username and password were incorrect.")
            return data

        return None


class UserAuthMixinByGet(UserAuthMixin):
    """
    Djangoユーザーの認証を行うローカルメソッド。passwordもしくはpassword2を指定する
    self.userに認証したユーザーオブジェクトが入る
    認証OK: None
    認証エラー: Json
    """
    def get_param(self, request):
        try:
            username = request.GET.get('username')
            password = request.GET.get('password')
        except KeyError:
            data = dict(result="NG", id='', errorcode="401", errortitle="Authentication Error",
                        errormsg="username, password parameter was not specified.")
            return data
        return dict(result="OK", username=username, password=password)


class AuthMixinActivateKey(object):
    """
    Djangoユーザーの認証を行うローカルメソッド。先に発行したアクティベートキーで認証する
    認証OK: json [result="OK", activation_key=activation_key]
    認証エラー: Json
    """
    def get_param(self, request):
        activation_key = request.GET.get('activation_key', None)
        if activation_key is None:
            activation_key = request.POST.get('activation_key', None)
        if activation_key is None:
            data = dict(result="NG", id='', errorcode="401", errortitle="Authentication Error",
                        errormsg="activation_key was not specified.")
            return data

        return dict(result="OK", activation_key=activation_key)

    def auth(self, request):
        data = self.get_param(request)
        if data["result"] != "OK":
            return data

        activation_key = data["activation_key"]

        auth = cache.get(activation_key, None)
        if auth is not None and auth is True:
            return dict(result="OK", activation_key=activation_key)

        data = dict(result="NG", id='', errorcode="401", errortitle="Authentication Error",
                    errormsg="Activation error!")
        return data

