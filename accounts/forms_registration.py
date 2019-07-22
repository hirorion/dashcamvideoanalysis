# -*- coding: UTF-8 -*-
import logging

from django import forms
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from registration.forms import RegistrationForm

from accounts.models import Users

logger = logging.getLogger(__name__)


class MyPasswordReset(object):
    def _send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()

    def get_users(self, username):
        active_users = Users.objects.filter(username=username, is_inactive=False)
        return active_users

    def clean_username(self):
        username = self.cleaned_data['username']
        if username is not None:
            active_users = self.get_users(username)
            if len(active_users) > 0:
                user = active_users[0]
                """emailが登録されているかをチェック"""
                if user.email is None or user.email == "":
                    raise forms.ValidationError('登録されているメールアドレスはありません')
            else:
                raise forms.ValidationError('登録されているIDはありません')

        return username

    def send_mail(self, domain_override=None,
             username=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        for user in self.get_users(username):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            email = user.email
            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            self._send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )


class MyPasswordResetForm(forms.Form, MyPasswordReset):
    """
    パスワード再設定のフォーム
    PasswordResetFormをもとにusernameでリセットができるように変更
    """
    username = forms.CharField(label="ログインID", max_length=8, required=True)

    def clean_username(self):
        username = self.cleaned_data['username']
        if username is not None:
            active_users = self.get_users(username)
            if len(active_users) > 0:
                user = active_users[0]
                """emailが登録されているかをチェック"""
                if user.email is None or user.email == "":
                    raise forms.ValidationError('登録されているメールアドレスはありません')
            else:
                raise forms.ValidationError('登録されているIDはありません')

        return username

    def save(self, **opts):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        username = self.cleaned_data["username"]
        opts.update({
            "username": username
        })
        self.send_mail(**opts)


class MyRegistrationForm(RegistrationForm):
    """
    Emailのみでログインさせるための独自登録フォーム
    TODO: どうするかまだ未定
    """
    """
    def clean(self):
        if "email" in self.cleaned_data:
            user = Users.objects.filter(email=self.cleaned_data["email"]).first()
            if user is not None:
                raise ValidationError(
                    _("This account already created.")
                )
        return self.cleaned_data

    @transaction.non_atomic_requests
    def save(self, commit=True):
        transaction.set_autocommit(False)
        try:
            user = Users.objects.create_user(self.cleaned_data["email"], self.cleaned_data["password1"])

            user_type = ['transcription']
            for t in user_type:
                obj = UserType.objects.filter(user=user, name=t).first()
                if obj is None:
                    obj = UserType()
                    obj.user = user
                    obj.name = t
                    obj.save()

            return user

        except Exception as e:
            transaction.rollback()
            logger.exception("Register error occurred.(%s)" % e)
            raise ValidationError(
                _("Internal server error occurred.")
            )

        finally:
            transaction.commit()
            transaction.set_autocommit(True)

    class Meta():
        model = Users
        fields = ('email',)
    """

