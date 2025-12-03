# Gmail API Setup for GMAIL_ACCESS_TOKEN

This guide shows how to obtain a Gmail OAuth 2.0 access token and configure the project to send meeting notification emails.

## Prerequisites
- A Google account
- A Google Cloud project
- Gmail API enabled for the project

## Enable Gmail API
1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Select your project.
3. Navigate to “APIs & Services” → “Library”.
4. Search “Gmail API” → Enable.

## Configure OAuth Consent Screen
1. In “APIs & Services” → “OAuth consent screen”, configure an External or Internal app.
2. Add yourself as a test user if the app is not published.
3. Save.

## Create OAuth Client
Choose ONE of the following depending on your method:

- If you will use OAuth 2.0 Playground with “Use your own OAuth credentials”, create a “Web application” client and add the redirect URI below.
- If you will run a local flow in code (loopback on localhost), create a “Desktop app” client.

Steps:
1. In “APIs & Services” → “Credentials” → “Create Credentials” → “OAuth client ID”.
2. Pick either:
   - “Web application”: add Authorized redirect URI `https://developers.google.com/oauthplayground`
   - “Desktop app”: no redirect URIs needed (used for local installed-app flow)
3. Download credentials (client ID and client secret).

## Quick Token via OAuth 2.0 Playground (Fastest)
1. Open: https://developers.google.com/oauthplayground/
2. Option A (recommended): do NOT use your own credentials. Leave “Use your own OAuth credentials” unchecked and proceed. This avoids redirect URI issues.
   - If you need to use your own credentials, then:
     - Click “Settings” (gear icon) → check “Use your own OAuth credentials” → paste the Client ID and Secret of the “Web application” client that has redirect URI `https://developers.google.com/oauthplayground`.
3. In the left scope list, find and select:
   - `https://www.googleapis.com/auth/gmail.send`
4. Click “Authorize APIs” → complete Google auth.
5. Click “Exchange authorization code for tokens”.
6. Copy the “Access token”.

Note: Access tokens expire (~1 hour). If you get HTTP 401, repeat the exchange to get a fresh token.

## Set Environment Variable
Create or update `.env` in the project root (`group-project/.env`) with:

```
GMAIL_ACCESS_TOKEN="<paste-access-token>"
```

The code loads `.env` via `python-dotenv`. You may also set `group-project/src/.env`, but the recommended location is the project root.

## Send Meeting Emails (CLI)
Use the meeting email mode to send notifications. Example:

```
uv run python src/main.py \
  --mode meeting_email \
  --subject "Meeting Scheduled: FYP Progress" \
  --attendees "alice@example.com,bob@example.com" \
  --calendar_link "https://calendar.google.com/event?..." \
  --notion_link "https://www.notion.so/your-page" \
  --suggestion_query "best practices for final year project demos"
```

- Adds calendar and Notion links.
- Optionally appends a “Resources” section from Google Search (Serper API).

## Troubleshooting
- 401 Unauthorized: Access token expired; get a new token in OAuth Playground.
- 403 Insufficient permission: Ensure the scope `gmail.send` was granted.
- 400 invalid_grant: Check that you used your own OAuth credentials and the consent screen allows your user.
- Missing token: Set `GMAIL_ACCESS_TOKEN` in `.env`.

### Error 400: redirect_uri_mismatch
這個錯誤代表 OAuth 用戶端的「授權的重新導向 URI」與實際使用的重新導向 URI 不一致。

修正方式（擇一）：
- 使用 OAuth Playground 的預設用戶端（在設定中不要勾選「Use your own OAuth credentials」），然後直接授權並交換 token。
- 若要使用自己的 OAuth 用戶端，在 Google Cloud Console 以「Web application」型態建立用戶端，並在授權的重新導向 URI 加入：
  - `https://developers.google.com/oauthplayground`
  然後在 OAuth Playground 設定中勾選「Use your own OAuth credentials」，填入該 Web application 的 Client ID/Secret。

注意：「Desktop app」型態沒有重新導向 URI 設定，若你在 Playground 使用自己的 Desktop app 憑證，會出現 `redirect_uri_mismatch`。Desktop app 用於本機程式的安裝式流程（loopback localhost），不適用於 Playground。

## Advanced: Refresh Tokens (Optional)
For long-running automation, implement the OAuth “installed app” flow to store a refresh token and exchange it for new access tokens programmatically. Libraries like `google-auth-oauthlib` can help.

## Security
- Do not commit tokens to version control.
- Restrict access to your Cloud project and OAuth credentials.

PYTHONPATH=. uv run python src/main.py --mode meeting_agent --request "Plan a meeting next Tuesday at 2pm to discuss our project progress. Include agenda items about: demo preparation, code review, and documentation updates. Invite team members: tianyuuu209@gmail.com" --attendees "tianyuuu209@gmail.com" --timezone "Asia/Hong_Kong" --suggestion_query "best practices for final year project demos" --traj_out results/meeting_trajectories.jsonl