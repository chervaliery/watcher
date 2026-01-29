from unittest.mock import patch

from django.test import TestCase, override_settings

from monitor.mailjet_send import send_alert_email


class SendAlertEmailTest(TestCase):
    @override_settings(
        MAILJET_API_KEY='',
        MAILJET_SECRET='',
        MAILJET_FROM_EMAIL='',
        MAILJET_ALERT_TO=[],
    )
    @patch('monitor.mailjet_send.requests.post')
    def test_not_configured_does_not_call_requests_post(self, mock_post):
        send_alert_email('Test subject', 'Test body', None)
        mock_post.assert_not_called()

    @override_settings(
        MAILJET_API_KEY='key',
        MAILJET_SECRET='secret',
        MAILJET_FROM_EMAIL='from@test.com',
        MAILJET_ALERT_TO=['to@test.com'],
    )
    @patch('monitor.mailjet_send.requests.post')
    def test_configured_calls_requests_post(self, mock_post):
        mock_post.return_value.status_code = 200
        send_alert_email('Subject', 'Body', None)
        mock_post.assert_called_once()
        call_kw = mock_post.call_args[1]
        self.assertEqual(call_kw['json']['Messages'][0]['Subject'], 'Subject')
        self.assertEqual(call_kw['json']['Messages'][0]['TextPart'], 'Body')
