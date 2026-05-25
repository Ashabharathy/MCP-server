"""
gmail.py — Gmail delivery module for Phase 4.

Handles drafting emails with the weekly pulse content.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def draft_email(
    to: str,
    subject: str,
    body: str,
    credentials_path: Optional[str] = None,
) -> dict:
    """
    Draft an email with the pulse content using Gmail API.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body content.
        credentials_path: Path to Google credentials JSON file (optional).

    Returns:
        Dictionary with success status and draft ID.

    Note:
        This implementation uses the Gmail API directly with OAuth 2.0 tokens.
        For production, this should use MCP server integration.
    """
    logger.info("Drafting email to: %s", to)
    logger.info("Subject: %s", subject)
    logger.info("Body length: %d characters", len(body))

    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64
        from email.mime.text import MIMEText

        # Try to get OAuth token from environment variable
        gmail_token_json = os.getenv("GMAIL_TOKEN_JSON")
        if gmail_token_json:
            import json
            token_info = json.loads(gmail_token_json)
            credentials = Credentials(
                token=token_info["token"],
                refresh_token=token_info.get("refresh_token"),
                token_uri=token_info["token_uri"],
                client_id=token_info["client_id"],
                client_secret=token_info["client_secret"],
                scopes=token_info["scopes"]
            )
        else:
            raise ValueError(
                "No Google credentials provided. Set GMAIL_TOKEN_JSON environment variable."
            )

        # Build the Gmail API service
        service = build("gmail", "v1", credentials=credentials)

        # Create the email message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the draft
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw_message}}
        ).execute()

        draft_id = draft["id"]
        logger.info("Successfully created Gmail draft: %s", draft_id)

        return {
            "success": True,
            "to": to,
            "subject": subject,
            "draft_id": draft_id,
            "message": "Email draft created successfully",
        }

    except ImportError:
        logger.error("google-api-python-client not installed. Run: pip install google-api-python-client google-auth")
        return {
            "success": False,
            "to": to,
            "subject": subject,
            "message": "google-api-python-client not installed",
        }
    except Exception as e:
        logger.error("Failed to draft email: %s", e)
        return {
            "success": False,
            "to": to,
            "subject": subject,
            "message": f"Error: {str(e)}",
        }
