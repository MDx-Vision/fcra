# SendCertified Setup Guide

> Instructions for setting up certified mail integration with SendCertifiedMail.com

---

## Current Status

| Step | Status | Notes |
|------|--------|-------|
| IP Whitelisted | ✅ Done | Claudia confirmed |
| Mailing Profile Created | ⏳ Pending | You do in portal |
| Test Work Order Submitted | ⏳ Pending | You do in portal |
| SFTP Credentials Received | ⏳ Waiting | Claudia sends after test |
| SFTP Configured & Tested | ⏳ Waiting | Claude configures |

---

## Step 1: Create Mailing Profile (Return Address)

The return address is the **client's address** (they're the sender disputing their credit).

1. Log into SendCertified portal
2. **Red Navigation Bar** → **Management** → **Mailing Profiles** → **Add New**
3. Enter test client info:
   ```
   Name: John Smith
   Address: 123 Main Street
   City: Brooklyn
   State: NY
   ZIP: 11201
   ```
4. **Save and note the ID number** (e.g., `1`, `2`, etc.)

> ⚠️ Each mailing profile gets a unique ID. This ID goes in your address list CSV.

---

## Step 2: Prepare Test Files

### Address List CSV

Location: `/static/test_files/sendcertified_address_list.csv`

```csv
letter_id,recipient_name,address1,address2,city,state,zip,return_address_id
TEST001,Equifax Information Services LLC,P.O. Box 740256,,Atlanta,GA,30374-0256,1
TEST002,Experian,P.O. Box 4500,,Allen,TX,75013,1
TEST003,TransUnion LLC,Consumer Dispute Center,P.O. Box 2000,Chester,PA,19016,1
```

**Important:** Change `return_address_id` column to match your mailing profile ID from Step 1.

### Sample Dispute Letter PDF

Location: `/static/test_files/sample_dispute_letter.pdf`

A sample FCRA dispute letter addressed to Equifax.

---

## Step 3: Submit Test Work Order

1. Log into SendCertified portal
2. **Red Navigation Bar** → **Address Letters** → **Submit Custom Work Order**
3. Fill out the form:
   - Select: **"Test/Proof data only"**
   - Select: **"Full service print and mail"**
   - Upload: Address list CSV
   - Upload: Sample PDF letter
4. Submit

> Note: Claudia mentioned she'll leave notes that you'll upload additional letter files to FTP server.

---

## Step 4: Receive SFTP Credentials

After Claudia reviews your test submission, she will send:

- SFTP Host
- SFTP Username
- SFTP Password
- SFTP Port (usually 22)
- Upload folder path
- Tracking download folder path

---

## Step 5: Configure SFTP in Platform

Once you have credentials, share them with Claude to configure:

### Environment Variables Needed

```
SENDCERTIFIED_SFTP_HOST=<host>
SENDCERTIFIED_SFTP_USERNAME=<username>
SENDCERTIFIED_SFTP_PASSWORD=<password>
SENDCERTIFIED_SFTP_PORT=22
```

### Files That Handle SFTP

- `services/sendcertified_sftp_service.py` - Batch upload via SFTP
- `services/sendcertified_service.py` - API integration
- `services/certified_mail_service.py` - High-level mail service

---

## Bureau Addresses (Built-in)

The platform already knows these addresses:

| Bureau | Address |
|--------|---------|
| **Equifax** | P.O. Box 740256, Atlanta, GA 30374-0256 |
| **Experian** | P.O. Box 4500, Allen, TX 75013 |
| **TransUnion** | P.O. Box 2000, Chester, PA 19016 |

---

## Cost Information

SendCertified pricing: **$11.00 per letter**
- Includes: Printing, certified mail, return receipt electronic

---

## Contact

**Claudia Wood** - SendCertified Support
- Handles IP whitelisting
- Sends SFTP credentials
- Reviews test submissions

---

## Download Test Files

From your running app:

```
/static/test_files/sendcertified_address_list.csv
/static/test_files/sample_dispute_letter.pdf
```

---

*Last updated: 2026-01-01*
