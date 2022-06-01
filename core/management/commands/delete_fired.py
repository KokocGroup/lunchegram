from django.core.management.base import BaseCommand
from core.utils import delete_fired


class Command(BaseCommand):
    help = 'Run delete_fired command'

    def handle(self, *args, **options):
        delete_fired()
