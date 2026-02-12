# Notion Database Setup Guide

This document explains how to set up Notion databases for the AgentCraft website.

## Prerequisites

- A Notion account
- Notion integration created (https://www.notion.so/my-integrations)

## Creating the Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "AgentCraft Website"
4. Select the workspace where you want to create the databases
5. Copy the "Internal Integration Token" - this is your `NOTION_API_KEY`

## Database Schemas

### 1. Blog Posts Database

Create a new database in Notion with the following properties:

| Property Name | Type | Configuration |
|--------------|------|---------------|
| Title | Title | (default) |
| Slug | Text | Used in URL, must be unique |
| Status | Select | Options: Draft, Published, Scheduled |
| Published Date | Date | Date when post goes live |
| Author | Person | Post author |
| Tags | Multi-select | Categories/topics |
| Featured Image | Files & media | Main post image |
| Excerpt | Text | Short summary (150-200 chars) |
| SEO Description | Text | Meta description for SEO |
| Content | Page content | (default) Write your blog post here |

**Steps:**
1. Create a new database in Notion
2. Add all properties listed above
3. Share the database with your integration
4. Copy the database ID from the URL (32 character string)
5. Set as `NOTION_BLOG_DATABASE_ID` in your environment variables

### 2. Analysis Database

Create a new database with these properties:

| Property Name | Type | Configuration |
|--------------|------|---------------|
| Title | Title | (default) |
| Slug | Text | Used in URL, must be unique |
| Status | Select | Options: Draft, Published |
| Analysis Type | Select | Options: Market, Technical, Case Study |
| Published Date | Date | Date when analysis goes live |
| Industry | Select | Options: AI, Automation, SaaS, Enterprise, etc. |
| Key Insights | Multi-select | Main takeaways |
| Lead Magnet | Checkbox | Check if this requires email signup |
| Download URL | URL | Link to downloadable resource |
| Content | Page content | (default) Write your analysis here |

**Steps:**
1. Create a new database in Notion
2. Add all properties listed above
3. Share the database with your integration
4. Copy the database ID from the URL
5. Set as `NOTION_ANALYSIS_DATABASE_ID` in your environment variables

### 3. Resources Database

Create a new database with these properties:

| Property Name | Type | Configuration |
|--------------|------|---------------|
| Title | Title | (default) |
| Type | Select | Options: eBook, Template, Guide, Checklist |
| Description | Text | What this resource offers |
| Gated | Checkbox | Check if email required to download |
| Download Link | URL | Direct download link |
| Cover Image | Files & media | Resource thumbnail |
| Tags | Multi-select | Categories/topics |

**Steps:**
1. Create a new database in Notion
2. Add all properties listed above
3. Share the database with your integration
4. Copy the database ID from the URL
5. Set as `NOTION_RESOURCES_DATABASE_ID` in your environment variables

### 4. Leads Database

Create a new database with these properties:

| Property Name | Type | Configuration |
|--------------|------|---------------|
| Email | Email | Lead's email address |
| Name | Text | Lead's name (optional) |
| Source | Select | Options: Blog, Analysis, Resource |
| Submitted Date | Created time | Automatically set |
| Resource Downloaded | Text | Name of resource if applicable |

**Steps:**
1. Create a new database in Notion
2. Add all properties listed above
3. Share the database with your integration
4. Copy the database ID from the URL
5. Set as `NOTION_LEADS_DATABASE_ID` in your environment variables

## Sharing Databases with Integration

For each database:
1. Open the database in Notion
2. Click "..." (more options) in the top right
3. Select "Add connections"
4. Find and select your "AgentCraft Website" integration
5. Click "Confirm"

## Environment Variables

After creating all databases, add these to your `.env` file:

```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_BLOG_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_ANALYSIS_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_RESOURCES_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_LEADS_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Example Content

### Example Blog Post

Create a page in your Blog Posts database with:
- **Title:** "Getting Started with AgentCraft"
- **Slug:** "getting-started-agentcraft"
- **Status:** Published
- **Published Date:** Today
- **Author:** Your name
- **Tags:** Tutorial, Getting Started
- **Excerpt:** "Learn how to get started with AgentCraft and build your first intelligent agent."
- **SEO Description:** "A comprehensive guide to getting started with AgentCraft for building intelligent agents."
- **Content:** Write your blog post content using Notion's editor

### Example Analysis Post

Create a page in your Analysis database with:
- **Title:** "State of AI Automation in 2024"
- **Slug:** "state-ai-automation-2024"
- **Status:** Published
- **Analysis Type:** Market
- **Published Date:** Today
- **Industry:** AI
- **Key Insights:** Market Growth, Key Players, Future Trends
- **Lead Magnet:** Checked (if you want to gate it)
- **Download URL:** Link to PDF or resource
- **Content:** Write your analysis content

### Example Resource

Create a page in your Resources database with:
- **Title:** "Agent Development Checklist"
- **Type:** Checklist
- **Description:** "A comprehensive checklist for developing production-ready AI agents."
- **Gated:** Unchecked (for free resources) or Checked (requires email)
- **Download Link:** Direct link to downloadable file
- **Tags:** Development, Best Practices

## Testing

After setting up:
1. Add test content to each database
2. Make sure all databases are shared with your integration
3. Set environment variables in your `.env` file
4. Run `npm run dev` in the website directory
5. Navigate to different pages to verify content appears

## Troubleshooting

**Content not appearing:**
- Verify database IDs are correct
- Check that databases are shared with your integration
- Ensure Status is set to "Published" for blog posts and analyses
- Check browser console for errors

**Integration errors:**
- Verify NOTION_API_KEY is correct
- Make sure integration has access to the databases
- Check that all required properties exist in databases

**Build failures:**
- The website will use mock data if Notion is unavailable
- Check GitHub Actions logs for specific errors
- Verify all environment variables are set in GitHub Secrets
