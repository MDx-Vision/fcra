# Manual Action Items - Human Tasks Required

> This document lists all tasks that require human action to complete.
> Code implementation is done - these items are blocked on external dependencies.
>
> **Last Updated**: 2026-01-20

---

## Status Summary

| Category | Code Status | Human Action Required |
|----------|-------------|----------------------|
| Test Coverage | ✅ 100% (98 test files, 88 services) | None |
| Features (P1-P35) | ✅ 100% Complete | None |
| Credit Import | ✅ Code Complete | ⏳ Some accounts need password reset |
| Send Certified Mail | ✅ Code Complete | ⏳ SFTP Credentials |
| SMS (Twilio) | ✅ Code Complete | ⏳ A2P 10DLC Approval |
| WhatsApp | ✅ Code Complete | ⏳ Template Approval |

---

## Priority 0: Credit Monitoring Password Resets

**Status**: ⏳ User Action Required
**Blocking**: Credit report auto-import for specific clients

### Clients Requiring Password Reset

| Client | Service | Issue | Action Required |
|--------|---------|-------|-----------------|
| Sharif Profit (ID: 515) | MyFreeScoreNow.com | "Password Change Required" | Reset password on MyFreeScoreNow.com, then update in `/dashboard/credit-import` |

### How to Fix

1. Go to https://member.myfreescorenow.com/login
2. Log in with current credentials: `Gotprofit@gmail.com` / `$Mp104624`
3. Complete the password reset process
4. Update the new password in your system at `/dashboard/credit-import` → Edit credential
5. Try import again

### Successfully Imported (2026-01-20)

| Client | Service | Scores |
|--------|---------|--------|
| Jennifer Nieves (ID: 519) | MyFreeScoreNow.com | TU: 380, EX: 810, EQ: 535 |

---

---

## Priority 1: SendCertified SFTP Credentials

**Status**: ⏳ Awaiting Credentials
**Blocking**: Automated certified mail sending
**Detailed Guide**: See `SENDCERTIFIED_SETUP.md` for step-by-step instructions

### Current Progress

| Step | Status | Notes |
|------|--------|-------|
| IP Whitelisted | ✅ Done | Claudia confirmed |
| Mailing Profile Created | ⏳ **YOU** | Do in portal |
| Test Work Order Submitted | ⏳ **YOU** | Do in portal |
| SFTP Credentials Received | ⏳ Waiting | Claudia sends after test |
| SFTP Configured & Tested | ⏳ Waiting | Claude configures |

### What You Need To Do

1. **Log into SendCertified Portal**

2. **Create Mailing Profile** (Return Address)
   - Red Navigation Bar → Management → Mailing Profiles → Add New
   - Enter test client info and save
   - Note the ID number

3. **Submit Test Work Order**
   - Red Navigation Bar → Address Letters → Submit Custom Work Order
   - Select: "Test/Proof data only"
   - Select: "Full service print and mail"
   - Upload: `/static/test_files/sendcertified_address_list.csv`
   - Upload: `/static/test_files/sample_dispute_letter.pdf`
   - Submit

4. **Wait for Claudia Wood** (SendCertified Support)
   - She will review your test submission
   - She will send SFTP credentials

5. **Share Credentials with Claude**
   - Once you receive: host, username, password, port
   - Claude will add to `.env` and test connection

### Files Ready (No Code Changes Needed)
- `services/sendcertified_service.py` - Mail generation
- `services/sendcertified_sftp_service.py` - SFTP upload
- `app.py` - API endpoints at `/api/va/*`
- `templates/va_approval.html` - Dashboard UI

---

## Priority 2: Twilio A2P 10DLC Campaign Approval

**Status**: ⏳ Pending Carrier Approval
**Blocking**: SMS delivery to US numbers (currently may have reduced deliverability)

### What You Need To Do

1. **Log into Twilio Console**
   - Go to: https://console.twilio.com/
   - Navigate to: Messaging → Services → A2P 10DLC

2. **Check Campaign Status**
   - Look for your registered campaign
   - Status should change from "Pending" to "Approved"
   - Approval typically takes 1-7 business days

3. **If Not Registered Yet**
   - Register your brand first (company info)
   - Then register a campaign (use case: Notifications)
   - Provide sample messages when prompted

4. **After Approval**
   - No code changes needed
   - SMS will automatically use approved campaign
   - Deliverability will improve

### Environment Variables (Already Set)
```bash
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

---

## Priority 3: WhatsApp Template Approval

**Status**: ⏳ Templates Need Approval
**Blocking**: Proactive WhatsApp notifications (replies still work)

### What You Need To Do

1. **Log into Twilio Console**
   - Go to: https://console.twilio.com/
   - Navigate to: Messaging → Content Templates

2. **Create Templates** (if not done)
   - Create templates for each type:
     - `document_request` - Request documents from client
     - `status_update` - Case status updates
     - `letters_ready` - Letters ready notification
     - `document_received` - Document receipt confirmation
     - `verification_code` - 2FA codes
     - `welcome` - Welcome message

3. **Submit for Approval**
   - Each template goes through Meta/WhatsApp review
   - Approval takes 24-72 hours typically

4. **After Approval - Update Template SIDs**
   - Edit `services/whatsapp_automation.py`
   - Replace placeholder SIDs with approved ones:
   ```python
   WHATSAPP_TEMPLATES = {
       'document_request': 'HX...',  # Your approved SID
       'status_update': 'HX...',
       # ... etc
   }
   ```

### Current Placeholders (Line 27-34)
```python
# services/whatsapp_automation.py
WHATSAPP_TEMPLATES = {
    'document_request': 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # Replace
    'status_update': 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',     # Replace
    'letters_ready': 'HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',     # Replace
    # ...
}
```

---

## Optional Enhancements (Low Priority)

### Stripe Payment Hold Release
**Status**: Minor enhancement, not blocking
**Location**: `services/scheduled_jobs_service.py:161`

The code has a TODO for releasing Stripe payment holds. This is only needed if you use Stripe's payment holds feature. Current flow works without it.

---

## Verification Checklist

After completing the manual items, verify:

- [ ] **SFTP**: Test connection shows green in `/dashboard/va-approval`
- [ ] **SMS**: Send test SMS, check Twilio logs for delivery
- [ ] **WhatsApp**: Send test template message, verify delivery

---

## Need Help?

| Service | Support Link |
|---------|-------------|
| SendCertifiedMail | https://www.sendcertifiedmail.com/support |
| Twilio | https://support.twilio.com/ |
| WhatsApp Business | https://business.whatsapp.com/support |

---

## Once Complete

After all items are done:

1. Update this file - mark items as ✅ Complete
2. Update `CLAUDE.md` - Change Phase 4 status
3. Update `FEATURE_BACKLOG.md` - Mark infrastructure items complete

---

*All code is implemented and tested. Only external credentials/approvals needed.*
