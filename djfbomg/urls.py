from django.conf.urls.defaults import *

from djfbomg.views import auth_callback

urlpatterns = patterns('djfbomg.views',
    url(r'^connect/$','connect',name="facebook_connect"),
    url(r'^auth-callback/$',auth_callback.as_view(), name="facebook_auth_callback"),
)
