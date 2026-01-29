from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command

from monitor.models import WatchedApplication, CheckResult


class RunChecksCommandTest(TestCase):
    def test_run_checks_no_apps_no_error(self):
        call_command('run_checks')

    @patch('monitor.checker.requests.get')
    def test_run_checks_with_active_app_performs_check(self, mock_get):
        mock_get.return_value.status_code = 200
        WatchedApplication.objects.create(
            base_url='https://example.com',
            is_active=True,
            check_interval_seconds=60,
        )
        call_command('run_checks')
        self.assertEqual(CheckResult.objects.count(), 1)
