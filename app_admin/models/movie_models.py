# -*- coding: UTF-8 -*-
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.timezone import now

from accounts.models import Users
from app_admin.models.user_models import ContractCompany

from app_admin.models.model_models import SystemModel


class UserMovie(models.Model):
    """
    動画管理
    ------------------------------------
    """
    # 契約会社ID 削除できない
    contract_company = models.ForeignKey(ContractCompany, on_delete=models.PROTECT)
    # ドライバーID 削除できない
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, blank=True, null=True, default=None)  # ドライバーと特定するためのID（NULLでもOK）
    # ドライバーID 削除できない TODO これが必要かどうか
    #contract_company_user = models.ForeignKey(ContractCompanyUser, on_delete=models.PROTECT, blank=True, null=True, default=None)

    internal_use = models.SmallIntegerField(default=0)  # 社内利用区分 0:社内利用不可、1:社内利用可
    external_use = models.SmallIntegerField(default=0)  # 社外利用区分 0:社外利用不可、1:社外利用可

    driving_day = models.DateField(blank=True, null=True, default=None)  # 運転日 (NULL OK)
    vehicle_number = models.IntegerField(default=0)  # 車両番号
    analysis_count = models.IntegerField(default=0)  # 分析回数 分析した回数
    is_save = models.BooleanField(default=False)  # 保存フラグ 0:保存しない、1:保存する 保存した動画は削除されない
    is_delete = models.BooleanField(default=False)  # 削除フラグ 0:未削除、1:削除済
    vehicle_type = models.SmallIntegerField(default=0)  # 車両種別区分 (属性情報)・分析の為に使用する車両種別・大型／中型を管理

    status = models.IntegerField(default=0)  # 0:None 1:creating 2:completion 3:stopped 10:any -1:error
    status_message = models.CharField(max_length=255, null=True, blank=True, default=None)
    unique_filename = models.CharField(max_length=512)  # システム保存名(拡張子付き)
    filename = models.CharField(max_length=512)  # アップロードされたファイル名
    length = models.IntegerField(null=True, blank=True, default=None)  # 録音長さ(秒)
    media_type = models.CharField(max_length=100, null=True, blank=True, default=None)  # audio/video
    meta_data = models.TextField(null=True, blank=True, default=None)  # アップロードされたファイル名のメタ情報

    parameter = models.CharField(max_length=512, null=True, blank=True, default=None)  # 書き起こしパラメータ名

    user_model = models.ForeignKey(SystemModel, on_delete=models.SET_NULL, null=True, blank=True, default=None)  # N:1 このデータに使ったモデル。既存レコードはnullなので、書き起こし時にモデルを指定させる

    user_model_name = models.CharField(max_length=512, null=True, blank=True, default=None)  # 設定したモデル名を保存
    user_parameter_name = models.CharField(max_length=521, null=True, blank=True, default=None)  # 設定したパラメーター名を保存

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_user_movies'


class UserMovieProgress(models.Model):
    """
    動画作成状況
    """
    progress = models.IntegerField(null=True, blank=True, default=None)  # %
    created_json_flag = models.BooleanField(default=False)  # vott jsonが完成したかどうかを判断
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    user_movie = models.ForeignKey(UserMovie, on_delete=models.PROTECT)  # N:1

    class Meta:
        db_table = 'dc_user_movie_progress'


class UserMovieStatusLog(models.Model):
    """
    動画作成のログ
    """
    log = models.TextField(default=None)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    user_movie = models.ForeignKey(UserMovie, on_delete=models.PROTECT)  # N:1

    class Meta:
        db_table = 'dc_user_movie_status_logs'


class UserMovieAnalysisResult(models.Model):
    """
    動画の解析結果で、不安全運転の情報を管理するテーブル
    """
    data = JSONField()  # カテゴリ、動画再生位置などを示したJSONファイル
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    user_movie = models.ForeignKey(UserMovie, on_delete=models.PROTECT)  # N:1

    class Meta:
        db_table = 'dc_user_movie_analysis_results'
