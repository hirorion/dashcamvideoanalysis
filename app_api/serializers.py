from rest_framework import serializers

from app_admin.models.movie_models import UserMovieAnalysisResult


class UserMovieAnalysisDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserMovieAnalysisResult
        fields = ("id", "data", "user_movie_id")
