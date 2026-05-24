#!/usr/bin/env python3
"""
Generate token.json from credentials.json using Google OAuth 2.0 flow.

This script performs the OAuth 2.0 authorization flow to generate
access and refresh tokens for Google APIs (Drive/Docs and Gmail).

Usage:
    python generate_token.py --service gdrive
    python generate_token.py --service gmail

Requirements:
    pip install google-auth-oauthlib google-auth-httplib2
"""

import json
import os
from pathlib import Path
import argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# OAuth scopes for different services
SCOPES = {
    "gdrive": [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file"
    ],
    "gmail": [
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send"
    ]
}

def generate_token(credentials_path: str, token_path: str, service: str):
    """
    Generate token.json from credentials.json using OAuth 2.0 flow.
    
    Args:
        credentials_path: Path to credentials.json
        token_path: Path where token.json will be saved
        service: Service name ('gdrive' or 'gmail')
    """
    creds = None
    
    # Check if token file already exists
    if os.path.exists(token_path):
        print(f"Token file already exists at {token_path}")
        print("Loading existing credentials...")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES[service])
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired, refreshing...")
            creds.refresh(Request())
        else:
            print(f"Starting OAuth 2.0 flow for {service}...")
            print(f"Reading credentials from: {credentials_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, 
                SCOPES[service]
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"Token successfully saved to: {token_path}")
    else:
        print("Credentials are valid. No action needed.")

def main():
    parser = argparse.ArgumentParser(description='Generate Google OAuth token.json')
    parser.add_argument(
        '--service', 
        required=True, 
        choices=['gdrive', 'gmail'],
        help='Service to generate token for (gdrive or gmail)'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to credentials.json (default: credentials.json)'
    )
    parser.add_argument(
        '--output',
        help='Output path for token.json (default: {service}-token.json)'
    )
    
    args = parser.parse_args()
    
    # Validate credentials file exists
    if not os.path.exists(args.credentials):
        print(f"Error: credentials.json not found at {args.credentials}")
        print("Please download OAuth credentials from Google Cloud Console and save as credentials.json")
        return 1
    
    # Determine output path
    if args.output:
        token_path = args.output
    else:
        token_path = f"{args.service}-token.json"
    
    print(f"Generating token for: {args.service}")
    print(f"Credentials: {args.credentials}")
    print(f"Output: {token_path}")
    print("-" * 50)
    
    try:
        generate_token(args.credentials, token_path, args.service)
        print("-" * 50)
        print("✓ Token generation complete!")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
