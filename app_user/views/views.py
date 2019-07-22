# -*- coding: UTF-8 -*-
import logging

# Create your views here.
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView

from accounts.forms_registration import MyPasswordReset
from accounts.models import Users
from app_user.forms import UserPasswordResetForm, UserCompanyUserForm
from app_user.views.view_job import SetUserMixin
from lib.mixin import LoginRequiredMixin

logger = logging.getLogger(__name__)


class UserDashboardView(LoginRequiredMixin, SetUserMixin, TemplateView):
    """
    ユーザーダッシュボード画面
    """
    template_name = 'user/dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UserChangePasswordView(LoginRequiredMixin, SetUserMixin, FormView):
    """
    パスワード変更の画面
    """
    template_name = 'user/password/password.html'
    form_class = UserPasswordResetForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class UserChangePasswordAjaxView(LoginRequiredMixin, MyPasswordReset, View):
    """
    パスワード再設定Ajax
    メール送信と完了メッセージを返信
    複数選択化
    POST処理なので、csrf_tokenがない画面からは受付されない
    （つまりその画面で正しくリストが作られていれば大丈夫ってこと）
    GETで来たら定義していないのでMethod now allowedのエラーになる
    """
    subject_template_name = 'registration/password_reset_subject.txt'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

    def post(self, request, *args, **kwargs):

        # idを取得
        ids = request.POST.getlist("selected")

        for user_id in ids:
            # パスワードリセットのメールを送信
            user_id = int(user_id)
            user = Users.get_valid_user_from_id(user_id)
            opts = {
                'username': user.username,
                'use_https': request.is_secure(),
                'token_generator': default_token_generator,
                'email_template_name': self.email_template_name,
                'subject_template_name': self.subject_template_name,
                'request': request,
                'html_email_template_name': None,
                'extra_email_context': None,
            }
            self.send_mail(**opts)

        result = {
            "result": 1,
        }
        return JsonResponse(result)


class UserCompanyUserView(LoginRequiredMixin, SetUserMixin, FormView):
    """
    ドライバー管理画面
    """
    template_name = 'user/companyuser/companyuser.html'
    form_class = UserCompanyUserForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class UserCompanyUserAjaxView(LoginRequiredMixin, View):
    """
    TODO 未実装
    ドライバー管理 いろいろAjax
    POST処理なので、csrf_tokenがない画面からは受付されない
    （つまりその画面で正しくリストが作られていれば大丈夫ってこと）
    """
    def post(self, request, *args, **kwargs):
        return JsonResponse("")


class UserAnalysisResultView(LoginRequiredMixin, SetUserMixin, TemplateView):
    """
    分析結果詳細画面
    """
    template_name = 'user/analysis_results/analysis_results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UserSystemSettingView(LoginRequiredMixin, SetUserMixin, TemplateView):
    """
    システム設定画面
    """
    template_name = 'user/system_setting/setting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
