"""
Send alert emails via Mailjet API v3.1.
Uses requests with Basic Auth; no mailjet-rest dependency.
"""
import base64
import logging

import requests

logger = logging.getLogger(__name__)

MAILJET_SEND_URL = "https://api.mailjet.com/v3.1/send"


def _sanitize_log(value):
    """Replace newlines/carriage returns to prevent log injection."""
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ")


def send_alert_email(subject, body_plain, recipients):
    """
    Send a plain-text email via Mailjet. If Mailjet is not configured
    (missing API key, secret, from email, or recipients), log and return without sending.
    """
    from django.conf import settings

    api_key = getattr(settings, "MAILJET_API_KEY", "") or ""
    secret = getattr(settings, "MAILJET_SECRET", "") or ""
    from_email = getattr(settings, "MAILJET_FROM_EMAIL", "") or ""
    to_list = getattr(settings, "MAILJET_ALERT_TO", None) or []

    if not recipients:
        recipients = to_list
    if not all([api_key, secret, from_email, recipients]):
        logger.info(
            "Mailjet not configured or no recipients; skipping alert email: %s",
            _sanitize_log(subject)[:50],
        )
        return

    auth = base64.b64encode(f"{api_key}:{secret}".encode()).decode()
    payload = {
        "Messages": [
            {
                "From": {"Email": from_email, "Name": "Watcher"},
                "To": [{"Email": email} for email in recipients],
                "Subject": subject,
                "TextPart": body_plain,
            }
        ]
    }
    try:
        resp = requests.post(
            MAILJET_SEND_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        if resp.status_code >= 400:
            logger.warning(
                "Mailjet send failed: status=%s body=%s",
                resp.status_code,
                _sanitize_log(resp.text)[:200],
            )
        else:
            logger.info("Alert email sent: %s", _sanitize_log(subject)[:50])
    except requests.RequestException as e:
        logger.warning("Mailjet send error: %s", _sanitize_log(e))
