import json
from django.db import models


def default_expected_status_codes():
    return [200]


class WatchedApplication(models.Model):
    """One monitored web application (hostname/URL)."""
    name = models.CharField(max_length=255)
    base_url = models.URLField(max_length=2048, help_text='e.g. https://app.example.com')
    hostname = models.CharField(max_length=255, blank=True, help_text='Optional display or Host header')
    check_interval_seconds = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional client certificate (filesystem paths)
    client_cert_path = models.CharField(max_length=1024, blank=True)
    client_key_path = models.CharField(max_length=1024, blank=True)
    ca_bundle_path = models.CharField(max_length=1024, blank=True)
    # P12 (PKCS#12) client certificate (alternative to cert+key)
    client_p12_path = models.CharField(max_length=1024, blank=True)
    client_p12_password = models.CharField(max_length=256, blank=True)

    # Expected HTTP status codes (JSON list, e.g. [200, 201])
    expected_status_codes = models.JSONField(default=default_expected_status_codes, blank=True)

    # Alert state: when we last sent "down" / "up" email (one per incident)
    alert_down_sent_at = models.DateTimeField(null=True, blank=True)
    alert_up_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name or self.base_url

    def get_expected_status_codes(self):
        if isinstance(self.expected_status_codes, list):
            return self.expected_status_codes
        if isinstance(self.expected_status_codes, str):
            try:
                return json.loads(self.expected_status_codes)
            except (json.JSONDecodeError, TypeError):
                return [200]
        return [200]


class CheckResult(models.Model):
    """One run of a health check for a watched application."""
    watched_application = models.ForeignKey(
        WatchedApplication,
        on_delete=models.CASCADE,
        related_name='check_results'
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    success = models.BooleanField()
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['watched_application', '-checked_at']),
        ]

    def __str__(self):
        return f'{self.watched_application_id} @ {self.checked_at} success={self.success}'
