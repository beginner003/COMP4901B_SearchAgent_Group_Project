# Google Calendar API Setup Guide

This guide explains how to set up Google Calendar API access for creating calendar events.

## Required Scope

To create calendar events, you need the following OAuth scope:
```
https://www.googleapis.com/auth/calendar
```

## Setup Steps

### 1. Go to Google OAuth 2.0 Playground

Visit: https://developers.google.com/oauthplayground/

### 2. Select Calendar API Scope

In the left panel:
1. Find **"Calendar API v3"** (scroll down if needed)
2. Check the box for: **`https://www.googleapis.com/auth/calendar`**
   - This scope allows creating, reading, updating, and deleting calendar events

### 3. Authorize APIs

1. Click **"Authorize APIs"** button
2. Sign in with your Google account
3. Review the permissions and click **"Allow"**

### 4. Exchange for Access Token

1. Click **"Exchange authorization code for tokens"**
2. Copy the **"Access token"** (starts with `ya29.`)

### 5. Add to .env File

Add the token to your `.env` file:

```bash
GOOGLE_CALENDAR_ACCESS_TOKEN=ya29.your_access_token_here
```

**OR** if you're using the same token for both Gmail and Calendar:

```bash
GMAIL_ACCESS_TOKEN=ya29.your_access_token_here
```

The code will check both `GOOGLE_CALENDAR_ACCESS_TOKEN` and `GMAIL_ACCESS_TOKEN`.

## Important Notes

### Token Expiration
- Access tokens expire after **1 hour**
- If you get 401 errors, refresh your token from OAuth Playground
- For production, you'll need to implement refresh tokens

### Scope Requirements
- **Gmail API**: Requires `https://www.googleapis.com/auth/gmail.send`
- **Calendar API**: Requires `https://www.googleapis.com/auth/calendar`
- You can authorize both scopes in the same OAuth session

### Using Multiple Scopes

If you need both Gmail and Calendar access:

1. In OAuth Playground, select **both** scopes:
   - `Gmail API v1` → `https://www.googleapis.com/auth/gmail.send`
   - `Calendar API v3` → `https://www.googleapis.com/auth/calendar`

2. Authorize both

3. Exchange for tokens

4. Use the same access token for both APIs (it will have both scopes)

## Troubleshooting

### Error 403: Insufficient Permissions

**Problem:** Token doesn't have the Calendar scope

**Solution:**
1. Make sure you selected `https://www.googleapis.com/auth/calendar` scope
2. Re-authorize in OAuth Playground
3. Get a fresh token
4. Update your `.env` file

### Error 401: Invalid Credentials

**Problem:** Token expired or invalid

**Solution:**
1. Tokens expire after 1 hour
2. Get a fresh token from OAuth Playground
3. Update your `.env` file immediately

### Error 400: Bad Request

**Problem:** Invalid date/time format or missing required fields

**Solution:**
- Check that `start_time` and `end_time` are in ISO 8601 format
- Example: `2024-12-15T14:00:00` or `2024-12-15T14:00:00+08:00`
- Make sure `summary` (event title) is provided

## Testing

Run the test script to verify your setup:

```bash
PYTHONPATH=. python scripts/test_calendar_tools.py
```

Choose option 1 (Create Simple Event) to test with minimal setup.

## API Endpoint

The calendar event creation uses:
```
POST https://www.googleapis.com/calendar/v3/calendars/primary/events
```

With headers:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

## Sample Request Body

```json
{
  "summary": "FYP Team Meeting",
  "start": {
    "dateTime": "2024-12-15T14:00:00",
    "timeZone": "Asia/Hong_Kong"
  },
  "end": {
    "dateTime": "2024-12-15T15:00:00",
    "timeZone": "Asia/Hong_Kong"
  },
  "description": "Team meeting to discuss project progress.",
  "attendees": [
    {"email": "yoyo@gmail.com"},
    {"email": "tianyuuu209@gmail.com"}
  ],
  "location": "Online Meeting"
}
```

## Next Steps

For production use, you should:
1. Implement OAuth 2.0 flow with refresh tokens
2. Store tokens securely (not in `.env` file)
3. Handle token refresh automatically
4. Use service accounts for server-to-server authentication (if applicable)

