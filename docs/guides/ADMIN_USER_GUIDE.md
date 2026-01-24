# FCRA Litigation Platform - Admin User Guide

## Overview

This guide covers all features available to staff members in the FCRA Litigation Platform admin interface. The platform helps manage credit dispute cases, generate dispute letters, track litigation progress, and communicate with clients.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Client Management](#client-management)
4. [Credit Report Analysis](#credit-report-analysis)
5. [Dispute Management](#dispute-management)
6. [Letter Generation](#letter-generation)
7. [Case Management](#case-management)
8. [Communication Tools](#communication-tools)
9. [Analytics & Reports](#analytics--reports)
10. [Settings & Configuration](#settings--configuration)
11. [Advanced Features](#advanced-features)
12. [Keyboard Shortcuts](#keyboard-shortcuts)
13. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Logging In

1. Navigate to `/staff/login`
2. Enter your email and password
3. Click **Login**

**Note:** After 5 failed login attempts, your account will be temporarily locked for security.

### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all features, user management, settings |
| **Attorney** | Case management, litigation review, document generation |
| **Paralegal** | Client management, analysis, letter generation |
| **Staff** | Basic client access, document viewing |

### First-Time Setup

1. Change your temporary password
2. Configure your notification preferences
3. Review the dashboard layout

---

## Dashboard Overview

**URL:** `/dashboard`

The main dashboard provides an at-a-glance view of your workload and key metrics.

### Dashboard Sections

| Section | Description |
|---------|-------------|
| **Quick Stats** | Total clients, active cases, pending analyses |
| **Recent Activity** | Latest client updates and case events |
| **Upcoming Deadlines** | Bureau response deadlines, follow-ups |
| **Action Items** | Tasks requiring immediate attention |

### Navigation Menu

The left sidebar contains links to all major sections:

- **Dashboard** - Main overview
- **Clients** - Client management
- **Client Manager** - Advanced client CRM
- **Analyses** - Credit report analyses
- **Cases** - Litigation cases
- **Letter Queue** - Pending letters
- **Automation Tools** - Batch processing
- **Analytics** - Reports and insights
- **Settings** - System configuration

---

## Client Management

### Viewing Clients

**URL:** `/dashboard/clients`

The clients page displays all clients in a sortable, searchable table.

**Features:**
- Search by name, email, or phone
- Filter by status (Active, Lead, Follow Up, etc.)
- Sort by any column
- Bulk selection for mass actions

### Client Manager (CRM)

**URL:** `/dashboard/client-manager`

The advanced client manager provides BAG CRM-style features:

#### Quick Filters
Click filter buttons to quickly view:
- **ACTIVE** - Active clients
- **LEADS** - New leads
- **FOLLOW UP** - Clients needing follow-up
- **SIGNUPS** - Recent signups

#### Table Columns

| Column | Description |
|--------|-------------|
| Checkbox | Select for bulk actions |
| Name | Client name (click to view details) |
| Type | C=Client, L=Lead, I=Inactive, X=Closed |
| Status | Current case status |
| Status 2 | Secondary status |
| Follow-Up | Next follow-up date (color-coded) |
| Phone | Phone number with verified indicator |
| Email | Email address |
| Tags | Assigned tags |
| Actions | Quick action icons |

#### Follow-Up Color Coding
- **Green** - Follow-up is in the future
- **Yellow** - Follow-up is today
- **Red** - Follow-up is overdue

#### Row Actions

| Icon | Action |
|------|--------|
| **Star** | Mark as favorite |
| **Flag** | Set priority flag (Mark 1/2) |
| **WF** | Open workflow selector |
| **N** | Add note |
| **D** | View documents |
| **View** | Open client details |
| **Delete** | Delete client |

#### Bulk Actions

1. Select multiple clients using checkboxes
2. Use the bulk action toolbar:
   - **Change Status** - Update status for all selected
   - **Assign** - Assign to staff member
   - **Delete** - Delete selected clients

#### Tags System

**Managing Tags:**
1. Click the gear icon next to the search bar
2. Select "Manage Tags"
3. Create, edit, or delete tags
4. Assign colors to tags for visual identification

**Assigning Tags to Clients:**
1. Click in the Tags column for a client
2. Select tags from the dropdown
3. Tags are saved automatically

#### Pagination

Use the pagination controls at the bottom:
- Select rows per page: 10, 25, 50, or 100
- Navigate between pages
- View total client count

### Creating a New Client

**URL:** `/dashboard/clients` → Click "Add Client"

**Required Fields:**
- First Name
- Last Name
- Email

**Optional Fields:**
- Phone, Mobile, Phone 2
- Address (Street, City, State, ZIP)
- Company
- Client Type
- Follow-up Date

### Client Detail View

Click on any client name to view their full profile:

**Tabs:**
1. **Overview** - Basic info, status, notes
2. **Documents** - Uploaded files, letters
3. **Analyses** - Credit report analyses
4. **Disputes** - Active disputes by bureau
5. **Timeline** - Activity history
6. **Communication** - SMS/Email logs
7. **Billing** - Payment history

### Adding Notes

1. Open client detail view
2. Click "Add Note" button
3. Type your note
4. Click "Save"

Notes are timestamped and show the staff member who created them.

---

## Credit Report Analysis

### Submitting a New Analysis

**URL:** `/admin`

1. Enter client information:
   - Client Name
   - Client Email
   - Credit Provider (optional)

2. Paste the credit report HTML into the text area

3. Select options:
   - **Dispute Round** - 1, 2, 3, or 4
   - **Analysis Mode** - Auto or Manual

4. Click **Analyze Report**

### Understanding Analysis Results

After analysis completes, you'll see:

**Violations Found:**
- Account name and creditor
- Bureau (Equifax, Experian, TransUnion)
- FCRA section violated
- Willfulness indicator
- Estimated damages

**Case Score:**
- Total score (1-10)
- Standing score
- Violation quality score
- Settlement probability

**Generated Letters:**
- One dispute letter per bureau
- Download individually or as ZIP

### Viewing Past Analyses

**URL:** `/dashboard/analyses`

Browse all completed analyses with:
- Client name and date
- Dispute round
- Number of violations found
- Case score
- Download links

### Analysis Review (Litigation)

**URL:** `/analysis/{id}/review`

The litigation review page provides:
- Complete case strength dashboard
- Detailed damages breakdown
- Willfulness indicators
- Strategic recommendations
- Accept/Reject workflow buttons

---

## Dispute Management

### Dispute Workflow

1. **Round 1** - Initial dispute letters sent to bureaus
2. **Response Period** - 30-45 days for bureau response
3. **Round 2+** - Follow-up disputes if items not resolved
4. **Escalation** - CFPB complaints, litigation referral

### Tracking Disputes

**URL:** `/dashboard/cases`

View all active disputes with:
- Client name
- Current round
- Bureau status (per bureau)
- Days remaining
- Next action needed

### Uploading Bureau Responses

**URL:** `/dashboard/client-manager` → Select Client → Documents

1. Click "Upload CRA Response"
2. Select the bureau
3. Upload the response letter (PDF/image)
4. Click "Analyze Response" for AI extraction

### Advancing Dispute Rounds

When all bureaus have responded:

1. Open the client's case
2. Review bureau responses
3. Click "Advance to Round X"
4. New dispute letters are generated

---

## Letter Generation

### Letter Queue

**URL:** `/dashboard/letter-queue`

Manage pending letters:
- View all generated letters
- Filter by status (Pending, Sent, Delivered)
- Bulk print or download
- Track certified mail status

### Letter Types

| Type | Description |
|------|-------------|
| **Dispute Letter** | Standard 609/611 dispute to bureaus |
| **Demand Letter** | Pre-litigation demand |
| **Freeze Letter** | Security freeze request |
| **CFPB Complaint** | Consumer Financial Protection Bureau complaint |
| **Cease & Desist** | Debt collector cease & desist |

### Generating Demand Letters

**URL:** `/dashboard/demand-generator`

1. Select the client
2. Choose recipient (bureau or furnisher)
3. Set settlement demand amount
4. Select letter template
5. Click "Generate"
6. Review and download PDF

### Freeze Letters

**URL:** `/dashboard/automation-tools` → Freeze Letters

Generate security freeze letters for all three bureaus:
1. Select clients
2. Click "Generate Freeze Letters"
3. Download ZIP with all letters

---

## Case Management

### Case Overview

**URL:** `/dashboard/case/{case_id}`

Each case page shows:
- Client information
- Case timeline
- All disputes by round
- Violations and damages
- Documents and letters
- Settlement offers

### Case Events

Track all case activity:
- Analysis completed
- Letters generated
- Letters sent
- Responses received
- Status changes

### Settlement Tracking

**URL:** `/dashboard/settlements`

Track settlement offers and payments:
- Pending offers
- Accepted settlements
- Payment received
- Case closed

---

## Communication Tools

### SMS Messaging

**URL:** `/dashboard/settings/sms`

**Setup:**
1. Enter Twilio credentials
2. Configure sender phone number
3. Save settings

**Sending SMS:**
1. Open client detail
2. Click "Send SMS"
3. Type message or select template
4. Click "Send"

**Bulk SMS:**
1. Select multiple clients
2. Click "Bulk SMS"
3. Enter message
4. Click "Send to All"

### Email

**URL:** `/dashboard/settings/email`

**Setup:**
1. Enter SendGrid API key
2. Configure sender email/name
3. Save settings

**Email Templates:**
- Welcome email
- Status update
- Document request
- Settlement notification
- Round completion

**Customizing Templates:**
1. Go to Settings → Email Templates
2. Select template to edit
3. Modify subject and body
4. Use variables: `{{client_name}}`, `{{case_status}}`, etc.
5. Save changes

---

## Analytics & Reports

### Analytics Dashboard

**URL:** `/dashboard/analytics`

View key metrics:
- Total cases by status
- Success rate by violation type
- Average settlement amounts
- Revenue trends
- Bureau compliance rates

### Predictive Analytics

**URL:** `/dashboard/predictive`

AI-powered insights:
- Settlement probability by case
- Churn risk prediction
- Revenue forecast
- Optimal case timing

### Attorney Performance

Track attorney metrics:
- Cases handled
- Win rate
- Average settlement
- Client satisfaction

### Generating Reports

1. Go to Analytics
2. Select date range
3. Choose report type
4. Click "Generate Report"
5. Download PDF or Excel

---

## Settings & Configuration

### General Settings

**URL:** `/dashboard/settings`

Configure:
- Company information
- Default email templates
- Notification preferences
- Auto-advance settings

### Staff Management

**URL:** `/dashboard/staff` (Admin only)

**Adding Staff:**
1. Click "Add Staff Member"
2. Enter name, email, role
3. Set temporary password
4. Click "Create"

**Managing Staff:**
- Edit roles and permissions
- Reset passwords
- Deactivate accounts

### API Keys

**URL:** `/dashboard/settings` → API Keys

**Creating API Key:**
1. Click "Generate New Key"
2. Enter key name
3. Select scopes
4. Set rate limits
5. Copy the key (shown only once!)

### Quick Links

Configure up to 8 custom quick link buttons:
1. Click the gear icon in header
2. Select "Quick Links"
3. Enter label and URL for each slot
4. Save

---

## Advanced Features

### Automation Tools

**URL:** `/dashboard/automation-tools`

Batch processing features:
- Bulk letter generation
- Mass status updates
- Scheduled follow-ups
- Auto-advance rounds

### Credit Import

**URL:** `/dashboard/credit-import`

Import credit reports directly:
1. Enter client's monitoring credentials
2. Select provider (MyScoreIQ, etc.)
3. Click "Import"
4. Report is automatically parsed

### Document Scanner

**URL:** `/dashboard/scanned-documents`

Scan and process documents:
1. Upload document images
2. AI extracts text and data
3. Review and approve
4. Attach to client file

### Specialty Bureaus

**URL:** `/dashboard/specialty-bureaus`

Manage disputes with specialty bureaus:
- ChexSystems
- LexisNexis
- NCTUE
- ARS
- Medical Information Bureau

### CFPB Complaints

**URL:** `/dashboard/cfpb`

Generate CFPB complaints:
1. Select client
2. Choose complaint type
3. AI generates complaint text
4. Review and submit

### Furnisher Database

**URL:** `/dashboard/furnishers`

Manage creditor/furnisher information:
- Contact addresses
- Dispute success rates
- Common violations
- Legal contacts

### Knowledge Base

**URL:** `/dashboard/knowledge-base`

Access reference materials:
- FCRA law summaries
- Case law citations
- Dispute templates
- Training materials

### SOPs

**URL:** `/dashboard/sops`

Standard Operating Procedures:
- New client intake
- Dispute workflow
- Settlement negotiation
- Litigation referral

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` | Quick search |
| `Ctrl + N` | New client |
| `Ctrl + S` | Save current form |
| `Esc` | Close modal/popup |
| `?` | Show keyboard shortcuts |

---

## Troubleshooting

### Common Issues

**"Session expired" error:**
- Your login session has timed out
- Log in again at `/staff/login`

**Analysis not completing:**
- Check credit report format (must be HTML)
- Verify Anthropic API key is configured
- Check the analysis queue for errors

**Letters not generating:**
- Ensure all required client data is present
- Check PDF generation logs
- Verify file storage permissions

**SMS/Email not sending:**
- Verify Twilio/SendGrid credentials
- Check for sufficient account balance
- Review communication logs for errors

### Getting Help

1. Check the Knowledge Base
2. Review SOPs for standard procedures
3. Contact your system administrator
4. Submit a support ticket

### Error Messages

| Error | Solution |
|-------|----------|
| "Missing required fields" | Fill in all required form fields |
| "Invalid email format" | Check email address formatting |
| "Rate limit exceeded" | Wait and try again, or contact admin |
| "Permission denied" | Your role doesn't have access to this feature |
| "Client not found" | Client may have been deleted |

---

## Security Best Practices

1. **Never share your login credentials**
2. **Log out when leaving your workstation**
3. **Use strong, unique passwords**
4. **Report suspicious activity immediately**
5. **Don't download client data to personal devices**
6. **Verify client identity before sharing information**

---

## Quick Reference

### Key URLs

| Page | URL |
|------|-----|
| Login | `/staff/login` |
| Dashboard | `/dashboard` |
| Clients | `/dashboard/clients` |
| Client Manager | `/dashboard/client-manager` |
| Analyses | `/dashboard/analyses` |
| Cases | `/dashboard/cases` |
| Letter Queue | `/dashboard/letter-queue` |
| Analytics | `/dashboard/analytics` |
| Settings | `/dashboard/settings` |
| Staff Management | `/dashboard/staff` |

### Status Codes

| Status | Meaning |
|--------|---------|
| **Active** | Client with active case |
| **Lead** | New potential client |
| **Follow Up** | Needs staff follow-up |
| **Pending** | Awaiting action |
| **Disputed** | Dispute in progress |
| **Resolved** | Case successfully resolved |
| **Closed** | Case closed (any reason) |
| **Litigation** | Referred to litigation |

### FCRA Sections Reference

| Section | Description |
|---------|-------------|
| §605B | Identity theft provisions |
| §607(b) | Accuracy requirement |
| §611 | Dispute investigation procedures |
| §623 | Furnisher responsibilities |

---

**Last Updated:** December 25, 2025
**Platform Version:** 2.0
