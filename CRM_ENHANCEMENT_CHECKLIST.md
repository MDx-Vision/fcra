# CRM Enhancement Checklist

> Master tracking document for CRM enhancements inspired by TNG CRM analysis
>
> Created: 2026-01-19
> Reference: `CRM_COMPARISON_FCRA_VS_TNG.md`

---

## Failproof Implementation Plan

### Pre-Build Safety Checks

Before starting ANY feature:

- [ ] Run full test suite: `python3 -m pytest --tb=short -q` (must be 5,725+ passing)
- [ ] Run Cypress E2E: `CI=true npx cypress run` (must be 88/88 passing)
- [ ] Create git branch: `git checkout -b feature/crm-[feature-name]`
- [ ] Document current state in this file

### During Build Safety

- [ ] Write tests FIRST (TDD approach)
- [ ] Add new database migrations (never modify existing)
- [ ] Use feature flags where possible
- [ ] Keep changes isolated to new files when possible
- [ ] Run tests after each significant change

### Post-Build Validation

- [ ] All existing tests still pass
- [ ] New feature has unit tests (90%+ coverage)
- [ ] New feature has Cypress E2E tests
- [ ] Manual smoke test of related features
- [ ] Update CLAUDE.md with changes
- [ ] Update FEATURE_BACKLOG.md
- [ ] Merge to main only after all checks pass

### Rollback Strategy

If something breaks:
1. `git stash` current changes
2. `git checkout main`
3. Restart Flask server
4. Verify tests pass
5. Investigate issue in isolated branch

---

## Priority 29: Unified Inbox

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Medium (2-3 weeks)
**Value**: HIGH - Single view for all client communications

### Description
Single view combining emails, SMS, portal messages, and call logs per client.

### Implementation Checklist

#### Phase 1: Database & Service
- [ ] Create `UnifiedMessage` view/model (virtual, combines existing tables)
- [ ] Create `UnifiedInboxService` (~500 lines)
  - [ ] `get_client_inbox(client_id)` - All messages for client
  - [ ] `get_staff_inbox(staff_id)` - Messages for assigned clients
  - [ ] `search_messages(query)` - Full-text search
  - [ ] `filter_by_channel(channel)` - Email/SMS/Portal/Call
  - [ ] `get_unread_counts()` - Per-channel counts
  - [ ] `mark_read(message_id)` - Mark as read
  - [ ] `get_conversation_thread(client_id)` - Threaded view

#### Phase 2: API Endpoints
- [ ] `GET /api/inbox` - Staff inbox with filters
- [ ] `GET /api/inbox/client/<id>` - Client's messages
- [ ] `GET /api/inbox/search` - Search messages
- [ ] `GET /api/inbox/unread` - Unread counts
- [ ] `PUT /api/inbox/<id>/read` - Mark read
- [ ] `POST /api/inbox/reply` - Reply to any channel

#### Phase 3: Dashboard UI
- [ ] Create `templates/unified_inbox.html`
  - [ ] Channel filter tabs (All, Email, SMS, Portal, Calls)
  - [ ] Client filter dropdown
  - [ ] Search bar
  - [ ] Message list with previews
  - [ ] Conversation thread view
  - [ ] Quick reply composer (auto-detects channel)
  - [ ] Unread badges
- [ ] Add sidebar link in Communication section

#### Phase 4: Testing
- [ ] Unit tests for UnifiedInboxService (40+ tests)
- [ ] Cypress E2E tests (20+ tests)
- [ ] Integration test with existing message systems

### Files to Create/Modify
- `services/unified_inbox_service.py` - NEW
- `templates/unified_inbox.html` - NEW
- `app.py` - Add endpoints
- `templates/includes/dashboard_sidebar.html` - Add link
- `tests/test_unified_inbox_service.py` - NEW

### Safety Notes
- Read-only from existing tables (ClientMessage, email logs, SMS logs)
- No modifications to existing message systems
- Additive only - doesn't replace existing pages

---

## Priority 30: Activity Timeline per Client

**Status**: [x] Complete (P30 was AI Chat Support)
**Note**: Renamed - Original P30 was AI Chat Support which is complete

---

## Priority 31: Credit Score Simulator

**Status**: [x] Complete
**Completed**: 2026-01-19

---

## Priority 32: Calendar Sync (Google/Outlook)

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Medium (2 weeks)
**Value**: MEDIUM - External calendar integration

### Description
Sync booking slots with Google Calendar and Outlook Calendar.

### Implementation Checklist

#### Phase 1: OAuth Setup
- [ ] Google Calendar API credentials
- [ ] Microsoft Graph API credentials
- [ ] Create `CalendarIntegration` model (stores OAuth tokens)
- [ ] Token refresh mechanism

#### Phase 2: Service Layer
- [ ] Create `CalendarSyncService` (~600 lines)
  - [ ] `connect_google(staff_id, auth_code)` - OAuth flow
  - [ ] `connect_outlook(staff_id, auth_code)` - OAuth flow
  - [ ] `disconnect(staff_id, provider)` - Remove integration
  - [ ] `sync_slots_to_calendar(staff_id)` - Push slots to external
  - [ ] `sync_calendar_to_slots(staff_id)` - Pull availability
  - [ ] `create_calendar_event(booking)` - Add booking as event
  - [ ] `delete_calendar_event(booking)` - Remove cancelled
  - [ ] `get_free_busy(staff_id, date_range)` - Check availability

#### Phase 3: API Endpoints
- [ ] `GET /api/calendar/status` - Connection status
- [ ] `POST /api/calendar/connect/google` - Start Google OAuth
- [ ] `POST /api/calendar/connect/outlook` - Start Outlook OAuth
- [ ] `GET /api/calendar/callback/google` - OAuth callback
- [ ] `GET /api/calendar/callback/outlook` - OAuth callback
- [ ] `POST /api/calendar/disconnect` - Disconnect
- [ ] `POST /api/calendar/sync` - Manual sync trigger

#### Phase 4: UI Integration
- [ ] Add calendar connection in Settings page
- [ ] Show sync status on Booking Management
- [ ] Auto-sync on booking creation/cancellation

#### Phase 5: Testing
- [ ] Unit tests with mocked OAuth (30+ tests)
- [ ] Manual OAuth flow testing

### Files to Create/Modify
- `database.py` - Add CalendarIntegration model
- `services/calendar_sync_service.py` - NEW
- `templates/settings.html` - Add calendar connection UI
- `templates/booking_management.html` - Show sync status
- `app.py` - Add endpoints
- `tests/test_calendar_sync_service.py` - NEW

### Environment Variables Required
```
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_REDIRECT_URI=
```

### Safety Notes
- OAuth tokens encrypted at rest
- Separate integration per staff member
- Graceful degradation if external API fails

---

## Priority 33: Call Logging

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Low (1 week)
**Value**: MEDIUM - Manual call tracking

### Description
Log calls manually with notes, duration, and outcome tracking.

### Implementation Checklist

#### Phase 1: Database
- [ ] Create `CallLog` model
  - Fields: client_id, staff_id, direction (inbound/outbound), duration_minutes, outcome, notes, call_type, scheduled_at, started_at, ended_at

#### Phase 2: Service
- [ ] Create `CallLogService` (~300 lines)
  - [ ] `log_call()` - Create call record
  - [ ] `get_client_calls(client_id)` - Call history
  - [ ] `get_staff_calls(staff_id)` - Staff's calls
  - [ ] `get_call_stats()` - Dashboard stats
  - [ ] `schedule_call()` - Schedule future call
  - [ ] `get_scheduled_calls()` - Upcoming calls

#### Phase 3: API & UI
- [ ] CRUD endpoints for call logs
- [ ] Add "Log Call" button on client detail page
- [ ] Call history tab on client page
- [ ] Scheduled calls sidebar

#### Phase 4: Testing
- [ ] Unit tests (20+ tests)
- [ ] Cypress tests (10+ tests)

### Files to Create/Modify
- `database.py` - Add CallLog model
- `services/call_log_service.py` - NEW
- `templates/clients.html` - Add Log Call button
- `app.py` - Add endpoints
- `tests/test_call_log_service.py` - NEW

### Safety Notes
- Simple CRUD, low risk
- No external integrations
- Additive feature

---

## Priority 34: Quick Notes

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Low (3 days)
**Value**: LOW - Convenience feature

### Description
One-click note adding on client records without navigating away.

### Implementation Checklist

- [ ] Add inline note form to client detail page
- [ ] Add note modal accessible from client list
- [ ] Keyboard shortcut (Ctrl+N) for quick note
- [ ] Recent notes sidebar widget
- [ ] Note templates for common entries

### Files to Modify
- `templates/clients.html` - Add quick note UI
- `app.py` - May need new endpoint or use existing

### Safety Notes
- Uses existing CaseNote model
- UI-only changes, minimal risk

---

## Priority 35: Task Assignment

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Medium (1-2 weeks)
**Value**: MEDIUM - Staff workflow improvement

### Description
Assign tasks to specific staff members with due dates and notifications.

### Implementation Checklist

#### Phase 1: Database Enhancement
- [ ] Enhance existing task queue or create `StaffTask` model
  - Fields: title, description, assigned_to, assigned_by, client_id, due_date, priority, status, completed_at, reminder_sent

#### Phase 2: Service
- [ ] Create `TaskAssignmentService` (~400 lines)
  - [ ] `create_task()` - Create and assign
  - [ ] `get_my_tasks(staff_id)` - Tasks for staff
  - [ ] `get_team_tasks()` - All team tasks
  - [ ] `complete_task()` - Mark complete
  - [ ] `reassign_task()` - Change assignee
  - [ ] `send_reminders()` - Due date reminders

#### Phase 3: UI
- [ ] My Tasks dashboard widget
- [ ] Task assignment modal
- [ ] Task list page with filters
- [ ] Due date notifications

#### Phase 4: Testing
- [ ] Unit tests (25+ tests)
- [ ] Cypress tests (15+ tests)

### Safety Notes
- Extends existing task system
- Non-breaking changes

---

## Priority 36: Scheduled Reports

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Low (1 week)
**Value**: LOW - Automation convenience

### Description
Auto-email weekly/monthly reports to owners and managers.

### Implementation Checklist

- [ ] Create `ScheduledReport` model (report_type, frequency, recipients, last_sent)
- [ ] Create `ReportSchedulerService`
- [ ] Add scheduled job to send reports
- [ ] Report types: Revenue, Client Success, Staff Performance, Pipeline
- [ ] Settings page to configure schedules

### Safety Notes
- Uses existing report generation
- Scheduled job pattern already established

---

## Priority 37: SMS Templates Library

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Low (3 days)
**Value**: LOW - Consistency improvement

### Description
Pre-built SMS templates similar to email templates.

### Implementation Checklist

- [ ] Create `SMSTemplate` model (mirrors EmailTemplate structure)
- [ ] Create `SMSTemplateService`
- [ ] SMS template management UI
- [ ] Variable substitution ({client_name}, etc.)
- [ ] Integration with existing SMS sending

### Safety Notes
- Mirrors existing email template pattern
- Low risk

---

## Priority 38: Client Tags

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Low (1 week)
**Value**: MEDIUM - Better segmentation

### Description
Flexible tagging system beyond client_type for segmentation.

### Implementation Checklist

- [ ] Create `ClientTag` model (name, color, description)
- [ ] Create `ClientTagAssignment` model (client_id, tag_id)
- [ ] Tag management UI
- [ ] Filter clients by tags
- [ ] Bulk tag assignment
- [ ] Use tags in workflow triggers

### Safety Notes
- Additive feature
- No changes to existing client_type

---

## Priority 39: Email Open/Click Tracking

**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete
**Effort**: Medium (1-2 weeks)
**Value**: LOW - Nice to have analytics

### Description
Track if clients opened emails and clicked links.

### Implementation Checklist

- [ ] Add tracking pixel to emails
- [ ] Add click tracking wrapper for links
- [ ] Create `EmailTrackingEvent` model
- [ ] Display open/click stats on email history
- [ ] Aggregate stats in email dashboard

### Safety Notes
- Modifies email sending
- Privacy considerations (may need opt-out)

---

## Implementation Order

### Phase 1 (Weeks 1-3): High Value
1. **P29: Unified Inbox** - Biggest UX improvement

### Phase 2 (Weeks 4-5): Medium Value
2. **P32: Calendar Sync** - External integration
3. **P33: Call Logging** - Quick win

### Phase 3 (Weeks 6-7): Quick Wins
4. **P34: Quick Notes** - Easy
5. **P35: Task Assignment** - Workflow improvement
6. **P36: Scheduled Reports** - Automation

### Phase 4 (Weeks 8+): Nice to Have
7. **P37: SMS Templates** - Consistency
8. **P38: Client Tags** - Segmentation
9. **P39: Email Tracking** - Analytics

---

## Current Test Baseline

**Before starting any feature, verify:**

```bash
# Unit tests
python3 -m pytest --tb=short -q
# Expected: 5,725+ tests passing

# Cypress E2E
CI=true npx cypress run
# Expected: 88/88 tests passing
```

**Document baseline here before each feature:**

| Feature | Date Started | Unit Tests Before | Cypress Before | Status |
|---------|--------------|-------------------|----------------|--------|
| P29 Unified Inbox | - | - | - | Not Started |
| P32 Calendar Sync | - | - | - | Not Started |
| P33 Call Logging | - | - | - | Not Started |

---

## Related Documentation

- `CRM_COMPARISON_FCRA_VS_TNG.md` - Full comparison analysis
- `FEATURE_BACKLOG.md` - Complete feature history
- `CLAUDE.md` - Session tracking
- `ARCHITECTURE.md` - Technical architecture

---

*Last updated: 2026-01-19*
