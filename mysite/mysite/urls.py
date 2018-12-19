from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
#    url(r'^$', views.index, name='index'),
    url(r'^ericoin/', include('ericoin.urls')),
    url(r'^admin/', admin.site.urls),
]

#urlpatterns += patterns('django.views.static',(r'^media/(?P<path>.*)','serve',{'document_root':settings.MEDIA_ROOT}), )


