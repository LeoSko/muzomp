from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url('', include('core.urls')),
    url('statistic/', include('statistic.urls')),
    url('admin/', admin.site.urls)
]
