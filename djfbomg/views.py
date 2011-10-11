import logging
import json
import urllib

from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import Http404
from django.conf import settings

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.auth import authenticate, login
from django.views.generic.base import RedirectView

from djfbomg.utils import graph_api, is_facebook_fan

log = logging.getLogger(__name__)

def connect(request):
    request.session['FACEBOOK_ABANDON_PATH'] = request.GET.get('return_url')
    scope = 'user_likes,email'
    if request.GET.get('extra_scope'):
        scope = '%s,%s' % (scope,request.GET.get('extra_scope'))

    redirect_uri = "http://%s%s" % (Site.objects.get_current().domain,\
        urllib.quote_plus(reverse("facebook_auth_callback")))

    kwargs = {
        'type': 'client_cred',
        'scope': scope,
        'client_id': settings.FACEBOOK_APP_ID,
        'redirect_uri': redirect_uri
    }

    return redirect("https://www.facebook.com/dialog/oauth?%s" % "&".join(["%s=%s" % (k,v) for k, v in kwargs.iteritems()]))

GRAPH_URL = "https://graph.facebook.com/oauth/access_token?"

class auth_callback(RedirectView): # This is where FB redirects you after auth.
    permanent = False
    def get(self, request, *args, **kwargs):
        self.return_url = urllib.unquote_plus(request.session.get("FACEBOOK_ABANDON_PATH") or "/")
        if not request.GET.get("code"): # Why are they here without a code var?
            return redirect(self.return_url)

        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': "http://%s%s" % (Site.objects.get_current(),reverse("facebook_auth_callback")),
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'code': request.GET.get("code"),
        }

        params = urllib.urlencode(params)
        req = urllib.urlopen("%s%s" % (GRAPH_URL, params))
        body = req.read()

        if "error" in body:
            log.debug("FB Authentication error: %s" % body)
            messages.error(request,"Some problem authenticating you. Maybe try again?")
            return redirect(self.return_url)

        self.token = body.split("&")[0].replace("access_token=","")

        req = urllib.urlopen("https://graph.facebook.com/me/?format=json&access_token=%s" % (self.token))
        data = json.loads(req.read())
        self.facebook_id = data['id']
        self.connect_success(request, *args, **kwargs)
        return redirect(self.return_url)

        def connect_success(self, request, *args, **kwargs):
            raise Exception("Override this")

            """

            Here's some example stuff you can do here:

            success_msg = "Facebook Connect successful"
            if request.user.is_authenticated():
                profile = request.user.get_profile()
                profile.facebook_token = self.token 
                profile.facebook_id = self.facebook_id
                profile.save()

                if not profile.facebook_fan:
                    success_msg = "%s &mdash; If you were our <a target=\"_new\" href=\"%s\">fan on Facebook</a>"\
                        " you'd be getting a free feature token!" % (success_msg,settings.FACEBOOK_PAGE_URL)
                        
                    if is_facebook_fan(request.user):
                        profile.feature_tokens += 1
                        profile.facebook_fan = True
                        profile.save()
                        success_msg = "Facebook connect successful &mdash; Feature token added for being our fan!" 

            else:
                try:
                    profile = UserProfile.objects.get(facebook_id=facebook_id)
                    user = authenticate(facebook_id=facebook_id)
                    login(request,user)
                    profile.facebook_token = token
                    profile.save()

                    if not user.email:
                        if data.get("email"):
                            user.email = data.get("email")
                            user.save()
                        else:
                            messages.warning(request,"We weren't able to get your email address "\
                                "from facebook so you won't receive activity notices")

                except UserProfile.DoesNotExist:
                    request.session['facebook_id'] = facebook_id
                    request.session['facebook_token'] = token
                    return redirect("%s?return_url=%s" % (reverse("facebook_claim_username"),return_url))

            messages.success(request,success_msg)
            """

def claim_username(request):
    if not request.session.get("facebook_id") or not request.session.get("facebook_token"):
        raise Http404

    form = ClaimUsernameForm(request.session.get('facebook_id'),request.session.get('facebook_token'),request.POST or None)

    if request.POST and form.is_valid():
        user = User.objects.create(username=form.cleaned_data.get("username"),password="")
        profile = user.get_profile()
        profile.facebook_id = form.facebook_id
        profile.save()
        user = authenticate(facebook_id=profile.facebook_id)
        login(request,user)
        return redirect(reverse("facebook_connect"))

    return render_to_response("facebook/claim_username.html", { "form": form }, context_instance=RequestContext(request))

def signup(request):
    if not request.POST.get("desired_username"):
        messages.error(request,"Sorry, you must enter a username and try again")

    if request.POST and request.POST.get("desired_username"):
        try:
            User.objects.get(username=request.POST.get("desired_username"))
            messages.error(request,"Sorry, that username is taken. If that's you, connect again after traditional login")

        except User.DoesNotExist:
            callback_url = urllib.urlencode(reverse("facebook_claim_username",args=[request.POST.get("desired_username")]))
            return redirect(reverse("facebook_connect"))

    return redirect("/accounts/register/")
