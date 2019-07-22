# -*- coding: UTF-8 -*-
from django.db import models


class SystemInfo(models.Model):
    """
    システム情報
    ------------------------------------
    システム情報を管理する。
    """
    admin_unusable_from_date = models.DateTimeField(blank=True, null=True, default=None)   # 管理者機能システム停止時間from
    admin_unusable_to_date = models.DateTimeField(blank=True, null=True, default=None)  # 管理者機能システム停止時間to
    user_unusable_from_date = models.DateTimeField(blank=True, null=True, default=None)   # ユーザポータル停止時間from
    user_unusable_to_date = models.DateTimeField(blank=True, null=True, default=None)  # ユーザポータル停止時間to

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_system_info'


class ServiceInfo(models.Model):
    """
    サービス情報
    ------------------------------------
    サービスパターンの情報を管理する。
    """
    service_name = models.CharField(max_length=40)  # サービス名称
    available_users = models.IntegerField()  # システムを利用可能なユーザ数
    available_movies = models.IntegerField()  # アップロード可能動画数
    valid_start_date = models.DateTimeField()   # サービスの有効期間開始日
    valid_end_date = models.DateTimeField()  # サービスの有効期間終了日

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_service_info'


class BusinessType(models.Model):
    """
    事業種別情報
    ------------------------------------
    事業種別の情報を管理する。
    """
    type_name = models.CharField(max_length=40)  # 種別名

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_business_type'
