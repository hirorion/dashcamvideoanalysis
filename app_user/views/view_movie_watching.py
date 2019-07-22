# -*- coding: UTF-8 -*-
import logging

# Create your views here.
import os

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from app_admin.models.movie_models import UserMovie
from app_user.forms import UserMovieSearchForm
from app_user.upload_mixin import get_meta_data, mv_creation_time, detecting_fps
from app_user.views.view_job import SetUserMixin, MoviePermissionMixin
from config.settings import MEDIA_ROOT
from lib.mixin import LoginRequiredMixin

logger = logging.getLogger(__name__)


class UserMovieWatchingView(LoginRequiredMixin, SetUserMixin, MoviePermissionMixin, FormView):
    """
    分析動画表示画面
    """
    template_name = 'user/movie_watching/movie_watching.html'
    form_class = UserMovieSearchForm

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        movie = get_object_or_404(UserMovie, id=self.movie_id)

        # 動画基本情報を取得
        path = os.path.join(MEDIA_ROOT, movie.user.username)
        movie_path = os.path.join(path, movie.unique_filename)
        try:
            json_meta_data = get_meta_data(movie_path)
        except Exception as e:
            logger.exception(e)
            raise Exception("file is invalid")

        if json_meta_data is None:
            raise Exception("json is None: %s" % movie_path)
        logger.debug("save_path = %s, ffprobe json = %s" % (movie_path, json_meta_data))

        dt = mv_creation_time(json_meta_data)
        dt_disp = None
        if dt is not None:
            dt_disp = dt.strftime('%Y-%-m-%-d %H:%M:%S')
            dt = dt.strftime('%Y-%m-%dT%H:%M:%S+09:00')

        fps = detecting_fps(json_meta_data)

        if movie.status == 1:
            # 処理中
            context.update({
                "disabled": "disabled"
            })
        elif movie.status == 2:
            # 成功
            context.update({
                "labeled_video_enable": True
            })

        org_url = reverse("user_get_movie", kwargs={'movie_id': self.movie_id, 'type': 'org_pv'})
        # 直接staticディレクトリを参照するように変更(TODO 動画は直接staticにあるのでセキュリティをどうするか)
        #unique_id, ext = os.path.splitext(movie.path)
        #mpath = os.path.join(movie.user.username, unique_id + "_pv.mp4")
        #if not os.path.exists(os.path.join(MEDIA_ROOT, mpath)):
        #    mpath = os.path.join(movie.user.username, movie.path)
        #if not os.path.exists(os.path.join(MEDIA_ROOT, mpath)):
        #    mpath = os.path.join("img", "waiting.mp4")
        #org_url = mpath

        labeled_url = reverse("user_get_movie", kwargs={'movie_id': self.movie_id, 'type': 'labeled'})

        context.update({
            "fps": fps,
            "creation_date_disp": dt_disp,
            "creation_date": dt,
            "movie": movie,
            "org_url": org_url,
            "labeled_url": labeled_url,
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


class UserMovieWatching3View(UserMovieWatchingView):
    template_name = 'user/movie_watching/movie_watching2.html'


class UserMovieWatching2View(LoginRequiredMixin, TemplateView):
    """
    未使用
    """
    template_name = 'user/movie_watching/test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context
