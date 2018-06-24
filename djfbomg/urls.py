from django.conf.urls import url

from djfbomg import views

urlpatterns = [
    url(r'^connect/$', views.connect, name="facebook_connect"),
    url(r'^auth-callback/$', views.auth_callback.as_view(), name="facebook_auth_callback"),
    url(r'^solicit-fail/(?P<permslug>[^/]+)/$', views.solicit, {'fail': True}, name="facebook_solicit_fail"),
    url(r'^solicit-succeed/(?P<permslug>[^/]+)/$', views.solicit, name="facebook_solicit_succeed"),
]
