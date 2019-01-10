from django.conf.urls import url
from django.contrib import admin
from controller import login,testFR
from pismap import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/$',views.login),
    url(r'^panel$',views.panel),
    url(r'^getface$',login.getface),
    url(r'^face$',testFR.face),
    url(r'^$',views.index),
    url(r'^login/panel/$',views.panel),
    url(r'^regist/$',views.regist),
    url(r'^login1/$',views.login1),
    url(r'^logout/$',views.logout),
    url(r'^index/$',views.index),
]
