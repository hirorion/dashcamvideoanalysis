# -*- coding: UTF-8 -*-
from django.db import models


class SystemModel(models.Model):
    """
    システムで使用できるモデルの定義を保存するテーブル
    ------------------------------------
    """
    model_dir_name = models.CharField(max_length=100, unique=True)  # モデルのディレクトリ名
    display_name = models.CharField(max_length=512)  # モデルの表示名
    model_filename = models.CharField(max_length=512)  # モデルのファイル名
    label_filename = models.CharField(max_length=512)  # ラベルのファイル名
    updated_at = models.DateTimeField(auto_now=True)  # 更新日
    is_user = models.BooleanField(default=False)  # 再学習したモデルかどうか

    class Meta:
        db_table = 'dc_system_models'
