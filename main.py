#!/usr/bin/env python3
"""
MCP Server Startup Script for Railway Deployment

This script initializes and starts the MCP servers for Google Drive/Docs and Gmail.
It handles OAuth token refresh and environment configuration.
"""

import os
import json
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Configure logging
logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_env_json(env_var_name: str) -> dict:
    """
    Load JSON configuration from environment variable.
    
    Args:
        env_var_name: Name of the environment variable containing JSON
        
    Returns:
        Parsed JSON dictionary
    """
    json_str = os.getenv(env_var_name)
    if not json_str:
        raise ValueError(f"Environment variable {env_var_name} is not set")
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {env_var_name}: {e}")

def refresh_token_if_needed(token_json: dict, credentials_json: dict):
    """
    Refresh OAuth token if expired.
    
    Args:
        token_json: Current token dictionary
        credentials_json: OAuth credentials dictionary
        
    Returns:
        Updated token dictionary
    """
    try:
        creds = Credentials.from_authorized_user_info(token_json)
        
        if creds.expired and creds.refresh_token:
            logger.info("Token expired, refreshing...")
            creds.refresh(Request())
            logger.info("Token refreshed successfully")
            return json.loads(creds.to_json())
        
        logger.info("Token is valid, no refresh needed")
        return token_json
        
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise

def setup_mcp_config():
    """
    Setup MCP server configuration from environment variables.
    """
    logger.info("Setting up MCP server configuration...")
    
    # Load OAuth credentials
    try:
        credentials = load_env_json("GOOGLE_CREDENTIALS_JSON")
        logger.info("Loaded Google OAuth credentials")
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        raise
    
    # Load and refresh Google Drive token
    try:
        gdrive_token = load_env_json("GDRIVE_TOKEN_JSON")
        gdrive_token = refresh_token_if_needed(gdrive_token, credentials)
        logger.info("Google Drive token configured")
    except Exception as e:
        logger.error(f"Failed to configure Google Drive token: {e}")
        raise
    
    # Load and refresh Gmail token
    try:
        gmail_token = load_env_json("GMAIL_TOKEN_JSON")
        gmail_token = refresh_token_if_needed(gmail_token, credentials)
        logger.info("Gmail token configured")
    except Exception as e:
        logger.error(f"Failed to configure Gmail token: {e}")
        raise
    
    # Create MCP config directory
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Write MCP config file
    mcp_config = {
        "gdrive_mcp": {
            "server": "@modelcontextprotocol/server-gdrive",
            "transport": "stdio",
            "credentials": credentials,
            "token": gdrive_token,
            "scopes": [
                "https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive.file"
            ],
            "tools": ["create_document", "update_document", "get_document_url"]
        },
        "gmail_mcp": {
            "server": "gmail-mcp-server",
            "transport": "stdio",
            "credentials": credentials,
            "token": gmail_token,
            "scopes": [
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.send"
            ],
            "default_mode": "draft",
            "tools": ["draft_email", "send_email"]
        },
        "agent": {
            "default_weeks": int(os.getenv("DEFAULT_WEEKS", "8")),
            "max_themes": int(os.getenv("MAX_THEMES", "5")),
            "max_pulse_words": int(os.getenv("MAX_PULSE_WORDS", "250")),
            "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
            "llm_model": os.getenv("LLM_MODEL", "gpt-4o"),
            "llm_token_budget_per_run": int(os.getenv("LLM_TOKEN_BUDGET", "50000")),
            "retry_max_attempts": int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            "log_dir": "logs/",
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "groq_api_key": os.getenv("GROQ_API_KEY")
        }
    }
    
    config_path = config_dir / "mcp-config.json"
    with open(config_path, 'w') as f:
        json.dump(mcp_config, f, indent=2)
    
    logger.info(f"MCP configuration written to {config_path}")
    return config_path

def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy", "service": "mcp-server"}

def main():
    """
    Main entry point for MCP server startup.
    """
    logger.info("Starting MCP server for Railway deployment...")
    logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    logger.info(f"Port: {os.getenv('PORT', '3000')}")
    
    try:
        # Setup MCP configuration
        config_path = setup_mcp_config()
        
        # TODO: Start actual MCP servers here
        # This is a placeholder - actual MCP server startup will be implemented
        # when the MCP servers are selected and configured
        logger.info("MCP server configuration complete")
        logger.info("Note: Actual MCP server startup will be implemented in Phase 4")
        
        # For now, keep the container running
        logger.info("MCP server ready and running...")
        
        # Keep the process alive (placeholder for actual server loop)
        import time
        while True:
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise

if __name__ == "__main__":
    main()
