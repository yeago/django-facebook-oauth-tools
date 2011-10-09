import urllib
import json
import logging

from django.conf import settings

log = logging.getLogger(__name__)

class OauthException(Exception):
    pass

def is_facebook_fan(user):
    profile = user.get_profile()
    for i in graph_api(profile.facebook_token,"likes")['data']:
        log.info(i)
        if i['id'] == settings.FACEBOOK_PAGE_ID:
            return True

    return False

def graph_api(token,node,who='me',as_json=True,post_data=None,extra_params=None,fail_silently=False):
    BASE_URL = 'https://graph.facebook.com/'

    params = {
        'format': 'json',
        'access_token': token,
    }

    if extra_params:
        params.update(extra_params)

    url = '%s%s/%s' % (BASE_URL,who,node)

    if post_data is not None:
        params.update(post_data)
        params = urllib.urlencode(params)
        req = urllib.urlopen(url,params)
        
    else: 
        params = urllib.urlencode(params)
        url = '%s?%s' % (url,params)
        req = urllib.urlopen(url)

    if not as_json:
        return req

    body = req.read()
    response = json.loads(body)

    if not fail_silently and isinstance(response,dict) and 'error' in response and 'type' in response['error']:
        raise OauthException(url,response['error']['type'])

    log.info(response)
    return response
