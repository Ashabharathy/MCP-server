# Render Deployment Plan — GROWW Weekly Review Pulse Agent

## Overview

This document provides a complete deployment plan for deploying the GROWW Weekly Review Pulse Agent MCP server on Render.com. The deployment includes Google Drive/Docs and Gmail MCP servers with OAuth 2.0 authentication, and supports both OpenAI and GROQ LLM providers.

## Prerequisites

Before deploying to Render, ensure you have:

1. **Render Account**: Create an account at [render.com](https://render.com)
2. **Google Cloud Project**: A Google Cloud project with OAuth 2.0 credentials
3. **GitHub Repository**: Your project code pushed to GitHub (Render integrates with GitHub)
4. **Google OAuth Credentials**: Downloaded `credentials.json` from Google Cloud Console
5. **GROQ API Key**: Get your API key from [console.groq.com](https://console.groq.com)

## Pre-Deployment Setup

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Docs API
   - Google Drive API
   - Gmail API
4. Configure OAuth 2.0 consent screen:
   - Go to APIs & Services → OAuth consent screen
   - Select "External" user type
   - Fill in required app information
   - Add scopes:
     - `https://www.googleapis.com/auth/documents`
     - `https://www.googleapis.com/auth/drive.file`
     - `https://www.googleapis.com/auth/gmail.compose`
     - `https://www.googleapis.com/auth/gmail.send`
5. Create OAuth 2.0 credentials:
   - Go to APIs & Services → Credentials
   - Create credentials → OAuth client ID
   - Application type: Web application
   - Add authorized redirect URIs (for Render, you'll add the Render URL later)
   - Download the credentials as `credentials.json`

### 2. Generate OAuth Tokens Locally

Use the provided `generate_token.py` script to generate tokens:

```bash
# Install dependencies
pip install google-auth-oauthlib google-auth-httplib2

# Generate Google Drive token
python generate_token.py --service gdrive

# Generate Gmail token
python generate_token.py --service gmail
```

This will create:
- `gdrive-token.json`
- `gmail-token.json`

### 3. Get GROQ API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Create a new API key
4. Copy the API key for later use

### 4. Prepare Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- `GOOGLE_CREDENTIALS_JSON`: Paste the contents of your `credentials.json` as a JSON string
- `GDRIVE_TOKEN_JSON`: Paste the contents of `gdrive-token.json` as a JSON string
- `GMAIL_TOKEN_JSON`: Paste the contents of `gmail-token.json` as a JSON string
- `OPENAI_API_KEY`: Your OpenAI API key (optional, if using OpenAI)
- `GROQ_API_KEY`: Your GROQ API key (optional, if using GROQ)
- `LLM_PROVIDER`: Choose between `openai` or `groq`

**Important**: Never commit `.env` to version control. Add it to `.gitignore`.

## Deployment Files

The following files are included for Render deployment:

### 1. `render.yaml`
Configuration file for Render deployment with build and environment settings.

### 2. `Dockerfile`
Docker container configuration for running the MCP server on Render.

### 3. `requirements.txt`
Python dependencies required for the MCP server (includes GROQ SDK).

### 4. `.env.example`
Template for environment variables (do not commit actual `.env`).

### 5. `start_mcp_server.py`
Startup script that initializes MCP servers and handles OAuth token refresh.

## Render Deployment Steps

### Step 1: Push Code to GitHub

Ensure your code is pushed to a GitHub repository:

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 2: Create New Web Service on Render

1. Log in to [render.com](https://render.com)
2. Click "New +"
3. Select "Web Service"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` configuration

### Step 3: Configure Environment Variables

1. In Render, go to your web service settings
2. Navigate to the "Environment" tab
3. Add the following environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_CREDENTIALS_JSON` | Your credentials.json as JSON string | Google OAuth credentials |
| `GDRIVE_TOKEN_JSON` | Your gdrive-token.json as JSON string | Google Drive OAuth token |
| `GMAIL_TOKEN_JSON` | Your gmail-token.json as JSON string | Gmail OAuth token |
| `OPENAI_API_KEY` | Your OpenAI API key | OpenAI API key (optional) |
| `GROQ_API_KEY` | Your GROQ API key | GROQ API key (optional) |
| `LLM_PROVIDER` | `openai` or `groq` | LLM provider to use |
| `DEFAULT_WEEKS` | `8` | Default look-back window in weeks |
| `MAX_THEMES` | `5` | Maximum number of themes |
| `MAX_PULSE_WORDS` | `250` | Maximum pulse word count |
| `LLM_MODEL` | `gpt-4o` or `llama3-70b-8192` | LLM model to use |
| `LLM_TOKEN_BUDGET` | `50000` | Token budget per run |
| `RETRY_MAX_ATTEMPTS` | `3` | Maximum retry attempts |
| `MCP_LOG_LEVEL` | `INFO` | Logging level |
| `PORT` | `3000` | Server port |

**Note**: For JSON values, paste the entire JSON content as a single-line string. You can use a tool like [JSON to String](https://www.freeformatter.com/json-escape.html) to escape the JSON properly.

### Step 4: Update Google OAuth Redirect URIs

1. Go back to Google Cloud Console
2. Navigate to APIs & Services → Credentials
3. Edit your OAuth 2.0 client ID
4. Add your Render service URL as an authorized redirect URI:
   - Format: `https://your-service-name.onrender.com/`
5. Save the changes
6. Download the updated `credentials.json`
7. Update the `GOOGLE_CREDENTIALS_JSON` environment variable in Render

### Step 5: Deploy

1. In Render, click "Create Web Service"
2. Render will build the Docker image and deploy your application
3. Monitor the deployment logs for any errors
4. Once deployed, you'll receive a Render URL for your MCP server

### Step 6: Verify Deployment

1. Check the Render logs to ensure the MCP server started successfully
2. Look for log messages indicating:
   - "Loaded Google OAuth credentials"
   - "Google Drive token configured"
   - "Gmail token configured"
   - "MCP server ready and running"

## Post-Deployment Configuration

### Update MCP Server URLs

After deployment, update your local `mcp-config.json` to use the Render URLs:

```json
{
  "gdrive_mcp": {
    "server": "https://your-service-name.onrender.com",
    "transport": "http"
  },
  "gmail_mcp": {
    "server": "https://your-service-name.onrender.com",
    "transport": "http"
  }
}
```

### Set Up Monitoring

1. Enable Render's built-in metrics and logging
2. Set up alerts for:
   - High error rates
   - Memory/CPU usage thresholds
   - Deployment failures

### Configure Scheduling (Optional)

If you want to run the agent on a schedule:

1. Use Render's cron jobs or external scheduler (e.g., GitHub Actions)
2. Configure the scheduler to trigger the agent pipeline
3. Ensure the agent can access the Render-deployed MCP servers

## LLM Provider Configuration

### Using GROQ

To use GROQ instead of OpenAI:

1. Set `LLM_PROVIDER=groq` in environment variables
2. Set `GROQ_API_KEY` to your GROQ API key
3. Set `LLM_MODEL` to a GROQ-supported model (e.g., `llama3-70b-8192`)

Available GROQ models:
- `llama3-70b-8192`
- `llama3-8b-8192`
- `mixtral-8x7b-32768`

### Using OpenAI

To use OpenAI:

1. Set `LLM_PROVIDER=openai` in environment variables
2. Set `OPENAI_API_KEY` to your OpenAI API key
3. Set `LLM_MODEL` to an OpenAI model (e.g., `gpt-4o`, `gpt-4-turbo`)

## Troubleshooting

### OAuth Token Expired

If you see "Token expired" errors:

1. Run `generate_token.py` locally again
2. Update the corresponding environment variable in Render
3. Redeploy

### Google API Quota Exceeded

If you hit Google API quotas:

1. Check your Google Cloud Console quota settings
2. Request quota increase if needed
3. Implement rate limiting in your application

### Render Build Failures

If the build fails:

1. Check the Render build logs
2. Ensure all dependencies in `requirements.txt` are correct
3. Verify the Dockerfile is compatible with Render's build environment

### MCP Server Connection Issues

If MCP servers can't connect:

1. Verify environment variables are set correctly
2. Check Render logs for authentication errors
3. Ensure Google OAuth credentials have the correct scopes
4. Verify the Render URL is added to Google OAuth redirect URIs

### GROQ API Errors

If you encounter GROQ API errors:

1. Verify your GROQ API key is correct
2. Check GROQ console for rate limits or quota issues
3. Ensure the selected model is available in your GROQ plan

## Security Considerations

1. **Never commit credentials**: Ensure `.env` and token files are in `.gitignore`
2. **Use Render's secret management**: Store sensitive data in Render environment variables, not in code
3. **Rotate tokens regularly**: OAuth tokens should be refreshed periodically
4. **Monitor access**: Keep track of who has access to your Render project and Google Cloud Console
5. **Use HTTPS**: Ensure all MCP server communications use HTTPS

## Cost Estimation

Render pricing:
- Free tier: Available for web services (with limitations)
- Standard tier: Starting at $7/month for production

Google Cloud pricing:
- Google Docs API: Free tier available
- Gmail API: Free tier available
- Additional usage may incur charges

GROQ pricing:
- Free tier: Available with rate limits
- Paid plans: Available for higher usage

OpenAI pricing:
- Pay-as-you-go based on token usage
- Check OpenAI pricing page for current rates

## Maintenance

### Regular Tasks

1. **Monitor logs**: Check Render logs for errors or warnings
2. **Update dependencies**: Keep Python packages updated
3. **Refresh tokens**: OAuth tokens may need periodic refresh
4. **Review quotas**: Monitor Google API usage and quotas
5. **Monitor LLM usage**: Track token usage for cost management

### Updates

To update the deployed application:

1. Make changes to your code
2. Commit and push to GitHub
3. Render will automatically redeploy on push (or trigger manual deploy)

## Rollback

If you need to rollback to a previous version:

1. Go to Render web service settings
2. Navigate to "Deployments"
3. Select the previous deployment
4. Click "Redeploy" to rollback

## Support

For issues related to:
- **Render**: Check [Render documentation](https://render.com/docs)
- **Google APIs**: Check [Google Cloud documentation](https://cloud.google.com/docs)
- **GROQ**: Check [GROQ documentation](https://console.groq.com/docs)
- **This project**: Check the main README.md and implementation-plan.md

## Next Steps

After successful deployment:

1. Test the MCP server endpoints
2. Integrate with the agent orchestrator (Phase 5)
3. Set up monitoring and alerting
4. Configure scheduled runs
5. Document the Render URL for your team

---

**Deployment Status**: Ready for deployment

**Last Updated**: 2026-05-25
