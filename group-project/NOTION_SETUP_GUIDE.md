# Notion API Setup Guide

Quick guide to set up Notion API credentials for the FYP Meeting Agenda Automation tools.

## Step 1: Get Your Notion API Key

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill in:
   - **Name**: e.g., "FYP Meeting Agent"
   - **Type**: Internal Integration
   - **Associated workspace**: Select your workspace
4. Click **"Submit"**
5. Copy the **Internal Integration Token** (starts with `secret_`)
   - This is your `NOTION_API_KEY`

## Step 2: Get Your Database ID
(Create a database for mockups)
1. Open your Notion database in a web browser
2. Look at the URL: `https://www.notion.so/workspace-name/DATABASE_ID?v=...`
3. The **Database ID** is the 32-character string between the last `/` and the `?`
   - Example: `https://www.notion.so/MyWorkspace/783f0e1074fc4c82b92b0f952b34f423?v=...`
   - Database ID: `783f0e1074fc4c82b92b0f952b34f423`

**Note**: Remove any hyphens from the URL if present. The actual ID is 32 characters without hyphens.

## Step 3: Share Database with Integration

1. Open your Notion database
2. Click **"..."** (three dots) in the top right
3. Click **"Connections"** → **"Add connections"**
4. Search for and select your integration (e.g., "FYP Meeting Agent")
5. Click **"Confirm"**

## Step 4: Add to .env File

Create or edit `.env` file in the `group-project` directory:

```bash
# Notion API Configuration
NOTION_API_KEY=secret_your_api_key_here
NOTION_DATABASE_ID=your_database_id_here
```

**Example:**
```bash
NOTION_API_KEY=secret_abc123xyz789...
NOTION_DATABASE_ID=783f0e1074fc4c82b92b0f952b34f423
```

## Step 5: Verify Setup

Run the test script to verify everything works:

```bash
PYTHONPATH=. python scripts/test_notion_tools.py
```

Select option **1** to test reading from the database.

## Troubleshooting

- **403 Forbidden**: Make sure you've shared the database with your integration (Step 3)
- **404 Not Found**: Check that your Database ID is correct (32 characters, no hyphens)
- **401 Unauthorized**: Verify your API key starts with `secret_` and is copied correctly

## Database Schema Requirements

Your Notion database must have these properties:
- **Meeting Title** (Title property)
- **Meeting Date** (Date property)
- **Status** (Status property with options: Scheduled, Ongoing, Completed, Cancelled)
- **Attendees** (Multi-select property)
- **Discussion Topics** (Rich text property)
- **Action Items** (Rich text property)

Check this template out: https://www.notion.so/FYP-Meeting-Database-1-2bee7c813e1c80c6ada8c63a8c11d6a8?source=copy_link

