from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from monitor.models import WatchedApplication, CheckResult
from monitor.checker import run_check, evaluate_alerts

# Mock response for requests.get
def mock_response(status_code=200):
    r = MagicMock()
    r.status_code = status_code
    return r


class RunCheckTest(TestCase):
    @patch('monitor.checker.requests.get')
    def test_run_check_success_creates_result(self, mock_get):
        mock_get.return_value = mock_response(200)
        app = WatchedApplication.objects.create(base_url='https://example.com')
        result = run_check(app)
        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.watched_application_id, app.id)
        mock_get.assert_called_once()

    @patch('monitor.checker.requests.get')
    def test_run_check_failure_creates_result(self, mock_get):
        mock_get.return_value = mock_response(404)
        app = WatchedApplication.objects.create(base_url='https://example.com')
        result = run_check(app)
        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 404)
        self.assertIn('404', result.error_message)

    @patch('monitor.checker.requests.get')
    def test_run_check_exception_creates_failed_result(self, mock_get):
        mock_get.side_effect = Exception('Connection refused')
        app = WatchedApplication.objects.create(base_url='https://example.com')
        result = run_check(app)
        self.assertFalse(result.success)
        self.assertIsNone(result.status_code)
        self.assertIn('Connection refused', result.error_message)


class EvaluateAlertsTest(TestCase):
    def test_fewer_than_threshold_no_alert(self):
        app = WatchedApplication.objects.create(base_url='https://example.com')
        for _ in range(3):
            CheckResult.objects.create(watched_application=app, success=False)
        with patch('monitor.checker.send_alert_email') as mock_send:
            evaluate_alerts(app)
        mock_send.assert_not_called()

    @patch('monitor.checker.settings')
    @patch('monitor.checker.send_alert_email')
    def test_n_consecutive_failures_sends_down_alert(self, mock_send, mock_settings):
        mock_settings.ALERT_THRESHOLD = 3
        app = WatchedApplication.objects.create(base_url='https://example.com')
        for _ in range(3):
            CheckResult.objects.create(watched_application=app, success=False)
        evaluate_alerts(app)
        self.assertEqual(mock_send.call_count, 1)
        call_args = mock_send.call_args[0]
        self.assertIn('down', call_args[0].lower())
        app.refresh_from_db()
        self.assertIsNotNone(app.alert_down_sent_at)

    @patch('monitor.checker.settings')
    @patch('monitor.checker.send_alert_email')
    def test_n_consecutive_success_after_down_sends_up_alert(self, mock_send, mock_settings):
        mock_settings.ALERT_THRESHOLD = 3
        app = WatchedApplication.objects.create(base_url='https://example.com')
        app.alert_down_sent_at = timezone.now()
        app.save()
        for _ in range(3):
            CheckResult.objects.create(watched_application=app, success=True)
        evaluate_alerts(app)
        calls = [c[0][0] for c in mock_send.call_args_list]
        self.assertTrue(any('back up' in s.lower() or 'up' in s.lower() for s in calls))
        app.refresh_from_db()
        self.assertIsNotNone(app.alert_up_sent_at)
