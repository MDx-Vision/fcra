# User Acceptance Testing (UAT) Plan

> Comprehensive manual testing checklist for Brightpath Ascend FCRA Platform
>
> Created: 2026-01-09

---

## Test Environment Setup

### Prerequisites
- [ ] PostgreSQL database running with test data
- [ ] Flask server running (`python3 app.py`)
- [ ] Test accounts created (see below)

### Test Accounts

| Role | Email | Password | Purpose |
|------|-------|----------|---------|
| Staff Admin | `test@example.com` | `testpass123` | Staff dashboard testing |
| Client | `testclient@example.com` | `test123` | Client portal testing |
| Partner | (create in test) | (create in test) | Partner portal testing |

---

## PART 1: Client Journey Testing

### 1.1 Signup Flow

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.1.1 | Access signup page | Navigate to `/get-started` | Signup form displays with all fields | [ ] | |
| 1.1.2 | Form validation - empty | Submit empty form | Error messages for required fields | [ ] | |
| 1.1.3 | Form validation - invalid email | Enter "notanemail" | Email validation error | [ ] | |
| 1.1.4 | Form validation - invalid phone | Enter "123" | Phone validation error | [ ] | |
| 1.1.5 | Credit monitoring dropdown | Click dropdown | All services listed (IdentityIQ, MyScoreIQ, etc.) | [ ] | |
| 1.1.6 | SSN field - masked input | Enter SSN last 4 | Input is masked/secure | [ ] | |
| 1.1.7 | Successful signup | Fill all fields, submit | Success message, redirect or email sent | [ ] | |
| 1.1.8 | Duplicate email | Try signup with existing email | Error: email already exists | [ ] | |
| 1.1.9 | SMS opt-in checkbox | Check/uncheck SMS opt-in | Preference saved correctly | [ ] | |
| 1.1.10 | Email opt-in checkbox | Uncheck email opt-in | Preference saved correctly | [ ] | |

### 1.2 Portal Login

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.2.1 | Access login page | Navigate to `/portal/login` | Login form displays | [ ] | |
| 1.2.2 | Invalid credentials | Enter wrong password | Error: invalid credentials | [ ] | |
| 1.2.3 | Valid login | Enter correct credentials | Redirects to portal dashboard | [ ] | |
| 1.2.4 | Forgot password link | Click "Forgot Password" | Password reset form appears | [ ] | |
| 1.2.5 | Password reset flow | Enter email, submit | Reset email sent (check logs) | [ ] | |
| 1.2.6 | Session persistence | Login, close browser, reopen | Session maintained | [ ] | |
| 1.2.7 | Logout | Click logout button | Redirected to login page | [ ] | |

### 1.3 Onboarding Wizard

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.3.1 | Onboarding navigation | Login as new client | See Setup, Agreements, Profile tabs | [ ] | |
| 1.3.2 | Personal info form | Fill personal information | Form saves, progress updates | [ ] | |
| 1.3.3 | ID upload - DL front | Upload driver's license front | File uploads, checkmark appears | [ ] | |
| 1.3.4 | ID upload - DL back | Upload driver's license back | File uploads successfully | [ ] | |
| 1.3.5 | ID upload - SSN card | Upload SSN card | File uploads successfully | [ ] | |
| 1.3.6 | ID upload - proof of address | Upload utility bill | File uploads successfully | [ ] | |
| 1.3.7 | File size validation | Upload file > 25MB | Error: file too large | [ ] | |
| 1.3.8 | File type validation | Upload .exe file | Error: invalid file type | [ ] | |
| 1.3.9 | Credit monitoring setup | Enter credentials | Credentials saved (encrypted) | [ ] | |
| 1.3.10 | Progress indicator | Complete each step | Progress bar updates | [ ] | |

### 1.4 Agreement Signing (CROA)

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.4.1 | Access agreements | Click Agreements tab | Document 1 displays | [ ] | |
| 1.4.2 | Scroll requirement | Try to sign without scrolling | Sign button disabled | [ ] | |
| 1.4.3 | Scroll to bottom | Scroll document to bottom | Sign button enables | [ ] | |
| 1.4.4 | Signature - drawn | Draw signature on canvas | Signature captured | [ ] | |
| 1.4.5 | Signature - typed | Type name in field | Name accepted as signature | [ ] | |
| 1.4.6 | Sign document | Click Sign & Continue | Progress to next document | [ ] | |
| 1.4.7 | Document order | Complete all 7 documents | Must sign in order (1-7) | [ ] | |
| 1.4.8 | Optional document skip | At HIPAA (doc 7) | "Skip" option available | [ ] | |
| 1.4.9 | Cancellation notice | After all signatures | 3-day cancellation countdown shows | [ ] | |
| 1.4.10 | Cancellation period | Check countdown timer | Shows correct end date (3 business days) | [ ] | |

### 1.5 Payment Flow

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.5.1 | Payment page display | After agreements | Payment form shows with pricing | [ ] | |
| 1.5.2 | Pricing breakdown | View pricing | Shows $199 analysis + $298 Round 1 | [ ] | |
| 1.5.3 | Credit card form | Enter test card | Stripe elements load | [ ] | |
| 1.5.4 | Invalid card | Enter invalid card number | Error: card declined | [ ] | |
| 1.5.5 | Successful payment | Use test card 4242... | Payment succeeds | [ ] | |
| 1.5.6 | Post-payment status | After payment | Client stage updates to active | [ ] | |

### 1.6 Active Client Dashboard

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.6.1 | Dashboard access | Login as active client | Full navigation visible | [ ] | |
| 1.6.2 | Case tab | Click Case tab | Dashboard with status cards | [ ] | |
| 1.6.3 | Current round display | View dashboard | Shows current dispute round | [ ] | |
| 1.6.4 | Bureau items count | View dashboard | Shows items per bureau | [ ] | |
| 1.6.5 | Recent activity | View dashboard | Shows latest case events | [ ] | |
| 1.6.6 | Bureau status detail | Click "View Details" | Detailed item breakdown | [ ] | |

### 1.7 Document Management

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.7.1 | Documents tab | Click Documents tab | Document list displays | [ ] | |
| 1.7.2 | Upload CRA response | Click "CRA Response" | Bureau selection appears | [ ] | |
| 1.7.3 | Bureau selection | Select Equifax | Checkbox selected | [ ] | |
| 1.7.4 | Round selection | Select Round 1 | Dropdown selects correctly | [ ] | |
| 1.7.5 | File upload | Upload PDF | File uploads successfully | [ ] | |
| 1.7.6 | Document preview | Click preview icon | PDF viewer opens | [ ] | |
| 1.7.7 | Document download | Click download icon | File downloads | [ ] | |
| 1.7.8 | Upload other docs | Upload ID, credit report | Files upload correctly | [ ] | |

### 1.8 Messaging

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.8.1 | Messages tab | Click Contact/Messages | Chat interface displays | [ ] | |
| 1.8.2 | Send message | Type and send message | Message appears in chat | [ ] | |
| 1.8.3 | Message history | View previous messages | History loads correctly | [ ] | |
| 1.8.4 | Unread count | Receive reply (staff side) | Unread badge updates | [ ] | |

### 1.9 Call Booking

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.9.1 | Booking page | Click "Book a Call" | Booking calendar displays | [ ] | |
| 1.9.2 | Available slots | View slots | Available times shown | [ ] | |
| 1.9.3 | Select slot | Click on available slot | Slot selected | [ ] | |
| 1.9.4 | Confirm booking | Click confirm | Booking created | [ ] | |
| 1.9.5 | View bookings | Check "Your Calls" | Upcoming booking listed | [ ] | |
| 1.9.6 | Cancel booking | Cancel a booking | Booking cancelled | [ ] | |

### 1.10 Journey Timeline

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.10.1 | Timeline access | Click Journey tab | Timeline displays | [ ] | |
| 1.10.2 | Events display | View timeline | Events in chronological order | [ ] | |
| 1.10.3 | Event categories | Check event badges | Correct category colors | [ ] | |
| 1.10.4 | Milestone markers | Look for milestones | Key events highlighted | [ ] | |

### 1.11 Profile Settings

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.11.1 | Profile tab | Click Profile tab | Profile form displays | [ ] | |
| 1.11.2 | Update phone | Change phone number | Phone updates | [ ] | |
| 1.11.3 | Update address | Change address | Address updates | [ ] | |
| 1.11.4 | Notification prefs | Toggle notifications | Preferences save | [ ] | |
| 1.11.5 | Push notifications | Enable push | Subscription created | [ ] | |
| 1.11.6 | Bureau freeze status | View freeze section | All 12 bureaus listed | [ ] | |
| 1.11.7 | Update freeze status | Change bureau status | Status updates | [ ] | |

### 1.12 Billing

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.12.1 | Billing section | Navigate to billing | Invoice list displays | [ ] | |
| 1.12.2 | Invoice download | Click download | PDF downloads | [ ] | |
| 1.12.3 | Payment plans | View payment plans | Plans display if any | [ ] | |
| 1.12.4 | Subscription | View subscription | Current plan shown | [ ] | |

### 1.13 Theme & PWA

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 1.13.1 | Dark mode toggle | Click theme toggle | Theme switches | [ ] | |
| 1.13.2 | Theme persistence | Refresh page | Theme preference retained | [ ] | |
| 1.13.3 | PWA install prompt | Visit on mobile | "Add to Home Screen" appears | [ ] | |
| 1.13.4 | Offline page | Disconnect internet | Offline page shows | [ ] | |

---

## PART 2: Staff Dashboard Testing

### 2.1 Staff Login

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.1.1 | Access login | Navigate to `/staff/login` | Login form displays | [ ] | |
| 2.1.2 | Valid login | Enter staff credentials | Redirects to dashboard | [ ] | |
| 2.1.3 | 2FA challenge | If 2FA enabled | 2FA code prompt appears | [ ] | |
| 2.1.4 | 2FA verify | Enter valid code | Login succeeds | [ ] | |
| 2.1.5 | Invalid 2FA code | Enter wrong code | Error message | [ ] | |
| 2.1.6 | Backup code | Use backup code | Login succeeds | [ ] | |

### 2.2 Dashboard Overview

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.2.1 | Dashboard loads | After login | Dashboard with stats displays | [ ] | |
| 2.2.2 | Sidebar navigation | Click sidebar items | All sections accessible | [ ] | |
| 2.2.3 | Accordion menu | Click section headers | Only one section open at a time | [ ] | |
| 2.2.4 | Quick stats | View top cards | Stats load correctly | [ ] | |

### 2.3 Client Management

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.3.1 | Client list | Click "All Clients" | Client table displays | [ ] | |
| 2.3.2 | Search clients | Enter search term | Results filter | [ ] | |
| 2.3.3 | Filter by status | Select status filter | Results filter | [ ] | |
| 2.3.4 | View client | Click client row | Client details page | [ ] | |
| 2.3.5 | Edit client | Edit client fields | Changes save | [ ] | |
| 2.3.6 | Lead score display | Check lead score column | Scores shown with colors | [ ] | |
| 2.3.7 | Batch select | Select multiple clients | Batch toolbar appears | [ ] | |
| 2.3.8 | Batch action | Run batch status update | Status updates for all | [ ] | |

### 2.4 Case Workflow

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.4.1 | Pending review | Click "Pending Review" | Cases needing review | [ ] | |
| 2.4.2 | Ready to deliver | Click "Ready to Deliver" | Letters ready to send | [ ] | |
| 2.4.3 | Bureau tracking | Click "Bureau Tracking" | Dispute tracking page | [ ] | |
| 2.4.4 | Track new dispute | Add new dispute | Dispute tracked with deadline | [ ] | |
| 2.4.5 | Record response | Record bureau response | Response logged | [ ] | |
| 2.4.6 | Overdue check | Check overdue disputes | Overdue items highlighted | [ ] | |

### 2.5 Credit Analysis

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.5.1 | Upload report | Upload credit report PDF | Report parses | [ ] | |
| 2.5.2 | Run analysis | Click "Analyze" | AI analysis runs | [ ] | |
| 2.5.3 | View violations | Check violations tab | Violations identified | [ ] | |
| 2.5.4 | View dispute items | Check dispute items | Items categorized | [ ] | |
| 2.5.5 | Generate letters | Click "Generate Letters" | Letters created | [ ] | |

### 2.6 Letter Management

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.6.1 | Letter templates | Click "Letter Templates" | Template list displays | [ ] | |
| 2.6.2 | Create template | Create new template | Template saves | [ ] | |
| 2.6.3 | Edit template | Edit existing template | Changes save | [ ] | |
| 2.6.4 | Preview template | Preview with variables | Variables substituted | [ ] | |
| 2.6.5 | Generate letter | Generate for client | Letter created | [ ] | |
| 2.6.6 | AI dispute writer | Use AI writer | Letters generated | [ ] | |

### 2.7 Communication

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.7.1 | Messages inbox | Click "Messages" | Client conversations list | [ ] | |
| 2.7.2 | Reply to client | Send reply message | Message sent | [ ] | |
| 2.7.3 | Unread badge | New message received | Badge updates | [ ] | |
| 2.7.4 | Email templates | Click "Email Templates" | Template library | [ ] | |
| 2.7.5 | Send email | Send templated email | Email sent | [ ] | |
| 2.7.6 | Drip campaigns | Click "Drip Campaigns" | Campaign list | [ ] | |
| 2.7.7 | Create campaign | Create new campaign | Campaign created | [ ] | |
| 2.7.8 | Enroll client | Enroll in campaign | Client enrolled | [ ] | |

### 2.8 Bookings

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.8.1 | Booking management | Click "Bookings" | Booking dashboard | [ ] | |
| 2.8.2 | Create slot | Create time slot | Slot available | [ ] | |
| 2.8.3 | Bulk create | Create bulk slots | Multiple slots created | [ ] | |
| 2.8.4 | View bookings | Check bookings tab | Client bookings listed | [ ] | |
| 2.8.5 | Complete booking | Mark booking complete | Status updates | [ ] | |

### 2.9 Analytics

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.9.1 | Analytics overview | Click "Analytics" | Overview dashboard | [ ] | |
| 2.9.2 | Revenue dashboard | Click "Revenue" | Revenue metrics display | [ ] | |
| 2.9.3 | Staff performance | Click "Staff Performance" | Leaderboard displays | [ ] | |
| 2.9.4 | Client success | Click "Client Success" | Success metrics | [ ] | |
| 2.9.5 | ROI calculator | Click "ROI Calculator" | Calculator page | [ ] | |
| 2.9.6 | Export data | Export CSV | File downloads | [ ] | |

### 2.10 Automation

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.10.1 | Workflow triggers | Click "Workflow Triggers" | Triggers list | [ ] | |
| 2.10.2 | Create trigger | Create new trigger | Trigger saves | [ ] | |
| 2.10.3 | Auto-pull | Click "Auto-Pull" | Credit pull dashboard | [ ] | |
| 2.10.4 | Add credentials | Add client credentials | Credentials saved | [ ] | |
| 2.10.5 | Manual pull | Trigger manual pull | Report pulled | [ ] | |
| 2.10.6 | Task queue | Click "Task Queue" | Queue status | [ ] | |

### 2.11 Settings

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 2.11.1 | Settings page | Click "Settings" | Settings form | [ ] | |
| 2.11.2 | 2FA setup | Enable 2FA | QR code displays | [ ] | |
| 2.11.3 | 2FA verify | Enter TOTP code | 2FA enabled | [ ] | |
| 2.11.4 | Staff management | Click "Staff Management" | Staff list | [ ] | |
| 2.11.5 | Audit logs | Click "Audit Logs" | Log entries display | [ ] | |

---

## PART 3: Partner Portal Testing

### 3.1 Partner Login

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.1.1 | Access login | Navigate to `/partner/login` | Login form displays | [ ] | |
| 3.1.2 | Create partner | (via admin) Create partner account | Account created | [ ] | |
| 3.1.3 | Valid login | Enter partner credentials | Redirects to partner dashboard | [ ] | |
| 3.1.4 | Forgot password | Click forgot password | Reset email sent | [ ] | |

### 3.2 Partner Dashboard

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.2.1 | Dashboard loads | After login | Stats and quick actions | [ ] | |
| 3.2.2 | Recent clients | View recent clients | Tenant's clients only | [ ] | |
| 3.2.3 | Quick stats | View stats cards | Correct counts | [ ] | |

### 3.3 Branding

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.3.1 | Branding page | Click "Branding" | Branding settings | [ ] | |
| 3.3.2 | Upload logo | Upload logo file | Logo saves | [ ] | |
| 3.3.3 | Upload favicon | Upload favicon | Favicon saves | [ ] | |
| 3.3.4 | Primary color | Change primary color | Color updates | [ ] | |
| 3.3.5 | Company info | Update company name | Info saves | [ ] | |
| 3.3.6 | Custom CSS | Add custom CSS | Styles apply | [ ] | |

### 3.4 Partner Clients

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.4.1 | Client list | Click "Clients" | Only tenant's clients | [ ] | |
| 3.4.2 | Search clients | Search by name | Results filter | [ ] | |
| 3.4.3 | Filter status | Filter by status | Results filter | [ ] | |
| 3.4.4 | Export CSV | Export clients | CSV downloads | [ ] | |

### 3.5 Partner Team

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.5.1 | Team page | Click "Team" | Team member list | [ ] | |
| 3.5.2 | Invite member | Click invite | Invite modal | [ ] | |
| 3.5.3 | Send invite | Enter email, send | Invite email sent | [ ] | |
| 3.5.4 | Remove member | Remove team member | Member removed | [ ] | |

### 3.6 Partner Analytics

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.6.1 | Analytics page | Click "Analytics" | Charts and metrics | [ ] | |
| 3.6.2 | Time filter | Change time period | Data updates | [ ] | |
| 3.6.3 | Chart display | View Chart.js chart | Chart renders | [ ] | |

### 3.7 Partner Settings

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 3.7.1 | Settings page | Click "Settings" | Settings form | [ ] | |
| 3.7.2 | Change password | Update password | Password changed | [ ] | |
| 3.7.3 | API key | View API key | Key displayed | [ ] | |
| 3.7.4 | Regenerate key | Click regenerate | New key generated | [ ] | |

---

## PART 4: Cross-Functional Testing

### 4.1 Email Notifications

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 4.1.1 | Welcome email | New client signup | Email sent | [ ] | |
| 4.1.2 | Password reset | Request password reset | Email sent | [ ] | |
| 4.1.3 | Booking confirmation | Book a call | Email sent | [ ] | |
| 4.1.4 | Document reminder | Trigger reminder | Email sent | [ ] | |

### 4.2 Theme Consistency

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 4.2.1 | Client portal light | View in light mode | Correct styling | [ ] | |
| 4.2.2 | Client portal dark | View in dark mode | Correct styling | [ ] | |
| 4.2.3 | Staff dashboard light | View in light mode | Correct styling | [ ] | |
| 4.2.4 | Staff dashboard dark | View in dark mode | Correct styling | [ ] | |
| 4.2.5 | Partner portal light | View in light mode | Correct styling | [ ] | |
| 4.2.6 | Partner portal dark | View in dark mode | Correct styling | [ ] | |

### 4.3 Responsive Design

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 4.3.1 | Desktop (1920px) | View on large screen | Full layout | [ ] | |
| 4.3.2 | Laptop (1280px) | View on laptop | Proper scaling | [ ] | |
| 4.3.3 | Tablet (768px) | View on tablet | Responsive layout | [ ] | |
| 4.3.4 | Mobile (375px) | View on mobile | Mobile navigation | [ ] | |
| 4.3.5 | Mobile navigation | Tap hamburger menu | Menu opens | [ ] | |

### 4.4 Security Testing

| # | Test Case | Steps | Expected Result | Pass/Fail | Notes |
|---|-----------|-------|-----------------|-----------|-------|
| 4.4.1 | Unauthenticated access | Visit protected page | Redirect to login | [ ] | |
| 4.4.2 | Role-based access | Client visits staff page | Access denied | [ ] | |
| 4.4.3 | Session timeout | Wait for timeout | Requires re-login | [ ] | |
| 4.4.4 | CSRF protection | Submit form | Token validated | [ ] | |
| 4.4.5 | XSS prevention | Enter script tags | Input sanitized | [ ] | |

---

## Test Summary

### Execution Log

| Date | Tester | Part | Tests Passed | Tests Failed | Notes |
|------|--------|------|--------------|--------------|-------|
| | | | | | |
| | | | | | |
| | | | | | |

### Defects Found

| # | Part | Test Case | Description | Severity | Status |
|---|------|-----------|-------------|----------|--------|
| | | | | | |
| | | | | | |
| | | | | | |

### Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | | | |
| Product Owner | | | |
| Developer | | | |

---

*Last Updated: 2026-01-09*
