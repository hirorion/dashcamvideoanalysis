"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.http import HttpResponse
from django.urls import include
from rest_framework import routers

from accounts.views import TopView
from stocks_app.views import StockViewSet

router = routers.DefaultRouter()
router.register(r'stock', StockViewSet)


urlpatterns = [
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),

    #path('', TemplateView.as_view(template_name='index.html'), name='index'),

    # stock/api/stock/
    #url(r'api/', include(router.urls)),
    # stock/test/
    #url(r'test/$', StockSampleView.as_view(), name='index'),
    # stock/
    #url(r'stocklist', index, name='stocklist'),


    url(r'^$', TopView.as_view(), name='home'),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^admin/', include('app_admin.urls')),
    url(r'^portal/', include('app_user.urls')),

    url(r'^ai/', include('app_ai.urls')),

    # API (rest frameworkでの実装でも化）
    url(r'^api/', include('app_api.urls')),

]
