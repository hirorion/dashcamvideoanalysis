# -*- coding: utf-8 -*-
"""
    管理者機能フォーム
"""
from django import forms
from django.forms import Widget, CheckboxInput
from django.forms.widgets import boolean_check

from accounts.models import Users


class AdminPasswordResetForm(forms.Form):
    """
    パスワード再設定の検索フォーム
    """

    search_type = forms.ChoiceField()
    search_name = forms.CharField()

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class RightCheckbox(Widget):
    render = CheckboxInput().render

    def __init__(self, attrs=None, check_test=None):
        super(RightCheckbox, self).__init__(attrs)
        self.check_test = boolean_check if check_test is None else check_test


class AdminIrricUserSearchForm(forms.Form):
    """
    IRRICユーザー管理の検索フォーム
    """

    login_id = forms.CharField(label="ログインID")
    name = forms.CharField(label="氏名")
    consultation_incomplete = forms.BooleanField(label='対面コンサル未実施有', widget=RightCheckbox(attrs={'class': 'check'}))
    report_incomplete = forms.BooleanField(label='診断レポート未提出有', widget=RightCheckbox(attrs={'class': 'check'}))

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


# TODO グループは別で定義した方がいい
IRRIC_USER_LEVEL_CHOICES = (
    (-1, '選択してください'),
    (2, 'システム管理者'),
    (3, 'コンサル担当')
)


class AdminIrricUserForm(forms.Form):
    """
    IRRICユーザーのベースフォーム
    """
    login_id = forms.CharField(label="ログインID", required=True)
    name = forms.CharField(label="氏名", required=True)
    furigana = forms.CharField(label="ふりがな", required=True)
    email = forms.EmailField(label="メールアドレス", required=True)
    level = forms.ChoiceField(
        label='利用者レベル',
        widget=forms.Select,
        choices=IRRIC_USER_LEVEL_CHOICES,
        required=True,
    )


class AdminIrricUserNewForm(AdminIrricUserForm):
    """
    IRRICユーザーの登録フォーム
    """
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(label="パスワード確認", widget=forms.PasswordInput(), required=True)

    password_auto_flag = forms.BooleanField(label='パスワード自動生成', initial=False, required=False, widget=RightCheckbox(attrs={'class': 'check'}))
    password_reset_next_login_flag = forms.BooleanField(label='次回ログイン時に強制的にパスワードを変更', initial=False, required=False, widget=RightCheckbox(attrs={'class': 'check'}))
    send_mail_flag = forms.BooleanField(label='アカウント情報をユーザーにメール送信', initial=False, required=False, widget=RightCheckbox(attrs={'class': 'check'}))

    def clean_login_id(self):
        login_id = self.cleaned_data['login_id']
        if len(login_id) != 8:
            raise forms.ValidationError('ログインIDは8文字で設定してください。')
        if Users.objects.filter(username=login_id).exists():
            raise forms.ValidationError('このログインIDはすでに使用中です。')
        return login_id

    def clean_level(self):
        level = self.cleaned_data['level']
        if int(level) == -1:
            raise forms.ValidationError('利用者レベルを選択してください')
        return level

    def clean_password2(self):
        password = self.cleaned_data['password']
        password2 = self.cleaned_data['password2']
        if password != password2:
            raise forms.ValidationError('パスワードが一致しません。')
        return password2

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class AdminIrricUserUpdateForm(AdminIrricUserForm):
    """
    IRRICユーザーの更新フォーム
    """
    def clean_level(self):
        level = self.cleaned_data['level']
        if int(level) == -1:
            raise forms.ValidationError('利用者レベルを選択してください')
        return level

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class AdminContractCompanyForm(forms.Form):
    """
    契約会社管理の検索フォーム
    """

    contract_id = forms.CharField()
    company_name = forms.CharField()
    company_consultant_name = forms.CharField()
    service_pattern_a = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_pattern_b = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_pattern_c = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_truck = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_bus = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_taxi = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_other = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))

    contract_start_date = forms.CharField()
    contract_end_date = forms.CharField()

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class AdminUserUsageForm(forms.Form):
    """
    利用状況の検索フォーム
    """

    company_name = forms.CharField()
    service_pattern_a = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_pattern_b = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_pattern_c = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_truck = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_bus = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_taxi = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))
    service_type_other = forms.BooleanField(widget=RightCheckbox(attrs={'class': 'check'}))

    contract_start_date = forms.CharField()
    contract_end_date = forms.CharField()

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class AdminNoticeForm(forms.Form):
    """
    お知らせ管理の検索フォーム
    """

    publish_start_date = forms.CharField()
    publish_end_date = forms.CharField()

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data
