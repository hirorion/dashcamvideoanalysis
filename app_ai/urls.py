# -*- coding: UTF-8 -*-
from django.conf.urls import url

from app_ai.views import AiMovieSearchView, AiMovieSearchListView, AiMovieGetImageAjaxView, AiMovieDrawFrameView, AiMovieDrawFrameGetDataView, AiMovieSearchCustomView

urlpatterns = [
    url(r'^$', AiMovieSearchView.as_view(), name="ai_movie_search"),
    url(r'^list/$', AiMovieSearchListView.as_view(), name="ai_movie_list"),
    url(r'^img/$', AiMovieGetImageAjaxView.as_view(), name="ai_movie_get_image_url"),
    url(r'^img/(?P<movie_id>[A-Za-z0-9_\-\.]+)/(?P<fno>[A-Za-z0-9_\-\.]+)/$', AiMovieGetImageAjaxView.as_view(), name="ai_movie_get_image"),

    url(r'^draw/$', AiMovieDrawFrameView.as_view(), name="ai_movie_draw_frame"),
    url(r'^draw/get/data/(?P<movie_id>[A-Za-z0-9_\-\.]+)/(?P<start_fno>[A-Za-z0-9_\-\.]+)/(?P<end_fno>[A-Za-z0-9_\-\.]+)/$', AiMovieDrawFrameGetDataView.as_view(), name="ai_movie_frame_get_data"),
    url(r'^draw/get/data/', AiMovieDrawFrameGetDataView.as_view(), name="ai_movie_frame_get_data_url"),

    url(r'^custom/', AiMovieSearchCustomView.as_view(), name="ai_movie_search_custom"),

]
