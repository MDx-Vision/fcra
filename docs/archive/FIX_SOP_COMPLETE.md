# FIX SIGNUP SOP - COMPLETE CLIENT JOURNEY

---

## WHAT NEEDS TO BE FIXED

1. **Step 2:** Show all 10 credit monitoring companies (not 4)
2. **Step 3:** Show all 6 plans with correct prices
3. **Step 3:** Show all 6 payment methods
4. **Continue flow:** After payment → Welcome page → Client Portal
5. **Screenshots:** Full page (not cut off)

---

## THE 10 CREDIT MONITORING COMPANIES (Step 2)

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

## THE 6 PLANS (Step 3)

| Plan | Price | Description |
|------|-------|-------------|
| Basic Analysis | FREE | Free credit analysis of negative accounts, identify problem areas |
| Starter | $300 | Full FCRA analysis + Round 1 dispute letters |
| Standard | $600 | Full analysis + Rounds 1-2 + notation documentation |
| Premium | $900 | Litigation ready, Rounds 1-3 + settlement + damages calc |
| Professional | $1,200 | Full litigation package, All 4 rounds + settlement demand |
| Elite | $1,500 | Maximum recovery, Attorney coordination + VIP support |

---

## THE 6 PAYMENT METHODS (Step 3)

1. Credit/Debit Card
2. PayPal
3. Cash App
4. Venmo
5. Zelle
6. Pay Later

---

## COMPLETE USER FLOW FOR SOP

The SOP must cover the ENTIRE journey:

1. **Step 1:** Personal Information
2. **Step 2:** Credit Monitoring Access (10 companies)
3. **Step 3:** Choose Plan (6 plans) + Payment Method (6 options)
4. **Step 4:** Agreement
5. **Submit** → Proceed to Payment
6. **Payment Complete** → Welcome Page with "Go to Client Portal" button
7. **Click Portal Button** → Create Password page
8. **Create Password** → Login page
9. **Login** → Client Portal Dashboard

---

## YOUR TASK

### PART 1: Update the signup form templates

**File: templates/client_signup.html**

1. Find the credit provider dropdown and add all 10 companies
2. Find the plans section and add all 6 plans with correct prices
3. Add all 6 payment method options

```bash
# Find where plans are defined
grep -n "plan\|Plan\|price\|Price\|FREE\|300\|600\|900\|1200\|1500" templates/client_signup.html | head -30
```

**File: templates/dashboard.html** (intake modal)

1. Update credit provider dropdown to have all 10 companies

```bash
grep -n "creditProvider\|IdentityIQ" templates/dashboard.html
```

### PART 2: Take screenshots of the COMPLETE flow

```python
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_complete_flow():
    os.makedirs("sop_screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1200})
        
        # ========== STEP 1: PERSONAL INFO ==========
        await page.goto("http://localhost:5001/signup")
        await page.wait_for_timeout(1500)
        
        # Screenshot 1: Step 1 empty
        await page.screenshot(path="sop_screenshots/01_step1_empty.png", full_page=True)
        print("✓ 01: Step 1 empty")
        
        # Fill Step 1
        await page.fill("#firstName", "John")
        await page.fill("#lastName", "Smith")
        await page.fill("#email", "john.smith@email.com")
        await page.fill("#phone", "555-123-4567")
        await page.fill("#addressStreet", "123 Main Street")
        await page.fill("#addressCity", "Los Angeles")
        await page.fill("#addressZip", "90001")
        
        state = await page.query_selector("#addressState, select[name='state']")
        if state:
            try:
                await state.select_option("CA")
            except:
                await state.fill("CA")
        
        dob = await page.query_selector("#dateOfBirth")
        if dob:
            await dob.fill("1985-06-15")
        
        ssn = await page.query_selector("#ssnLast4")
        if ssn:
            await ssn.fill("1234")
        
        # Screenshot 2: Step 1 filled
        await page.screenshot(path="sop_screenshots/02_step1_filled.png", full_page=True)
        print("✓ 02: Step 1 filled")
        
        # Click Next
        next_btn = await page.query_selector("button:has-text('Next')")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)
        
        # ========== STEP 2: CREDIT MONITORING ==========
        
        # Screenshot 3: Step 2 empty
        await page.screenshot(path="sop_screenshots/03_step2_empty.png", full_page=True)
        print("✓ 03: Step 2 empty")
        
        # Click dropdown to show all 10 companies
        dropdown = await page.query_selector("#creditProvider, select[name='creditProvider']")
        if dropdown:
            await dropdown.click()
            await page.wait_for_timeout(500)
        
        # Screenshot 4: Dropdown open showing all 10 companies
        await page.screenshot(path="sop_screenshots/04_step2_dropdown.png", full_page=True)
        print("✓ 04: Step 2 dropdown with 10 companies")
        
        # Select a provider
        if dropdown:
            await dropdown.select_option("MyScoreIQ.com")
        
        # Fill credentials
        username = await page.query_selector("#creditUsername")
        if username:
            await username.fill("johnsmith_credit")
        
        password = await page.query_selector("#creditPassword")
        if password:
            await password.fill("MySecurePass123")
        
        # Screenshot 5: Step 2 filled
        await page.screenshot(path="sop_screenshots/05_step2_filled.png", full_page=True)
        print("✓ 05: Step 2 filled")
        
        # Click Next
        next_btn = await page.query_selector("button:has-text('Next'):visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)
        
        # ========== STEP 3: PLANS & PAYMENT ==========
        
        # Screenshot 6: Step 3 - All 6 plans visible
        await page.screenshot(path="sop_screenshots/06_step3_plans.png", full_page=True)
        print("✓ 06: Step 3 - All 6 plans")
        
        # Select Standard plan ($600)
        standard_plan = await page.query_selector("[data-plan='standard'], input[value='standard'], .plan-card:has-text('Standard')")
        if standard_plan:
            await standard_plan.click()
            await page.wait_for_timeout(500)
        
        # Screenshot 7: Plan selected
        await page.screenshot(path="sop_screenshots/07_step3_plan_selected.png", full_page=True)
        print("✓ 07: Step 3 - Plan selected")
        
        # Screenshot 8: Payment methods section
        await page.screenshot(path="sop_screenshots/08_step3_payment_methods.png", full_page=True)
        print("✓ 08: Step 3 - Payment methods")
        
        # Click Next/Continue
        next_btn = await page.query_selector("button:has-text('Continue'), button:has-text('Next'):visible")
        if next_btn:
            await next_btn.click()
            await page.wait_for_timeout(800)
        
        # ========== STEP 4: AGREEMENT ==========
        
        # Screenshot 9: Agreement page
        await page.screenshot(path="sop_screenshots/09_step4_agreement.png", full_page=True)
        print("✓ 09: Step 4 - Agreement")
        
        # Check agreement checkbox
        checkbox = await page.query_selector("input[type='checkbox']")
        if checkbox:
            await checkbox.click()
        
        # Screenshot 10: Agreement checked
        await page.screenshot(path="sop_screenshots/10_step4_checked.png", full_page=True)
        print("✓ 10: Step 4 - Agreement checked")
        
        # ========== SUBMIT & POST-SIGNUP FLOW ==========
        # Note: These may need manual screenshots if the flow requires actual payment
        
        # Screenshot 11: Ready to submit
        await page.screenshot(path="sop_screenshots/11_ready_submit.png", full_page=True)
        print("✓ 11: Ready to submit")
        
        # Try to capture welcome page if accessible
        await page.goto("http://localhost:5001/signup/welcome")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="sop_screenshots/12_welcome_page.png", full_page=True)
        print("✓ 12: Welcome page (if exists)")
        
        # Try to capture portal login
        await page.goto("http://localhost:5001/portal/login")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="sop_screenshots/13_portal_login.png", full_page=True)
        print("✓ 13: Portal login")
        
        # Try to capture portal dashboard (may need auth)
        await page.goto("http://localhost:5001/portal/dashboard")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="sop_screenshots/14_portal_dashboard.png", full_page=True)
        print("✓ 14: Portal dashboard (if accessible)")
        
        await browser.close()
        print("\n✅ All screenshots captured")

asyncio.run(capture_complete_flow())
```

### PART 3: Create the Word document

```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def create_complete_sop():
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
    
    subtitle = doc.add_paragraph('Complete Registration to Portal Access')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    doc.add_paragraph('Version 1.1 | December 2025')
    
    doc.add_page_break()
    
    # ============ TABLE OF CONTENTS ============
    doc.add_heading('Table of Contents', level=1)
    doc.add_paragraph()
    doc.add_paragraph('1. Overview')
    doc.add_paragraph('2. Step 1: Personal Information')
    doc.add_paragraph('3. Step 2: Credit Monitoring Access')
    doc.add_paragraph('4. Step 3: Choose Your Plan & Payment')
    doc.add_paragraph('5. Step 4: Review & Agreement')
    doc.add_paragraph('6. Payment Processing')
    doc.add_paragraph('7. Welcome Page')
    doc.add_paragraph('8. Create Your Password')
    doc.add_paragraph('9. Client Portal Login')
    doc.add_paragraph('10. Need Help?')
    
    doc.add_page_break()
    
    # ============ OVERVIEW ============
    doc.add_heading('Overview', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'Welcome! This guide walks you through the complete signup process, '
        'from registration to accessing your Client Portal. '
        'The process takes about 10-15 minutes.'
    )
    doc.add_paragraph()
    doc.add_paragraph('Before you begin, please have ready:')
    doc.add_paragraph('• Valid email address', style='List Bullet')
    doc.add_paragraph('• Phone number', style='List Bullet')
    doc.add_paragraph('• Current mailing address', style='List Bullet')
    doc.add_paragraph('• Credit monitoring service login (if you have one)', style='List Bullet')
    doc.add_paragraph('• Payment method (if selecting a paid plan)', style='List Bullet')
    
    doc.add_page_break()
    
    # ============ STEP 1: PERSONAL INFO ============
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
    
    doc.add_paragraph()
    doc.add_paragraph('Click "Next" to continue.')
    
    doc.add_page_break()
    
    # ============ STEP 2: CREDIT MONITORING ============
    doc.add_heading('Step 2: Credit Monitoring Access', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'If you have an existing credit monitoring account, select your provider '
        'and enter your login credentials.'
    )
    
    doc.add_paragraph()
    doc.add_heading('Supported Credit Monitoring Services (10 Options):', level=2)
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
    
    if os.path.exists("sop_screenshots/04_step2_dropdown.png"):
        doc.add_picture("sop_screenshots/04_step2_dropdown.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 2: Credit Monitoring Service Selection')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_paragraph()
    doc.add_paragraph('After selecting your provider, enter your username and password.')
    
    doc.add_paragraph()
    note = doc.add_paragraph()
    note.add_run('🔒 Security: ').bold = True
    note.add_run('Your credentials are encrypted using bank-level security.')
    
    doc.add_paragraph()
    doc.add_paragraph('Click "Next" to continue.')
    
    doc.add_page_break()
    
    # ============ STEP 3: PLANS & PAYMENT ============
    doc.add_heading('Step 3: Choose Your Plan & Payment', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Select the plan that best fits your needs.')
    
    doc.add_paragraph()
    doc.add_heading('Available Plans:', level=2)
    doc.add_paragraph()
    
    # All 6 plans
    p1 = doc.add_paragraph()
    p1.add_run('Basic Analysis - FREE').bold = True
    doc.add_paragraph('Free credit analysis of negative accounts, identify problem areas')
    doc.add_paragraph()
    
    p2 = doc.add_paragraph()
    p2.add_run('Starter - $300').bold = True
    doc.add_paragraph('Full FCRA analysis + Round 1 dispute letters')
    doc.add_paragraph()
    
    p3 = doc.add_paragraph()
    p3.add_run('Standard - $600').bold = True
    doc.add_paragraph('Full analysis + Rounds 1-2 + notation documentation')
    doc.add_paragraph()
    
    p4 = doc.add_paragraph()
    p4.add_run('Premium - $900').bold = True
    doc.add_paragraph('Litigation ready, Rounds 1-3 + settlement + damages calculation')
    doc.add_paragraph()
    
    p5 = doc.add_paragraph()
    p5.add_run('Professional - $1,200').bold = True
    doc.add_paragraph('Full litigation package, All 4 rounds + settlement demand')
    doc.add_paragraph()
    
    p6 = doc.add_paragraph()
    p6.add_run('Elite - $1,500').bold = True
    doc.add_paragraph('Maximum recovery, Attorney coordination + VIP support')
    
    doc.add_paragraph()
    
    if os.path.exists("sop_screenshots/06_step3_plans.png"):
        doc.add_picture("sop_screenshots/06_step3_plans.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 3: Plan Selection')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_page_break()
    
    doc.add_heading('Payment Methods:', level=2)
    doc.add_paragraph()
    doc.add_paragraph('We accept the following payment methods:')
    doc.add_paragraph()
    doc.add_paragraph('• Credit/Debit Card', style='List Bullet')
    doc.add_paragraph('• PayPal', style='List Bullet')
    doc.add_paragraph('• Cash App', style='List Bullet')
    doc.add_paragraph('• Venmo', style='List Bullet')
    doc.add_paragraph('• Zelle', style='List Bullet')
    doc.add_paragraph('• Pay Later', style='List Bullet')
    
    doc.add_paragraph()
    
    if os.path.exists("sop_screenshots/08_step3_payment_methods.png"):
        doc.add_picture("sop_screenshots/08_step3_payment_methods.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 4: Payment Methods')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_paragraph()
    doc.add_paragraph('Select your plan and payment method, then click "Continue to Agreement".')
    
    doc.add_page_break()
    
    # ============ STEP 4: AGREEMENT ============
    doc.add_heading('Step 4: Review & Agreement', level=1)
    doc.add_paragraph()
    doc.add_paragraph('Review the terms and conditions carefully.')
    
    doc.add_paragraph()
    doc.add_heading('To complete:', level=2)
    doc.add_paragraph('1. Read the Terms of Service', style='List Number')
    doc.add_paragraph('2. Read the Privacy Policy', style='List Number')
    doc.add_paragraph('3. Check the agreement checkbox', style='List Number')
    doc.add_paragraph('4. Click "Proceed to Payment"', style='List Number')
    
    doc.add_paragraph()
    
    if os.path.exists("sop_screenshots/10_step4_checked.png"):
        doc.add_picture("sop_screenshots/10_step4_checked.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 5: Agreement Page')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_page_break()
    
    # ============ PAYMENT PROCESSING ============
    doc.add_heading('Payment Processing', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'After clicking "Proceed to Payment", you will be directed to our secure '
        'payment processor. Complete your payment using your selected method.'
    )
    doc.add_paragraph()
    doc.add_paragraph('Once payment is confirmed, you will see a confirmation message.')
    
    doc.add_page_break()
    
    # ============ WELCOME PAGE ============
    doc.add_heading('Welcome Page', level=1)
    doc.add_paragraph()
    doc.add_paragraph(
        'After successful payment, you will see the Welcome page. '
        'This page confirms your registration is complete.'
    )
    doc.add_paragraph()
    doc.add_paragraph('Click the "Go to Client Portal" button to continue.')
    
    doc.add_paragraph()
    
    if os.path.exists("sop_screenshots/12_welcome_page.png"):
        doc.add_picture("sop_screenshots/12_welcome_page.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 6: Welcome Page')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_page_break()
    
    # ============ CREATE PASSWORD ============
    doc.add_heading('Create Your Password', level=1)
    doc.add_paragraph()
    doc.add_paragraph('You will be prompted to create a password for your Client Portal account.')
    doc.add_paragraph()
    
    doc.add_heading('Password Requirements:', level=2)
    doc.add_paragraph('• At least 8 characters', style='List Bullet')
    doc.add_paragraph('• At least one uppercase letter', style='List Bullet')
    doc.add_paragraph('• At least one number', style='List Bullet')
    doc.add_paragraph('• At least one special character', style='List Bullet')
    
    doc.add_paragraph()
    doc.add_paragraph('Enter your password twice to confirm, then click "Create Account".')
    
    doc.add_page_break()
    
    # ============ CLIENT PORTAL LOGIN ============
    doc.add_heading('Client Portal Login', level=1)
    doc.add_paragraph()
    doc.add_paragraph('You can now log into your Client Portal.')
    doc.add_paragraph()
    
    doc.add_heading('To log in:', level=2)
    doc.add_paragraph('1. Go to the Client Portal login page', style='List Number')
    doc.add_paragraph('2. Enter your email address', style='List Number')
    doc.add_paragraph('3. Enter your password', style='List Number')
    doc.add_paragraph('4. Click "Login"', style='List Number')
    
    doc.add_paragraph()
    
    if os.path.exists("sop_screenshots/13_portal_login.png"):
        doc.add_picture("sop_screenshots/13_portal_login.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 7: Client Portal Login')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_paragraph()
    doc.add_paragraph(
        'Once logged in, you will see your Client Portal Dashboard where you can '
        'track your case progress, view documents, and communicate with your case manager.'
    )
    
    doc.add_paragraph()
    
    if os.path.exists("sop_screenshots/14_portal_dashboard.png"):
        doc.add_picture("sop_screenshots/14_portal_dashboard.png", width=Inches(5.5))
        caption = doc.add_paragraph('Figure 8: Client Portal Dashboard')
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.runs[0].font.italic = True
    
    doc.add_page_break()
    
    # ============ WHAT'S NEXT ============
    doc.add_heading("What's Next?", level=1)
    doc.add_paragraph()
    doc.add_paragraph('After completing registration:')
    doc.add_paragraph()
    doc.add_paragraph('1. Check your email for a welcome message', style='List Number')
    doc.add_paragraph('2. Log into your Client Portal regularly to check updates', style='List Number')
    doc.add_paragraph('3. Our team will analyze your credit report', style='List Number')
    doc.add_paragraph('4. You will receive a separate SOP for navigating the Client Portal', style='List Number')
    
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
    print("✅ Complete SOP created: Client_Signup_SOP_Complete.docx")

create_complete_sop()
```

---

## STEP 4: Run everything

```bash
# Start app
CI=true python app.py &
sleep 3

# Install python-docx if needed
pip install python-docx --break-system-packages

# Capture screenshots
python3 capture_screenshots.py

# Create SOP
python3 create_sop.py

# Copy to outputs
cp Client_Signup_SOP_Complete.docx /mnt/user-data/outputs/
```

---

## VERIFICATION CHECKLIST

The final SOP must include:

- [ ] Full-page screenshots (not cut off)
- [ ] Step 2: All 10 credit monitoring companies listed
- [ ] Step 2: Screenshot showing dropdown with all 10 options
- [ ] Step 3: All 6 plans with correct prices
- [ ] Step 3: All 6 payment methods
- [ ] Flow continues past submit to Welcome page
- [ ] Create Password step
- [ ] Client Portal login
- [ ] Client Portal dashboard

---

## ⚠️ IMPORTANT ⚠️

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   1. UPDATE signup form with 10 credit companies                 ║
║   2. UPDATE signup form with 6 plans + prices                    ║
║   3. UPDATE signup form with 6 payment methods                   ║
║   4. CAPTURE full journey screenshots                            ║
║   5. CREATE Word doc with complete flow                          ║
║                                                                  ║
║   THE SOP MUST GO FROM SIGNUP TO CLIENT PORTAL LOGIN             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**CREATE THE COMPLETE CLIENT SIGNUP SOP.**
