"""
alerting.py — Failure alerting system for Phase 6.

Handles alerting on unrecoverable failures via email or Slack webhook.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def send_alert(
    run_id: str,
    stage: str,
    error_summary: str,
    alert_channel: str = "email",
    webhook_url: Optional[str] = None,
    recipient: Optional[str] = None,
) -> bool:
    """
    Send an alert on unrecoverable failure.

    Args:
        run_id: Run ID of the failed pipeline run.
        stage: Stage where failure occurred.
        error_summary: Error summary message.
        alert_channel: Alert channel - "email" or "slack".
        webhook_url: Slack webhook URL (required for slack channel).
        recipient: Email recipient (required for email channel).

    Returns:
        True if alert sent successfully, False otherwise.
    """
    logger.info(f"Sending alert via {alert_channel}: {stage} - {error_summary}")

    try:
        if alert_channel == "slack":
            return _send_slack_alert(run_id, stage, error_summary, webhook_url)
        elif alert_channel == "email":
            return _send_email_alert(run_id, stage, error_summary, recipient)
        else:
            logger.error(f"Unknown alert channel: {alert_channel}")
            return False
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        return False


def _send_slack_alert(
    run_id: str,
    stage: str,
    error_summary: str,
    webhook_url: Optional[str],
) -> bool:
    """
    Send alert via Slack webhook.

    Args:
        run_id: Run ID of the failed pipeline run.
        stage: Stage where failure occurred.
        error_summary: Error summary message.
        webhook_url: Slack webhook URL.

    Returns:
        True if alert sent successfully, False otherwise.
    """
    if not webhook_url:
        logger.error("Slack webhook URL not provided")
        return False

    try:
        import requests

        message = {
            "text": f"⚠️ Pipeline Failure Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ Pipeline Failure Alert"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Run ID:*\n{run_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Stage:*\n{stage}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error:*\n{error_summary}"
                    }
                }
            ]
        }

        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()

        logger.info("Slack alert sent successfully")
        return True

    except ImportError:
        logger.error("requests library not installed")
        return False
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


def _send_email_alert(
    run_id: str,
    stage: str,
    error_summary: str,
    recipient: Optional[str],
) -> bool:
    """
    Send alert via email using Gmail API.

    Args:
        run_id: Run ID of the failed pipeline run.
        stage: Stage where failure occurred.
        error_summary: Error summary message.
        recipient: Email recipient.

    Returns:
        True if alert sent successfully, False otherwise.
    """
    if not recipient:
        logger.error("Email recipient not provided")
        return False

    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64
        from email.mime.text import MIMEText

        # Get Gmail token from environment
        gmail_token_json = os.getenv("GMAIL_TOKEN_JSON")
        if not gmail_token_json:
            logger.error("GMAIL_TOKEN_JSON not set")
            return False

        token_info = json.loads(gmail_token_json)
        credentials = Credentials(
            token=token_info["token"],
            refresh_token=token_info.get("refresh_token"),
            token_uri=token_info["token_uri"],
            client_id=token_info["client_id"],
            client_secret=token_info["client_secret"],
            scopes=token_info["scopes"]
        )

        # Build Gmail service
        service = build("gmail", "v1", credentials=credentials)

        # Create email message
        subject = f"[ALERT] Pipeline Failure - {stage}"
        body = f"""
Pipeline Failure Alert

Run ID: {run_id}
Stage: {stage}
Error: {error_summary}

Please check the logs for more details.
"""

        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send email (not draft)
        service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()

        logger.info(f"Email alert sent successfully to {recipient}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False
