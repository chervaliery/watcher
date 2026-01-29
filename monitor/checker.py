"""
HTTP health check logic for WatchedApplication.
Uses requests with optional client certificate (PEM or P12) and measures response time.
Evaluates alert threshold and sends Mailjet emails when N consecutive down/up.
"""
import time
import requests
from django.conf import settings
from django.utils import timezone

from .models import WatchedApplication, CheckResult
from .mailjet_send import send_alert_email


DEFAULT_TIMEOUT = 10


def run_check(app: WatchedApplication) -> CheckResult:
    """
    Perform a single HTTP GET to app.base_url and record the result.
    Uses P12 or PEM client cert and CA bundle from app if configured.
    """
    verify = app.ca_bundle_path if app.ca_bundle_path else True
    headers = {'Host': app.hostname} if app.hostname else None
    expected = app.get_expected_status_codes()
    start = time.perf_counter()

    try:
        if app.client_p12_path:
            from requests_pkcs12 import get as pkcs12_get
            resp = pkcs12_get(
                app.base_url,
                pkcs12_filename=app.client_p12_path,
                pkcs12_password=app.client_p12_password or None,
                verify=verify,
                timeout=DEFAULT_TIMEOUT,
                allow_redirects=True,
                headers=headers,
            )
        else:
            kwargs = {
                'url': app.base_url,
                'timeout': DEFAULT_TIMEOUT,
                'allow_redirects': True,
                'verify': verify,
            }
            if app.client_cert_path and app.client_key_path:
                kwargs['cert'] = (app.client_cert_path, app.client_key_path)
            if headers:
                kwargs['headers'] = headers
            resp = requests.get(**kwargs)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        success = resp.status_code in expected
        return CheckResult.objects.create(
            watched_application=app,
            status_code=resp.status_code,
            response_time_ms=elapsed_ms,
            success=success,
            error_message='' if success else f'Unexpected status {resp.status_code}',
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return CheckResult.objects.create(
            watched_application=app,
            status_code=None,
            response_time_ms=elapsed_ms if elapsed_ms else None,
            success=False,
            error_message=str(e),
        )


def evaluate_alerts(app: WatchedApplication):
    """
    If the last N checks are all failures, send one "down" email (unless already sent for this incident).
    If the last N checks are all successes and we had sent a "down" email, send one "back up" email.
    N = ALERT_THRESHOLD from settings.
    """
    threshold = getattr(settings, 'ALERT_THRESHOLD', 5)
    results = list(app.check_results.order_by('-checked_at')[:threshold])
    if len(results) < threshold:
        return

    now = timezone.now()
    all_failed = all(not r.success for r in results)
    all_success = all(r.success for r in results)

    app_name = app.name or app.base_url
    if all_failed:
        # Send down alert if we never sent one, or we already sent "up" after the last "down"
        should_send_down = (
            app.alert_down_sent_at is None
            or (app.alert_up_sent_at is not None and app.alert_up_sent_at > app.alert_down_sent_at)
        )
        if should_send_down:
            last = results[0]
            subject = f"Watcher: {app_name} is down"
            body = (
                f"Application: {app_name}\n"
                f"URL: {app.base_url}\n"
                f"Failed {threshold} times in a row.\n"
                f"Last check: {last.checked_at.isoformat()}\n"
                f"Last error: {last.error_message or 'N/A'}\n"
            )
            send_alert_email(subject, body, None)
            app.alert_down_sent_at = now
            app.save(update_fields=['alert_down_sent_at'])

    if all_success:
        # Send up alert if we had sent a down alert and not yet sent up for this incident
        should_send_up = (
            app.alert_down_sent_at is not None
            and (app.alert_up_sent_at is None or app.alert_up_sent_at < app.alert_down_sent_at)
        )
        if should_send_up:
            subject = f"Watcher: {app_name} is back up"
            body = (
                f"Application: {app_name}\n"
                f"URL: {app.base_url}\n"
                f"Recovered after {threshold} consecutive successful checks.\n"
            )
            send_alert_email(subject, body, None)
            app.alert_up_sent_at = now
            app.save(update_fields=['alert_up_sent_at'])


def run_checks_for_active_apps():
    """
    Run a check for each active WatchedApplication that is due (last check
    older than check_interval_seconds).
    """
    now = timezone.now()
    for app in WatchedApplication.objects.filter(is_active=True):
        last = app.check_results.order_by('-checked_at').first()
        if last:
            delta = (now - last.checked_at).total_seconds()
            if delta < app.check_interval_seconds:
                continue
        run_check(app)
        evaluate_alerts(app)
