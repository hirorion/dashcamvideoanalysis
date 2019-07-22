# -*- coding: UTF-8 -*-
import random

import pytz
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.db import models
from django.db.models import SmallIntegerField

from app_admin.models.user_models import IrricUser, ContractCompany, ContractCompanyUser


class UserGroup(models.Model):
    """
    ユーザーグループ情報
    """
    id = models.IntegerField(primary_key=True)  # 自動裁判ではないID
    group_name = models.CharField(max_length=40)  # グループ名称
    admin_functions_class = SmallIntegerField()  # 管理者機能使用区分

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_user_groups'


class UserManager(BaseUserManager):
    """TODO: django2.2からBaseUserManagerにこれらがない"""
    """ユーザーマネージャクラス"""
    use_in_migrations = True

    def _create_user(self, username, email, password, group_id, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        if not email:
            email = self.normalize_email(email)
        if not group_id:
            raise ValueError('The given group_id must be set')

        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, user_group_id=group_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, group_id=None, **extra_fields):
        return self._create_user(username, email, password, group_id, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        #extra_fields.setdefault('is_staff', True)
        #extra_fields.setdefault('is_superuser', True)
        #if extra_fields.get('is_staff') is not True:
        #    raise ValueError('Superuser must have is_staff=True.')
        #if extra_fields.get('is_superuser') is not True:
        #    raise ValueError('Superuser must have is_superuser=True.')

        irric_user = IrricUser()
        irric_user.name = "システム管理者"
        irric_user.furigana = ""
        irric_user.save()

        user_group_id = 1
        extra_fields.setdefault('irric_user_id', irric_user.id)

        return self._create_user(username, None, password, user_group_id, **extra_fields)


class Users(AbstractBaseUser):
    """
    ユーザー情報
    """
    username = models.CharField(max_length=256, unique=True)  # ログイン用のID(社員番号、契約会社ID、契約会社ユーザーID)

    email = models.EmailField(max_length=256, blank=True, null=True, default=None)  # email

    is_force_password_change = models.BooleanField(default=False)  # パスワード強制変更フラグ 0:強制変更無,1:強制変更有
    is_delete = models.BooleanField(default=False)  # 削除フラグ 0:未削除、1:削除済
    is_inactive = models.BooleanField(default=False)  # 利用停止フラグ 0:利用可、1:利用停止中

    # AbstractBaseUserから継承される
    # password = models.CharField(_('password'), max_length=128)   # パスワード
    # last_login = models.DateTimeField(_('last login'), blank=True, null=True)  # 最終ログイン日時

    # グループ 削除できない
    user_group = models.ForeignKey(UserGroup, on_delete=models.PROTECT)  # ユーザーグループ情報を特定する為のID

    irric_user = models.ForeignKey(IrricUser, on_delete=models.PROTECT, blank=True, null=True, default=None)  # IRRICユーザー情報を特定する為のID
    contract_company = models.ForeignKey(ContractCompany, on_delete=models.PROTECT, blank=True, null=True, default=None)  # 契約会社情報を特定する為のID
    contract_company_user = models.ForeignKey(ContractCompanyUser, on_delete=models.PROTECT, blank=True, null=True, default=None)  # 契約会社ドライバー情報を特定する為のID

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    timezone = pytz.timezone('Asia/Tokyo')

    @property
    def generate_password(self):
        alphabet = "abcdefghijkmnopqrstuwxyzABCDEFGHJKLMNPQRSTUWXYZ23456789"
        return "".join([random.choice(alphabet) for x in range(10)])

    @classmethod
    def get_valid_user_from_id(cls, user_id):
        """
        有効なユーザーをidで取得する
        :param user_id:
        :return:
        """
        return cls.objects.get(id=user_id, is_inactive=False)

    @property
    def get_last_login_date(self):
        """
        最終ログイン日時をJSTで返す
        :return:
        """
        last_login = self.last_login
        if last_login:
            return last_login.astimezone(self.timezone).strftime('%Y-%-m-%-d %H:%M:%S')
        else:
            return "未ログイン"

    @property
    def get_is_active_string(self):
        if self.is_inactive is False:
            return "利用中"
        else:
            return "利用停止中"

    def my_update(self, updated_user_id):
        """
        アップデートするときに指定ユーザーをセットする
        :param updated_user_id:
        :return:
        """
        self.updated_user_id = updated_user_id
        self.save()

    def my_new_save(self, created_user_id):
        """
        新規作成するときに指定ユーザーをセットする
        :param created_user_id:
        :return:
        """
        self.created_user_id = created_user_id
        self.updated_user_id = created_user_id
        self.save()

    class Meta:
        db_table = 'dc_users'
