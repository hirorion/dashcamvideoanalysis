# -*- coding: utf-8 -*-
"""
    管理者機能フォーム
"""
from django import forms
from django.forms import Widget, CheckboxInput
from django.forms.widgets import boolean_check


class UserPasswordResetForm(forms.Form):
    """
    パスワード再設定の検索フォーム
    """

    search_name = forms.ChoiceField()

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


class UserCompanyUserForm(forms.Form):
    """
    ドライバー管理の検索フォーム
    """

    login_id = forms.CharField(label="ログインID")
    shimei = forms.CharField(label="氏名")
    consultation_incomplete = forms.BooleanField(label='対面コンサル未実施有', widget=RightCheckbox(attrs={'class': 'check'}))
    report_incomplete = forms.BooleanField(label='診断レポート未提出有', widget=RightCheckbox(attrs={'class': 'check'}))

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class UserMovieSearchForm(forms.Form):
    """
    動画管理の検索フォーム
    """
    VIOLATION_TYPE = [
        (1, '法令遵守'),
        (2, '運転操作'),
        (3, 'その他'),
    ]
    VIOLATION_ITEM = [
        (1, '赤信号無視'),
        (2, '停止できるタイミングの黄信号通過'),
        (3, '速度超過'),
        (4, '駐車禁止場所での駐車'),
    ]

    driver_id = forms.CharField(label="ドライバーID")
    name = forms.CharField(label="氏名")
    violation_type = forms.ChoiceField(choices=VIOLATION_TYPE)
    violation_item = forms.ChoiceField(choices=VIOLATION_ITEM)

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data


class UserMovieUploadForm(forms.Form):
    """
    動画のアップロードフォーム
    """
    driver_id = forms.ChoiceField(required=True)
    vehicle_no = forms.CharField(required=True)
    vehicle_type = forms.CharField(required=True)
    drive_record_maker = forms.CharField(required=True)
    drive_record_typeno = forms.CharField(required=True)
    drive_record_high = forms.CharField(required=True)

    def clean(self):
        """
        全文の個別クリーンが終わってから呼ばれる
        :return:
        """
        cleaned_data = self.cleaned_data

        return cleaned_data

