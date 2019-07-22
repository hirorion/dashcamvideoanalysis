# -*- coding: UTF-8 -*-
import pandas as pd
from django.db import models
from django.utils import timezone

from app_admin.models.info_models import ServiceInfo, BusinessType


class IrricUser(models.Model):
    """
    IRRICユーザー情報
    ------------------------------------
    IRRICユーザー情報を管理する。
    """
    name = models.CharField(max_length=40)  # 氏名
    furigana = models.CharField(max_length=40)  # ふりがな

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_irric_users'


class ContractCompany(models.Model):
    """
    契約会社
    ------------------------------------
    契約会社の情報を管理する。
    """
    name = models.CharField(max_length=100)  # 契約会社名
    furigana = models.CharField(max_length=100)  # ふりがな

    department_name = models.CharField(max_length=80)  # 部署名
    contract_start_date = models.DateTimeField()  # 契約期間開始日
    contract_end_date = models.DateTimeField()  # 契約期間終了日
    diagnosis_date = models.DateTimeField()  # 診断実施日
    is_diagnosis_complete = models.BooleanField(default=False)  # 診断完了フラグ 0:未完了 1:完了

    # # 事業種別区分
    business_type = models.ForeignKey(BusinessType, on_delete=models.PROTECT)

    # サービス情報 削除できない
    service_info = models.ForeignKey(ServiceInfo, on_delete=models.PROTECT)

    # 主担当コンサルタントのユーザID 削除できない
    main_consultant_irric_user = models.ForeignKey(IrricUser, on_delete=models.PROTECT)

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    @property
    def get_status_string(self):
        if self.contract_start_date <= timezone.now() <= self.contract_end_date:
            return "契約中"
        else:
            return "契約終了"

    class Meta:
        db_table = 'dc_contract_companies'


class ContractCompanyUser(models.Model):
    """
    契約会社ユーザ情報
    ------------------------------------
    契約社管理者、ドライバーの情報を管理します。
    属性情報も管理します。
    """
    name = models.CharField(max_length=40)  # 氏名
    furigana = models.CharField(max_length=40)  # ふりがな

    # id 管理者WEBログイン用のID(社員番号)
    gender = models.SmallIntegerField()  # 性別区分 (属性情報)0:男性、1:女性
    birth_date = models.DateField()  # 生年月日 (属性情報)運転経験年数を識別する為に使用
    recruit_date = models.DateField()  # 採用年月日 (属性情報)
    total_mileage = models.SmallIntegerField()  # 年間走行距離 (属性情報)
    age = models.IntegerField(blank=True, null=True, default=None)  # 年齢 (テーブルでソートするに必要)
    # TODO 運転履歴をここに入れないとテーブルでソートできない

    # 契約会社ID 削除できない
    contract_company = models.ForeignKey(ContractCompany, on_delete=models.PROTECT)

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    @property
    def user_id(self):
        from accounts.models import Users
        return Users.objects.get(contract_company_user_id=self.id).username

    def get_age(self):
        """
        年齢
        :return: int
        """
        if self.birth_date:
            today = int(pd.to_datetime('today').strftime('%Y%m%d'))
            birthday = int(self.birth_date.strftime('%Y%m%d'))
            return int((today - birthday) / 10000)

        return None

    @property
    def get_status_string(self):
        from accounts.models import Users
        user = Users.objects.get(contract_company_user_id=self.id)
        if user.is_inactive is False:
            return "利用中"
        else:
            return "利用停止中"

    class Meta:
        db_table = 'dc_contract_company_users'


class UserContractCompanyRelated(models.Model):
    """
    IRRICユーザー契約会社関連
    ------------------------------------
    IRRICユーザと契約会社社の紐付きを管理する情報。
    契約会社に対して主担当と主担当ではないが編集権限を持つ全てのユーザを管理する。
    """
    primary_type = models.SmallIntegerField()  # 主担当区分 0:主担当ではない、1:主担当

    # ユーザID 削除できない
    irric_user = models.ForeignKey(IrricUser, on_delete=models.PROTECT)

    # 契約会社ID 削除できない
    contract_company = models.ForeignKey(ContractCompany, on_delete=models.PROTECT)

    # 作成、更新関係の共通カラム
    created_user_id = models.CharField(max_length=8)  # 作成ユーザー
    updated_user_id = models.CharField(max_length=8)  # 更新ユーザー
    created_at = models.DateTimeField(auto_now_add=True)  # 作成日時
    updated_at = models.DateTimeField(auto_now_add=True)  # 更新日時

    class Meta:
        db_table = 'dc_user_contract_company_related'
