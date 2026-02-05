# FIX SIGNUP SOP - 10 CREDIT MONITORING COMPANIES + FULL SCREENSHOTS

---

## TWO PROBLEMS TO FIX

1. **Screenshots are cut in half** - need full page captures
2. **Step 2 shows only 4 credit monitoring companies** - should show all 10

---

## THE 10 CREDIT MONITORING COMPANIES

The signup form Step 2 must show these 10 options:

1. IdentityIQ.com
2. MyScoreIQ.com
3. SmartCredit.com
4. MyFreeScoreNow.com
5. HighScoreNow.com
6. IdentityClub.com
7. PrivacyGuard.com
8. IDClub.com
9. MyThreeScores.com
10. MyScore750.com

---

## YOUR TASK

1. Update the signup form template to include all 10 credit monitoring companies
2. Take new full-page screenshots
3. Recreate the SOP document with correct content

---

## STEP 1: Update the signup form template

Find the credit monitoring dropdown in `templates/client_signup.html` and update it:

```bash
grep -n "creditProvider\|credit.*select\|IdentityIQ\|MyScoreIQ" templates/client_signup.html
```

Then update the select dropdown to include all 10:

```html
<select id="creditProvider" name="creditProvider" required>
    <option value="">Select Your Credit Monitoring Service</option>
    <option value="IdentityIQ.com">IdentityIQ.com</option>
    <option value="MyScoreIQ.com">MyScoreIQ.com</option>
    <option value="SmartCredit.com">SmartCredit.com</option>
    <option value="MyFreeScoreNow.com">MyFreeScoreNow.com</option>
    <option value="HighScoreNow.com">HighScoreNow.com</option>
    <option value="IdentityClub.com">IdentityClub.com</option>
    <option value="PrivacyGuard.com">PrivacyGuard.com</option>
    <option value="IDClub.com">IDClub.com</option>
    <option value="MyThreeScores.com">MyThreeScores.com</option>
    <option value="MyScore750.com">MyScore750.com</option>
    <option value="Other">Other</option>
</select>
```

---

## STEP 2: Also update dashboard.html intake form

The dashboard intake modal also needs all 10 providers:

```bash
grep -n "creditProvider\|IdentityIQ" templates/dashboard.html
```

Update that dropdown too with all 10 companies.

---

## STEP 3: Take new FULL screenshots

```python
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_full_screenshots():
    os.makedirs("sop_screenshots", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # LARGER viewport for full capture
        page = await browser.new_page(viewport={"width": 1400, "height": 1200})

        await page.goto("http://localhost:5001/signup")
        await page.wait_for_timeout(1500)

        # Screenshot 1: Step 1 empty
        await page.screenshot(path="sop_screenshots/01_step1_empty.png", full_page=True)
        print("✓ Screenshot 1: Step 1 empty")

        # Fill Step 1
        await page.fill("#firstName", "John")
        await page.fill("#lastName", "Smith")
        await page.fill("#email", "john.smith@email.com")
        await page.fill("#phone", "555-123-4567")
        await page.fill("#addressStreet", "123 Main Street")
        await page.fill("#addressCity", "Los Angeles")
        await page.fill("#addressZip", "90001")

        # Screenshot 2: Step 1 filled
        await page.screenshot(path="sop_screenshots/02_step1_filled.png", full_page=True)
        print("✓ Screenshot 2: Step 1 filled")

        # Go to Step 2
        next_btn = await page.query_selector("button:has-text('Next')")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)

        # Screenshot 3: Step 2 - Credit Monitoring (showing dropdown)
        await page.screenshot(path="sop_screenshots/03_step2_credit.png", full_page=True)
        print("✓ Screenshot 3: Step 2 credit monitoring")

        # Click dropdown to show all 10 options
        dropdown = await page.query_selector("#creditProvider, select[name='creditProvider']")
        if dropdown:
            await dropdown.click()
            await page.wait_for_timeout(500)

        # Screenshot 4: Step 2 - Dropdown open showing all 10 companies
        await page.screenshot(path="sop_screenshots/04_step2_dropdown_open.png", full_page=True)
        print("✓ Screenshot 4: Step 2 dropdown open with 10 companies")

        # Select a provider and fill credentials
        if dropdown:
            await dropdown.select_option("MyScoreIQ.com")

        username = await page.query_selector("#creditUsername")
        if username:
            await username.fill("johnsmith_credit")

        password = await page.query_selector("#creditPassword")
        if password:
            await password.fill("MySecurePass123")

        # Screenshot 5: Step 2 filled
        await page.screenshot(path="sop_screenshots/05_step2_filled.png", full_page=True)
        print("✓ Screenshot 5: Step 2 filled")

        # Go to Step 3
        next_btn = await page.query_selector("button:has-text('Next'):visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)

        # Screenshot 6: Step 3 - Plan selection
        await page.screenshot(path="sop_screenshots/06_step3_plans.png", full_page=True)
        print("✓ Screenshot 6: Step 3 plans")

        # Select a plan
        plan = await page.query_selector("input[type='radio']")
        if plan:
            await plan.click()

        # Screenshot 7: Step 3 plan selected
        await page.screenshot(path="sop_screenshots/07_step3_selected.png", full_page=True)
        print("✓ Screenshot 7: Step 3 plan selected")

        # Go to Step 4
        next_btn = await page.query_selector("button:has-text('Next'):visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)

        # Screenshot 8: Step 4 - Agreement
        await page.screenshot(path="sop_screenshots/08_step4_agreement.png", full_page=True)
        print("✓ Screenshot 8: Step 4 agreement")

        # Check agreement
        checkbox = await page.query_selector("input[type='checkbox']")
        if checkbox:
            await checkbox.click()

        # Screenshot 9: Step 4 ready to submit
        await page.screenshot(path="sop_screenshots/09_step4_ready.png", full_page=True)
        print("✓ Screenshot 9: Step 4 ready to submit")

        await browser.close()
        print("\n✅ All screenshots captured")

asyncio.run(capture_full_screenshots())
```

---

## STEP 4: Create the SOP Word document

```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def create_signup_sop():
    doc = Document()

    # Set margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # ============ COVER PAGE ============
    doc.add_paragraph()
    doc.add_paragraph()

    title = doc.add_heading('Client Signup Guide', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph('Standard Operating Procedure')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    doc.add_paragraph('Version 1.0 | December 2025')

    doc.add_page_break()

    # ============ TABLE OF CONTENTS ============
    doc.add_heading('Table of Contents', level=1)
    doc.add_paragraph()
    doc.add_paragraph('1. Overview')
    doc.add_paragraph('2. Step 1: Personal Information')
    doc.add_paragraph('3. Step 2: Credit Monitoring Access')
    doc.add_paragraph('4. Step 3: Select Your Plan')
    doc.add_paragraph('5. Step 4: Review & Submit')
    doc.add_paragraph('6. What Happens Next')
    doc.add_paragraph('7. Need Help?')

    doc.add_page_break()

    # ============ OVERVIEW ============
    doc.add_heading('Overview', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'Welcome! This guide walks you through the client signup process. '
        'The process has 4 simple steps and takes about 5-10 minutes.'
    )
    doc.add_paragraph()
    doc.add_paragraph('Before you begin, please have ready:')
    doc.add_paragraph('• Valid email address', style='List Bullet')
    doc.add_paragraph('• Phone number', style='List Bullet')
    doc.add_paragraph('• Current mailing address', style='List Bullet')
    doc.add_paragraph('• Credit monitoring service login (if you have one)', style='List Bullet')

    doc.add_page_break()

    # ============ STEP 1 ============
    doc.add_heading('Step 1: Personal Information', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Enter your personal information. All fields marked with * are required.')
    doc.add_paragraph()

    doc.add_heading('Required Fields:', level=2)
    doc.add_paragraph('• First Name *', style='List Bullet')
    doc.add_paragraph('• Last Name *', style='List Bullet')
    doc.add_paragraph('• Email Address *', style='List Bullet')
    doc.add_paragraph('• Phone Number *', style='List Bullet')
    doc.add_paragraph('• Street Address *', style='List Bullet')
    doc.add_paragraph('• City *', style='List Bullet')
    doc.add_paragraph('• State *', style='List Bullet')
    doc.add_paragraph('• ZIP Code *', style='List Bullet')
    doc.add_paragraph('• Date of Birth', style='List Bullet')
    doc.add_paragraph('• Last 4 of SSN (for verification)', style='List Bullet')

    doc.add_paragraph()

    if os.path.exists("sop_screenshots/02_step1_filled.png"):
        doc.add_picture("sop_screenshots/02_step1_filled.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 1: Personal Information Form')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
        caption.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    doc.add_paragraph('Click "Next" to continue to Step 2.')

    doc.add_page_break()

    # ============ STEP 2 - CREDIT MONITORING ============
    doc.add_heading('Step 2: Credit Monitoring Access', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'If you have an existing credit monitoring account, select your provider '
        'and enter your login credentials. This allows us to automatically '
        'retrieve your credit report.'
    )

    doc.add_paragraph()
    doc.add_heading('Supported Credit Monitoring Services:', level=2)
    doc.add_paragraph()

    # List all 10 companies
    doc.add_paragraph('1. IdentityIQ.com', style='List Number')
    doc.add_paragraph('2. MyScoreIQ.com', style='List Number')
    doc.add_paragraph('3. SmartCredit.com', style='List Number')
    doc.add_paragraph('4. MyFreeScoreNow.com', style='List Number')
    doc.add_paragraph('5. HighScoreNow.com', style='List Number')
    doc.add_paragraph('6. IdentityClub.com', style='List Number')
    doc.add_paragraph('7. PrivacyGuard.com', style='List Number')
    doc.add_paragraph('8. IDClub.com', style='List Number')
    doc.add_paragraph('9. MyThreeScores.com', style='List Number')
    doc.add_paragraph('10. MyScore750.com', style='List Number')

    doc.add_paragraph()

    if os.path.exists("sop_screenshots/04_step2_dropdown_open.png"):
        doc.add_picture("sop_screenshots/04_step2_dropdown_open.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 2: Credit Monitoring Service Selection (10 Options)')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
        caption.runs[0].font.size = Pt(10)

    doc.add_paragraph()

    doc.add_heading('After selecting your provider:', level=2)
    doc.add_paragraph('• Enter your username/email for that service', style='List Bullet')
    doc.add_paragraph('• Enter your password', style='List Bullet')
    doc.add_paragraph('• Your credentials are encrypted and secure', style='List Bullet')

    doc.add_paragraph()

    if os.path.exists("sop_screenshots/05_step2_filled.png"):
        doc.add_picture("sop_screenshots/05_step2_filled.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 3: Credit Monitoring Credentials Entered')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
        caption.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    note = doc.add_paragraph()
    note.add_run('🔒 Security Note: ').bold = True
    note.add_run('Your credentials are encrypted using bank-level security.')

    doc.add_paragraph()
    doc.add_paragraph('Click "Next" to continue to Step 3.')

    doc.add_page_break()

    # ============ STEP 3 ============
    doc.add_heading('Step 3: Select Your Plan', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Choose the service plan that best fits your needs.')

    doc.add_paragraph()

    if os.path.exists("sop_screenshots/07_step3_selected.png"):
        doc.add_picture("sop_screenshots/07_step3_selected.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 4: Plan Selection')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
        caption.runs[0].font.size = Pt(10)

    doc.add_paragraph()
    doc.add_paragraph('Click on your preferred plan to select it, then click "Next".')

    doc.add_page_break()

    # ============ STEP 4 ============
    doc.add_heading('Step 4: Review & Submit', level=1)
    doc.add_paragraph()
    doc.add_paragraph('This is the final step. Review the terms and conditions, then submit.')

    doc.add_paragraph()

    doc.add_heading('To complete:', level=2)
    doc.add_paragraph('1. Read the Terms of Service', style='List Number')
    doc.add_paragraph('2. Check the agreement checkbox', style='List Number')
    doc.add_paragraph('3. Click "Submit"', style='List Number')

    doc.add_paragraph()

    if os.path.exists("sop_screenshots/09_step4_ready.png"):
        doc.add_picture("sop_screenshots/09_step4_ready.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 5: Agreement & Submit')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
        caption.runs[0].font.size = Pt(10)

    doc.add_page_break()

    # ============ WHAT'S NEXT ============
    doc.add_heading("What Happens Next", level=1)
    doc.add_paragraph()

    doc.add_paragraph('After submitting your registration:')
    doc.add_paragraph()
    doc.add_paragraph('1. You will receive a confirmation email within minutes', style='List Number')
    doc.add_paragraph('2. Our team reviews your information (1-2 business days)', style='List Number')
    doc.add_paragraph('3. You receive portal login credentials', style='List Number')
    doc.add_paragraph('4. Log in to track your case progress', style='List Number')

    doc.add_page_break()

    # ============ HELP ============
    doc.add_heading('Need Help?', level=1)
    doc.add_paragraph()
    doc.add_paragraph('If you have questions or encounter issues:')
    doc.add_paragraph()
    doc.add_paragraph('Email: support@example.com')
    doc.add_paragraph('Phone: (555) 123-4567')
    doc.add_paragraph('Hours: Monday - Friday, 9am - 5pm EST')

    # Save
    doc.save('Client_Signup_SOP_Fixed.docx')
    print("✅ SOP document created: Client_Signup_SOP_Fixed.docx")

create_signup_sop()
```

---

## STEP 5: Run everything

```bash
# Start app
CI=true python app.py &
sleep 3

# Capture screenshots
python3 capture_screenshots.py

# Create SOP
python3 create_sop.py

# Copy to outputs
cp Client_Signup_SOP_Fixed.docx /mnt/user-data/outputs/
```

---

## VERIFICATION

The SOP must include:
- ✅ Full-page screenshots (not cut off)
- ✅ All 10 credit monitoring companies listed
- ✅ Screenshot showing the dropdown with all 10 options
- ✅ Clear step-by-step instructions

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. UPDATE the signup form to have all 10 credit companies      ║
║   2. Take FULL screenshots (not cut off)                         ║
║   3. Include screenshot of dropdown showing all 10 options       ║
║   4. Create professional SOP document                            ║
║   5. Save as Client_Signup_SOP_Fixed.docx                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**FIX THE FORM AND CREATE THE SOP WITH ALL 10 CREDIT MONITORING COMPANIES.**
