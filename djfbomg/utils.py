import requests
import json
import logging

from django.conf import settings

log = logging.getLogger(__name__)


class OauthException(Exception):
    pass


def is_facebook_fan(user):
    profile = user.userprofile
    for i in graph_api(profile.facebook_token, "me").get('data') or []:
        try:
            if i['id'] == settings.FACEBOOK_PAGE_ID:
                return True
        except:
            raise Exception("%s - %s" % (user, i))
    return False


def graph_api(token, *args, **kwargs):
    as_json = kwargs.pop('as_json', True)
    post_data = kwargs.pop('post_data', None)
    fail_silently = kwargs.pop('fail_silently', False)

    BASE_URL = 'https://graph.facebook.com/'

    params = {
        'format': 'json',
        'access_token': token,
    }

    params.update(kwargs)

    url = '%s%s' % (BASE_URL, "/".join(args))

    if post_data is not None:
        params.update(post_data)
        response = requests.get(url, data=params, timeout=5)
    else:
        url = '%s?%s' % (url, params)
        response = requests.get(url, timeout=5)

    if not as_json:
        return response.content

    log.info(response)
    if not fail_silently and 'error' in response.json() and 'type' in response.json()['error']:
        raise OauthException(url, response.json()['error']['type'], response)
    return response.json()
