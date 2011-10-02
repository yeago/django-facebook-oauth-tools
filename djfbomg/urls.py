urlpatterns = patterns('djfbomg.views',
    url(r'^connect/$','connect',name="facebook_connect"),
    url(r'^auth-callback/$','auth_callback',name="facebook_auth_callback"),
)
