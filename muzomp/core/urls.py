from django.conf.urls import url

from . import views

app_name = 'core'
urlpatterns = [
    url('upload_view/', views.UploaderFormView.as_view(), name='upload_form'),
    url('upload/', views.UploadView.as_view(), name='upload'),
    url('queue/', views.QueueView.as_view(), name='queue'),
    url('search/', views.QueryView.as_view(), name='search'),
    url('statistic/', views.StatisticView.as_view(), name='statistic'),
    url('audio/(?P<id>\d+)', views.AudioView.as_view(), name='audio'),
    url('', views.IndexView.as_view(), name='index'),
]
