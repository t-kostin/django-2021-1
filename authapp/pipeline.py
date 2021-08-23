from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlencode, urlunparse
import requests
from django.utils import timezone
from social_core.exceptions import AuthForbidden
from authapp.models import ShopUserProfile


def save_user_profile(backend, user, response, *args, **kwargs):
    if backend.name != 'vk-oauth2':
        return

    api_url = urlunparse((
        'https',
        'api.vk.com',
        '/method/users.get',
        None,
        urlencode(
            OrderedDict(
                fields=','.join(('bdate', 'sex', 'about', 'domain', 'language')),
                access_token=response['access_token'],
                v='5.131'
            )
        ),
        None
    ))

    resp = requests.get(api_url)

    if resp.status_code != 200:
        return

    data = resp.json()['response'][0]

    if data['sex']:
        user.shopuserprofile.gender = ShopUserProfile.MALE if data['sex'] == 2 else ShopUserProfile.FEMALE

    if data['domain']:
        user.shopuserprofile.vk_profile_address = ''.join(('https://vk.com/',data['domain']))

    if data['language']:
        if data['language'] == '0':
            user.shopuserprofile.vk_language = 'Русский'
        elif data['language'] == '1':
            user.shopuserprofile.vk_language = 'Українська'
        elif data['language'] == '3':
            user.shopuserprofile.vk_language = 'English'

    if data['about']:
        user.shopuserprofile.about_me = data['about']

    if data['bdate']:
        bdate = datetime.strptime(data['bdate'], '%d.%m.%Y').date()
        age = timezone.now().date().year - bdate.year
        user.age = age
        if age < 18:
        # if age < 100:
            user.delete()
            raise AuthForbidden('social_core.backends.vk.VKOAuth2')

    user.save()