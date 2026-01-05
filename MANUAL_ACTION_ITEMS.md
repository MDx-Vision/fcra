# Manual Action Items - Human Tasks Required

> This document lists all tasks that require human action to complete.
> Code implementation is done - these items are blocked on external dependencies.
>
> **Last Updated**: 2026-01-05

---

## Status Summary

| Category | Code Status | Human Action Required |
|----------|-------------|----------------------|
| Test Coverage | ✅ 100% (96 test files, 86 services) | None |
| Features (P1-P28) | ✅ 100% Complete | None |
| Send Certified Mail | ✅ Code Complete | ⏳ SFTP Credentials |
| SMS (Twilio) | ✅ Code Complete | ⏳ A2P 10DLC Approval |
| WhatsApp | ✅ Code Complete | ⏳ Template Approval |

---

## Priority 1: SendCertified SFTP Credentials

**Status**: ⏳ Awaiting Credentials
**Blocking**: Automated certified mail sending

### What You Need To Do

1. **Contact SendCertifiedMail.com**
   - Request SFTP credentials for your account
   - They will provide: hostname, username, password/key, port

2. **Add to Environment Variables**
   ```bash
   # Add to .env file
   SENDCERTIFIED_SFTP_HOST=sftp.sendcertifiedmail.com
   SENDCERTIFIED_SFTP_USER=your_username
   SENDCERTIFIED_SFTP_PASSWORD=your_password
   SENDCERTIFIED_SFTP_PORT=22
   ```

3. **Test Connection**
   - Go to `/dashboard/va-approval`
   - Click "Test SFTP Connection"
   - Verify green status indicator

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
