from django.conf import settings
from redis import Redis
from accounts.models import User
from api.kit_hr import get_kit_hr_client

FIRED_STATUSES = ['NEVER_WORK', 'IN_DISMISS', 'DISMISSED']


def get_redis():
    return Redis.from_url(settings.REDIS_URL)


def delete_fired():
    client = get_kit_hr_client()
    kokoc_api_users = client.get('users')

    kokoc_users = dict()
    for kokoc_user in kokoc_api_users:
        if kokoc_user['telegram']:
            username = kokoc_user['telegram'].lstrip('@').lower()
            fired = True if kokoc_user['status']['id'] in FIRED_STATUSES else False
            kokoc_users[username] = dict()
            kokoc_users[username]['fired'] = fired

    lunch_users = User.objects.all()
    for user in lunch_users:
        uname = user.username.lower()
        if uname not in kokoc_users or kokoc_users[uname]['fired']:
            user.delete()

    return
