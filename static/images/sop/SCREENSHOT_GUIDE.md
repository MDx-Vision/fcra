# Screenshot Capture Guide

Capture these 20 screenshots to complete the Client Portal SOP.

---

## Automatic Capture (Recommended)

Run this on your local machine:

```bash
# 1. Start the Flask server
CI=true python app.py &

# 2. Wait for server to start
sleep 10

# 3. Run the screenshot capture script
npx cypress run --spec "cypress/e2e/capture_sop_screenshots.cy.js"

# 4. Copy screenshots to the correct folder
cp cypress/screenshots/capture_sop_screenshots.cy.js/*.png static/images/sop/
```

Screenshots will be saved to `static/images/sop/`

---

## Manual Capture

**On Mac**: `Cmd + Shift + 4` then select area
**On Windows**: `Win + Shift + S` then select area
**On Chrome**: `F12` → `Cmd/Ctrl + Shift + P` → type "screenshot" → "Capture full size screenshot"

---

## Screenshots to Capture

### Stage 1: Getting Started

| # | Filename | URL | What to Capture |
|---|----------|-----|-----------------|
| 01 | `01-signup-form.png` | `/get-started` | The full signup form with all fields |
| 02 | `02-login-page.png` | `/portal/login` | Login page with email/password fields |

### Stage 2: Onboarding

| # | Filename | URL | What to Capture |
|---|----------|-----|-----------------|
| 03 | `03-onboarding-nav.png` | `/portal/onboarding` | Top navigation showing Setup, Agreements, Profile tabs |
| 04 | `04-personal-info.png` | `/portal/onboarding` | Personal information form section |
| 05 | `05-id-upload.png` | `/portal/onboarding` | ID document upload boxes (DL, SSN, Proof of Address) |
| 06 | `06-credit-monitoring.png` | `/portal/onboarding` | Credit monitoring credentials section |
| 07 | `07-agreements.png` | `/portal/agreements` | Agreement document with signature canvas |
| 08 | `08-cancellation.png` | `/portal/agreements` | 3-day cancellation countdown notice |
| 09 | `09-payment.png` | `/portal/onboarding` | Payment form section |

### Stage 3: Active Client Portal

| # | Filename | URL | What to Capture |
|---|----------|-----|-----------------|
| 10 | `10-active-nav.png` | `/portal/dashboard` | Navigation bar with all 5 tabs (Case, Documents, Contact, Journey, Profile) |
| 11 | `11-case-dashboard.png` | `/portal/dashboard` | Full dashboard with round status and stats |
| 12 | `12-bureau-status.png` | `/portal/status` | Bureau breakdown showing Equifax, Experian, TransUnion sections |

### Stage 4: Ongoing Tasks

| # | Filename | URL | What to Capture |
|---|----------|-----|-----------------|
| 13 | `13-cra-upload.png` | `/portal/documents` | CRA Response upload section with bureau dropdown |
| 14 | `14-documents-list.png` | `/portal/documents` | Document list with Preview/Download buttons |
| 15 | `15-messages.png` | `/portal/messages` | Messaging interface with chat history |
| 16 | `16-booking.png` | `/portal/booking` | Call booking calendar |
| 17 | `17-timeline.png` | `/portal/timeline` | Journey timeline with events |

### Stage 5: Profile & Settings

| # | Filename | URL | What to Capture |
|---|----------|-----|-----------------|
| 18 | `18-profile.png` | `/portal/profile` | Profile settings form |
| 19 | `19-freeze-status.png` | `/portal/status` | Secondary bureau freeze section (scroll down on status page) |
| 20 | `20-billing.png` | `/portal/invoices` | Invoice list |

---

## Tips for Best Screenshots

1. **Use an incognito/private window** - Cleaner look, no extensions
2. **Set browser width to 1280px** - Consistent sizing
3. **Hide bookmarks bar** - Cleaner appearance
4. **Use light mode** - Better for printed docs
5. **Crop to just the relevant area** - Remove browser chrome if possible
6. **Save as PNG** - Best quality for text

---

## Test Client Login

Use these credentials to access the portal:

- **URL**: `http://localhost:5000/portal/login` (dev) or your production URL
- **Email**: `testclient@example.com`
- **Password**: `test123`

---

## Quick Capture Checklist

- [ ] 01-signup-form.png
- [ ] 02-login-page.png
- [ ] 03-onboarding-nav.png
- [ ] 04-personal-info.png
- [ ] 05-id-upload.png
- [ ] 06-credit-monitoring.png
- [ ] 07-agreements.png
- [ ] 08-cancellation.png
- [ ] 09-payment.png
- [ ] 10-active-nav.png
- [ ] 11-case-dashboard.png
- [ ] 12-bureau-status.png
- [ ] 13-cra-upload.png
- [ ] 14-documents-list.png
- [ ] 15-messages.png
- [ ] 16-booking.png
- [ ] 17-timeline.png
- [ ] 18-profile.png
- [ ] 19-freeze-status.png
- [ ] 20-billing.png
