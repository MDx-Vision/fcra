# Brightpath Ascend Group (BAG) CRM System
## Complete Feature Documentation for FCRA System Implementation

**Document Purpose:** This document provides a comprehensive breakdown of all features visible in the BAG CRM system to be used as a reference for implementing similar functionality in the FCRA litigation platform.

**Date Created:** December 7, 2025

---

## 1. CONTACT LIST MAIN VIEW

### 1.1 Header Navigation Bar

| Feature | Description | FCRA Implementation Notes |
|---------|-------------|---------------------------|
| **MENU** | Main dropdown menu for system navigation | Keep existing sidebar navigation |
| **HOME** | Return to dashboard/home screen | Already implemented |
| **Version Badge** | Shows "premium version 12.06.25" - displays current system version | Add version display to header |
| **ADD CONTACT** | Opens form to add new contact/client | Implement "Add Dispute" or "Add Client" |
| **SELECT CONTACTS** | Bulk selection tool for multiple contacts | Implement bulk actions for disputes |
| **CHANGE CONTACTS** | Bulk edit selected contacts | Bulk update dispute statuses |
| **GO TO INVOICES** | Navigate to invoices/billing section | Link to payment/fee tracking |
| **MARKETING** | Marketing tools and campaigns | N/A for FCRA |
| **VIRTUAL ASSISTANT MANAGER** | Manage VA assignments | Could adapt for paralegal assignments |
| **TOOLS** | Dropdown with utility tools | Implement tools menu |
| **E-MAILS RELATED** | View all emails for a contact | Link to dispute correspondence |
| **POST PORTALS** | Bulk post to client portals | Bulk document delivery |
| **AFFILIATE LEADS FINDER** | Find affiliate-referred leads | N/A for FCRA |
| **MY NOTES** | Personal notes section | Implement case notes |

### 1.2 Quick Filter Buttons (Below Navigation)

| Button | Function | FCRA Equivalent |
|--------|----------|-----------------|
| **Show Basic Icons** | Toggle between simple/advanced icon display | Keep for FCRA |
| **MARK 1** | Filter by Mark 1 flag | Priority 1 disputes |
| **MARK 2** | Filter by Mark 2 flag | Priority 2 disputes |
| **AFFILIATES** | Show only affiliate contacts | Show attorney referrals |
| **ACTIVE** | Show only active clients | Active disputes |
| **LEADS** | Show only leads (not yet clients) | Intake/prospective clients |
| **FOLLOW UP** | Show contacts needing follow-up | Disputes needing action |
| **SIGNUPS** | Show recent signups | New intakes |
| **LAST 25** | Show last 25 records | Recent 25 disputes |
| **SHOW ALL** | Remove all filters | Show all disputes |
| **Search Keyword** | Text search field | Search by client/bureau/account |
| **Search Button** | Execute search | Execute search |
| **Rows Dropdown** | Select rows per page (100 default) | Pagination control |
| **Page Navigation** | First/Prev/Next/Last buttons | Pagination |
| **Page Indicator** | Shows "47 of 47 of 121 Total" | Record count display |
| **GET PORTAL DATA** | Sync/refresh portal data | Refresh dispute data |

### 1.3 Top Right User Area

| Element | Function | FCRA Equivalent |
|---------|----------|-----------------|
| **Logged as: [username]** | Shows current user | Current user display |
| **Logout** | Log out of system | Logout |
| **My Links** | User's saved links | Quick links |
| **SUPPORT TICKET** | Submit support request | Help/Support |
| **MAKE MONEY WITH US** | Affiliate/referral program | N/A |
| **Numbered Buttons (1-8)** | Quick access to 8 custom links | Customizable shortcuts |
| **View Log** | View activity/audit log | Audit trail |
| **Commissions Report** | View affiliate commissions | N/A |

---

## 2. ROW-LEVEL ACTION ICONS (Left Side of Each Contact Row)

These icons appear on the left side of each contact row and provide quick actions.

### 2.1 Icon Column Breakdown (Left to Right)

| Icon | Visual | Function | Tooltip/Behavior | FCRA Equivalent |
|------|--------|----------|------------------|-----------------|
| **1. Delete** | Red trash can | Delete this client | "Delete this client" - Requires confirmation | Delete dispute/client |
| **2. Flag/Priority** | Orange flag | Mark as priority/important | Toggle priority status | High priority case |
| **3. Charge ($)** | Green dollar sign | Charge client for services | Opens integration options: Chargebee, Pabbly, Authorize.Net, Digital Checks | Process payment |
| **4. Credit Plan** | Blue puzzle piece | Generate Credit Action Plan using LevelupScore | Integrates with LevelupScore API for credit analysis | Generate dispute strategy |
| **5. View Details** | Eye icon | View full contact details | Opens contact detail modal/page | View dispute details |
| **6. Documents** | Folder icon | Access client documents area | Shows warning if no documents. "Click to go to this client's documents area" | Client documents |
| **7. Workflow (WF)** | "WF" badge (yellow/green) | Access Workflow Manager | "Click to go to this client's Workflow Manager" - Opens workflow selector | Dispute workflow stages |
| **8. Notes (N)** | "N" badge (red) | Access client notes | "Click to go to this client's notes" - Opens notes history | Case notes |
| **9. Documents (D)** | "D" badge (blue/red) | Secondary document function | Document status indicator | Document status |
| **10. Star** | Red/yellow star | Mark as starred/favorite | Toggle star status | Starred cases |

### 2.2 Icon States and Colors

| Icon | Active State | Inactive State | Meaning |
|------|--------------|----------------|---------|
| WF Badge | Green background | Yellow background | Workflow in progress vs. needs attention |
| N Badge | Red background | Gray background | Has notes vs. no notes |
| D Badge | Blue background | Red background | Documents complete vs. incomplete |
| Star | Yellow/filled | Hollow/gray | Starred vs. not starred |

---

## 3. DATA COLUMNS

### 3.1 Column Headers (Left to Right)

| Column | Data Type | Sortable | FCRA Equivalent |
|--------|-----------|----------|-----------------|
| **Checkbox** | Selection checkbox | No | Bulk select disputes |
| **[Action Icons]** | See Section 2 | No | See Section 2 |
| **ID/Appt** | Appointment indicator | Yes | Scheduled actions |
| **TYPE** | Contact type code (C, L, I, O, P, X) | Yes | Client status |
| **FIRST NAME** | Client first name | Yes | Client first name |
| **LAST NAME** | Client last name | Yes | Client last name |
| **P** | Unknown (possibly Priority) | - | - |
| **COMPANY** | Company/business name | Yes | Employer/company |
| **STATUS 1** | Primary status (Active Client, Lead, etc.) | Yes | Dispute status |
| **STATUS 2** | Secondary status/tags | Yes | Sub-status |
| **TAGS/GROUPS** | Grouping tags | Yes | Case tags |
| **FOLLOW UP** | Follow-up date (color coded) | Yes | Next action date |
| **MOBILE** | Mobile phone number | Yes | Phone |
| **Checkbox (Mobile)** | Mobile verified checkbox | No | Phone verified |
| **PHONE** | Secondary phone | Yes | Alt phone |
| **EMAIL** | Email address | Yes | Email |
| **AFFILIATE** | Affiliate name/badge | Yes | Referring party |
| **COMM** | Commission indicator | - | N/A |
| **$ STATUS** | Payment status | Yes | Payment status |
| **DATE PAID** | Last payment date | Yes | Payment date |
| **ASSIGNED** | Assigned staff member | Yes | Assigned paralegal |

### 3.2 TYPE Column Values

| Code | Meaning | Color | FCRA Equivalent |
|------|---------|-------|-----------------|
| **C** | Active Client | Green circle | Active Dispute |
| **L** | Lead | Yellow/orange circle | Intake/Prospect |
| **I** | Inactive Client | Gray circle | Closed Dispute |
| **O** | Other | White/hollow circle | Other |
| **P** | Provider | Blue circle | N/A |
| **X** | Cancelled | Red circle | Cancelled |

### 3.3 STATUS 1 Dropdown Options

| Status | Description | FCRA Equivalent |
|--------|-------------|-----------------|
| Active Client | Currently active paying client | Active Dispute |
| Cancelled | Client cancelled services | Dispute Withdrawn |
| Inactive Client | No longer active but not cancelled | Dispute Paused |
| Lead | Prospective client not yet signed | Intake |
| Other | Miscellaneous | Other |
| Provider | Service provider (not a client) | N/A |

### 3.4 Follow-Up Date Color Coding

| Color | Meaning | Action Required |
|-------|---------|-----------------|
| **Green** | Follow-up date in future | Scheduled, no immediate action |
| **Yellow/Orange** | Follow-up date is today or soon | Action needed soon |
| **Red** | Follow-up date is past due | Urgent action required |
| **No color** | No follow-up date set | May need to schedule |

---

## 4. INTERACTIVE ELEMENTS

### 4.1 Name Click Actions

When clicking on a contact's FIRST NAME or LAST NAME:

| Click Combination | Action |
|-------------------|--------|
| **Single Click** | EDIT this contact - Opens full edit form |
| **Click + SHIFT** | SELECT ONLY this contact - Clears other selections |
| **Click + SHIFT + CTRL** | OMIT this contact from the list - Temporarily hide |
| **Click + SHIFT + CTRL + ALT** | COPY Full Name - Copy name to clipboard |

### 4.2 PP Column (Portal Post) Actions

| Click Combination | Action |
|-------------------|--------|
| **Single Click** | VIEW the Client Portal - Opens portal preview |
| **Click (on green PP)** | Click to POST the Client Portal - Publish to client |
| **Click + SHIFT** | Go to Client Portal Options - Configure portal settings |

### 4.3 Hovering on Contact Row

When hovering over a contact row, a quick info popup appears showing:
- Contact ID
- Type
- Company
- Full Address (Street, City, State, ZIP, Country)
- Phone 1 & Phone 2
- Mobile
- Website
- Referrals
- Related To
- Is Affiliate (Yes/No)
- Social Security (masked)
- DOB
- Status 1 & Status 2
- Groups
- Created By
- Created On (Date/Time)

### 4.4 Column-Specific Dropdowns

**STATUS 1 Column Dropdown:**
- Click on status badge to get dropdown with all status options
- Change status in-line without opening full record

**TYPE Column Dropdown:**
- Quick change contact type
- Shows letter codes with descriptions

---

## 5. SPECIAL FEATURES

### 5.1 LevelupScore Integration (Credit Action Plan)

**Tooltip Instructions (from Image 13):**

**Setting Up LevelupScore into the PROGRAM:**
1. Inside your LevelupScore account, go to Integrations > Credit Money Machine
2. Enter your program in the Subdomain field (e.g. 2000.lmrweb2.com)
3. Click Update. LevelupScore will generate an API Key everytime this button is clicked
4. Click the Copy icon of the API Key Field
5. Now, go to your program
6. In the program, click Menu > My Settings > More Settings > LevelupScore Settings
7. Paste the copied API Key in the API Key field
8. (Optional) Enter the description for this integration
9. Click Save Settings

**Sending Data from the PROGRAM to your LevelupScore account:**

Note: Only the following credit report providers are accepted:
- SmartCredit
- IdentityIQ
- MyFreeScoreNow
- MyScoreIQ
- MyScoreNow
- MyThreeScores
- CreditHeroScore

**Steps:**
1. In the Program, go to the Contact List
2. Show the Advanced Icons by clicking the Advanced button
3. There is the blue LevelupScore icon at the left side of the contact you want to use
4. Click the icon to generate the client's Credit Action Plan using Levelup
5. Once generated, the PDF icon will be active. Click the active PDF icon to show the plan in PDF format
6. There is also the Email icon beside the PDF icon which becomes active as well. Click this icon to email the Credit Action Plan to this client.

**FCRA Implementation:** Create similar integration with credit report parsing to auto-generate dispute strategies.

### 5.2 Workflow Manager (Image 16)

The Workflow Selector popup shows:
- **Title:** "WORKFLOW SELECTOR for [Client Name]"
- **Status Tabs:** Status 1: [Current Status] | Status 2:
- **Toggle A/C Button:** Toggle active/cancelled
- **Workflow List with:**
  - Workflow Name (e.g., "FREEZE STATUS REMINDER", "TEST-Email-Trigger")
  - Status Badge showing current workflow status
  - **Go Button:** Execute workflow immediately (green)
  - **All Button:** Apply to all (blue)
  - **Pending Button:** Set to pending (yellow)
  - **Trigger Now Button:** Manually trigger (red)
- **Close Button:** Close the popup

**FCRA Implementation:** Create workflow triggers for:
- Send dispute letter reminders
- Bureau response deadline tracking
- 30/45 day follow-up automation
- Escalation triggers

### 5.3 Notes System (Image 18)

The Notes page shows:
- **Header:** Contact List breadcrumb
- **Navigation:** Back button (arrow icon), Tutorials, Dashboard
- **Action Buttons:** Add New, Show All, Search Keyword, Search
- **Contact Badge:** Shows "Contact: [Client Name]" in red/coral color
- **Table Columns:**
  - Checkbox (for selection)
  - Edit button (blue pencil)
  - Delete button (red X)
  - **EDITED ON:** Date and time of note
  - **Author:** Who created the note (e.g., "Brightpath Ascend Group")
  - **NOTE:** The note content (e.g., "Credit Audit Sent")

**FCRA Implementation:** Case notes for tracking:
- Client communications
- Internal notes
- Dispute progress
- Follow-up reminders
- Credit audit status

### 5.4 Client Portal Post (PP) Column

**States:**
- **Gray PP:** Portal not yet posted
- **Green PP:** Portal has been posted/is live

**Actions:**
- Post portal to make client-facing information available
- Client can view their progress, documents, action items

**FCRA Implementation:** Client portal showing:
- Dispute status
- Documents sent/received
- Bureau responses
- Next steps

### 5.5 Document Management (Folder Icon)

**Warning Message (Image 19):**
"WARNING! There are no documents to print"
"Click to go to this client's documents area"

**FCRA Implementation:**
- Credit reports storage
- Dispute letters (sent/received)
- Bureau correspondence
- Supporting documents
- ID verification docs

---

## 6. PAYMENT/CHARGING INTEGRATION (Image 12)

When clicking the $ (Charge) icon, a dropdown appears showing:

**Charge Client**
- Chargebee | Pabbly | Authorize.Net | Digital Checks

**FCRA Implementation Options:**
- Stripe integration for payment processing
- Invoice generation for attorney fees
- Payment plan tracking
- Retainer management

---

## 7. EMAIL FROM SYSTEM (Image 2)

Example email sent from system (in Spanish):

**From:** Brightpath Ascend Group Customer Support <support@brightpathascendgroup.com>
**To:** client email
**Subject:** Información necesaria sobre las multas de E-ZPass

**Template includes:**
1. Personalized greeting
2. Numbered questions/requirements list
3. Checkbox items for document types needed
4. Clear call to action
5. Professional closing

**FCRA Implementation:** Email templates for:
- Initial intake questionnaire
- Document request letters
- Status updates
- Bureau response notifications
- Next steps instructions

---

## 8. AFFILIATE BADGE SYSTEM

Contacts can have affiliate badges showing:
- Who referred them
- Commission tracking
- Affiliate portal access

**Visible in screenshots:**
- "Luckie Goggns" badge next to some contacts
- "Nora Razak" badge on others
- "ERNEST RACINE" on others

**FCRA Implementation:** Could track:
- Referring attorneys
- Marketing source
- Partner law firms

---

## 9. SYSTEM ARCHITECTURE NOTES

### 9.1 URL Structure
- Main application: `1773.lmrweb2.com/index.php#2`
- Uses PHP backend
- Hash-based routing (#2 indicates section/view)

### 9.2 Session Management
- Shows "Logged as: rafael" in header
- Session-based authentication

### 9.3 Database Structure (Inferred)

**contacts table:**
- id, first_name, last_name, email, phone, mobile
- type (C/L/I/O/P/X)
- status1, status2
- company, address, city, state, zip, country
- ssn, dob
- follow_up_date
- affiliate_id
- assigned_to
- created_by, created_at, updated_at

**notes table:**
- id, contact_id, note_text
- created_by, created_at, updated_at

**workflows table:**
- id, name, trigger_conditions
- status, actions

**documents table:**
- id, contact_id, filename, file_path
- document_type, uploaded_at

---

## 10. RECOMMENDED FCRA IMPLEMENTATION PRIORITY

### Phase 1: Core Contact Management
1. Client list view with filtering
2. Basic CRUD operations
3. Status management
4. Notes system

### Phase 2: Document Management
1. Document upload/storage
2. Credit report parsing integration
3. Dispute letter templates
4. Document generation

### Phase 3: Workflow Automation
1. Workflow triggers
2. Status-based automation
3. Follow-up reminders
4. Deadline tracking

### Phase 4: Client Portal
1. Client-facing view
2. Secure document access
3. Status visibility
4. Communication portal

### Phase 5: Integrations
1. Payment processing
2. Email automation
3. Credit report providers
4. Calendar/scheduling

---

## 11. UI/UX PATTERNS TO REPLICATE

### 11.1 Color Coding System
- **Green:** Active/Good/Complete
- **Yellow/Orange:** Pending/Needs Attention
- **Red:** Urgent/Overdue/Error
- **Blue:** Information/Action Available
- **Gray:** Inactive/Disabled

### 11.2 Icon-Based Quick Actions
- Row-level icons for immediate actions
- Hover tooltips explaining each icon
- Consistent icon placement across all rows

### 11.3 Inline Editing
- Click on status to change in-line
- Dropdown menus for quick selection
- No need to open full edit form for common changes

### 11.4 Bulk Operations
- Checkbox selection for multiple records
- Top-bar actions apply to selected records
- Clear indication of selected count

### 11.5 Filtering and Search
- Multiple filter buttons for common views
- Text search across all fields
- Combinable filters

---

## 12. TECHNICAL IMPLEMENTATION NOTES FOR CLAUDE AI

When implementing these features in the FCRA system:

1. **Database Schema:** Create tables matching the inferred structure with FCRA-specific fields (bureau names, account numbers, dispute reasons, etc.)

2. **API Endpoints:** Build RESTful APIs for all CRUD operations with proper authentication and authorization

3. **Frontend Components:**
   - Reusable table component with sorting/filtering
   - Icon action bar component
   - Modal components for quick edits
   - Dropdown menu components
   - Badge/status components

4. **State Management:** Use appropriate state management for:
   - Selected rows
   - Active filters
   - Current view/page
   - User preferences

5. **Real-time Updates:** Consider WebSockets for:
   - Status changes
   - New notes added
   - Workflow triggers

6. **Security:**
   - Role-based access control
   - Audit logging
   - Sensitive data encryption (SSN, etc.)

---

**END OF DOCUMENT**

*This document should be shared with Claude AI when implementing FCRA system features to ensure feature parity with the BAG CRM system.*
