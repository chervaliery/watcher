import json
from django.test import TestCase, Client
from django.urls import reverse

from monitor.models import WatchedApplication, CheckResult


class ApplicationListCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_empty_list(self):
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(data['results'], [])

    def test_get_list_after_creating_apps(self):
        WatchedApplication.objects.create(name='A', base_url='https://a.com')
        WatchedApplication.objects.create(name='B', base_url='https://b.com')
        response = self.client.get('/api/applications/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 2)
        names = [r['name'] for r in data['results']]
        self.assertIn('A', names)
        self.assertIn('B', names)

    def test_post_creates_app_201(self):
        response = self.client.post(
            '/api/applications/',
            data=json.dumps({'base_url': 'https://new.com', 'name': 'New'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['base_url'], 'https://new.com')
        self.assertEqual(data['name'], 'New')
        self.assertEqual(WatchedApplication.objects.count(), 1)

    def test_post_missing_base_url_400(self):
        response = self.client.post(
            '/api/applications/',
            data=json.dumps({'name': 'No URL'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_post_invalid_json_400(self):
        response = self.client.post(
            '/api/applications/',
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class ApplicationDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_detail_200(self):
        app = WatchedApplication.objects.create(name='X', base_url='https://x.com')
        response = self.client.get(f'/api/applications/{app.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], app.id)
        self.assertEqual(data['name'], 'X')

    def test_get_detail_404(self):
        response = self.client.get('/api/applications/99999/')
        self.assertEqual(response.status_code, 404)

    def test_patch_updates_app(self):
        app = WatchedApplication.objects.create(name='X', base_url='https://x.com')
        response = self.client.patch(
            f'/api/applications/{app.id}/',
            data=json.dumps({'name': 'Updated', 'is_active': False}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.name, 'Updated')
        self.assertFalse(app.is_active)

    def test_delete_204_and_removes_app(self):
        app = WatchedApplication.objects.create(name='X', base_url='https://x.com')
        response = self.client.delete(f'/api/applications/{app.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(WatchedApplication.objects.filter(pk=app.id).exists())


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_dashboard_200_and_items(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('items', data)
        self.assertEqual(data['items'], [])


class ApplicationHistoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_history_200_paginated(self):
        app = WatchedApplication.objects.create(name='X', base_url='https://x.com')
        CheckResult.objects.create(watched_application=app, success=True)
        response = self.client.get(f'/api/applications/{app.id}/history/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('total', data)
        self.assertIn('page', data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(len(data['results']), 1)

    def test_get_history_404_missing_app(self):
        response = self.client.get('/api/applications/99999/history/')
        self.assertEqual(response.status_code, 404)
