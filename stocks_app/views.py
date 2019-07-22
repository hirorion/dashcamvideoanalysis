import os

from django.conf import settings
from django.http.response import HttpResponse
from django.views.generic import TemplateView
from rest_framework import viewsets

from stocks_app.models import Stock

# 静的ファイルを返すView
from stocks_app.serializers import StockSerializer


def index(_):
    """カスタムコンポーネントを使う"""
    # render等でDjangoのtemplateとして処理すると「{{}}」がVue.jsに渡る前消えてしまう。
    # 良い解決方法が浮かばなかったので、static配下に置いたファイルをopenして投げることで回避。
    html = open(
        os.path.join(settings.STATICFILES_DIRS[1], "vue_grid.html")).read()
    return HttpResponse(html)


class StockSampleView(TemplateView):
    """単一ファイルコンポーネントを使う場合"""

    template_name = "vue_test.html"


# RestAPIのviewsets
class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    # APIのフィルタで使えるフィールドを指定
    filter_fields = ("id", "title", 'stock_count')
