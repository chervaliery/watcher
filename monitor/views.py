import json
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.http import JsonResponse
from django.utils import timezone as dj_timezone
from django.views import View
from django.shortcuts import get_object_or_404

from .checker import _is_url_allowed
from .models import WatchedApplication

PARIS_TZ = ZoneInfo('Europe/Paris')


def _format_checked_at_paris(dt):
    """Format datetime in Paris timezone, European style: dd/MM/yyyy HH:mm:ss (24H)."""
    if dt is None:
        return ''
    if dj_timezone.is_naive(dt):
        dt = dj_timezone.make_aware(dt)
    local = dt.astimezone(PARIS_TZ)
    return local.strftime('%d/%m/%Y %H:%M:%S')


def _application_to_dict(app, include_last_check=True):
    d = {
        'id': app.id,
        'name': app.name,
        'base_url': app.base_url,
        'hostname': app.hostname or '',
        'check_interval_seconds': app.check_interval_seconds,
        'is_active': app.is_active,
        'created_at': app.created_at.isoformat(),
        'updated_at': app.updated_at.isoformat(),
        'client_cert_path': app.client_cert_path or '',
        'client_key_path': app.client_key_path or '',
        'ca_bundle_path': app.ca_bundle_path or '',
        'client_p12_path': app.client_p12_path or '',
        'client_p12_password': app.client_p12_password or '',
        'expected_status_codes': app.get_expected_status_codes(),
    }
    if include_last_check:
        last = app.check_results.order_by('-checked_at').first()
        if last:
            d['last_check'] = {
                'checked_at': last.checked_at.isoformat(),
                'checked_at_display': _format_checked_at_paris(last.checked_at),
                'status_code': last.status_code,
                'response_time_ms': last.response_time_ms,
                'success': last.success,
                'error_message': last.error_message or '',
            }
        else:
            d['last_check'] = None
    return d


def _check_result_to_dict(r):
    return {
        'id': r.id,
        'checked_at': r.checked_at.isoformat(),
        'checked_at_display': _format_checked_at_paris(r.checked_at),
        'status_code': r.status_code,
        'response_time_ms': r.response_time_ms,
        'success': r.success,
        'error_message': r.error_message or '',
    }


class ApplicationListCreate(View):
    def get(self, _request):
        apps = WatchedApplication.objects.all().order_by('name')
        return JsonResponse({
            'results': [_application_to_dict(a) for a in apps],
        })

    def post(self, request):
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        name = body.get('name', '').strip()
        base_url = (body.get('base_url') or '').strip()
        if not base_url:
            return JsonResponse({'error': 'base_url is required'}, status=400)
        if not _is_url_allowed(base_url):
            return JsonResponse({'error': 'base_url not allowed (scheme or host blocked for security)'}, status=400)
        app = WatchedApplication(
            name=name or base_url,
            base_url=base_url,
            hostname=(body.get('hostname') or '').strip(),
            check_interval_seconds=int(body.get('check_interval_seconds', 60)),
            is_active=body.get('is_active', True),
            client_cert_path=(body.get('client_cert_path') or '').strip(),
            client_key_path=(body.get('client_key_path') or '').strip(),
            ca_bundle_path=(body.get('ca_bundle_path') or '').strip(),
            client_p12_path=(body.get('client_p12_path') or '').strip(),
            client_p12_password=(body.get('client_p12_password') or '').strip(),
            expected_status_codes=body.get('expected_status_codes') or [200],
        )
        app.save()
        return JsonResponse(_application_to_dict(app), status=201)


class ApplicationDetail(View):
    def get(self, _request, pk):
        app = get_object_or_404(WatchedApplication, pk=pk)
        return JsonResponse(_application_to_dict(app))

    def patch(self, request, pk):
        app = get_object_or_404(WatchedApplication, pk=pk)
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        if 'name' in body:
            app.name = (body['name'] or '').strip() or app.base_url
        if 'base_url' in body:
            url = (body['base_url'] or '').strip()
            if url and not _is_url_allowed(url):
                return JsonResponse({'error': 'base_url not allowed (scheme or host blocked for security)'}, status=400)
            if url:
                app.base_url = url
        if 'hostname' in body:
            app.hostname = (body['hostname'] or '').strip()
        if 'check_interval_seconds' in body:
            app.check_interval_seconds = int(body['check_interval_seconds'])
        if 'is_active' in body:
            app.is_active = bool(body['is_active'])
        if 'client_cert_path' in body:
            app.client_cert_path = (body['client_cert_path'] or '').strip()
        if 'client_key_path' in body:
            app.client_key_path = (body['client_key_path'] or '').strip()
        if 'ca_bundle_path' in body:
            app.ca_bundle_path = (body['ca_bundle_path'] or '').strip()
        if 'client_p12_path' in body:
            app.client_p12_path = (body['client_p12_path'] or '').strip()
        if 'client_p12_password' in body:
            app.client_p12_password = (body['client_p12_password'] or '').strip()
        if 'expected_status_codes' in body:
            app.expected_status_codes = body['expected_status_codes']
        app.save()
        return JsonResponse(_application_to_dict(app))

    def delete(self, _request, pk):
        app = get_object_or_404(WatchedApplication, pk=pk)
        app.delete()
        return JsonResponse({}, status=204)


class ApplicationHistory(View):
    def get(self, _request, pk):
        app = get_object_or_404(WatchedApplication, pk=pk)
        try:
            page = max(1, int(_request.GET.get('page', 1)))
            page_size = min(100, max(1, int(_request.GET.get('page_size', 20))))
        except (TypeError, ValueError):
            page, page_size = 1, 20
        qs = app.check_results.order_by('-checked_at')
        total = qs.count()
        start = (page - 1) * page_size
        results = list(qs[start:start + page_size])
        return JsonResponse({
            'results': [_check_result_to_dict(r) for r in results],
            'count': len(results),
            'total': total,
            'page': page,
            'page_size': page_size,
        })


class DashboardView(View):
    def get(self, _request):
        apps = WatchedApplication.objects.all().order_by('name')
        items = []
        for app in apps:
            last = app.check_results.order_by('-checked_at').first()
            recent = list(app.check_results.order_by('-checked_at')[:5])
            day_ago = dj_timezone.now() - timedelta(hours=24)
            last_24h = app.check_results.filter(checked_at__gte=day_ago)
            total_24h = last_24h.count()
            success_24h = last_24h.filter(success=True).count()
            rate_24h = (success_24h / total_24h * 100) if total_24h else None
            items.append({
                'application': _application_to_dict(app, include_last_check=False),
                'last_check': _check_result_to_dict(last) if last else None,
                'recent_checks': [_check_result_to_dict(r) for r in recent],
                'success_rate_24h': round(rate_24h, 1) if rate_24h is not None else None,
                'checks_24h': total_24h,
            })
        return JsonResponse({'items': items})
