from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

app_name = 'core'
urlpatterns = [
    url('upload_view/', views.UploaderFormView.as_view(), name='upload_form'),
    url('upload/', views.UploadView.as_view(), name='upload'),
    url('queue/', views.QueueView.as_view(), name='queue'),
    url('search/', RedirectView.as_view(url='index/', permanent=False), name='search'),
    url('search/(?P<query>\w*)', views.QueryView.as_view(), name='search'),
    url('statistic/', views.StatisticView.as_view(), name='statistic'),
    url('audio/(?P<id>\d+)', views.AudioView.as_view(), name='audio'),
    url('index/audio', views.IndexAudioView.as_view(), name='index_audio'),
    url('index/processing', views.IndexProcessingView.as_view(), name='index_processing'),
    url('index/queue', views.IndexQueueView.as_view(), name='index_queue'),
    url('index/', views.IndexView.as_view(), name='index'),
    url('', RedirectView.as_view(url='index/', permanent=False))
]
