# -*- coding: UTF-8 -*-

# Create your views here.
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated

from app_admin.models.movie_models import UserMovieAnalysisResult
from app_api.serializers import UserMovieAnalysisDataSerializer


class RestAPIGetMovieAnalysisList(generics.ListAPIView):
    """
    その動画の不安全運転のパラメータを取得する
    """
    permission_classes = (IsAuthenticated,)
    #queryset = UserMovieAnalysisResult.objects.all()
    serializer_class = UserMovieAnalysisDataSerializer
    lookup_url_kwarg = "movie_id"

    # APIのフィルタで使えるフィールドを指定
    # filter_fields = ("id", "data", "user_movie_id")

    def get_queryset(self):
        mvid = self.kwargs.get(self.lookup_url_kwarg)
        ret = UserMovieAnalysisResult.objects.filter(user_movie_id=mvid)
        return ret
