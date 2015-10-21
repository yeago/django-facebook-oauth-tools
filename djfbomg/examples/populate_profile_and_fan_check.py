from django.contrib import messages
from myapp.models import UserProfile

from myapp.tasks import fb_sync

class auth_callback(base_auth_callback):
    def connect_success(self, request, *args, **kwargs):
        success_msg = "Facebook Connect successful"
        profile = None
        if request.user.is_authenticated():
            profile = request.user.userprofile
            profile.facebook_token = self.token 
            profile.facebook_id = self.facebook_id
            profile.save()
        else:
            try:
                profile = UserProfile.objects.get(facebook_id=self.facebook_id)
                user = authenticate(facebook_id=self.facebook_id)
                login(request,user)
                profile.facebook_token = self.token
                profile.facebook_last_update = datetime.datetime.now()
                profile.save()

            except UserProfile.DoesNotExist:
                request.session['facebook_id'] = self.facebook_id
                request.session['facebook_token'] = self.token
                self.return_url = "%s?return_url=%s" % (reverse("facebook_claim_username"),self.return_url)

        if profile:
            if not profile.facebook_fan:
                success_msg = "%s &mdash; If you were our <a target=\"_new\" href=\"%s\">fan on Facebook</a>"\
                    " you''ll get a free feature token!" % (success_msg,settings.FACEBOOK_PAGE_URL)
                    
                if is_facebook_fan(request.user):
                    profile.feature_tokens += 1
                    profile.facebook_fan = True
                    profile.save()
                    success_msg = "Facebook connect successful &mdash; Feature token added for being our fan!" 

                fb_sync.apply_async(args=[profile.user.pk])

        messages.success(request,success_msg)
