# BAG/FCRA E-Signature System Implementation Guide

## Legal Compliance Summary

This system implements **legally binding electronic signatures** in compliance with:

| Law | Citation | Requirement | How We Comply |
|-----|----------|-------------|---------------|
| **ESIGN Act** | 15 U.S.C. § 7001 | Federal e-signature validity | Full consent flow, intent capture, audit trail |
| **UETA** | State-level | State e-signature validity | Adopted by 49 states, same requirements as ESIGN |
| **CROA** | 15 U.S.C. § 1679 | Rights disclosure first, 3-day cancel | Enforced signing order, cancellation tracking |

---

## Four Legal Requirements Met

### 1. Intent to Sign ✓
- Explicit checkbox: "I intend this to be my legally binding signature"
- Typed name must match name on file
- Click "Sign Document" button required

### 2. Consent to Electronic Transactions ✓
- Full ESIGN disclosure presented BEFORE any documents
- Three required acknowledgments:
  - Hardware/software requirements
  - Right to paper copies
  - Right to withdraw consent
- Consent recorded with timestamp, IP, user agent

### 3. Attribution ✓
- Signer identity captured:
  - IP address
  - User agent
  - Device fingerprint
  - Email (verified)
  - Timestamp to the second

### 4. Record Retention ✓
- Signed documents stored permanently
- PDF copies emailed to client
- Portal access to download anytime
- Signature certificates generated

---

## Tamper-Evidence (SHA-256 Hashing)

Every signed document includes:

```python
document_hash_sha256 = hashlib.sha256(document_html.encode('utf-8')).hexdigest()
```

This hash is:
- Computed at signing time
- Stored in database
- Embedded in PDF
- Included in certificate
- Used to verify document integrity

**If anyone modifies the document after signing, the hash won't match → PROOF OF TAMPERING**

---

## Complete Audit Trail

Every action is logged with:

| Field | Description |
|-------|-------------|
| `timestamp` | UTC timestamp to the millisecond |
| `action` | What happened (consent_given, document_signed, etc.) |
| `ip_address` | Client's IP address |
| `user_agent` | Browser/device info |
| `details` | JSON with additional context |
| `request_data` | Sanitized raw request for evidence |

### Logged Actions:
1. `session_initiated`
2. `consent_page_viewed`
3. `esign_consent_given`
4. `documents_presented`
5. `document_reviewed`
6. `signature_field_focused`
7. `signature_entered`
8. `intent_confirmed`
9. `document_signed`
10. `pdf_generated`
11. `session_completed`
12. `documents_emailed`

---

## Database Schema

```
clients
├── id, uuid, name, email, phone, address
├── email_verified, email_verification_token
└── created_at, updated_at

signature_sessions
├── session_uuid, client_id, status
├── esign_consent_given, esign_consent_timestamp
├── hardware_software_acknowledged
├── paper_copy_right_acknowledged
├── consent_withdrawal_acknowledged
├── ip_address, user_agent, device_fingerprint
└── initiated_at, consent_at, completed_at

signed_documents
├── document_uuid, client_id, session_id, template_id
├── document_html, document_pdf
├── document_hash_sha256, document_hash_algorithm
├── signature_type, signature_value
├── intent_checkbox_checked, intent_statement
├── signer_name, signer_email, signer_ip, signer_user_agent
├── document_presented_at, signature_timestamp
├── review_duration_seconds, scrolled_to_bottom
├── certificate_number, certificate_pdf
└── status (signed, voided, superseded)

signature_audit_logs
├── session_id, document_id
├── action, action_details
├── ip_address, user_agent
├── timestamp, raw_request_data

croa_compliance_tracker
├── client_id
├── rights_disclosure_signed, rights_disclosure_signed_at
├── contract_package_signed, contract_package_signed_at
├── cancellation_period_start, cancellation_period_end
├── cancellation_period_complete
├── client_cancelled, client_cancelled_at
└── work_can_begin, work_began_at
```

---

## API Endpoints

### Session Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/esign/session/initiate` | Start signing session |
| GET | `/api/esign/session/{uuid}/consent` | Get consent disclosure |
| POST | `/api/esign/session/{uuid}/consent` | Submit consent |
| GET | `/api/esign/session/{uuid}/documents` | Get documents to sign |
| POST | `/api/esign/session/{uuid}/complete` | Complete session |

### Document Signing
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/esign/session/{uuid}/document/{id}/review` | Record document review |
| POST | `/api/esign/session/{uuid}/document/{id}/sign` | Sign document |

### Verification & Audit
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/esign/session/{uuid}/audit-trail` | Get complete audit trail |
| GET | `/api/esign/document/{uuid}/verify` | Verify document integrity |

---

## Integration with Existing BAG/FCRA System

### File Locations

```
bag-fcra-platform/
├── app/
│   ├── routes/
│   │   ├── esign.py          # NEW - E-signature routes
│   │   └── ...existing routes
│   ├── models/
│   │   ├── esign_models.py   # NEW - E-signature models
│   │   └── ...existing models
│   └── utils/
│       ├── pdf_generator.py  # NEW - Signed PDF generation
│       ├── business_days.py  # NEW - CROA calendar calc
│       └── ...existing utils
├── frontend/
│   └── components/
│       ├── SigningComponents.jsx  # NEW - Signing UI
│       └── ...existing components
└── prompts/
    ├── FCRA_PROMPT_00_CROA_INTAKE.md  # Already created
    └── ...existing prompts
```

### Registration (app/__init__.py)

```python
from routes.esign import esign_bp
app.register_blueprint(esign_bp)
```

### Database Migration

```bash
flask db migrate -m "Add e-signature tables"
flask db upgrade
```

---

## CROA-Specific Implementation

### Signing Order Enforcement

```python
# In sign_document route:
if not template.must_sign_before_contract:
    rights_disclosure = SignedDocument.query.join(DocumentTemplate).filter(
        SignedDocument.session_id == session.id,
        DocumentTemplate.must_sign_before_contract == True
    ).first()

    if not rights_disclosure:
        return jsonify({
            'error': 'Consumer Credit File Rights Disclosure must be signed first',
            'code': 'RIGHTS_DISCLOSURE_REQUIRED'
        }), 400
```

### 3-Business-Day Cancellation Calculation

```python
from utils.business_days import add_business_days

# Contract signed Monday Dec 16, 2024 at 2:30 PM
contract_signed = datetime(2024, 12, 16, 14, 30, 0)

# Day 1 = Tuesday Dec 17
# Day 2 = Wednesday Dec 18
# Day 3 = Thursday Dec 19
cancellation_end = add_business_days(contract_signed, 3)
# Result: Thursday Dec 19, 2024 at 11:59:59 PM

# Work can begin Friday Dec 20, 2024
```

---

## PDF Certificate Example

Each signed document includes an embedded signature block:

```
┌─────────────────────────────────────────────────┐
│ ELECTRONIC SIGNATURE                            │
├─────────────────────────────────────────────────┤
│                                                 │
│  John Smith                      December 24,   │
│  ─────────────────               2024           │
│  Signature                       Date           │
│                                                 │
├─────────────────────────────────────────────────┤
│ ELECTRONIC SIGNATURE CERTIFICATE                │
│                                                 │
│ Certificate Number: BAG-20241224-A3F8B2C1      │
│ Signed By:         John Smith                   │
│ Signature Time:    December 24, 2024 2:30:15 PM │
│ Document Hash:     a3f8b2c1d4e5f6a7b8c9d0e1... │
│                                                 │
│ This document was electronically signed in      │
│ compliance with the ESIGN Act (15 U.S.C. § 7001)│
│ and UETA. The signature is legally binding.     │
└─────────────────────────────────────────────────┘
```

---

## Standalone Certificate PDF

A separate certificate is generated for each signature containing:

- Certificate number (unique identifier)
- Document name
- Signer name and email
- Signature date/time
- IP address at signing
- SHA-256 document hash
- Verification status
- Legal notice confirming ESIGN/UETA compliance

---

## Testing Checklist

### Consent Flow
- [ ] Consent page loads correctly
- [ ] All 3 acknowledgments required before proceeding
- [ ] Consent recorded with IP, timestamp, user agent
- [ ] Audit log created for consent

### Document Review
- [ ] Rights Disclosure presented first
- [ ] Cannot sign contract before Rights Disclosure
- [ ] Scroll tracking works
- [ ] Minimum review time enforced

### Signature Capture
- [ ] Typed name must match client name
- [ ] Intent checkbox required
- [ ] Signature preview displays
- [ ] Document hash computed correctly

### PDF Generation
- [ ] Signature block embedded in document
- [ ] Certificate number included
- [ ] Hash displayed in document
- [ ] WeasyPrint renders correctly

### CROA Compliance
- [ ] 3-business-day calculation correct
- [ ] Federal holidays excluded
- [ ] Work blocked during cancellation period
- [ ] Cancellation tracking works

### Audit Trail
- [ ] All actions logged
- [ ] IP addresses captured
- [ ] Timestamps precise
- [ ] Audit trail exportable

---

## Production Deployment Notes

### Environment Variables

```bash
DATABASE_URL=postgresql://...
SECRET_KEY=<secure-random-key>
ESIGN_CERT_PREFIX=BAG
ESIGN_VERSION=1.0
```

### Security Requirements

1. **HTTPS Required** - All traffic must be encrypted
2. **Database Encryption** - Sensitive fields encrypted at rest
3. **Access Logging** - All API access logged
4. **Backup Strategy** - Daily backups of signed documents
5. **Retention Policy** - Keep signatures 7+ years (legal requirement)

### Rate Limiting

```python
# Prevent abuse
@limiter.limit("10 per minute")
def sign_document():
    ...
```

---

## Summary

This e-signature system provides:

✅ **Full ESIGN Act compliance** (15 U.S.C. § 7001)
✅ **Full UETA compliance** (49 states)
✅ **CROA integration** (Rights Disclosure first, 3-day cancel)
✅ **Tamper-evident documents** (SHA-256 hashing)
✅ **Complete audit trail** (every action logged)
✅ **Signature certificates** (legal evidence)
✅ **PDF generation** (WeasyPrint)
✅ **React frontend** (client portal integration)
✅ **Flask backend** (fits existing architecture)

**No third-party e-sign services needed - fully integrated into BAG/FCRA platform.**
