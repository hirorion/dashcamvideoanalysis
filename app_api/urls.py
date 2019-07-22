# -*- coding: utf-8 -*-
"""
    urls

    @author: $Author$
    @version: $Id$

"""
from django.conf.urls import url

from app_api.view_rest import RestAPIGetMovieAnalysisList
from app_api.views import APIDownloadData, APIMovieUpdateLog, APIMovieUpdateJobStatus, APIMovieGetStatus, APIAuthCheck, APIMovieUploadData

#router = routers.DefaultRouter()
#router.register(r'get/movie/analysis', RestAPIGetMovieAnalysisDataViewSet)

urlpatterns = [
    # ================================================================================
    # AIサーバーとのAPI
    # ================================================================================
    # update log.
    url(r'^movie/update/log/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', APIMovieUpdateLog.as_view(), name="api_movie_update_log"),

    # update job status and set message.
    url(r'^movie/update/job/status/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', APIMovieUpdateJobStatus.as_view(), name="api_movie_update_job_status"),

    # download user data
    url(r'^movie/download/$', APIDownloadData.as_view(), name='api_movie_download_data'),

    # upload user data
    url(r'^movie/upload/(?P<movie_id>[A-Za-z0-9_\-\.]+)/$', APIMovieUploadData.as_view(), name='api_movie_upload_data'),

    # get job status and message.
    url(r'^movie/get/status/(?P<movie_id>[A-Za-z0-9]+)/$', APIMovieGetStatus.as_view(), name='api_movie_status'),

    # 動画の解析結果を取得するAPI
    url(r'^movie/get/analysis/(?P<movie_id>[A-Za-z0-9]+)/$', RestAPIGetMovieAnalysisList.as_view(), name="api_movie_get_analysis"),

    # auth check
    url(r'^authcheck/$', APIAuthCheck.as_view(), name='api_auth_check'),

]
