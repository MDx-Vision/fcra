"""
CROA Document Loader Script
Run this after saving all 7 Word docs as "Web Page, Filtered" (.htm files)

Usage:
1. Save your 7 Word docs as .htm files in a folder
2. Update DOCS_FOLDER path below
3. Run: python load_croa_documents.py
"""

import os
from datetime import date

# =============================================================================
# CONFIGURATION - UPDATE THIS PATH
# =============================================================================

DOCS_FOLDER = "/Users/rafaelrodriguez/fcra/docs/htm"  # Your CROA documents folder

# =============================================================================
# DOCUMENT DEFINITIONS (in signing order)
# =============================================================================

DOCUMENTS = [
    {
        "code": "CROA_01_RIGHTS_DISCLOSURE",
        "name": "Consumer Credit File Rights Disclosure",
        "description": "Required disclosure of your rights under federal law (CROA § 1679c)",
        "filename": "CROA_01_RIGHTS_DISCLOSURE.html",
        "must_sign_before_contract": True,  # ONLY this one is True
        "signing_order": 1,
    },
    {
        "code": "CROA_02_LPOA",
        "name": "Limited Power of Attorney",
        "description": "Authorization for us to communicate with credit bureaus on your behalf",
        "filename": "CROA_02_LPOA.html",
        "must_sign_before_contract": False,
        "signing_order": 2,
    },
    {
        "code": "CROA_03_SERVICE_AGREEMENT",
        "name": "Service Agreement",
        "description": "Terms, conditions, and fee structure for services",
        "filename": "CROA_03_SERVICE_AGREEMENT.html",
        "must_sign_before_contract": False,
        "signing_order": 3,
    },
    {
        "code": "CROA_04_CANCELLATION_NOTICE",
        "name": "Notice of Right to Cancel",
        "description": "Your 3-business-day cancellation rights under CROA",
        "filename": "CROA_04_CANCELLATION_NOTICE.html",
        "must_sign_before_contract": False,
        "signing_order": 4,
    },
    {
        "code": "CROA_05_SERVICE_COMPLETION",
        "name": "Service Completion Authorization",
        "description": "Authorization to begin work after cancellation period",
        "filename": "CROA_05_SERVICE_COMPLETION.html",
        "must_sign_before_contract": False,
        "signing_order": 5,
    },
    {
        "code": "CROA_06_HIPAA",
        "name": "HIPAA Authorization",
        "description": "Authorization to access health-related information if applicable",
        "filename": "CROA_06_HIPAA.html",
        "must_sign_before_contract": False,
        "signing_order": 6,
    },
    {
        "code": "CROA_07_WELCOME_PACKET",
        "name": "Client Welcome Packet",
        "description": "Welcome information and next steps",
        "filename": "CROA_07_WELCOME_PACKET.html",
        "must_sign_before_contract": False,
        "signing_order": 7,
    },
]


def clean_html(html_content):
    """Remove unnecessary Word artifacts from HTML"""
    import re
    
    # Remove XML declarations
    html_content = re.sub(r'<\?xml[^>]*\?>', '', html_content)
    
    # Remove Word-specific meta tags
    html_content = re.sub(r'<meta[^>]*ProgId[^>]*>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<meta[^>]*Generator[^>]*>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<meta[^>]*Originator[^>]*>', '', html_content, flags=re.IGNORECASE)
    
    # Remove Word namespace declarations
    html_content = re.sub(r'xmlns:[a-z]+="[^"]*"', '', html_content, flags=re.IGNORECASE)
    
    # Remove mso- styles (Microsoft Office specific)
    html_content = re.sub(r'mso-[^;:"]+:[^;:"]+;?', '', html_content)
    
    # Remove empty style attributes
    html_content = re.sub(r'style="\s*"', '', html_content)
    
    # Remove Word-specific class names
    html_content = re.sub(r'class="Mso[^"]*"', '', html_content)
    
    # Clean up extra whitespace
    html_content = re.sub(r'\s+', ' ', html_content)
    
    return html_content.strip()


def extract_body_content(html_content):
    """Extract just the body content, not full HTML document"""
    import re
    
    # Try to extract body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    if body_match:
        return body_match.group(1).strip()
    
    return html_content


def load_documents():
    """Load all CROA documents into database"""

    # Import database modules
    try:
        from database import SessionLocal, DocumentTemplate, Base, engine
    except ImportError as e:
        print(f"ERROR: Cannot import required modules: {e}")
        print("Make sure you're running this from your project root directory.")
        print("And ensure DATABASE_URL is set.")
        return

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        loaded = 0
        skipped = 0
        errors = 0

        for doc in DOCUMENTS:
            filepath = os.path.join(DOCS_FOLDER, doc["filename"])

            # Check if file exists
            if not os.path.exists(filepath):
                print(f"❌ FILE NOT FOUND: {filepath}")
                errors += 1
                continue

            # Check if already exists in database
            existing = db.query(DocumentTemplate).filter_by(code=doc["code"]).first()
            if existing:
                print(f"⏭️  SKIPPED (already exists): {doc['name']}")
                skipped += 1
                continue

            # Read and clean HTML
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_html = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='latin-1') as f:
                    raw_html = f.read()

            cleaned_html = clean_html(raw_html)
            body_content = extract_body_content(cleaned_html)

            # Create database record
            template = DocumentTemplate(
                code=doc["code"],
                name=doc["name"],
                description=doc["description"],
                content_html=body_content,
                must_sign_before_contract=doc["must_sign_before_contract"],
                is_croa_required=True,
                signing_order=doc["signing_order"],
                effective_date=date.today(),
                is_active=True,
                version="1.0"
            )

            db.add(template)
            print(f"✅ LOADED: {doc['name']}")
            loaded += 1

        # Commit all changes
        if loaded > 0:
            db.commit()

        print("\n" + "=" * 50)
        print(f"SUMMARY:")
        print(f"  ✅ Loaded:  {loaded}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  ❌ Errors:  {errors}")
        print("=" * 50)

        if loaded > 0:
            print("\n🎉 Documents ready for e-signature system!")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("CROA DOCUMENT LOADER")
    print("=" * 50)
    print(f"\nLooking for .html files in: {DOCS_FOLDER}\n")

    if DOCS_FOLDER == "/path/to/your/htm/files":
        print("❌ ERROR: Update DOCS_FOLDER path first!")
        print("   Edit this script and change line 14")
    else:
        load_documents()
