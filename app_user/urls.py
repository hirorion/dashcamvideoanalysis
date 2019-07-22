# -*- coding: UTF-8 -*-
from django.conf.urls import url

from app_user.views.view_job import SubmitJob, StopJob, GetJobStatus
from app_user.views.view_movie import UserMovieView, UserMovieUpload, UserMovieGetThumbnailVideo, UserMovieGetVideoData, UserMovieDelete, UserMovieAnalysisView
from app_user.views.view_movie_watching import UserMovieWatchingView, UserMovieWatching2View, UserMovieWatching3View
from app_user.views.view_tables import UserMovieListView, UserChangePasswordListView, UserCompanyUserListView, UserAnalysisResultListView
from app_user.views.views import UserDashboardView, UserChangePasswordView, UserCompanyUserView, UserChangePasswordAjaxView, UserAnalysisResultView, UserSystemSettingView

urlpatterns = [
    url(r'^$', UserDashboardView.as_view(), name="user_dashboard"),

    url(r'^password/$', UserChangePasswordView.as_view(), name="user_password"),
    url(r'^password/list/$', UserChangePasswordListView.as_view(), name="user_password_list"),
    url(r'^password/reset/$', UserChangePasswordAjaxView.as_view(), name="user_password_reset"),

    url(r'^company/user/$', UserCompanyUserView.as_view(), name="user_company_user"),
    url(r'^company/user/list/$', UserCompanyUserListView.as_view(), name="user_company_user_list"),

    url(r'^movie/$', UserMovieView.as_view(), name="user_movie"),
    url(r'^movie/list/$', UserMovieListView.as_view(), name="user_movie_list"),
    url(r'^movie/upload/$', UserMovieUpload.as_view(), name="user_movie_upload"),
    url(r'^movie/get/thumbnail/(?P<movie_id>[A-Za-z0-9_\-\.]+)/(?P<uid>[A-Za-z0-9_\-\.]+)/(?P<fn>[A-Za-z0-9_\-\.]+)/$', UserMovieGetThumbnailVideo.as_view(), name="user_get_thumbnail_movie"),
    url(r'^movie/watching/$', UserMovieWatchingView.as_view(), name="user_movie_watching_url"),
    url(r'^movie/watching/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', UserMovieWatchingView.as_view(), name="user_movie_watching"),

    url(r'^movie/watching/(?P<movie_id>[A-Za-z0-9_\-\.]+)/2/$', UserMovieWatching3View.as_view(), name="user_movie_watching2"),

    url(r'^movie/test/$', UserMovieWatching2View.as_view(), name="user_movie_test"),

    # download video data
    url(r'^movie/get/(?P<movie_id>[A-Za-z0-9_\-\.]+)/(?P<type>[A-Za-z0-9_\-\.]+)/$', UserMovieGetVideoData.as_view(), name='user_get_movie'),
    url(r'^movie/delete/$', UserMovieDelete.as_view(), name='user_movie_delete_url'),
    url(r'^movie/delete/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', UserMovieDelete.as_view(), name='user_movie_delete'),

    url(r'^movie/analysis/$', UserMovieAnalysisView.as_view(), name="user_movie_analysis_url"),
    url(r'^movie/analysis/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', UserMovieAnalysisView.as_view(), name="user_movie_analysis"),

    url(r'^analysis/results/$', UserAnalysisResultView.as_view(), name="user_analysis_result"),
    url(r'^analysis/results/list/$', UserAnalysisResultListView.as_view(), name="user_analysis_result_list_url"),
    url(r'^analysis/results/list/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', UserAnalysisResultListView.as_view(), name="user_analysis_result_list"),

    url(r'^system/setting/$', UserSystemSettingView.as_view(), name="user_system_setting"),

    # submit job
    url(r'^movie/submit/job/$', SubmitJob.as_view(), name='user_movie_submit_job_url'),
    url(r'^movie/submit/job/(?P<movie_id>[A-Za-z0-9\.]+)/$', SubmitJob.as_view(), name='user_movie_submit_job'),
    # stop job
    url(r'^movie/stop/job/(?P<movie_id>[A-Za-z0-9\.]+)/$', StopJob.as_view(), name='user_movie_stop_job'),
    # get job status
    url(r'^movie/get/job/status/$', GetJobStatus.as_view(), name="user_movie_get_job_status_url"),
    url(r'^movie/get/job/status/(?P<movie_id>[A-Za-z0-9\.]+)/$', GetJobStatus.as_view(), name="user_movie_get_job_status"),

]
