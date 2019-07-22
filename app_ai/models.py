# -*- coding: UTF-8 -*-
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.query import RawQuerySet

from app_admin.models.movie_models import UserMovie


class AiMovie(models.Model):
    """
    ムービー情報
    """
    # アップした動画ファイル名
    name = models.CharField(max_length=512)
    # システム保存名(拡張子付き)
    unique_name = models.CharField(max_length=512)
    # JSON解析結果ファイル名
    json_path = models.CharField(max_length=512)
    # ユーザーがアップした動画のID（DASHCAM_WEB user_movieのid)
    user_movie_id = models.IntegerField(blank=True, null=True, default=None)
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'ai_movies'


class AiFrameInfo(models.Model):
    """
    フレーム情報
    """
    id = models.BigAutoField(primary_key=True)
    fno = models.IntegerField()  # フレーム番号
    speed = models.FloatField()  # そのフレームの自車の速度
    meta = JSONField(encoder=DjangoJSONEncoder)  # フレームに関する情報

    # 動画
    movie = models.ForeignKey(AiMovie, on_delete=models.PROTECT)

    class Meta:
        db_table = 'ai_frame_info'
        indexes = [
            models.Index(fields=['movie', 'fno', 'speed']),
        ]


class CountableRawQuerySet(RawQuerySet):
    """
    rawでのカウント処理の拡張
    """
    def count(self):
        return sum([1 for obj in self])
        #return len(list(self))


class AiFrameObjectManager(models.Manager):
    """
    rawで検索させるための拡張
    """
    def raw(self, raw_query, params=None, *args, **kwargs):
        return CountableRawQuerySet(raw_query=raw_query, model=self.model, params=params, using=self._db, *args, **kwargs)


class AiFrameObject(models.Model):
    """
    フレームのオブジェクト毎のテーブル
    """
    id = models.BigAutoField(primary_key=True)
    fno = models.IntegerField()  # フレーム番号
    tag = models.CharField(max_length=256)  # 認識オブジェクトタグ名
    score = models.FloatField()  # 認識オブジェクトスコア
    pose_ground_center = models.FloatField(default=0)  # グランド認識オブジェクトのセンター位置
    data = JSONField(encoder=DjangoJSONEncoder)  # 認識オブジェクトに関する情報（JSONで格納）

    # 動画
    movie = models.ForeignKey(AiMovie, on_delete=models.PROTECT)

    objects = AiFrameObjectManager()

    class Meta:
        db_table = 'ai_frame_objects'
        indexes = [
            models.Index(fields=['movie', 'fno', 'tag']),
            models.Index(fields=['movie', 'fno', 'tag', 'score']),
            models.Index(fields=['movie', 'fno', 'tag', 'score', 'pose_ground_center']),
        ]


class AiFrameObjectTags(models.Model):
    """
    オブジェクト検索用テーブル
    フレームにあるオブジェクトのタグがリストで保存される
    """
    id = models.BigAutoField(primary_key=True)
    fno = models.IntegerField()
    tag = JSONField(encoder=DjangoJSONEncoder)

    movie = models.ForeignKey(AiMovie, on_delete=models.PROTECT)

    class Meta:
        db_table = 'ai_frame_object_tags'
