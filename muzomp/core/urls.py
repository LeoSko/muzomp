from django.conf.urls import url

from . import views

app_name = 'core'
urlpatterns = [
    url('upload/', views.UploaderView.as_view(), name='upload'),
    url('queue/', views.QueueView.as_view(), name='queue'),
    url('search/', views.QueryView.as_view(), name='search'),
    url('statistic/', views.StatisticView.as_view(), name='statistic'),
    url('', views.IndexView.as_view(), name='index'),
]
