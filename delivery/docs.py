"""
docs.py — Google Docs delivery module for Phase 4.

Handles updating Google Docs with the weekly pulse content.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def update_google_doc(
    doc_id: str,
    content: str,
    credentials_path: Optional[str] = None,
) -> dict:
    """
    Update a Google Doc with the pulse content.

    Args:
        doc_id: Google Doc ID to update.
        content: Markdown content to write to the doc.
        credentials_path: Path to Google credentials JSON file (optional).

    Returns:
        Dictionary with success status and doc URL.

    Note:
        This implementation uses the Google Docs API directly.
        For production, this should use MCP server integration.
    """
    logger.info("Updating Google Doc: %s", doc_id)
    logger.info("Content length: %d characters", len(content))

    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        # Try to get OAuth token from environment variable
        gdrive_token_json = os.getenv("GDRIVE_TOKEN_JSON")
        if gdrive_token_json:
            import json
            token_info = json.loads(gdrive_token_json)
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
                "No Google credentials provided. Set GDRIVE_TOKEN_JSON environment variable."
            )

        # Build the Docs API service
        service = build("docs", "v1", credentials=credentials)

        # Get the document to check if it exists
        doc = service.documents().get(documentId=doc_id).execute()
        logger.info("Document title: %s", doc.get("title", "Unknown"))

        # Get the document length
        content_elements = doc.get("body", {}).get("content", [])
        doc_length = content_elements[-1].get("endIndex", 1) if content_elements else 1

        # Delete all content first
        if doc_length > 1:
            requests = [
                {
                    "deleteContentRange": {
                        "range": {
                            "startIndex": 1,
                            "endIndex": doc_length
                        }
                    }
                }
            ]
            try:
                service.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": requests}
                ).execute()
            except Exception as e:
                logger.warning("Failed to delete content: %s", e)

        # Insert all content as plain text at index 1
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": content
                }
            }
        ]
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        logger.info("Successfully updated Google Doc")
        logger.info("Doc URL: %s", doc_url)

        return {
            "success": True,
            "doc_id": doc_id,
            "doc_url": doc_url,
            "message": "Document updated successfully",
        }

    except ImportError:
        logger.error("google-api-python-client not installed. Run: pip install google-api-python-client google-auth")
        return {
            "success": False,
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "message": "google-api-python-client not installed",
        }
    except Exception as e:
        logger.error("Failed to update Google Doc: %s", e)
        return {
            "success": False,
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "message": f"Error: {str(e)}",
        }
