import requests
from django.conf import settings


class KitHrException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class KitHrBadRequest(KitHrException):
    pass


class KitHrUnauthorizedAccessError(KitHrException):
    pass


class KitHrServerError(KitHrException):
    pass


class KitHrNotFound(KitHrException):
    pass


class KitHrUnknownError(KitHrException):
    pass


class KitHrClient(object):
    _base_url = 'https://gkit.ru/hr/api/'

    def __init__(self, token=None):
        self.token = token

    def get(self, api_method, params=None, json=None):
        return self._make_request('get', api_method, params, json)

    def post(self, api_method, params=None, json=None, token=None):
        return self._make_request('post', api_method, params, json, token)

    def _make_request(self, request_method, api_method, params=None, json=None, token=None):
        if token is None:
            token = self.token
        headers = {'APIKEY': token}
        url = self._build_url(api_method)
        response = requests.request(request_method, url, params=params, json=json, headers=headers, timeout=10, verify=False)
        if response.status_code != 200:
            message = response.content.decode()
            code = response.status_code
            if response.status_code == 400:
                raise KitHrBadRequest(message, code)
            elif response.status_code == 401:
                raise KitHrUnauthorizedAccessError(message, code)
            elif response.status_code == 404:
                raise KitHrNotFound(message, code)
            elif response.status_code == 500:
                raise KitHrServerError(message, code)
            else:
                raise KitHrUnknownError(message, code)
        else:
            jsn = response.json()

        return jsn['data']

    def _build_url(self, path):
        return self._base_url + path + '/'


def get_kit_hr_client():
    return KitHrClient(settings.KIT_API_KEY)
