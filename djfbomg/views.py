import logging
import json
import urllib2
from urllib import urlencode, quote_plus, unquote_plus

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

log = logging.getLogger(__name__)

"""
You should subclass auth_callback and do something fun with your
users once connected. Check out the examples directory for inspiration
"""

def connect(request):
    URL_GROUPS = [('return_url','FACEBOOK_ABANDON_URL'),('success_url','FACEBOOK_SUCCESS_URL'),('fail_url','FACEBOOK_FAIL_URL')]

    for group in URL_GROUPS:
        if request.session.get(group[1]):
            del request.session[group[1]]

        if request.GET.get(group[0]):
            request.session[group[1]] = request.GET.get(group[0])
    
    scope = getattr(settings,'FACEBOOK_DEFAULT_SCOPE',False) or None
    if request.GET.get('extra_scope'):
        if scope:
            scope = '%s,%s' % (scope,request.GET['extra_scope'])
        else:
            scope = request.GET['extra_scope']

    redirect_uri = "http://%s%s" % (Site.objects.get_current().domain,\
        quote_plus(reverse("facebook_auth_callback")))

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
        self.return_url = "/"
        self.abandon_url = None
        self.success_url = None
        self.fail_url = None
    
        if request.session.get("FACEBOOK_ABANDON_URL"):
            self.abandon_url = unquote_plus(request.session.get("FACEBOOK_ABANDON_URL"))

        if request.session.get("FACEBOOK_SUCCESS_URL"):
            self.success_url = unquote_plus(request.session.get("FACEBOOK_SUCCESS_URL"))

        if request.session.get("FACEBOOK_FAIL_URL"):
            self.fail_url = unquote_plus(request.session.get("FACEBOOK_FAIL_URL"))

        self.return_url = self.success_url or self.abandon_url or self.return_url

        if not request.GET.get("code"): # Why are they here without a code var?
            return redirect(self.return_url)

        params = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': "http://%s%s" % (Site.objects.get_current(),reverse("facebook_auth_callback")),
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'code': request.GET.get("code"),
        }

        params = urlencode(params)
        req = urllib2.urlopen("%s%s" % (GRAPH_URL, params), timeout=5)
        body = req.read()

        if "error" in body:
            log.debug("FB Authentication error: %s" % body)
            messages.error(request,"Some problem authenticating you. Maybe try again?")
            self.return_url = self.fail_url or self.return_url
            return redirect(self.return_url)

        self.response = body
        self.token = body.split("&")[0].replace("access_token=","")

        req = urllib2.urlopen("https://graph.facebook.com/me/?format=json&access_token=%s" % (self.token), timeout=5)
        self.data = json.loads(req.read())
        self.facebook_id = self.data['id']
        self.connect_success(request, *args, **kwargs)
        return redirect(self.success_url or self.return_url)

        def connect_success(self, request, *args, **kwargs):
            raise Exception("Override this")

def solicit(request,permslug,fail=False):
    """
    The convention in place is this:

    We want to ask users whether they want to give us some permission
    to do something. We don't care what the something is called, but 
    we call it a 'permslug'. the NullBool field 'facebook_solicit_SOMEPERM'
    must be on their profile. This tracks whether the user has A) Accepted
    B) Rejected or C) Not been solicited. 
    """
    profile_field = "facebook_solicit_%s" % permslug
    profile = request.user.userprofile

    if not hasattr(profile,profile_field):
        raise Http404 # Profile needs to have the field for this to be useful

    setattr(profile,profile_field,fail == False)
    profile.save()
    return redirect(request.GET.get('return_url') or '/')

def claim_username(request):
    if not request.session.get("facebook_id") or not request.session.get("facebook_token"):
        raise Http404

    form = ClaimUsernameForm(request.session.get('facebook_id'),request.session.get('facebook_token'),request.POST or None)

    if request.POST and form.is_valid():
        user = User.objects.create(username=form.cleaned_data.get("username"),password="")
        profile = user.userprofile
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
            callback_url = urlencode(reverse("facebook_claim_username",args=[request.POST.get("desired_username")]))
            return redirect(reverse("facebook_connect"))

    return redirect("/accounts/register/")
