# -*- coding: UTF-8 -*-
import os

import pandas as pd
import pytz
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
from django.db.models import Q
from django.urls import reverse
from django_datatables_view.base_datatable_view import BaseDatatableView

from accounts.models import Users
from app_admin.models.movie_models import UserMovie, UserMovieAnalysisResult
from app_user.views.view_job import SetUserMixinForDataTable, NotAllowGetMethodMixin
from config.settings import MEDIA_ROOT


class UserChangePasswordListView(LoginRequiredMixin, SetUserMixinForDataTable, NotAllowGetMethodMixin, BaseDatatableView):
    """
    パスワード変更のユーザーリストのJSONを返す
    POST処理なので、csrf_tokenがない画面からは受付されない
    （つまりその画面で正しくリストが作られていれば大丈夫ってこと）
    GETで来た場合はエラーにされる
    """

    # The model we're going to show
    model = Users

    columns = ['']

    order_columns = ['id', 'username', 'user_group.group_name', 'name', 'email', 'created_at', 'updated_at']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        search_name = self.request.POST.get("search_name", None)
        search_user_group = self.request.POST.get("search_user_group", None)

        # 契約会社管理者とドライバー
        company_id = self.user.contract_company.id
        if self.user.user_group.id == 4 and company_id is not None:   # TODO ユーザーグループをどこかで定義した方がいい
            # 契約会社管理者
            cond1 = Q(is_inactive=False, is_delete=False, contract_company_id=company_id)
        else:
            # ドライバー
            cond1 = Q(is_inactive=False, is_delete=False, id=self.user.id)

        if search_user_group is not None and search_user_group == "1":
            # ドライバーのみ
            cond2 = Q(user_group_id=5)
            sobj = self.model.objects.filter(cond1, cond2)
        else:
            if search_name is not None and search_name != "":
                sobj = self.model.objects.filter(cond1, contract_company_user__name__contains=search_name)
            else:
                sobj = self.model.objects.filter(cond1)

        return sobj

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            # チェックフォーム
            checkbox_contents = "<input type='checkbox' name='selected' value='%d'>" % item.id

            # ドライバー氏名/会社名
            name = None
            if item.contract_company_user_id is not None:
                name = item.contract_company_user.name
            elif item.contract_company_id is not None:
                name = item.contract_company.name

            json_data.append({
                "dataId": "row_%d" % item.id,
                "checkbox_contents": checkbox_contents,
                "username": item.username,
                "group": item.user_group.group_name,
                "name": name,
                "email": item.email,
                "created_at": item.created_at.strftime('%Y-%-m-%-d %H:%M:%S'),
                "updated_at": item.updated_at.strftime('%Y-%-m-%-d %H:%M:%S'),
                })
        return json_data

    def ordering(self, qs):
        """
        ソートのorderをsuperに実行させ、セッションに覚える
        :param qs:
        :return:
        """
        qs = super().ordering(qs)
        #self.request.session['table_query_orderby'] = qs.query.order_by
        return qs

    def filter_queryset(self, qs):
        """
        検索のカラムを覚える
        :param qs:
        :return:
        """
        qs = super().filter_queryset(qs)
        return qs


class UserCompanyUserListView(LoginRequiredMixin, SetUserMixinForDataTable, NotAllowGetMethodMixin, BaseDatatableView):
    """
    ドライバーリストのJSONを返す
    POST処理なので、csrf_tokenがない画面からは受付されない
    （つまりその画面で正しくリストが作られていれば大丈夫ってこと）
    """

    # The model we're going to show
    model = Users

    # define the columns that will be returned
    columns = ['']

    order_columns = ['id', 'username', '', 'contract_company_user.name', 'contract_company_user.gender', 'contract_company_user.birth_date', 'contract_company_user.age',  'contract_company_user.recruit_date', '', 'last_login']

    def get_initial_queryset(self):
        search_login_id = self.request.POST.get("search_login_id", None)
        search_name = self.request.POST.get("search_name", None)
        search_type = self.request.POST.get("search_type", None)

        # 契約会社管理者とドライバー
        company_id = self.user.contract_company.id
        if self.user.user_group.id == 4 and company_id is not None:  # TODO ユーザーグループをどこかで定義した方がいい
            # 契約会社管理者
            # 自分以外のドライバー一覧で検索
            cond1 = Q(is_delete=False, contract_company_id=company_id)
            cond2 = ~Q(id=self.user.id)
        else:
            # ドライバー自身
            cond1 = Q(is_delete=False)
            cond2 = Q(id=self.user.id)

        sobj = self.model.objects.filter(cond1, cond2)

        if search_type is not None and search_type != "":
            if search_type == '1':  # 利用中
                cond3 = Q(is_inactive=False)
                sobj = self.model.objects.filter(cond1, cond2, cond3)
            elif search_type == '2':  # 利用停止中
                cond3 = Q(is_inactive=True)
                sobj = self.model.objects.filter(cond1, cond2, cond3)

        else:
            cond3 = Q()
            if search_login_id is not None and search_login_id != "":
                cond3 = Q(username__contains=search_login_id)
                sobj = self.model.objects.filter(cond1, cond2, cond3)

            if search_name is not None and search_name != "":
                cond4 = Q(contract_company_user__name__contains=search_name)
                sobj = self.model.objects.filter(cond1, cond2, cond3, cond4)

        return sobj

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        timezone = pytz.timezone('Asia/Tokyo')

        json_data = []
        for item in qs:
            # チェックフォーム
            checkbox_contents = "<input type='checkbox' name='selected' value='%d'>" % item.id

            # ドライバー氏名/会社名
            name = None
            if item.contract_company_user_id is not None:
                name = item.contract_company_user.name
            elif item.contract_company_id is not None:
                name = item.contract_company.name

            # 性別
            gender = None
            if item.contract_company_user.gender == 0:
                gender = "男性"
            else:
                gender = "女性"

            # 生年月日
            birthday = item.contract_company_user.birth_date
            if birthday:
                birthday = birthday.strftime('%Y-%-m-%-d')

            # 年齢
            age = item.contract_company_user.age
            if age:
                age = "%d歳" % age

            # 採用年月日
            recruit_date = item.contract_company_user.recruit_date
            if recruit_date:
                recruit_date = recruit_date.strftime('%Y-%-m-%-d')

            json_data.append({
                "dataId": "row_%d" % item.id,
                "checkbox_contents": checkbox_contents,
                "username": item.username,
                "status": item.contract_company_user.get_status_string,
                "name": name,
                "gender": gender,
                "birthday": birthday,
                "age": age,
                "recruit_date": recruit_date,
                "history_driving": "",  # TODO この項目は？
                "last_login": item.get_last_login_date
                })
        return json_data


class UserMovieListView(LoginRequiredMixin, SetUserMixinForDataTable, NotAllowGetMethodMixin, BaseDatatableView):
    """
    動画リストのJSONを返す
    """

    # The model we're going to show
    model = UserMovie

    # define the columns that will be returned
    columns = ['']

    order_columns = ['id', 'user.username', '', '', 'driving_day', 'status', 'is_save']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        search_driver_id = self.request.POST.get("search_driver_id", None)
        search_driver_name = self.request.POST.get("search_driver_name", None)
        search_contract_start_date = self.request.POST.get("search_contract_start_date", None)
        search_contract_end_date = self.request.POST.get("search_contract_end_date", None)
        search_violation_type = self.request.POST.get("search_violation_type", None)
        search_violation_item = self.request.POST.get("search_violation_item", None)
        search_status = self.request.POST.get("search_status", None)

        # 契約会社管理者とドライバーの動画一覧の条件をセット
        company_id = self.user.contract_company.id
        if self.user.user_group.id == 4 and company_id is not None:  # TODO ユーザーグループをどこかで定義した方がいい
            # 契約会社管理者
            # 自分以外のドライバー一覧で検索
            cond = ~Q(id=self.user.id)  # 自分以外
            driver_objs = Users.objects.filter(cond, contract_company_user__isnull=False, contract_company_id=self.user.contract_company.id)
            ids = [d.id for d in driver_objs]
            cond1 = Q(is_delete=False, user_id__in=ids)  # TODO ユーザーがいない場合の確認
        else:
            # ドライバー自身
            cond1 = Q(is_delete=False, user_id=self.user.id)

        sobj = self.model.objects.filter(cond1)

        if search_status is not None and search_status != "":
            # ショートカット検索
            cond2 = Q()
            if search_status == '1':  # 分析前
                cond2 = Q(status=0)
                sobj = self.model.objects.filter(cond1, cond2)
            elif search_status == '2':  # 分析中
                cond2 = Q(status=1)
                sobj = self.model.objects.filter(cond1, cond2)
            elif search_status == '3':  # 分析完了
                cond2 = Q(status=2)
            sobj = self.model.objects.filter(cond1, cond2)

        else:
            # 通常検索
            cond2 = Q()
            if search_driver_id is not None and search_driver_id != "":
                cond2 = Q(user_id=search_driver_id)
                sobj = self.model.objects.filter(cond1, cond2)

            if search_driver_name is not None and search_driver_name != "":
                cond3 = Q(user__contract_company_user__name__contains=search_driver_name)
                sobj = self.model.objects.filter(cond1, cond2, cond3)

        return sobj

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        i = 0
        for item in qs:
            # チェックフォーム
            checkbox_contents = "<input type='checkbox' name='selected' value='%d'>" % item.id

            # サムネイル動画の取得のURL
            fn, ext = os.path.splitext(item.unique_filename)
            thumb_path = os.path.join(MEDIA_ROOT, item.user.username, fn + ".jpg")
            if os.path.exists(thumb_path):
                thumb_movie_url = reverse("user_get_thumbnail_movie", kwargs={'movie_id': item.id, 'uid': item.user.username, 'fn': fn})
                movie = "<a id='preview%d' class='video-preview' data-frames='30' data-preview-id=%d data-source='%s'></a><script>$('#preview%d').videoPreview();</script>" % (i, i, thumb_movie_url, i)
            else:
                thumb_movie_url = "/static/img/waiting.jpg"
                movie = "<img style='width: 150px' src='%s'>" % thumb_movie_url

            movie_info = ""
            if item.driving_day is not None:
                movie_info = "%s" % item.driving_day.strftime('%Y-%-m-%-d')
            if item.length is not None:
                movie_info = movie_info + "<br>%d秒" % item.length
            if item.filename is not None:
                movie_info = movie_info + "<br>" + item.filename

            status = None
            if item.status == 0:
                status = "分析前"
            elif item.status == 1:
                status = "分析中"
            elif item.status == 2:
                status = "分析完了"
            elif item.status == -1:
                status = "分析エラー"

            json_data.append({
                "dataId": "row_%d" % item.id,
                "checkbox_contents": checkbox_contents,
                "id_name": "%s(%s)" % (item.user.contract_company_user.name, item.user.username),
                "select": "<button style='margin: 2px; padding: 2px;' data-movie-id=%d class='btn btn-sm btn-dark mybtn-delete'>削除</button>"
                          "<button style='margin: 2px; padding: 2px;' data-movie-id=%d  class='btn btn-sm btn-dark mybtn-analysis'>分析</button>"
                          "<button style='margin: 2px; padding: 2px;' data-movie-id=%d  class='btn btn-sm btn-dark mybtn-watching'>視聴</button><br>"
                          "<button style='margin: 2px; padding: 2px;' data-movie-id=%d  class='btn btn-sm btn-dark mybtn-dl'>DL</button>"
                          "<button style='margin: 2px; padding: 2px;' data-movie-id=%d  class='btn btn-sm btn-dark mybtn-result'>結果</button>" % (item.id, item.id, item.id, item.id, item.id),
                "movie": movie,
                "movie_info": movie_info,
                "status": status,
                "is_save": "保存しない",
                ##"created_at": item.created_at.strftime('%Y-%-m-%-d %H:%M:%S'),
                ##"updated_at": item.updated_at.strftime('%Y-%-m-%-d %H:%M:%S'),
                })
            i += 1
        return json_data


class UserAnalysisResultListView(LoginRequiredMixin, SetUserMixinForDataTable, BaseDatatableView):
    """
    分析結果詳細リスト
    """

    # The model we're going to show
    model = Users

    columns = ['']

    order_columns = ['id']

    def get_initial_queryset(self):
        movie_id = self.kwargs.get("movie_id", None)
        qs = UserMovieAnalysisResult.objects.filter(user_movie_id=movie_id)
        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            for d in item.data:
                jd = {}
                for v in d["violations"]:
                    jd['category'] = d['category']
                    jd['group'] = d['group']
                    jd['start_fno'] = v["start_fno"]
                    jd['last_fno'] = v["last_fno"]
                    json_data.append(jd)
        return json_data
