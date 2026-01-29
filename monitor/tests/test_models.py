from django.test import TestCase

from monitor.models import WatchedApplication, CheckResult


class WatchedApplicationModelTest(TestCase):
    def test_create_with_required_fields(self):
        app = WatchedApplication.objects.create(
            name='Test App',
            base_url='https://example.com',
        )
        self.assertEqual(app.name, 'Test App')
        self.assertEqual(app.base_url, 'https://example.com')
        self.assertTrue(app.is_active)
        self.assertEqual(app.check_interval_seconds, 60)
        self.assertEqual(app.get_expected_status_codes(), [200])

    def test_get_expected_status_codes_list(self):
        app = WatchedApplication.objects.create(
            base_url='https://example.com',
            expected_status_codes=[200, 201],
        )
        self.assertEqual(app.get_expected_status_codes(), [200, 201])

    def test_get_expected_status_codes_string_invalid(self):
        app = WatchedApplication.objects.create(
            base_url='https://example.com',
            expected_status_codes='not-json',
        )
        self.assertEqual(app.get_expected_status_codes(), [200])

    def test_str_returns_name_or_base_url(self):
        app = WatchedApplication.objects.create(name='My App', base_url='https://a.com')
        self.assertEqual(str(app), 'My App')
        app2 = WatchedApplication.objects.create(base_url='https://b.com')
        self.assertEqual(str(app2), 'https://b.com')


class CheckResultModelTest(TestCase):
    def test_create_linked_to_app(self):
        app = WatchedApplication.objects.create(base_url='https://example.com')
        result = CheckResult.objects.create(
            watched_application=app,
            success=True,
            status_code=200,
            response_time_ms=50,
        )
        self.assertEqual(result.watched_application, app)
        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(app.check_results.count(), 1)

    def test_ordering_by_checked_at_desc(self):
        app = WatchedApplication.objects.create(base_url='https://example.com')
        r1 = CheckResult.objects.create(watched_application=app, success=True)
        r2 = CheckResult.objects.create(watched_application=app, success=False)
        results = list(app.check_results.order_by('-checked_at')[:2])
        self.assertEqual(results[0].id, r2.id)
        self.assertEqual(results[1].id, r1.id)
