# -*- coding: UTF-8 -*-

# Create your views here.
import datetime

from django.db.models import Q, Count
from django.utils import timezone
from django_datatables_view.base_datatable_view import BaseDatatableView

from accounts.models import Users
from app_user.views.view_job import NotAllowGetMethodMixin
from lib.mixin import AdminLoginRequiredMixin


class AdminChangePasswordListView(AdminLoginRequiredMixin, NotAllowGetMethodMixin, BaseDatatableView):
    """
    パスワード変更のユーザーリストのJSONを返す
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
        search_text = self.request.POST.get("search_text", None)
        search_user_group = self.request.POST.get("search_user_group", None)

        cond1 = Q(is_delete=False, is_inactive=False)
        if search_user_group is not None and search_user_group != "" and search_user_group != '0':
                sobj = self.model.objects.filter(cond1, user_group_id=search_user_group)

        elif search_name is not None and search_name != "" and search_text is not None and search_text != "":
            if search_name == "personal_name":
                # TODO ユーザーグループをどこかで定義した方がいい
                # 氏名
                sobj = self.model.objects.filter(cond1, shimei__contains=search_text, user_group_id__in=[2, 3, 4])
            else:
                # TODO まだ未実装
                # 契約会社
                sobj = self.model.objects.filter(cond1, shimei__contains=search_text, user_group_id=5)
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

            # name
            name = None
            if item.irric_user:
                name = item.irric_user.name
            elif item.contract_company:
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


class AdminIrricUserListView(AdminLoginRequiredMixin, NotAllowGetMethodMixin, BaseDatatableView):
    """
    IRRICユーザーリストのJSONを返す
    """

    # The model we're going to show
    model = Users

    # define the columns that will be returned
    columns = ['']

    # company_countは契約会社数をannotateで設定した名前
    order_columns = ['id', 'username', '', 'group', 'name', 'company_count', '', '', 'last_login']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        search_login_id = self.request.POST.get("search_login_id", None)
        search_name = self.request.POST.get("search_name", None)
        search_user_group = self.request.POST.get("search_user_group", None)

        # TODO グループをどっかで定義して方がいい
        cond1 = Q(is_delete=False, user_group_id__in=[2, 3])
        if search_user_group is not None and search_user_group != "" and search_user_group != '0':
            if search_user_group == "1":
                sobj = self.model.objects.filter(cond1, user_group_id=2)
            elif search_user_group == "2":
                sobj = self.model.objects.filter(cond1, user_group_id=3)
            elif search_user_group == "3":
                sobj = self.model.objects.filter(cond1, is_inactive=True)

        else:
            cond2 = Q()
            cond3 = Q()
            if search_login_id is not None and search_login_id != "":
                cond2 = Q(username__contains=search_login_id)
            if search_name is not None and search_name != "":
                cond3 = Q(irric_user__name__contains=search_name)
            sobj = self.model.objects.filter(cond1, cond2, cond3)

        # 契約会社数の集計を載せる (irric_user__contractcompany -> forgienkey __ db名)
        sobj = sobj.annotate(company_count=Count("irric_user__contractcompany", distinct=True))

        return sobj

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            # チェックフォーム
            checkbox_contents = "<input type='checkbox' name='selected' value='%d'>" % item.id

            # 氏名/会社名
            name = None
            if item.irric_user_id is not None:
                name = item.irric_user.name
            elif item.contract_company_id is not None:
                name = item.contract_company.name
            elif item.contract_company_user_id is not None:
                name = item.contract_company_user.name

            json_data.append({
                "dataId": "row_%d" % item.id,
                "checkbox_contents": checkbox_contents,
                "username": "<a class='mylink-user-update' href='#'>%s</a>" % item.username,
                "status": item.get_is_active_string,
                "group": item.user_group.group_name,
                "name": name,
                "count_contract_company": item.company_count,
                "consultation_status": "未実施",
                "report_status": "未提出",
                "last_login": item.get_last_login_date
                })
        return json_data


class AdminContractCompanyListView(AdminLoginRequiredMixin, NotAllowGetMethodMixin, BaseDatatableView):
    """
    契約会社リストのJSONを返す
    """

    # The model we're going to show
    model = Users

    # define the columns that will be returned
    columns = ['']

    # company_countは契約会社数をannotateで設定した名前
    order_columns = ['id', 'username', 'contract_company.name', '', 'contract_company.service_info.service_name', 'contract_company.contract_start_date', 'contract_company.business_type.type_name', 'contract_company.main_consultant_irric_user.name', 'driver_count', 'movie_count', 'contract_company.diagnosis_date']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        # TODO グループをどっかで定義した方がいい
        cond1 = Q(is_delete=False, user_group_id__in=[4])
        sobj = self.model.objects.filter(cond1)

        # ドライバー数の集計を載せる
        sobj = sobj.annotate(driver_count=Count("contract_company__contractcompanyuser", distinct=True))
        # 動画アップロード数の集計を載せる
        sobj = sobj.annotate(movie_count=Count("usermovie", distinct=True))

        return sobj

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)

        s_contract_id = self.request.POST.get("s_contract_id", None)
        s_company_name = self.request.POST.get("s_company_name", None)
        s_company_consultant_name = self.request.POST.get("s_company_consultant_name", None)
        s_service_patterns = self.request.POST.getlist("s_service_pattern[]", None)
        s_business_types = self.request.POST.getlist("s_business_type[]", None)
        s_contract_start_date = self.request.POST.get("s_contract_start_date", None)
        s_contract_end_date = self.request.POST.get("s_contract_end_date", None)

        search_type = self.request.POST.get("search_type", None)

        # TODO グループをどっかで定義した方がいい
        cond1 = Q(is_delete=False, user_group_id__in=[4])
        if search_type is not None and search_type != "" and search_type != '0':
            if search_type == "1":  # 契約中
                qs = qs.filter(cond1, is_inactive=False, contract_company__contract_start_date__lte=timezone.now(), contract_company__contract_end_date__gte=timezone.now())
            elif search_type == "2":  # 契約終了
                qs = qs.filter(cond1, is_inactive=False, contract_company__contract_start_date__gt=timezone.now(), contract_company__contract_end_date__lt=timezone.now())
            elif search_type == "3":  # 利用停止中
                qs = qs.filter(cond1, is_inactive=True)

        else:
            cond2 = Q()
            cond3 = Q()
            cond4 = Q()
            cond5 = Q()
            cond6 = Q()
            cond7 = Q()
            cond8 = Q()
            if s_contract_id is not None and s_contract_id != "":
                cond2 = Q(username__contains=s_contract_id)
            if s_company_name is not None and s_company_name != "":
                cond3 = Q(contract_company__name__contains=s_company_name)
            if s_company_consultant_name is not None and s_company_consultant_name != "":
                cond4 = Q(contract_company__main_consultant_irric_user__name__contains=s_company_consultant_name)
            if s_service_patterns is not None and len(s_service_patterns) > 0:
                s_service_patterns = [int(s) for s in s_service_patterns]
                cond5 = Q(contract_company__service_info_id__in=s_service_patterns)
            if s_business_types is not None and len(s_business_types) > 0:
                s_business_types = [int(s) for s in s_business_types]
                cond6 = Q(contract_company__business_type_id__in=s_business_types)
            if s_contract_start_date is not None and s_contract_start_date != "":
                string_date = s_contract_start_date + " 00:00:00"
                string_date = string_date.replace("-", "/")
                s_contract_start_date = datetime.datetime.strptime(string_date, '%Y/%m/%d %H:%M:%S')
                cond7 = Q(contract_company__contract_start_date__lte=s_contract_start_date)
            if s_contract_end_date is not None and s_contract_end_date != "":
                string_date = s_contract_end_date + " 23:59:59"
                string_date = string_date.replace("-", "/")
                s_contract_end_date = datetime.datetime.strptime(string_date, '%Y/%m/%d %H:%M:%S')
                cond8 = Q(contract_company__contract_end_date__gte=s_contract_end_date)
            qs = qs.filter(cond1, cond2, cond3, cond4, cond5, cond6, cond7, cond8)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            # チェックフォーム
            checkbox_contents = "<input type='checkbox' name='selected' value='%d'>" % item.id

            # 契約状況
            if item.is_inactive is True:
                status = "利用停止中"
            else:
                status = item.contract_company.get_status_string

            # 契約期間
            contract_due_date = None
            start = item.contract_company.contract_start_date
            end = item.contract_company.contract_end_date
            if start is not None and end is not None:
                contract_due_date = start.strftime('%Y-%-m-%-d') + "から" + end.strftime('%Y-%-m-%-d')

            # 対面診断実施日
            diagnosis_date = item.contract_company.diagnosis_date
            if diagnosis_date is not None:
                diagnosis_date = diagnosis_date.strftime('%Y-%-m-%-d')

            json_data.append({
                "dataId": "row_%d" % item.id,
                "checkbox_contents": checkbox_contents,
                "username": "<a href=''>%s</a>" % item.username,
                "name": item.contract_company.name,
                "status": status,
                "service_pattern": item.contract_company.service_info.service_name,
                "contract_due_date": contract_due_date,
                "business_type": item.contract_company.business_type.type_name,
                "main_consultant_name": item.contract_company.main_consultant_irric_user.name,
                "driver_count": item.driver_count,
                "upload_video_count": item.movie_count,
                "diagnosis_date": diagnosis_date
                })
        return json_data


class AdminNoticeListView(AdminLoginRequiredMixin, NotAllowGetMethodMixin, BaseDatatableView):
    """
    お知らせ管理リストのJSONを返す
    """

    # The model we're going to show
    model = Users

    columns = ['']

    order_columns = ['id']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        s_publish_start_date = self.request.POST.get("s_publish_start_date", None)
        s_publish_end_date = self.request.POST.get("s_publish_end_date", None)
        search_type = self.request.POST.get("search_type", None)

        return None

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        return json_data
