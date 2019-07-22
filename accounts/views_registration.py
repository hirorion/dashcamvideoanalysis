# -*- coding: UTF-8 -*-
import logging

from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetCompleteView, \
    PasswordResetConfirmView
from django.urls import reverse_lazy
from registration.backends.default.views import ActivationView, RegistrationView

from accounts.forms_registration import MyPasswordResetForm

logger = logging.getLogger(__name__)


class MyRegistrationView(RegistrationView):
    """
    通常ユーザーの登録
    """
    pass


class MyActivationView(ActivationView):
    """
    通常のユーザー登録後のメールからのアクティベーションの処理
    """

    def get_success_url(self, user):

        return 'registration_activation_complete', (), {}


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'registration/password_reset_subject.txt'
    email_template_name = 'registration/password_reset_email.html'
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')

    form_class = MyPasswordResetForm

    def form_valid(self, form):
        return super().form_valid(form)


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'registration/password_reset_done.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'registration/password_reset_complete.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    success_url = reverse_lazy('password_reset_complete')
    template_name = 'registration/password_reset_confirm.html'
