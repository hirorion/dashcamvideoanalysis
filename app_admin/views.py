# -*- coding: UTF-8 -*-
import json
import logging

from django import http, forms
# Create your views here.
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView

from accounts.forms_registration import MyPasswordReset
from accounts.models import Users
from app_admin.forms import AdminPasswordResetForm, AdminIrricUserSearchForm, AdminContractCompanyForm, AdminUserUsageForm, AdminNoticeForm, AdminIrricUserForm, AdminIrricUserNewForm, \
    AdminIrricUserUpdateForm
from app_admin.models.info_models import ServiceInfo, BusinessType
from app_admin.models.user_models import IrricUser
from lib.mixin import AdminLoginRequiredMixin

logger = logging.getLogger(__name__)


class AdminDashboardView(AdminLoginRequiredMixin, TemplateView):
    """
    管理者ダッシュボード画面
    """
    template_name = 'admin/dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AdminChangePasswordView(AdminLoginRequiredMixin, FormView):
    """
    パスワード変更の画面
    """
    template_name = 'admin/password/password.html'
    form_class = AdminPasswordResetForm

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


class AdminChangePasswordAjaxView(AdminLoginRequiredMixin, MyPasswordReset, View):
    """
    パスワード再設定Ajax
    メール送信と完了メッセージを返信
    複数選択化
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
        return http.HttpResponse(json.dumps(result), content_type='text/plain')


class AdminIrricUserView(AdminLoginRequiredMixin, FormView):
    """
    IRRICユーザー管理画面
    """
    template_name = 'admin/irricuser/irricuser.html'
    form_class = AdminIrricUserSearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

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


class AdminIrricUserNewView(AdminLoginRequiredMixin, FormView):
    """
    IRRICユーザー作成の画面
    """
    template_name = 'admin/irricuser/irricuser_new_form.html'
    form_class = AdminIrricUserNewForm
    success_url = reverse_lazy('admin_irricuser')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(form=form))

    @transaction.non_atomic_requests
    def form_valid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        transaction.set_autocommit(False)
        try:
            user = Users()
            user.username = form.cleaned_data['login_id']
            user.email = Users.objects.normalize_email(form.cleaned_data['email'])
            user.set_password(form.cleaned_data['password'])
            user.user_group_id = int(form.cleaned_data['level'])
            irric_user = IrricUser()
            irric_user.name = form.cleaned_data['name']
            irric_user.furigana = form.cleaned_data['furigana']
            if form.cleaned_data["password_reset_next_login_flag"] is True:
                user.is_force_password_change = True

            now = timezone.now()
            user.created_user_id = self.request.user.id
            user.updated_user_id = self.request.user.id
            user.created_at = now
            user.updated_at = now
            irric_user.created_user_id = self.request.user.id
            irric_user.updated_user_id = self.request.user.id
            irric_user.created_at = now
            irric_user.updated_at = now

            irric_user.save()

            user.irric_user_id = irric_user.id
            user.save()

            if form.cleaned_data["send_mail_flag"] is True:
                # TODO IRRICユーザー作成後にメール送信
                pass

        except Exception as e:
            logger.exception(e)
            transaction.rollback()
            return self.form_invalid(form)

        finally:
            transaction.commit()
            transaction.set_autocommit(True)

        return super().form_valid(form)


class AdminIrricUserUpdateView(AdminLoginRequiredMixin, FormView):
    """
    IRRICユーザー更新の画面
    """
    template_name = 'admin/irricuser/irricuser_update_form.html'
    form_class = AdminIrricUserUpdateForm
    success_url = reverse_lazy('admin_irricuser')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # formのインスタンス化
        form_class = self.get_form_class()
        form = self.get_form(form_class)  # これを呼ばないとポストされた値が入ってこない

        user_id = None
        pk = self.kwargs.get("pk", None)
        if pk is not None:
            user = Users.objects.get(id=pk)
            user_id = user.username
            form.fields['login_id'].widget = forms.HiddenInput()

        context.update({
            "user_id": user_id,
            "form": form
        })
        return context

    def get_initial(self):
        initial = super().get_initial()
        pk = self.kwargs.get("pk", None)
        if pk is not None:
            user = Users.objects.get(id=pk)
            initial["login_id"] = user.username
            initial["name"] = user.irric_user.name
            initial["furigana"] = user.irric_user.furigana
            initial["email"] = user.email
            initial["level"] = user.user_group_id
        return initial

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(form=form))

    @transaction.non_atomic_requests
    def form_valid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        transaction.set_autocommit(False)
        try:
            pk = self.kwargs.get("pk", None)
            if pk is not None:
                user = get_object_or_404(Users, id=pk)  # 同じ名前を削除したユーザーも含めて検索（ただしusernameは削除すると先頭に_が付くので関係ない）
                user.email = Users.objects.normalize_email(form.cleaned_data['email'])
                user.irric_user.name = form.cleaned_data['name']
                user.irric_user.furigana = form.cleaned_data['furigana']
                user.irric_user.user_group_id = int(form.cleaned_data['level'])

                now = timezone.now()
                user.updated_user_id = self.request.user.id
                user.updated_at = now
                user.irric_user.updated_user_id = self.request.user.id
                user.irric_user.updated_at = now
                user.irric_user.save()
                user.save()

        except Exception as e:
            logger.exception(e)
            transaction.rollback()
            return self.form_invalid(form)

        finally:
            transaction.commit()
            transaction.set_autocommit(True)

        return super().form_valid(form)


class AdminIrricUserAjaxView(AdminLoginRequiredMixin, View):
    """
    IRRICユーザー管理 利用停止、利用再開、削除のAJAX処理
    """
    def post(self, request, *args, **kwargs):

        # cmd
        cmd = request.POST.get("cmd", None)
        if cmd is None:
            logger.error("cmd was not specified.")
            return HttpResponseServerError()

        # idを取得
        ids = request.POST.getlist("selected")

        for user_id in ids:
            user_id = int(user_id)

            if cmd == "inactive":
                Users.objects.filter(id=user_id).update(is_inactive=True, updated_user_id=request.user.id, updated_at=timezone.now())
            elif cmd == "active":
                Users.objects.filter(id=user_id).update(is_inactive=False, updated_user_id=request.user.id, updated_at=timezone.now())
            elif cmd == "delete":
                # TODO ユーザー削除でemailも削除した
                Users.objects.filter(id=user_id).update(is_delete=True, username="_" + request.user.username, email=None, updated_user_id=request.user.id, updated_at=timezone.now())

        result = {
            "result": 1,
        }
        return JsonResponse(result)


class AdminContractCompanyView(AdminLoginRequiredMixin, FormView):
    """
    IRRICユーザー管理画面
    """
    template_name = 'admin/contract_company/contract_company.html'
    form_class = AdminContractCompanyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # サービスパターンリストを作成
        si = ServiceInfo.objects.all().order_by('id')

        # 事業種別リストを作成
        bt = BusinessType.objects.all().order_by('id')

        context.update({
            "service_infos": si,
            "business_types": bt
        })

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


class AdminContractCompanyAjaxView(AdminIrricUserAjaxView):
    """
    契約会社管理 利用停止、利用再開、削除のAJAX処理
    """


class AdminUserUsageView(AdminLoginRequiredMixin, FormView):
    """
    利用状況画面
    """
    template_name = 'admin/user_usage/user_usage.html'
    form_class = AdminUserUsageForm

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


class AdminNoticeView(AdminLoginRequiredMixin, FormView):
    """
    お知らせ管理画面
    """
    template_name = 'admin/notice/notice.html'
    form_class = AdminNoticeForm

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


class AdminSystemSettingView(AdminLoginRequiredMixin, TemplateView):
    """
    システム設定画面
    """
    template_name = 'admin/system_setting/setting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
