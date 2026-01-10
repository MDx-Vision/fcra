# ✅ Client Signup Workflow - Testing Checklist

**Date Started:** ___________  
**Tester Name:** ___________  
**Test Email:** ___________  

---

## 🎯 STAGE 1: FORM DATA COLLECTION
**What to test:** Can client fill out 4-step form and all data is captured?

### Step 1: Personal Information
```
☐ Fill First Name: "John"
☐ Fill Last Name: "Doe"
☐ Fill Email: [use a real test email]
☐ Fill Phone: "(555) 123-4567"
☐ Fill Street Address: "123 Main St"
☐ Fill City: "New York"
☐ Select State: "NY"
☐ Fill ZIP Code: "10001"
☐ Fill Date of Birth: "06/15/1985"
☐ Fill Last 4 SSN: "1234"
☐ Leave Referral Code blank (optional)
☐ Click "Continue to Credit Access" button
☐ Progress indicator updates to Step 2
```
**Issues Found:**  
_________________________________

---

### Step 2: Credit Access
```
☐ Page displays with credit service options
☐ Select Credit Service: "MyScoreIQ.com"
☐ Fill Username: [test MyScoreIQ account username]
☐ Fill Password: [test MyScoreIQ account password]
☐ Click "Continue to Plan & Payment"
☐ Progress indicator updates to Step 3
```
**Notes:** (Is MyScoreIQ login working? Any other services to test?)  
_________________________________

---

### Step 3: Plan & Payment
```
☐ Plan selection displayed (Free, Tier 1, Tier 2, Tier 3)
☐ Select Payment: "Tier 1" + "Free" option
☐ Or try: Stripe payment method
☐ Click "Continue to Agreement"
☐ Progress indicator updates to Step 4
```
**Notes:**  
_________________________________

---

### Step 4: Agreement
```
☐ Agreement text displayed
☐ Checkbox visible: "I agree to terms"
☐ Check the agreement checkbox
☐ "Complete Signup" button becomes clickable
☐ Click "Complete Signup"
```
**Issues Found:**  
_________________________________

---

## 🔄 STAGE 2: BACKEND PROCESSING
**What to test:** API receives data and creates database records

### API Response Check
```
☐ Wait 2-3 seconds for API response
☐ Success message appears: "Registration complete!"
☐ See "Client ID" displayed (e.g., "ID: 42")
☐ See "Referral Code" displayed (e.g., "BP3F8A7E")
☐ See "Case Number" displayed (e.g., "BP-2025-0342")
☐ Portal token shown or stored (check browser console)
```

**Expected Response:**
```json
{
  "success": true,
  "clientId": [number],
  "caseNumber": "[BP-YYYY-XXXX]",
  "referralCode": "[BP-xxxxxxxx]",
  "portalToken": "[long token]",
  "message": "Registration complete! We will pull your credit report..."
}
```

**Actual Response:**  
```
_________________________________
_________________________________
```

---

## 💾 STAGE 3: DATABASE VERIFICATION
**What to test:** Records created correctly in database

### Check clients Table
```
Run in database:
SELECT id, name, first_name, last_name, email, phone, 
       credit_monitoring_service, status, agreement_signed 
FROM clients 
WHERE email = '[test email]' 
ORDER BY id DESC LIMIT 1;
```

**Expected Results:**
```
☐ Record exists
☐ id: [number from API]
☐ name: "John Doe"
☐ first_name: "John"
☐ last_name: "Doe"
☐ email: [correct]
☐ phone: "(555) 123-4567"
☐ credit_monitoring_service: "MyScoreIQ.com"
☐ status: "signup"
☐ agreement_signed: true
```

**Actual Query Result:**  
```
_________________________________
```

---

### Check Encrypted Fields
```
Run in database:
SELECT id, credit_monitoring_username, 
       credit_monitoring_password_encrypted, 
       ssn_last_four
FROM clients 
WHERE email = '[test email]' 
ORDER BY id DESC LIMIT 1;
```

**Expected Results:**
```
☐ credit_monitoring_username: "[encrypted or visible]"
☐ credit_monitoring_password_encrypted: "[visible in DB but encrypted - should NOT be plaintext]"
☐ ssn_last_four: "1234"
```

**Actual Query Result:**  
```
_________________________________
```

---

### Check cases Table
```
Run in database:
SELECT id, client_id, case_number, status, pricing_tier, intake_at
FROM cases 
WHERE client_id = [id from clients table] 
LIMIT 1;
```

**Expected Results:**
```
☐ Record exists
☐ client_id: [matches client ID]
☐ case_number: "[BP-YYYY-XXXX]" format
☐ status: "intake"
☐ pricing_tier: "tier1"
☐ intake_at: [recent timestamp]
```

**Actual Query Result:**  
```
_________________________________
```

---

### Check case_events Table
```
Run in database:
SELECT id, case_id, event_type, description, created_at
FROM case_events 
WHERE case_id = [id from cases table]
ORDER BY created_at DESC LIMIT 1;
```

**Expected Results:**
```
☐ Record exists
☐ event_type: "signup"
☐ description: contains "signed up"
☐ created_at: [recent timestamp]
```

**Actual Query Result:**  
```
_________________________________
```

---

### Check credit_monitoring_credentials Table
```
Run in database:
SELECT id, client_id, service_name, username, 
       last_import_status, last_import_at, last_report_path
FROM credit_monitoring_credentials 
WHERE client_id = [id from clients table]
LIMIT 1;
```

**Expected Results:**
```
☐ Record exists (NEW!)
☐ service_name: "MyScoreIQ.com"
☐ username: "[test username]"
☐ last_import_status: "success" or "pending" or "failed"
☐ last_import_at: [if successful, recent timestamp]
☐ last_report_path: "/uploads/credit_reports/..." (if successful)
```

**Actual Query Result:**  
```
_________________________________
```

---

## ⚡ STAGE 4: AUTO-IMPORT TRIGGER
**What to test:** Credit report automatically imported

### Check Server Logs
```
Open Flask Server logs and look for:

☐ "🚀 Auto-importing credit report for John Doe..."
☐ "📥 Starting credit import..."
☐ "✅ Auto-import successful for John Doe"

OR

☐ "❌ Import failed..." (check error message)
☐ "⚠️  Auto-import error (non-fatal): [error details]"
```

**Actual Log Output:**  
```
_________________________________
_________________________________
```

---

### Check Uploaded Report File
```
Check if file exists:
ls -lah uploads/credit_reports/ | grep [client_id]
```

**Expected Results:**
```
☐ File exists: uploads/credit_reports/[client_id]_[timestamp].html
☐ File size > 10KB (should contain credit report HTML)
```

**Actual Files:**  
```
_________________________________
```

---

### View Report in Browser
```
Go to URL: /api/credit-import/report/[credential_id]
(Get credential_id from credit_monitoring_credentials query above)
```

**Expected to see:**
```
☐ Credit Scores displayed (TransUnion, Equifax, Experian)
☐ Accounts/Tradelines listed
☐ Payment history visible
☐ Inquiries shown
☐ Creditor contacts if available
```

**Screenshots/Notes:**  
```
_________________________________
_________________________________
```

---

## 📧 STAGE 5: EMAIL NOTIFICATION
**What to test:** Welcome email sent to client

### Check Email
```
Go to test email inbox and look for:

☐ Email from: noreply@brightpathascend.com (or configured sender)
☐ Subject: contains "Welcome"
☐ Recipient: [test email address]
☐ Email received within 5 minutes of signup
```

**Email Content Should Include:**
```
☐ Client name: "John Doe"
☐ Portal login link with token
☐ Referral code: [BP-xxxxxxxx]
☐ Next steps
☐ Contact information
```

**Email Status:**
- ☐ Received
- ☐ Not received (check server logs for SendGrid errors)
- ☐ Received but incomplete

**Issues:**  
```
_________________________________
```

---

## 📱 STAGE 6: SMS NOTIFICATION
**What to test:** Welcome SMS sent to client phone

### Check SMS
```
Check test phone number for text message:

☐ SMS received from: Brightpath Ascend (or configured sender)
☐ Within 5 minutes of signup
☐ Contains: "Welcome to Brightpath Ascend"
☐ Contains: Portal login link or instructions
```

**SMS Content:**
```
_________________________________
_________________________________
```

**SMS Status:**
- ☐ Received
- ☐ Not received (check server logs for Twilio errors)

**Issues:**  
```
_________________________________
```

---

## 🎯 STAGE 7: CLIENT PORTAL ACCESS
**What to test:** Can client log into portal with token?

### Test Portal Login
```
Go to: /portal/login
Enter email: [test email]
Click "Send Login Link"
```

**Expected:**
```
☐ Login page loads
☐ "Check your email for login link" message appears
☐ Email received with portal login link
☐ Click link in email
☐ Redirected to portal
☐ Can see client dashboard
```

**Issues:**  
```
_________________________________
```

---

### Test Portal Token Method
```
Go to: /portal/[token from API response]
(Use exact token from signup response)
```

**Expected:**
```
☐ Portal loads without login required
☐ Displays client dashboard
☐ Shows client name: "John Doe"
☐ Shows case information
☐ Shows credit report summary (if auto-import succeeded)
```

**Issues:**  
```
_________________________________
```

---

## 💳 STAGE 8: PAYMENT PROCESSING (Optional)
**What to test:** Payment methods work correctly

### Free Tier Test
```
☐ Selected free tier before completing signup
☐ No payment form shown
☐ Signed up completed successfully
☐ Marked as "free" in case record
```

**Status:** ☐ Working ☐ Issue Found

**Issues:**  
```
_________________________________
```

---

### Stripe Payment Test
```
If you want to test Stripe:
☐ Selected paid tier
☐ Clicked checkout button
☐ Redirected to Stripe checkout page
☐ See amount and product details
☐ Can enter test card: 4242 4242 4242 4242
```

**Status:** ☐ Working ☐ Issue Found

**Issues:**  
```
_________________________________
```

---

### Manual Payment Test
```
If you selected CashApp/Venmo/Zelle:
☐ See payment instructions
☐ Shows payment method (e.g., $@brightpath_ascend)
☐ Message: "We'll confirm payment and start your analysis"
```

**Status:** ☐ Working ☐ Issue Found

**Issues:**  
```
_________________________________
```

---

## 🔗 STAGE 9: REFERRAL TRACKING (Optional)
**What to test:** Referral code system works

### Generate Referral First
```
Complete a signup, get referral code: [e.g., BP3F8A7E]
```

### Use Referral Code
```
Go to /signup
Fill form normally
In Step 1, fill "Referral Code": [referral code from above]
Complete signup
```

**Expected in Database:**
```
Run query:
SELECT referring_client_id, referred_name, referred_email, status
FROM client_referrals
WHERE referred_email = '[second signup email]'
LIMIT 1;

☐ Record exists
☐ referring_client_id: [first signup client ID]
☐ referred_name: "John Doe" (or whatever name entered)
☐ status: "signed_up"
```

**Status:** ☐ Working ☐ Issue Found

**Issues:**  
```
_________________________________
```

---

## 📊 STAGE 10: WORKFLOW AUTOMATION (Optional)
**What to test:** Automated workflows triggered

### Check Server Logs
```
Look for lines like:
"WorkflowTriggersService.evaluate_triggers('case_created'...)"
"Welcome sequence triggered"
"Auto-generated emails queued"
```

**Expected:**
```
☐ Workflow logged in server output
☐ Tasks created for staff (check dashboard)
☐ Auto-generated letters created (check case files)
```

**Status:** ☐ Working ☐ Issue Found

**Issues:**  
```
_________________________________
```

---

## ✨ FINAL VERIFICATION CHECKLIST

### Required to Pass
```
☐ Client record created in database
☐ Case record created with case number
☐ Credentials stored (encrypted password)
☐ Success response returned to client
☐ Form validation working (no errors on submit)
```

### Auto-Import Features
```
☐ Credit report file downloaded and saved
☐ Report path stored in credentials table
☐ Server logs show successful import
☐ Report viewable via /api/credit-import/report/[id]
```

### Notifications
```
☐ Welcome email sent
☐ SMS notification sent (if enabled)
☐ Links in emails/SMS working
```

### Portal Access
```
☐ Client can access portal with token
☐ Client can access portal with email login
☐ Dashboard shows correct client info
```

---

## 🐛 ISSUES FOUND

### Issue #1
**Description:**  
```
_________________________________
_________________________________
```
**Expected vs Actual:**  
```
_________________________________
```
**Severity:** ☐ Critical ☐ Major ☐ Minor  
**Fixed:** ☐ Yes ☐ No  
**Solution:**  
```
_________________________________
```

---

### Issue #2
**Description:**  
```
_________________________________
_________________________________
```
**Expected vs Actual:**  
```
_________________________________
```
**Severity:** ☐ Critical ☐ Major ☐ Minor  
**Fixed:** ☐ Yes ☐ No  
**Solution:**  
```
_________________________________
```

---

### Issue #3
**Description:**  
```
_________________________________
_________________________________
```
**Expected vs Actual:**  
```
_________________________________
```
**Severity:** ☐ Critical ☐ Major ☐ Minor  
**Fixed:** ☐ Yes ☐ No  
**Solution:**  
```
_________________________________
```

---

## 📝 NOTES & OBSERVATIONS

```
_________________________________
_________________________________
_________________________________
_________________________________
```

---

## ✅ TEST COMPLETION SUMMARY

**Total Stages Tested:** _____ / 10  
**Issues Found:** _____  
**Issues Fixed:** _____  
**Issues Remaining:** _____  

**Overall Status:**
- ☐ All Systems Go ✅
- ☐ Minor Issues (Non-blocking)
- ☐ Major Issues (Needs Fixes)
- ☐ Critical Issues (Blocked)

**Next Steps:**
```
_________________________________
_________________________________
```

---

**Test Date Completed:** ___________  
**Next Test Date:** ___________
