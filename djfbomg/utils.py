import urllib

from django.conf import settings

def is_facebook_fan(user):
    profile = user.get_profile()

    LIKES_URL = "https://graph.facebook.com/me/likes"

    params = {
        'access_token': profile.facebook_token,
    }

    params = urllib.urlencode(params)

    req = urllib.urlopen("%s?format=json&%s" % (LIKES_URL,params))
    body = req.read()

    data = json.loads(body)

    for i in data['data']:
        if i['id'] == settings.FACEBOOK_PAGE_ID:
            return True

    return False

def graph_api(token,node,who='me',as_json=True,post_data=None,extra_params=None):
    params = {
        'format': 'json',
        'access_token': token,
    }

    if extra_params:
        params.update(extra_params)

    if post_data is not None:
        params.update(post_data)
        params = urllib.urlencode(params)
        url = '%s%s/%s'% (BASE_URL,who,node)
        req = urllib.urlopen(url,params)
        
    else: 
        params = urllib.urlencode(params)
        url = '%s%s/%s?%s'% (BASE_URL,who,node,params)
        req = urllib.urlopen(url)

    if not as_json:
        return req

    body = req.read()
    response = json.loads(body)

    if isinstance(response,dict) and 'error' in response:
        raise ValueError(url,response)

    return response
