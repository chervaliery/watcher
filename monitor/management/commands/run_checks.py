from django.core.management.base import BaseCommand
from monitor.checker import run_checks_for_active_apps


class Command(BaseCommand):
    help = 'Run health checks for all active watched applications that are due.'

    def handle(self, *args, **options):
        run_checks_for_active_apps()
        self.stdout.write(self.style.SUCCESS('Checks completed.'))
