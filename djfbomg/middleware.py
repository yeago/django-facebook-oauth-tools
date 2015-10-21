from django.contrib import messages

from django.core.urlresolvers import reverse

"""
This is one option for getting users to re-authorize once their token has expired.

Somewhere along the line you detect an OauthException by an authenticated user. 
If you clear their facebook_token, and yet they still have a facebook_id, we 
assume this user is in need of re-authentication.

We then flash them a message and offer them the ability to make their token permanent.

"""

class FacebookReconnectWarning(object):
    def process_request(self, request, *args, **kwargs):
        if request.POST or request.GET:
            return

        if request.user.is_authenticated() and request.user.userprofile.facebook_id \
            and not request.user.userprofile.facebook_token:
            messages.warning(request, "Your Facebook token has expired. Please <a href=\"%s?return_url=%s\">"\
                "Reconnect</a>. To avoid this message in the future <a href=\"%s?return_url=%s&extra_scope=offline_access\">click here</a>" % \
                (reverse("facebook_connect"),request.path,reverse("facebook_connect"),request.path))
