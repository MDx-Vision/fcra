# FIX SOP - CAPTURE MISSING SCREENSHOTS

---

## WHAT'S MISSING

The Client_Signup_SOP_Complete.docx has blank pages for:
1. **Success message** - What client sees after clicking "Complete Signup"
2. **Portal Login page** - `/portal/login`
3. **Portal Dashboard** - What client sees after logging in

---

## YOUR TASK

1. Find test client credentials from the database
2. Capture the missing screenshots
3. Update the Word document with the new screenshots

---

## STEP 1: Find test client credentials

```python
# Find a test client with portal access
from database import SessionLocal, Client

session = SessionLocal()

# Find clients with email that looks like test account
clients = session.query(Client).filter(
    Client.email.isnot(None)
).order_by(Client.id.desc()).limit(10).all()

print("Available test clients:")
for c in clients:
    print(f"  ID: {c.id}, Name: {c.name}, Email: {c.email}")

# Get the most recent one
if clients:
    test_client = clients[0]
    print(f"\nUsing: {test_client.name} ({test_client.email})")

session.close()
```

---

## STEP 2: Capture the missing screenshots

```python
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_missing_screenshots():
    os.makedirs("sop_screenshots", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1200})

        # ========== SCREENSHOT 1: SUCCESS MESSAGE ==========
        # Go through signup flow to get success message
        await page.goto("http://localhost:5001/signup")
        await page.wait_for_timeout(1500)

        # Fill Step 1 - Personal Info
        await page.fill("#firstName", "Test")
        await page.fill("#lastName", "Client")

        # Generate unique email to avoid duplicate
        import time
        unique_email = f"test{int(time.time())}@example.com"
        await page.fill("#email", unique_email)
        await page.fill("#phone", "555-123-4567")
        await page.fill("#addressStreet", "123 Test Street")
        await page.fill("#addressCity", "Los Angeles")
        await page.fill("#addressZip", "90001")

        # Try to fill state
        state = await page.query_selector("#addressState, select[name='state']")
        if state:
            try:
                await state.select_option("CA")
            except:
                await state.fill("CA")

        # Click Next to Step 2
        next_btn = await page.query_selector("button:has-text('Next'), button:has-text('Continue')")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)

        # Step 2 - Credit Access (skip or fill minimally)
        next_btn = await page.query_selector("button:has-text('Next'):visible, button:has-text('Continue'):visible, button:has-text('Skip'):visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)

        # Step 3 - Select Free plan
        free_plan = await page.query_selector("[data-plan='free'], input[value='free'], .plan-card:has-text('Free'), .plan-card:has-text('FREE'), input[name='plan'][value='free']")
        if free_plan:
            await free_plan.click()
            await page.wait_for_timeout(500)

        next_btn = await page.query_selector("button:has-text('Continue'):visible, button:has-text('Next'):visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)

        # Step 4 - Agreement
        checkbox = await page.query_selector("input[type='checkbox']")
        if checkbox:
            await checkbox.click()
            await page.wait_for_timeout(300)

        # Click Complete Signup
        submit_btn = await page.query_selector("button:has-text('Complete'), button:has-text('Submit'), button[type='submit']")
        if submit_btn:
            await submit_btn.click()
            await page.wait_for_timeout(3000)  # Wait for API response

        # Screenshot: Success message
        await page.screenshot(path="sop_screenshots/12_success_message.png", full_page=True)
        print("✓ 12: Success message captured")

        # ========== SCREENSHOT 2: PORTAL LOGIN ==========
        await page.goto("http://localhost:5001/portal/login")
        await page.wait_for_timeout(1500)
        await page.screenshot(path="sop_screenshots/13_portal_login.png", full_page=True)
        print("✓ 13: Portal login page captured")

        # ========== SCREENSHOT 3: PORTAL DASHBOARD ==========
        # Try to log in with the test email we just created
        email_field = await page.query_selector("input[type='email'], input[name='email'], #email")
        if email_field:
            await email_field.fill(unique_email)

        # Look for login button or send link button
        login_btn = await page.query_selector("button:has-text('Login'), button:has-text('Send'), button[type='submit']")
        if login_btn:
            await login_btn.click()
            await page.wait_for_timeout(2000)

        # If portal uses token-based login, try direct access
        # First check if we're already on dashboard
        current_url = page.url
        if "dashboard" not in current_url:
            # Try direct portal access for most recent client
            await page.goto("http://localhost:5001/portal/dashboard")
            await page.wait_for_timeout(1500)

        await page.screenshot(path="sop_screenshots/14_portal_dashboard.png", full_page=True)
        print("✓ 14: Portal dashboard captured")

        await browser.close()
        print("\n✅ Missing screenshots captured")

asyncio.run(capture_missing_screenshots())
```

---

## STEP 3: Check what screenshots we have

```bash
ls -la sop_screenshots/
```

If screenshots 12, 13, 14 exist and have content, proceed to update the Word doc.

---

## STEP 4: Update the Word document

```python
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def update_sop_with_screenshots():
    # Open existing document
    doc = Document('Client_Signup_SOP_Complete.docx')

    # Find and update the sections with blank images
    # We need to locate the paragraphs and add images

    # For now, let's just verify the screenshots exist
    screenshots = [
        "sop_screenshots/12_success_message.png",
        "sop_screenshots/13_portal_login.png",
        "sop_screenshots/14_portal_dashboard.png"
    ]

    for ss in screenshots:
        if os.path.exists(ss):
            size = os.path.getsize(ss)
            print(f"✓ {ss} exists ({size} bytes)")
        else:
            print(f"✗ {ss} MISSING")

    # If all exist, we can rebuild the document or manually add images
    print("\nScreenshots ready. Document can be updated.")

update_sop_with_screenshots()
```

---

## STEP 5: Rebuild complete SOP with all screenshots

Since updating existing Word docs with images is complex, rebuild the full document:

```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def rebuild_complete_sop():
    doc = Document()

    # Set margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # Helper function to add image if exists
    def add_image(path, caption, width=5.5):
        if os.path.exists(path):
            doc.add_picture(path, width=Inches(width))
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].font.italic = True
            cap.runs[0].font.size = Pt(10)
            return True
        else:
            doc.add_paragraph(f"[Screenshot: {caption} - not captured]")
            return False

    # ============ COVER PAGE ============
    doc.add_paragraph()
    doc.add_paragraph()
    title = doc.add_heading('Client Signup Guide', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph('Complete Registration to Portal Access')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    doc.add_paragraph('Version 1.2 | December 2025')
    doc.add_page_break()

    # ============ TABLE OF CONTENTS ============
    doc.add_heading('Table of Contents', level=1)
    doc.add_paragraph()
    toc_items = [
        '1. Overview',
        '2. Step 1: Personal Information',
        '3. Step 2: Credit Monitoring Access',
        '4. Step 3: Choose Your Plan & Payment',
        '5. Step 4: Review & Agreement',
        '6. Registration Complete',
        '7. Client Portal Login',
        '8. Client Portal Dashboard',
        '9. Need Help?'
    ]
    for item in toc_items:
        doc.add_paragraph(item)
    doc.add_page_break()

    # ============ OVERVIEW ============
    doc.add_heading('Overview', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'Welcome! This guide walks you through the complete signup process, '
        'from registration to accessing your Client Portal.'
    )
    doc.add_paragraph()
    doc.add_paragraph('Before you begin, please have ready:')
    doc.add_paragraph('• Valid email address', style='List Bullet')
    doc.add_paragraph('• Phone number', style='List Bullet')
    doc.add_paragraph('• Current mailing address', style='List Bullet')
    doc.add_paragraph('• Credit monitoring service login (optional)', style='List Bullet')
    doc.add_paragraph('• Payment method (if selecting a paid plan)', style='List Bullet')
    doc.add_page_break()

    # ============ STEP 1 ============
    doc.add_heading('Step 1: Personal Information', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Enter your personal information. Fields marked with * are required.')
    doc.add_paragraph()
    add_image("sop_screenshots/02_step1_filled.png", "Figure 1: Personal Information Form")
    doc.add_paragraph()
    doc.add_paragraph('Click "Next" to continue.')
    doc.add_page_break()

    # ============ STEP 2 ============
    doc.add_heading('Step 2: Credit Monitoring Access', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Select your credit monitoring provider from the 10 supported services:')
    doc.add_paragraph()
    companies = [
        'IdentityIQ.com', 'MyScoreIQ.com', 'SmartCredit.com', 'MyFreeScoreNow.com',
        'HighScoreNow.com', 'IdentityClub.com', 'PrivacyGuard.com', 'IDClub.com',
        'MyThreeScores.com', 'MyScore750.com'
    ]
    for i, company in enumerate(companies, 1):
        doc.add_paragraph(f'{i}. {company}', style='List Number')
    doc.add_paragraph()
    add_image("sop_screenshots/04_step2_dropdown.png", "Figure 2: Credit Monitoring Selection")
    doc.add_paragraph()
    doc.add_paragraph('Enter your username and password, then click "Next".')
    doc.add_page_break()

    # ============ STEP 3 ============
    doc.add_heading('Step 3: Choose Your Plan & Payment', level=1)
    doc.add_paragraph()
    doc.add_heading('Available Plans:', level=2)
    plans = [
        ('Basic Analysis', 'FREE', 'Free credit analysis, identify problem areas'),
        ('Starter', '$300', 'Full FCRA analysis + Round 1 dispute letters'),
        ('Standard', '$600', 'Full analysis + Rounds 1-2 + documentation'),
        ('Premium', '$900', 'Litigation ready, Rounds 1-3 + settlement'),
        ('Professional', '$1,200', 'Full litigation package, All 4 rounds'),
        ('Elite', '$1,500', 'Maximum recovery, Attorney coordination + VIP')
    ]
    for name, price, desc in plans:
        p = doc.add_paragraph()
        p.add_run(f'{name} - {price}').bold = True
        doc.add_paragraph(desc)
    doc.add_paragraph()
    add_image("sop_screenshots/06_step3_plans.png", "Figure 3: Plan Selection")
    doc.add_paragraph()
    doc.add_heading('Payment Methods:', level=2)
    methods = ['Credit/Debit Card', 'PayPal', 'Cash App', 'Venmo', 'Zelle', 'Pay Later']
    for method in methods:
        doc.add_paragraph(f'• {method}', style='List Bullet')
    doc.add_paragraph()
    doc.add_paragraph('Select your plan and payment method, then click "Continue to Agreement".')
    doc.add_page_break()

    # ============ STEP 4 ============
    doc.add_heading('Step 4: Review & Agreement', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Review the terms and conditions.')
    doc.add_paragraph()
    doc.add_paragraph('1. Read the Terms of Service', style='List Number')
    doc.add_paragraph('2. Check the agreement checkbox', style='List Number')
    doc.add_paragraph('3. Click "Complete Signup"', style='List Number')
    doc.add_paragraph()
    add_image("sop_screenshots/10_step4_checked.png", "Figure 4: Agreement Page")
    doc.add_page_break()

    # ============ REGISTRATION COMPLETE ============
    doc.add_heading('Registration Complete', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'After clicking "Complete Signup", you will see a success message confirming '
        'your registration is complete.'
    )
    doc.add_paragraph()
    doc.add_paragraph('The confirmation shows:')
    doc.add_paragraph('• Your Client ID', style='List Bullet')
    doc.add_paragraph('• Your Referral Code', style='List Bullet')
    doc.add_paragraph('• Your Case Number', style='List Bullet')
    doc.add_paragraph()
    add_image("sop_screenshots/12_success_message.png", "Figure 5: Registration Success")
    doc.add_paragraph()
    doc.add_paragraph('Save your Referral Code - you can share it with friends!')
    doc.add_page_break()

    # ============ PORTAL LOGIN ============
    doc.add_heading('Client Portal Login', level=1)
    doc.add_paragraph()
    doc.add_paragraph('To access your Client Portal:')
    doc.add_paragraph()
    doc.add_paragraph('1. Go to the Client Portal login page', style='List Number')
    doc.add_paragraph('2. Enter your email address', style='List Number')
    doc.add_paragraph('3. Click "Send Login Link"', style='List Number')
    doc.add_paragraph('4. Check your email and click the login link', style='List Number')
    doc.add_paragraph()
    add_image("sop_screenshots/13_portal_login.png", "Figure 6: Portal Login Page")
    doc.add_page_break()

    # ============ PORTAL DASHBOARD ============
    doc.add_heading('Client Portal Dashboard', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'Once logged in, you will see your Client Portal Dashboard where you can:'
    )
    doc.add_paragraph()
    doc.add_paragraph('• Track your case progress', style='List Bullet')
    doc.add_paragraph('• View documents and letters', style='List Bullet')
    doc.add_paragraph('• See your credit report analysis', style='List Bullet')
    doc.add_paragraph('• Communicate with your case manager', style='List Bullet')
    doc.add_paragraph()
    add_image("sop_screenshots/14_portal_dashboard.png", "Figure 7: Portal Dashboard")
    doc.add_paragraph()
    doc.add_paragraph(
        'You will receive a separate SOP guide for navigating the Client Portal.'
    )
    doc.add_page_break()

    # ============ HELP ============
    doc.add_heading('Need Help?', level=1)
    doc.add_paragraph()
    doc.add_paragraph('If you have questions or encounter issues:')
    doc.add_paragraph()
    doc.add_paragraph('Email: support@brightpathascend.com')
    doc.add_paragraph('Phone: (555) 123-4567')
    doc.add_paragraph('Hours: Monday - Friday, 9am - 5pm EST')

    # Save
    doc.save('Client_Signup_SOP_Complete.docx')
    print("✅ Complete SOP rebuilt with all screenshots")

rebuild_complete_sop()
```

---

## STEP 6: Copy to outputs and verify

```bash
# Copy final document
cp Client_Signup_SOP_Complete.docx /mnt/user-data/outputs/

# List screenshots to verify
ls -la sop_screenshots/*.png

echo "✅ SOP Complete - download Client_Signup_SOP_Complete.docx"
```

---

## VERIFICATION

The final SOP must have real screenshots for:
- [ ] Step 1: Personal Info (filled)
- [ ] Step 2: Credit Monitoring dropdown (10 companies)
- [ ] Step 3: Plans (6 plans visible)
- [ ] Step 4: Agreement (checked)
- [ ] Success message (with Client ID, Referral Code, Case Number)
- [ ] Portal Login page
- [ ] Portal Dashboard

---

## ⚠️ IMPORTANT ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. Complete a REAL signup to capture success message           ║
║   2. Use test client from database for portal login              ║
║   3. All screenshots must show REAL content (not blank)          ║
║   4. Rebuild the Word document with all screenshots              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**CAPTURE THE MISSING SCREENSHOTS AND REBUILD THE SOP.**
