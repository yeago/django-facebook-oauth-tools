"""
Be nice to your web processes and users and make this kinda stuff
asyncronous

"""


from celery.decorators import task
from djfbomg.utils import graph_api, is_facebook_fan, OauthException

from myapp import models as bm

@task
def fb_sync(user_id):
    profile = bm.UserProfile.objects.get(user=user_id)

    try:
        friend_ids = [f['id'] for f in graph_api(profile.facebook_token,'friends')['data']]
    except OauthException:
        profile.facebook_token = None
        profile.save()
        return

    if not profile.facebook_fan:
        try:
            if is_facebook_fan(profile.user):
                profile.facebook_fan = True
                profile.feature_tokens += 1
                profile.save()
        except OauthException:
            profile.facebook_token = None
            profile.save()
            return
