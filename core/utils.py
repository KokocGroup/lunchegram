from django.conf import settings
from redis import Redis
from accounts.models import User
from api.kit_hr import get_kit_hr_client

FIRED_STATUSES = ['NEVER_WORK', 'IN_DISMISS', 'DISMISSED']


def get_redis():
    return Redis.from_url(settings.REDIS_URL)


def kokoc_users_sync():
    client = get_kit_hr_client()
    kokoc_api_users = client.get('users')

    kokoc_users = dict()
    for kokoc_user in kokoc_api_users:
        if kokoc_user['telegram']:
            username = kokoc_user['telegram'].lstrip('@').lower()
            fired = True if kokoc_user['status']['id'] in FIRED_STATUSES else False
            kokoc_users[username] = dict()
            kokoc_users[username]['fired'] = fired
            kokoc_users[username]['bitrix_id'] = kokoc_user['bitrix_id']
            kokoc_users[username]['name'] = kokoc_user['name']
            kokoc_users[username]['surname'] = kokoc_user['surname']

    lunch_users = User.objects.all()
    for user in lunch_users:
        uname = user.username.lower()
        if uname not in kokoc_users or kokoc_users[uname]['fired']:
            user.delete()
        elif uname in kokoc_users:
            employee = user.employees.filter(company__invite_token='kokoc2020').first()
            if employee:
                employee.external_id = kokoc_users[uname]['bitrix_id']
                employee.external_first_name = kokoc_users[uname]['name']
                employee.external_last_name = kokoc_users[uname]['surname']
                employee.save()

    return
