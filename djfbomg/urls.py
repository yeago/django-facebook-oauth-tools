try:
    from django.conf.urls.defaults import * # Django 1.4
except ImportError:
    from django.conf.urls import * # Django >= 1.6

from djfbomg.views import auth_callback

urlpatterns = patterns('djfbomg.views',
    url(r'^connect/$','connect',name="facebook_connect"),
    url(r'^auth-callback/$',auth_callback.as_view(), name="facebook_auth_callback"),
    url(r'^solicit-fail/(?P<permslug>[^/]+)/$', 'solicit', {'fail': True}, name="facebook_solicit_fail"),
    url(r'^solicit-succeed/(?P<permslug>[^/]+)/$', 'solicit', name="facebook_solicit_succeed"),
)
