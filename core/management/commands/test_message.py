from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as __
from lunchegram import bot
from accounts.models import User
from core.models import Employee


class Command(BaseCommand):
    help = 'Test script'

    def handle(self, *args, **options):
        self.test_message()

    @staticmethod
    def test_message():
        test_user_id = 7
        user_to_id = 95
        # user = User.objects.get(pk=user_to_id)
        partner_user = User.objects.get(pk=test_user_id)
        employee = Employee.objects.get(user=test_user_id)
        message = __('Hello! Your next random lunch partner is here: [{}](tg://user?id={})(@{} [открыть на портале]({}))').format(
            employee.get_full_name(), partner_user.telegram_account.uid, partner_user.username, employee.get_external_link())
        print(message)
        bot.send_message(479007211, message, parse_mode='Markdown')