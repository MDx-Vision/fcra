# ADD CREATE PASSWORD SCREENSHOT TO SOP

---

## WHAT'S MISSING

The SOP needs a screenshot of the **Create Password** page that clients see when setting up their portal account.

---

## YOUR TASK

1. Find/capture the Create Password page screenshot
2. Add it to the SOP document between "Registration Complete" and "Portal Login"

---

## STEP 1: Find the Create Password page URL

```bash
# Search for password creation routes
grep -n "password\|create.*account\|set.*password\|reset" app.py | head -20
```

Common URLs to try:
- `/portal/create-password`
- `/portal/set-password`
- `/portal/setup`
- `/portal/register`
- `/signup/password`

---

## STEP 2: Capture the Create Password screenshot

```python
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_create_password():
    os.makedirs("sop_screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1200})
        
        # Try different possible URLs for create password page
        urls_to_try = [
            "http://localhost:5001/portal/create-password",
            "http://localhost:5001/portal/set-password",
            "http://localhost:5001/portal/setup",
            "http://localhost:5001/portal/register",
            "http://localhost:5001/signup/password",
            "http://localhost:5001/portal/activate",
        ]
        
        for url in urls_to_try:
            await page.goto(url)
            await page.wait_for_timeout(1000)
            
            # Check if page has password fields
            content = await page.content()
            if "password" in content.lower() and "create" in content.lower():
                await page.screenshot(path="sop_screenshots/15_create_password.png", full_page=True)
                print(f"✓ Found Create Password page at: {url}")
                break
            elif "password" in content.lower():
                await page.screenshot(path="sop_screenshots/15_create_password.png", full_page=True)
                print(f"✓ Found password page at: {url}")
                break
        
        # If none found, check if it's part of signup flow
        # Or look in templates
        await browser.close()

asyncio.run(capture_create_password())
```

---

## STEP 3: If page not found, check templates

```bash
# Find password-related templates
ls templates/ | grep -i password
ls templates/ | grep -i portal

# Search for create password in templates
grep -r "Create.*Password\|Set.*Password\|password" templates/portal*.html 2>/dev/null | head -10
```

---

## STEP 4: Update the SOP document

```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def add_create_password_to_sop():
    # Load existing document
    doc = Document('Client_Signup_SOP_Complete.docx')
    
    # We need to insert the Create Password section
    # Find the right location (after Registration Complete, before Portal Login)
    
    # Since modifying existing docx is complex, rebuild with the new section
    
    # Helper function
    def add_image(doc, path, caption, width=5.5):
        if os.path.exists(path):
            doc.add_picture(path, width=Inches(width))
            cap = doc.add_paragraph(caption)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].font.italic = True
            cap.runs[0].font.size = Pt(10)
            return True
        return False
    
    # Create new document with Create Password section added
    new_doc = Document()
    
    # Set margins
    for section in new_doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
    
    # ============ COVER PAGE ============
    new_doc.add_paragraph()
    new_doc.add_paragraph()
    title = new_doc.add_heading('Client Signup Guide', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = new_doc.add_paragraph('Complete Registration to Portal Access')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    new_doc.add_paragraph()
    new_doc.add_paragraph('Version 1.3 | December 2025')
    new_doc.add_page_break()
    
    # ============ TABLE OF CONTENTS ============
    new_doc.add_heading('Table of Contents', level=1)
    new_doc.add_paragraph()
    toc_items = [
        '1. Overview',
        '2. Step 1: Personal Information',
        '3. Step 2: Credit Monitoring Access',
        '4. Step 3: Choose Your Plan & Payment',
        '5. Step 4: Review & Agreement',
        '6. Registration Complete',
        '7. Create Your Password',
        '8. Client Portal Login',
        '9. Client Portal Dashboard',
        '10. Need Help?'
    ]
    for item in toc_items:
        new_doc.add_paragraph(item)
    new_doc.add_page_break()
    
    # ============ OVERVIEW ============
    new_doc.add_heading('Overview', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph(
        'Welcome! This guide walks you through the complete signup process, '
        'from registration to accessing your Client Portal.'
    )
    new_doc.add_paragraph()
    new_doc.add_paragraph('Before you begin, please have ready:')
    new_doc.add_paragraph('• Valid email address', style='List Bullet')
    new_doc.add_paragraph('• Phone number', style='List Bullet')
    new_doc.add_paragraph('• Current mailing address', style='List Bullet')
    new_doc.add_paragraph('• Credit monitoring service login (optional)', style='List Bullet')
    new_doc.add_paragraph('• Payment method (if selecting a paid plan)', style='List Bullet')
    new_doc.add_page_break()
    
    # ============ STEP 1 ============
    new_doc.add_heading('Step 1: Personal Information', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph('Enter your personal information. Fields marked with * are required.')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/02_step1_filled.png", "Figure 1: Personal Information Form")
    new_doc.add_paragraph()
    new_doc.add_paragraph('Click "Next" to continue.')
    new_doc.add_page_break()
    
    # ============ STEP 2 ============
    new_doc.add_heading('Step 2: Credit Monitoring Access', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph('Select your credit monitoring provider from the 10 supported services:')
    new_doc.add_paragraph()
    companies = [
        'IdentityIQ.com', 'MyScoreIQ.com', 'SmartCredit.com', 'MyFreeScoreNow.com',
        'HighScoreNow.com', 'IdentityClub.com', 'PrivacyGuard.com', 'IDClub.com',
        'MyThreeScores.com', 'MyScore750.com'
    ]
    for i, company in enumerate(companies, 1):
        new_doc.add_paragraph(f'{i}. {company}', style='List Number')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/04_step2_dropdown.png", "Figure 2: Credit Monitoring Selection")
    new_doc.add_paragraph()
    new_doc.add_paragraph('Enter your username and password, then click "Next".')
    new_doc.add_page_break()
    
    # ============ STEP 3 ============
    new_doc.add_heading('Step 3: Choose Your Plan & Payment', level=1)
    new_doc.add_paragraph()
    new_doc.add_heading('Available Plans:', level=2)
    plans = [
        ('Basic Analysis', 'FREE', 'Free credit analysis, identify problem areas'),
        ('Starter', '$300', 'Full FCRA analysis + Round 1 dispute letters'),
        ('Standard', '$600', 'Full analysis + Rounds 1-2 + documentation'),
        ('Premium', '$900', 'Litigation ready, Rounds 1-3 + settlement'),
        ('Professional', '$1,200', 'Full litigation package, All 4 rounds'),
        ('Elite', '$1,500', 'Maximum recovery, Attorney coordination + VIP')
    ]
    for name, price, desc in plans:
        p = new_doc.add_paragraph()
        p.add_run(f'{name} - {price}').bold = True
        new_doc.add_paragraph(desc)
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/06_step3_plans.png", "Figure 3: Plan Selection")
    new_doc.add_paragraph()
    new_doc.add_heading('Payment Methods:', level=2)
    methods = ['Credit/Debit Card', 'PayPal', 'Cash App', 'Venmo', 'Zelle', 'Pay Later']
    for method in methods:
        new_doc.add_paragraph(f'• {method}', style='List Bullet')
    new_doc.add_paragraph()
    new_doc.add_paragraph('Select your plan and payment method, then click "Continue to Agreement".')
    new_doc.add_page_break()
    
    # ============ STEP 4 ============
    new_doc.add_heading('Step 4: Review & Agreement', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph('Review the terms and conditions.')
    new_doc.add_paragraph()
    new_doc.add_paragraph('1. Read the Terms of Service', style='List Number')
    new_doc.add_paragraph('2. Check the agreement checkbox', style='List Number')
    new_doc.add_paragraph('3. Click "Complete Signup"', style='List Number')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/10_step4_checked.png", "Figure 4: Agreement Page")
    new_doc.add_page_break()
    
    # ============ REGISTRATION COMPLETE ============
    new_doc.add_heading('Registration Complete', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph(
        'After clicking "Complete Signup", you will see a success message confirming '
        'your registration is complete.'
    )
    new_doc.add_paragraph()
    new_doc.add_paragraph('The confirmation shows:')
    new_doc.add_paragraph('• Your Client ID', style='List Bullet')
    new_doc.add_paragraph('• Your Referral Code', style='List Bullet')
    new_doc.add_paragraph('• Your Case Number', style='List Bullet')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/12_success_message.png", "Figure 5: Registration Success")
    new_doc.add_paragraph()
    new_doc.add_paragraph('Save your Referral Code - you can share it with friends!')
    new_doc.add_page_break()
    
    # ============ CREATE PASSWORD (NEW SECTION) ============
    new_doc.add_heading('Create Your Password', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph(
        'After registration, you will be prompted to create a password for your '
        'Client Portal account.'
    )
    new_doc.add_paragraph()
    new_doc.add_heading('Password Requirements:', level=2)
    new_doc.add_paragraph('• At least 8 characters', style='List Bullet')
    new_doc.add_paragraph('• At least one uppercase letter', style='List Bullet')
    new_doc.add_paragraph('• At least one lowercase letter', style='List Bullet')
    new_doc.add_paragraph('• At least one number', style='List Bullet')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/15_create_password.png", "Figure 6: Create Password")
    new_doc.add_paragraph()
    new_doc.add_paragraph('Enter your password twice to confirm, then click "Create Account".')
    new_doc.add_page_break()
    
    # ============ PORTAL LOGIN ============
    new_doc.add_heading('Client Portal Login', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph('To access your Client Portal:')
    new_doc.add_paragraph()
    new_doc.add_paragraph('1. Go to the Client Portal login page', style='List Number')
    new_doc.add_paragraph('2. Enter your email address', style='List Number')
    new_doc.add_paragraph('3. Enter your password', style='List Number')
    new_doc.add_paragraph('4. Click "Login"', style='List Number')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/13_portal_login.png", "Figure 7: Portal Login Page")
    new_doc.add_page_break()
    
    # ============ PORTAL DASHBOARD ============
    new_doc.add_heading('Client Portal Dashboard', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph(
        'Once logged in, you will see your Client Portal Dashboard where you can:'
    )
    new_doc.add_paragraph()
    new_doc.add_paragraph('• Track your case progress', style='List Bullet')
    new_doc.add_paragraph('• View documents and letters', style='List Bullet')
    new_doc.add_paragraph('• See your credit report analysis', style='List Bullet')
    new_doc.add_paragraph('• Communicate with your case manager', style='List Bullet')
    new_doc.add_paragraph()
    add_image(new_doc, "sop_screenshots/14_portal_dashboard.png", "Figure 8: Portal Dashboard")
    new_doc.add_paragraph()
    new_doc.add_paragraph(
        'You will receive a separate SOP guide for navigating the Client Portal.'
    )
    new_doc.add_page_break()
    
    # ============ HELP ============
    new_doc.add_heading('Need Help?', level=1)
    new_doc.add_paragraph()
    new_doc.add_paragraph('If you have questions or encounter issues:')
    new_doc.add_paragraph()
    new_doc.add_paragraph('Email: support@brightpathascend.com')
    new_doc.add_paragraph('Phone: (555) 123-4567')
    new_doc.add_paragraph('Hours: Monday - Friday, 9am - 5pm EST')
    
    # Save
    new_doc.save('Client_Signup_SOP_Complete.docx')
    print("✅ SOP updated with Create Password section")

add_create_password_to_sop()
```

---

## STEP 5: Copy to outputs

```bash
cp Client_Signup_SOP_Complete.docx /mnt/user-data/outputs/
echo "✅ Done - download Client_Signup_SOP_Complete.docx"
```

---

## ⚠️ IMPORTANT ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. Find the Create Password page URL                           ║
║   2. Capture screenshot of Create Password page                  ║
║   3. Add to SOP between Registration Complete and Portal Login   ║
║   4. Save as sop_screenshots/15_create_password.png              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**ADD THE CREATE PASSWORD SCREENSHOT TO THE SOP.**
