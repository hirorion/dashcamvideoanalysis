# -*- coding: UTF-8 -*-
from django.conf.urls import url

from app_admin.view_tables import AdminChangePasswordListView, AdminIrricUserListView, AdminContractCompanyListView, AdminNoticeListView
from app_admin.views import AdminDashboardView, AdminChangePasswordView, AdminChangePasswordAjaxView, AdminIrricUserView, AdminContractCompanyView, AdminUserUsageView, AdminNoticeView, \
    AdminIrricUserAjaxView, AdminContractCompanyAjaxView, AdminIrricUserNewView, AdminIrricUserUpdateView, AdminSystemSettingView

urlpatterns = [
    url(r'^$', AdminDashboardView.as_view(), name="admin_dashboard"),
    url(r'^password/$', AdminChangePasswordView.as_view(), name="admin_password"),
    url(r'^password/list/$', AdminChangePasswordListView.as_view(), name="admin_password_list"),
    url(r'^password/reset/$', AdminChangePasswordAjaxView.as_view(), name="admin_password_reset"),

    url(r'^user/$', AdminIrricUserView.as_view(), name="admin_irricuser"),
    url(r'^user/list/$', AdminIrricUserListView.as_view(), name="admin_irricuser_list"),
    url(r'^user/new/$', AdminIrricUserNewView.as_view(), name="admin_irricuser_new"),
    url(r'^user/update/$', AdminIrricUserUpdateView.as_view(), name="admin_irricuser_update_url"),
    url(r'^user/update/(?P<pk>[A-Za-z0-9_\-\.]+)/$', AdminIrricUserUpdateView.as_view(), name="admin_irricuser_update"),
    url(r'^user/ctrl/$', AdminIrricUserAjaxView.as_view(), name="admin_irricuser_ctrl"),

    url(r'^contract/companies/$', AdminContractCompanyView.as_view(), name="admin_contract_company"),
    url(r'^contract/companies/list/$', AdminContractCompanyListView.as_view(), name="admin_contract_company_list"),
    url(r'^contract/companies/ctrl/$', AdminContractCompanyAjaxView.as_view(), name="admin_contractcompany_ctrl"),

    url(r'^usage/$', AdminUserUsageView.as_view(), name="admin_user_usage"),

    url(r'^notice/$', AdminNoticeView.as_view(), name="admin_notice"),
    url(r'^notice/list/$', AdminNoticeListView.as_view(), name="admin_notice_list"),

    url(r'^system/setting/$', AdminSystemSettingView.as_view(), name="admin_system_setting"),

]
