# thinktank_project/thinktank_project/management/commands/test_command.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'A simple test command'

    def handle(self, *args, **options):
        self.stdout.write("Test command executed successfully!")