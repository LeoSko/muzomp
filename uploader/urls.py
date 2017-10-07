from django.conf.urls import url

from . import views

app_name = 'uploader'
urlpatterns = [
	url(r'^$', views.UploaderView.as_view(), name='index')
]
