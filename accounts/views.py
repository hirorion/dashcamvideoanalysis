# -*- coding: UTF-8 -*-
"""
ログインViewクラス
"""
import logging

from class_based_auth_views.views import LoginView, LogoutView
from django.contrib import auth
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import RedirectView

logger = logging.getLogger(__name__)


class TopView(RedirectView):
    """トップビュー"""
    def get_redirect_url(self, *args, **kwargs):
        return reverse('login')


class MyLoginView(LoginView):
    """
    ログイン後のサイト切り替え
    """

    def dispatch(self, *args, **kwargs):
        """
        ページ初期セット
        :param args:
        :param kwargs:
        :return:
        """
        if self.request.user.is_authenticated:
            # ログイン済みの場合はページ移動
            return redirect(self._redirect_page())

        return super(MyLoginView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        """
        POST後の処理
        :return:
        """
        return self._redirect_page()

    def _redirect_page(self):

        user = self.request.user

        logger.info("Login user: " + user.username)

        # 契約会社管理者とドライバーはポータルへ
        if user.user_group.id >= 4:  # TODO 別で定義した方がいい
            return reverse("user_dashboard")

        return reverse("admin_dashboard")


class MyLogoutView(LogoutView):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            auth.logout(self.request)
        return redirect(self.get_redirect_url())
