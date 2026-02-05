# SINGLE TASK: CREATE CLIENT SIGNUP SOP WITH SCREENSHOTS

---

## YOUR TASK

Create a professional SOP (Standard Operating Procedure) document showing clients how to sign up, with screenshots of each step.

---

## STEP 1: Take screenshots of each signup step

```python
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_signup_screenshots():
    """Capture screenshots of each signup step"""

    os.makedirs("sop_screenshots", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        # Screenshot 1: Landing page / Start
        await page.goto("http://localhost:5001/signup")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="sop_screenshots/01_signup_start.png", full_page=False)
        print("✓ Screenshot 1: Signup start page")

        # Screenshot 2: Step 1 - Personal Info (empty)
        await page.screenshot(path="sop_screenshots/02_step1_empty.png", full_page=False)
        print("✓ Screenshot 2: Step 1 empty")

        # Screenshot 3: Step 1 - Personal Info (filled)
        await page.fill("#firstName", "John")
        await page.fill("#lastName", "Smith")
        await page.fill("#email", "john.smith@example.com")
        await page.fill("#phone", "555-123-4567")
        await page.fill("#addressStreet", "123 Main Street")
        await page.fill("#addressCity", "Los Angeles")

        # Try to fill state if it exists
        state_field = await page.query_selector("#addressState, [name='addressState'], select[name='state']")
        if state_field:
            tag = await state_field.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                await state_field.select_option("CA")
            else:
                await state_field.fill("CA")

        await page.fill("#addressZip", "90001")

        # Date of birth if exists
        dob_field = await page.query_selector("#dateOfBirth, [name='dateOfBirth']")
        if dob_field:
            await dob_field.fill("1985-06-15")

        # SSN last 4 if exists
        ssn_field = await page.query_selector("#ssnLast4, [name='ssnLast4']")
        if ssn_field:
            await ssn_field.fill("1234")

        await page.screenshot(path="sop_screenshots/03_step1_filled.png", full_page=False)
        print("✓ Screenshot 3: Step 1 filled")

        # Screenshot 4: Click Next, show Step 2
        next_btn = await page.query_selector("button:has-text('Next'), .next-btn, [onclick*='nextStep']")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(500)

        await page.screenshot(path="sop_screenshots/04_step2_credit.png", full_page=False)
        print("✓ Screenshot 4: Step 2 - Credit Access")

        # Screenshot 5: Step 2 filled (if has fields)
        username_field = await page.query_selector("#creditUsername, [name='creditUsername']")
        if username_field:
            await username_field.fill("myusername")

        password_field = await page.query_selector("#creditPassword, [name='creditPassword']")
        if password_field:
            await password_field.fill("••••••••")

        await page.screenshot(path="sop_screenshots/05_step2_filled.png", full_page=False)
        print("✓ Screenshot 5: Step 2 filled")

        # Screenshot 6: Click Next, show Step 3 (Plan Selection)
        next_btn = await page.query_selector("button:has-text('Next'):visible, .next-btn:visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(500)

        await page.screenshot(path="sop_screenshots/06_step3_plans.png", full_page=False)
        print("✓ Screenshot 6: Step 3 - Plan Selection")

        # Screenshot 7: Select a plan
        plan_radio = await page.query_selector("input[type='radio'][name='plan'], .plan-option, .pricing-card")
        if plan_radio:
            await plan_radio.click()
            await page.wait_for_timeout(300)

        await page.screenshot(path="sop_screenshots/07_step3_selected.png", full_page=False)
        print("✓ Screenshot 7: Plan selected")

        # Screenshot 8: Click Next, show Step 4 (Agreement)
        next_btn = await page.query_selector("button:has-text('Next'):visible, .next-btn:visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(500)

        await page.screenshot(path="sop_screenshots/08_step4_agreement.png", full_page=False)
        print("✓ Screenshot 8: Step 4 - Agreement")

        # Screenshot 9: Check agreement box
        checkbox = await page.query_selector("input[type='checkbox'], #terms, #agreement")
        if checkbox:
            await checkbox.click()
            await page.wait_for_timeout(300)

        await page.screenshot(path="sop_screenshots/09_step4_checked.png", full_page=False)
        print("✓ Screenshot 9: Agreement checked")

        # Screenshot 10: Final submit button visible
        await page.screenshot(path="sop_screenshots/10_ready_submit.png", full_page=False)
        print("✓ Screenshot 10: Ready to submit")

        await browser.close()

        print("\n✅ All screenshots captured in sop_screenshots/")

asyncio.run(capture_signup_screenshots())
```

---

## STEP 2: Create the Word document

After capturing screenshots, create the SOP document:

```python
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def create_signup_sop():
    """Create professional SOP document with screenshots"""

    doc = Document()

    # Title
    title = doc.add_heading('Client Signup Guide', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle
    subtitle = doc.add_paragraph('Step-by-Step Instructions for New Client Registration')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()  # Spacing

    # Introduction
    doc.add_heading('Overview', level=1)
    doc.add_paragraph(
        'This guide walks you through the client signup process. '
        'The signup consists of 4 simple steps that should take approximately 5 minutes to complete.'
    )

    doc.add_paragraph()

    # Step 1
    doc.add_heading('Step 1: Personal Information', level=1)
    doc.add_paragraph(
        'Enter your personal details including your name, email, phone number, and address.'
    )

    doc.add_paragraph('Required fields:', style='List Bullet')
    doc.add_paragraph('First Name', style='List Bullet')
    doc.add_paragraph('Last Name', style='List Bullet')
    doc.add_paragraph('Email Address', style='List Bullet')
    doc.add_paragraph('Phone Number', style='List Bullet')
    doc.add_paragraph('Street Address', style='List Bullet')
    doc.add_paragraph('City, State, ZIP Code', style='List Bullet')

    # Add screenshot if exists
    if os.path.exists("sop_screenshots/03_step1_filled.png"):
        doc.add_paragraph()
        doc.add_picture("sop_screenshots/03_step1_filled.png", width=Inches(5.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('Figure 1: Personal Information Form', style='Caption')

    doc.add_paragraph()
    doc.add_paragraph('Click the "Next" button to continue to Step 2.', style='Intense Quote')

    # Step 2
    doc.add_heading('Step 2: Credit Access (Optional)', level=1)
    doc.add_paragraph(
        'If you have existing credit monitoring credentials, enter them here. '
        'This allows us to automatically pull your credit report for analysis.'
    )

    if os.path.exists("sop_screenshots/05_step2_filled.png"):
        doc.add_paragraph()
        doc.add_picture("sop_screenshots/05_step2_filled.png", width=Inches(5.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('Figure 2: Credit Access Form', style='Caption')

    doc.add_paragraph()
    doc.add_paragraph('Click the "Next" button to continue to Step 3.', style='Intense Quote')

    # Step 3
    doc.add_heading('Step 3: Select Your Plan', level=1)
    doc.add_paragraph(
        'Choose the service plan that best fits your needs. '
        'Each plan offers different levels of support and features.'
    )

    if os.path.exists("sop_screenshots/07_step3_selected.png"):
        doc.add_paragraph()
        doc.add_picture("sop_screenshots/07_step3_selected.png", width=Inches(5.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('Figure 3: Plan Selection', style='Caption')

    doc.add_paragraph()
    doc.add_paragraph('Click on your preferred plan, then click "Next" to continue.', style='Intense Quote')

    # Step 4
    doc.add_heading('Step 4: Review & Submit', level=1)
    doc.add_paragraph(
        'Review the terms and conditions, then check the agreement box to confirm. '
        'Click "Submit" to complete your registration.'
    )

    if os.path.exists("sop_screenshots/09_step4_checked.png"):
        doc.add_paragraph()
        doc.add_picture("sop_screenshots/09_step4_checked.png", width=Inches(5.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph('Figure 4: Agreement & Submit', style='Caption')

    doc.add_paragraph()
    doc.add_paragraph('Check the agreement box and click "Submit" to complete signup.', style='Intense Quote')

    # What's Next
    doc.add_heading("What's Next?", level=1)
    doc.add_paragraph(
        'After submitting your registration:'
    )
    doc.add_paragraph('You will receive a confirmation email', style='List Number')
    doc.add_paragraph('Our team will review your information', style='List Number')
    doc.add_paragraph('You will receive login credentials for the client portal', style='List Number')
    doc.add_paragraph('Log in to track your case progress', style='List Number')

    # Contact
    doc.add_heading('Need Help?', level=1)
    doc.add_paragraph(
        'If you encounter any issues during signup, please contact our support team.'
    )

    # Save
    doc.save('/mnt/user-data/outputs/Client_Signup_SOP.docx')
    print("✅ SOP document created: Client_Signup_SOP.docx")

create_signup_sop()
```

---

## STEP 3: Run both scripts

```bash
# Make sure app is running
CI=true python app.py &
sleep 3

# Install python-docx if needed
pip install python-docx --break-system-packages

# Capture screenshots
python3 capture_screenshots.py

# Create SOP document
python3 create_sop.py
```

---

## STEP 4: Verify output

Check that these files exist:
- `sop_screenshots/` folder with 10 screenshots
- `Client_Signup_SOP.docx` - the final document

---

## OUTPUT

The final SOP document should include:
1. Title and overview
2. Step 1: Personal Information (with screenshot)
3. Step 2: Credit Access (with screenshot)
4. Step 3: Plan Selection (with screenshot)
5. Step 4: Agreement & Submit (with screenshot)
6. What's Next section
7. Contact/Help section

---

## ⚠️ RULES ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. Capture clear screenshots at each step                      ║
║   2. Fill in realistic example data (not "test test")            ║
║   3. Create professional Word document                           ║
║   4. Include all 4 signup steps with images                      ║
║   5. Save final doc to /mnt/user-data/outputs/                   ║
║                                                                  ║
║   THIS IS YOUR ONLY TASK.                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**CREATE THE CLIENT SIGNUP SOP WITH SCREENSHOTS.**
