"""
Debug Script: PDF Text Extraction Tester
=========================================
Run this in your Replit to see exactly what text is being extracted from the credit report PDF.

Usage:
    python debug_pdf_extraction.py /path/to/RRodriguez11_17_20_25.pdf
"""

import sys
import os
import re
from datetime import datetime

def debug_extract_pdf(file_path: str):
    """Extract and analyze PDF content for debugging."""
    
    print("=" * 70)
    print("PDF EXTRACTION DEBUG REPORT")
    print(f"File: {file_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if not os.path.exists(file_path):
        print(f"\n❌ ERROR: File not found: {file_path}")
        return
    
    file_size = os.path.getsize(file_path)
    print(f"\n📄 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # ==========================================================================
    # PDFPLUMBER EXTRACTION
    # ==========================================================================
    print("\n" + "=" * 70)
    print("PDFPLUMBER EXTRACTION")
    print("=" * 70)
    
    try:
        import pdfplumber
        print("✅ pdfplumber is installed")
    except ImportError:
        print("❌ pdfplumber NOT installed. Run: pip install pdfplumber")
        return
    
    all_text = []
    all_tables = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"\n📑 Total pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n--- Page {page_num} ---")
                
                # Extract text
                text = page.extract_text()
                if text:
                    print(f"  Text extracted: {len(text)} characters")
                    all_text.append(f"\n{'='*50}\nPAGE {page_num} TEXT\n{'='*50}\n{text}")
                else:
                    print(f"  ⚠️ No text extracted from page {page_num}")
                
                # Extract tables
                tables = page.extract_tables()
                print(f"  Tables found: {len(tables)}")
                
                for table_idx, table in enumerate(tables):
                    if table:
                        rows = len(table)
                        cols = max(len(row) for row in table if row) if table else 0
                        print(f"    Table {table_idx + 1}: {rows} rows x {cols} cols")
                        
                        # Store table as formatted text
                        table_text = f"\n{'='*50}\nPAGE {page_num} TABLE {table_idx + 1}\n{'='*50}\n"
                        for row in table:
                            if row:
                                row_text = " | ".join([str(cell).strip() if cell else "[empty]" for cell in row])
                                table_text += row_text + "\n"
                        all_tables.append(table_text)
    
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Combine all extracted content
    full_text = "\n".join(all_text)
    full_tables = "\n".join(all_tables)
    combined = full_text + "\n\n" + full_tables
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"   Total text characters: {len(full_text):,}")
    print(f"   Total table characters: {len(full_tables):,}")
    print(f"   Combined: {len(combined):,}")
    
    # ==========================================================================
    # SAVE DEBUG FILES
    # ==========================================================================
    print("\n" + "=" * 70)
    print("SAVING DEBUG FILES")
    print("=" * 70)
    
    debug_dir = "debug_output"
    os.makedirs(debug_dir, exist_ok=True)
    
    # Save full text
    text_file = os.path.join(debug_dir, "extracted_text.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"✅ Saved: {text_file}")
    
    # Save tables
    tables_file = os.path.join(debug_dir, "extracted_tables.txt")
    with open(tables_file, "w", encoding="utf-8") as f:
        f.write(full_tables)
    print(f"✅ Saved: {tables_file}")
    
    # Save combined
    combined_file = os.path.join(debug_dir, "combined_extraction.txt")
    with open(combined_file, "w", encoding="utf-8") as f:
        f.write(combined)
    print(f"✅ Saved: {combined_file}")
    
    # ==========================================================================
    # PATTERN ANALYSIS
    # ==========================================================================
    print("\n" + "=" * 70)
    print("PATTERN ANALYSIS - Checking for expected content")
    print("=" * 70)
    
    # Define what we expect to find
    expected_patterns = {
        # Report identifiers
        "Reference Number": r"Reference\s*#?\s*:?\s*[A-Z0-9]+",
        "Report Date": r"Report\s*Date\s*:?\s*\d{1,2}/\d{1,2}/\d{4}",
        
        # Bureau names
        "TransUnion": r"TransUnion",
        "Experian": r"Experian", 
        "Equifax": r"Equifax",
        
        # Scores (three digit numbers)
        "Credit Score 615": r"615",
        "Credit Score 528": r"528",
        "Credit Score 625": r"625",
        
        # Personal info
        "Name RAFAEL": r"RAFAEL",
        "Name RODRIGUEZ": r"RODRIGUEZ",
        "DOB 1972": r"1972",
        "Address 161ST": r"161ST",
        "Employer NICEHR": r"NICEHR",
        
        # Account names (expected creditors)
        "APPLE CARD": r"APPLE\s*CARD",
        "GS BANK": r"GS\s*BANK",
        "CAPITAL ONE": r"CAPITAL\s*ONE",
        "NAVY FEDERAL": r"NAVY\s*FEDERAL",
        "LEAD BANK": r"LEAD\s*BANK",
        "KOVO": r"KOVO",
        "AFFIRM": r"AFFIRM",
        "KLARNA": r"KLARNA",
        "SELF FINANCIAL": r"SELF\s*FINANCIAL",
        "AMEX": r"AMEX|AMERICAN\s*EXPRESS",
        
        # Payment statuses
        "30 days past due": r"30\s*days?\s*past\s*due",
        "60 days past due": r"60\s*days?\s*past\s*due",
        "Current/Agreed": r"(?:Current|Pays\s*(?:account\s*)?as\s*agreed|Paid\s*or\s*paying)",
        
        # Payment history markers
        "OK status": r"\bOK\b",
        "Payment History section": r"(?:Two-Year\s*)?[Pp]ayment\s*[Hh]istory",
        
        # Key sections
        "Personal Information": r"Personal\s*Information",
        "Credit Score section": r"Credit\s*Score",
        "Summary section": r"Summary",
        "Account History": r"Account\s*History",
        "Inquiries section": r"Inquir(?:y|ies)",
        "Public Information": r"Public\s*(?:Information|Records?)",
        "Creditor Contacts": r"Creditor\s*Contacts?",
        
        # Table structure indicators
        "Three column header": r"TransUnion\s*\|?\s*Experian\s*\|?\s*Equifax",
        "Account # field": r"Account\s*#?\s*:",
        "Balance field": r"Balance\s*:",
        "Credit Limit field": r"Credit\s*Limit\s*:",
        "Payment Status field": r"Payment\s*Status\s*:",
        "Date Opened field": r"Date\s*Opened\s*:",
    }
    
    found_count = 0
    missing = []
    
    for name, pattern in expected_patterns.items():
        matches = re.findall(pattern, combined, re.IGNORECASE)
        if matches:
            print(f"  ✅ {name}: Found {len(matches)} match(es)")
            found_count += 1
        else:
            print(f"  ❌ {name}: NOT FOUND")
            missing.append(name)
    
    print(f"\n📈 PATTERN SUMMARY:")
    print(f"   Found: {found_count}/{len(expected_patterns)}")
    print(f"   Missing: {len(missing)}")
    
    if missing:
        print(f"\n⚠️ MISSING PATTERNS (may indicate parsing issues):")
        for m in missing:
            print(f"   - {m}")
    
    # ==========================================================================
    # CREDITOR ANALYSIS
    # ==========================================================================
    print("\n" + "=" * 70)
    print("CREDITOR/ACCOUNT ANALYSIS")
    print("=" * 70)
    
    # Expected creditors from the report
    expected_creditors = [
        "APPLE CARD",
        "GS BANK", 
        "CAPITAL ONE",
        "NAVY FEDERAL",
        "LEAD BANK",
        "KOVO",
        "AFFIRM",
        "KLARNA",
        "SELF FINANCIAL",
        "AMEX",
        "SYNCB"
    ]
    
    print("\nSearching for creditor names:")
    found_creditors = []
    for creditor in expected_creditors:
        pattern = creditor.replace(" ", r"\s*")
        matches = re.findall(pattern, combined, re.IGNORECASE)
        if matches:
            print(f"  ✅ {creditor}: Found {len(matches)} times")
            found_creditors.append(creditor)
        else:
            print(f"  ❌ {creditor}: NOT FOUND")
    
    print(f"\n📊 Creditors found: {len(found_creditors)}/{len(expected_creditors)}")
    
    # ==========================================================================
    # DEROGATORY DETECTION
    # ==========================================================================
    print("\n" + "=" * 70)
    print("DEROGATORY MARKERS ANALYSIS")
    print("=" * 70)
    
    derogatory_patterns = {
        "30 days late": r"30\s*days?",
        "60 days late": r"60\s*days?",
        "90 days late": r"90\s*days?",
        "Past due": r"past\s*due",
        "Late payment": r"late\s*payment",
        "Collection": r"collection",
        "Charge off": r"charge\s*off",
        "Delinquent": r"delinquent",
        "Derogatory": r"derogatory"
    }
    
    for name, pattern in derogatory_patterns.items():
        matches = re.findall(pattern, combined, re.IGNORECASE)
        if matches:
            print(f"  ⚠️ {name}: Found {len(matches)} times")
        else:
            print(f"  ✅ {name}: None found")
    
    # ==========================================================================
    # SAMPLE CONTENT
    # ==========================================================================
    print("\n" + "=" * 70)
    print("SAMPLE EXTRACTED CONTENT (first 3000 chars)")
    print("=" * 70)
    print(combined[:3000])
    print("\n... [truncated]")
    
    # ==========================================================================
    # RECOMMENDATIONS
    # ==========================================================================
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if len(combined) < 5000:
        print("⚠️ Very little text extracted. This PDF may be:")
        print("   - Image-based (scanned document) - needs OCR")
        print("   - Password protected")
        print("   - Corrupted")
        print("\n   Recommendation: Try OCR extraction instead")
    
    if "TransUnion" in combined and "Experian" in combined and "Equifax" in combined:
        print("✅ All three bureau names found - this is a three-bureau report")
    else:
        print("⚠️ Not all bureau names found - may be single bureau or extraction issue")
    
    if len(found_creditors) < 5:
        print(f"⚠️ Only {len(found_creditors)} creditors found (expected 10+)")
        print("   - Check if table extraction is working")
        print("   - Tables may be in image format")
    
    if not re.search(r"30\s*days?\s*past\s*due", combined, re.IGNORECASE):
        print("⚠️ '30 days past due' not found - but we know Apple Card has this")
        print("   - Parser may be using wrong payment status field")
        print("   - Check raw extracted text for payment status wording")
    
    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print(f"Check the '{debug_dir}/' folder for full extracted content")
    print("=" * 70)
    
    return {
        "text_length": len(full_text),
        "tables_length": len(full_tables),
        "found_patterns": found_count,
        "missing_patterns": missing,
        "found_creditors": found_creditors
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf_extraction.py <path_to_pdf>")
        print("\nExample:")
        print("  python debug_pdf_extraction.py uploads/RRodriguez11_17_20_25.pdf")
        
        # Try to find PDF in common locations
        common_paths = [
            "uploads/",
            "static/uploads/",
            "data/",
            "./"
        ]
        
        print("\nSearching for PDF files...")
        for path in common_paths:
            if os.path.exists(path):
                pdfs = [f for f in os.listdir(path) if f.lower().endswith('.pdf')]
                if pdfs:
                    print(f"  Found in {path}: {pdfs}")
        
        return
    
    file_path = sys.argv[1]
    debug_extract_pdf(file_path)


if __name__ == "__main__":
    main()
