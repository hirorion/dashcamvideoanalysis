# -*- coding: UTF-8 -*-
from django.conf.urls import url, include

from accounts.forms_registration import MyRegistrationForm
from accounts.views import MyLoginView, MyLogoutView
from accounts.views_registration import PasswordReset, PasswordResetDone, PasswordResetComplete, \
    PasswordResetConfirm, MyRegistrationView

urlpatterns = [
    url(r'^login/$', MyLoginView.as_view(template_name='accounts/login.html'), name="login"),
    url(r'^logout/$', MyLogoutView.as_view(), name="logout"),

    # Password URL workarounds for Django 1.6:
    #   http://stackoverflow.com/questions/19985103/
    url(r'^password/reset/$', PasswordReset.as_view(), name='password_reset'),
    url(r'^password/reset/done/$', PasswordResetDone.as_view(), name='password_reset_done'),

    url(r'^password/reset/complete/$', PasswordResetComplete.as_view(), name='password_reset_complete'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', PasswordResetConfirm.as_view(),
        name='password_reset_confirm'),

    # 通常の新規登録
    url(r'^register/$', MyRegistrationView.as_view(form_class=MyRegistrationForm), name='registration_register', ),

    # 通常のアクティベーション
    #url(r'^activate/(?P<activation_key>\w+)/$', MyActivationView.as_view(), name='registration_activate'),

    #url(r'^register/complete/$', MyTemplateView.as_view(template_name='registration/registration_complete.html'),
    #    name='registration_complete'),
    # 通常新規登録がクローズされている場合
    #url(r'^register/closed/$', MyTemplateView.as_view(template_name='registration/registration_closed.html'), name='registration_disallowed'),

    url(r'', include('registration.backends.default.urls')),
]
