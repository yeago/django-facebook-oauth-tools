import urllib2
from urllib import urlencode
import json
import logging

from django.conf import settings

log = logging.getLogger(__name__)

class OauthException(Exception):
    pass

def is_facebook_fan(user):
    profile = user.userprofile
    for i in graph_api(profile.facebook_token,"me").get('data') or []:
        try:
            if i['id'] == settings.FACEBOOK_PAGE_ID:
                return True
        except:
            raise Exception("%s - %s" % (user,i))
    return False

def graph_api(*args, **kwargs):
    args = list(args)
    token = args.pop(0)
    as_json = kwargs.pop('as_json',True)
    post_data = kwargs.pop('post_data',None)
    fail_silently = kwargs.pop('fail_silently',False)

    BASE_URL = 'https://graph.facebook.com/'

    params = {
        'format': 'json',
        'access_token': token,
    }

    params.update(kwargs)

    url = '%s%s' % (BASE_URL,"/".join(args))

    if post_data is not None:
        params.update(post_data)
        params = urlencode(params)
        log.info(url)
        req = urllib2.urlopen(url, params, timeout=5)
        
    else: 
        params = urlencode(params)
        url = '%s?%s' % (url,params)
        log.debug(url)
        req = urllib2.urlopen(url, timeout=5)

    if not as_json:
        return req

    body = req.read()
    response = json.loads(body)

    if not fail_silently and isinstance(response,dict) and 'error' in response and 'type' in response['error']:
        log.debug(response)
        #import pdb;pdb.set_trace()
        raise OauthException(url,response['error']['type'], response)

    log.info(response)
    return response
