from django.core.management.base import BaseCommand
from core.utils import kokoc_users_sync


class Command(BaseCommand):
    help = 'Run kokoc_users_sync command'

    def handle(self, *args, **options):
        kokoc_users_sync()
