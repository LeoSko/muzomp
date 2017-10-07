from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^', include('core.urls')),
    url(r'^upload/', include('uploader.urls')),
    url(r'^statistic/', include('statistic.urls')),
    url(r'^admin/', admin.site.urls)
]
