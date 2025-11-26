"""
OCR Service for extracting data from CRA response documents and collection letters.
Uses Claude (Anthropic API) for document analysis and data extraction.
"""
import os
import json
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from anthropic import Anthropic
from database import SessionLocal, ClientUpload

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get('FCRA Automation Secure', '')
if not ANTHROPIC_API_KEY or len(ANTHROPIC_API_KEY) < 20:
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

_anthropic_client = None

def get_anthropic_client() -> Optional[Anthropic]:
    """Get or create Anthropic client instance."""
    global _anthropic_client
    if _anthropic_client is None:
        if ANTHROPIC_API_KEY and len(ANTHROPIC_API_KEY) >= 20 and 'invalid' not in ANTHROPIC_API_KEY.lower():
            try:
                _anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                logger.info("OCR Service: Anthropic client initialized")
            except Exception as e:
                logger.error(f"OCR Service: Failed to initialize Anthropic client: {e}")
                return None
        else:
            logger.warning("OCR Service: Invalid or missing Anthropic API key")
            return None
    return _anthropic_client


def _load_image_as_base64(file_path: str) -> Optional[str]:
    """Load an image file and return its base64 encoding."""
    try:
        with open(file_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to load image {file_path}: {e}")
        return None


def _get_media_type(file_path: str, file_type: str) -> str:
    """Determine the media type for an image file."""
    ext = file_type.lower() if file_type else file_path.lower().split('.')[-1]
    media_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')


def _extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts) if text_parts else None
    except ImportError:
        logger.warning("pypdf not available, trying PyPDF2")
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts) if text_parts else None
        except ImportError:
            logger.error("No PDF reading library available (pypdf or PyPDF2)")
            return None
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {e}")
        return None


def _convert_pdf_to_images(file_path: str) -> Optional[List[str]]:
    """Convert PDF pages to images and return base64 encoded images."""
    try:
        from pdf2image import convert_from_path
        import tempfile
        
        images = convert_from_path(file_path, dpi=150, first_page=1, last_page=5)
        base64_images = []
        
        for i, img in enumerate(images):
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name, 'PNG')
                with open(tmp.name, 'rb') as f:
                    base64_images.append(base64.standard_b64encode(f.read()).decode('utf-8'))
                os.unlink(tmp.name)
        
        return base64_images if base64_images else None
    except ImportError:
        logger.warning("pdf2image not available, falling back to text extraction")
        return None
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        return None


CRA_RESPONSE_PROMPT = """You are an expert at analyzing Credit Reporting Agency (CRA) response documents.
Analyze this document and extract the following information in JSON format.

IMPORTANT: Return ONLY valid JSON, no additional text or explanation.

Extract:
{
    "bureau_name": "Equifax" | "Experian" | "TransUnion" | null,
    "response_type": "Results of Investigation" | "Verification Passed" | "Item Deleted" | "Account Updated" | "Dispute Processed" | "Frivolous" | "Other",
    "response_type_detail": "detailed description of the response type",
    "response_date": "YYYY-MM-DD format or null",
    "acdv_reference_number": "reference number if present or null",
    "account_details": [
        {
            "creditor_name": "name",
            "account_number": "masked account number",
            "status": "verified" | "deleted" | "updated" | "disputed",
            "changes_made": "description of changes if any"
        }
    ],
    "items_disputed": ["list of disputed items"],
    "items_verified": ["list of verified items - no changes"],
    "items_updated": ["list of items that were updated/corrected"],
    "items_deleted": ["list of deleted items"],
    "investigation_summary": "brief summary of the investigation results",
    "next_steps_recommended": ["recommended actions based on this response"],
    "raw_text_extracted": "key text from the document",
    "confidence_score": 0.0 to 1.0
}

If the bureau name is provided separately, use: {bureau_hint}

Analyze the document carefully and extract all relevant information."""


COLLECTION_LETTER_PROMPT = """You are an expert at analyzing collection letters and identifying potential FDCPA violations.
Analyze this collection letter and extract the following information in JSON format.

IMPORTANT: Return ONLY valid JSON, no additional text or explanation.

Extract:
{
    "collection_agency_name": "name of the collection agency",
    "original_creditor": "original creditor name if different from collection agency",
    "account_number": "account number (may be masked)",
    "amount_claimed": 0.00,
    "date_of_letter": "YYYY-MM-DD format or null",
    "debt_type": "credit card" | "medical" | "utility" | "auto" | "student loan" | "other",
    "threat_of_legal_action": true | false,
    "legal_action_details": "details if legal action threatened",
    "validation_notice_included": true | false,
    "dispute_instructions_included": true | false,
    "mini_miranda_included": true | false,
    "fdcpa_violations_detected": [
        {
            "violation_type": "type of violation",
            "description": "detailed description",
            "section": "FDCPA section reference",
            "severity": "high" | "medium" | "low",
            "confidence": 0.0 to 1.0
        }
    ],
    "recommended_response": "suggested response strategy",
    "urgency_level": "immediate" | "within_30_days" | "standard",
    "key_dates": {
        "debt_date": "YYYY-MM-DD or null",
        "last_payment_date": "YYYY-MM-DD or null",
        "statute_of_limitations_concern": true | false
    },
    "raw_text_extracted": "key text from the letter",
    "confidence_score": 0.0 to 1.0
}

Common FDCPA violations to look for:
1. Failure to provide validation notice (30-day notice)
2. Threatening arrest or imprisonment
3. Misrepresenting the amount owed
4. Using obscene or profane language
5. Threatening to take actions that cannot legally be taken
6. Communicating with third parties about the debt
7. Calling at unreasonable hours
8. Failing to identify as debt collector
9. False representation of legal status
10. Adding unauthorized fees or charges

Analyze carefully and identify any potential violations."""


FCRA_VIOLATION_ANALYSIS_PROMPT = """You are an FCRA (Fair Credit Reporting Act) compliance expert.
Analyze the provided document data for potential FCRA violations.

Document Type: {document_type}
Document Data:
{document_data}

Identify potential FCRA violations and return in JSON format.

IMPORTANT: Return ONLY valid JSON, no additional text or explanation.

{
    "violations_detected": [
        {
            "violation_type": "type of violation",
            "fcra_section": "relevant FCRA section (e.g., 611, 623, 605)",
            "description": "detailed description of the violation",
            "evidence": "specific evidence from the document",
            "severity": "critical" | "high" | "medium" | "low",
            "confidence_score": 0.0 to 1.0,
            "statutory_damages_range": {
                "min": 0,
                "max": 0
            },
            "willfulness_indicator": true | false,
            "willfulness_reasoning": "reasoning if willful"
        }
    ],
    "overall_violation_count": 0,
    "highest_severity": "critical" | "high" | "medium" | "low" | "none",
    "total_potential_damages": {
        "statutory_min": 0,
        "statutory_max": 0
    },
    "recommended_actions": ["list of recommended legal or dispute actions"],
    "litigation_worthiness": {
        "score": 0 to 10,
        "reasoning": "explanation of litigation potential"
    }
}

Common FCRA violations to identify:
1. §611: Failure to investigate disputed information within 30 days
2. §611: Reporting after dispute without proper investigation
3. §611: Failure to mark account as "disputed" during investigation
4. §623: Furnishing inaccurate information after notice of dispute
5. §605: Re-aging of accounts (changing dates to extend reporting period)
6. §605: Reporting obsolete information (beyond 7-year limit)
7. §609: Failure to disclose file contents upon request
8. §604: Obtaining credit report without permissible purpose

Analyze thoroughly and identify all potential violations with supporting evidence."""


def extract_cra_response_data(
    file_path: str, 
    file_type: str, 
    bureau: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract data from CRA (Credit Reporting Agency) response documents.
    
    Args:
        file_path: Path to the image (jpg/png) or PDF file
        file_type: File type (jpg, png, pdf)
        bureau: Optional bureau name hint (Equifax, Experian, TransUnion)
    
    Returns:
        Dictionary with extracted data or error information
    """
    client = get_anthropic_client()
    if not client:
        return {
            "success": False,
            "error": "Anthropic API client not available",
            "data": None
        }
    
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "data": None
        }
    
    try:
        file_type_lower = file_type.lower() if file_type else file_path.lower().split('.')[-1]
        bureau_hint = f"Bureau: {bureau}" if bureau else "Bureau not specified - detect from document"
        prompt = CRA_RESPONSE_PROMPT.replace("{bureau_hint}", bureau_hint)
        
        messages_content = []
        
        if file_type_lower == 'pdf':
            pdf_images = _convert_pdf_to_images(file_path)
            if pdf_images:
                for img_base64 in pdf_images:
                    messages_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    })
            else:
                pdf_text = _extract_text_from_pdf(file_path)
                if pdf_text:
                    messages_content.append({
                        "type": "text",
                        "text": f"Document Text Content:\n\n{pdf_text}"
                    })
                else:
                    return {
                        "success": False,
                        "error": "Could not extract content from PDF",
                        "data": None
                    }
        else:
            image_base64 = _load_image_as_base64(file_path)
            if not image_base64:
                return {
                    "success": False,
                    "error": "Could not load image file",
                    "data": None
                }
            messages_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": _get_media_type(file_path, file_type),
                    "data": image_base64
                }
            })
        
        messages_content.append({
            "type": "text",
            "text": prompt
        })
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{
                "role": "user",
                "content": messages_content
            }]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as je:
            logger.warning(f"Failed to parse JSON response, attempting repair: {je}")
            extracted_data = {
                "raw_response": response_text,
                "parse_error": str(je),
                "confidence_score": 0.5
            }
        
        return {
            "success": True,
            "error": None,
            "data": extracted_data,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }
        
    except Exception as e:
        logger.error(f"Error extracting CRA response data: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


def analyze_collection_letter(
    file_path: str, 
    file_type: str
) -> Dict[str, Any]:
    """
    Analyze a collection letter for key information and FDCPA violations.
    
    Args:
        file_path: Path to the image (jpg/png) or PDF file
        file_type: File type (jpg, png, pdf)
    
    Returns:
        Dictionary with extracted data and detected violations
    """
    client = get_anthropic_client()
    if not client:
        return {
            "success": False,
            "error": "Anthropic API client not available",
            "data": None
        }
    
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "data": None
        }
    
    try:
        file_type_lower = file_type.lower() if file_type else file_path.lower().split('.')[-1]
        
        messages_content = []
        
        if file_type_lower == 'pdf':
            pdf_images = _convert_pdf_to_images(file_path)
            if pdf_images:
                for img_base64 in pdf_images:
                    messages_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    })
            else:
                pdf_text = _extract_text_from_pdf(file_path)
                if pdf_text:
                    messages_content.append({
                        "type": "text",
                        "text": f"Collection Letter Text Content:\n\n{pdf_text}"
                    })
                else:
                    return {
                        "success": False,
                        "error": "Could not extract content from PDF",
                        "data": None
                    }
        else:
            image_base64 = _load_image_as_base64(file_path)
            if not image_base64:
                return {
                    "success": False,
                    "error": "Could not load image file",
                    "data": None
                }
            messages_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": _get_media_type(file_path, file_type),
                    "data": image_base64
                }
            })
        
        messages_content.append({
            "type": "text",
            "text": COLLECTION_LETTER_PROMPT
        })
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{
                "role": "user",
                "content": messages_content
            }]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as je:
            logger.warning(f"Failed to parse collection letter JSON: {je}")
            extracted_data = {
                "raw_response": response_text,
                "parse_error": str(je),
                "confidence_score": 0.5
            }
        
        return {
            "success": True,
            "error": None,
            "data": extracted_data,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }
        
    except Exception as e:
        logger.error(f"Error analyzing collection letter: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


def detect_fcra_violations(
    document_data: Dict[str, Any], 
    document_type: str
) -> Dict[str, Any]:
    """
    Analyze extracted document data for potential FCRA violations.
    
    Args:
        document_data: Previously extracted document data (from CRA response or other)
        document_type: Type of document (cra_response, collection_letter, credit_report)
    
    Returns:
        Dictionary with detected violations and recommendations
    """
    client = get_anthropic_client()
    if not client:
        return {
            "success": False,
            "error": "Anthropic API client not available",
            "violations": []
        }
    
    if not document_data:
        return {
            "success": False,
            "error": "No document data provided",
            "violations": []
        }
    
    try:
        prompt = FCRA_VIOLATION_ANALYSIS_PROMPT.format(
            document_type=document_type,
            document_data=json.dumps(document_data, indent=2)
        )
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = response.content[0].text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            violations_data = json.loads(response_text)
        except json.JSONDecodeError as je:
            logger.warning(f"Failed to parse violations JSON: {je}")
            violations_data = {
                "raw_response": response_text,
                "parse_error": str(je),
                "violations_detected": []
            }
        
        return {
            "success": True,
            "error": None,
            "violations": violations_data.get("violations_detected", []),
            "overall_count": violations_data.get("overall_violation_count", 0),
            "highest_severity": violations_data.get("highest_severity", "none"),
            "potential_damages": violations_data.get("total_potential_damages", {}),
            "recommended_actions": violations_data.get("recommended_actions", []),
            "litigation_worthiness": violations_data.get("litigation_worthiness", {}),
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }
        
    except Exception as e:
        logger.error(f"Error detecting FCRA violations: {e}")
        return {
            "success": False,
            "error": str(e),
            "violations": []
        }


def update_client_upload_ocr(
    upload_id: int, 
    ocr_data: Dict[str, Any]
) -> bool:
    """
    Update a ClientUpload record with OCR extracted data.
    
    Args:
        upload_id: ID of the ClientUpload record
        ocr_data: Extracted OCR data to store
    
    Returns:
        True if successful, False otherwise
    """
    session = SessionLocal()
    try:
        upload = session.query(ClientUpload).filter(
            ClientUpload.id == upload_id
        ).first()
        
        if not upload:
            logger.error(f"ClientUpload {upload_id} not found")
            return False
        
        upload.ocr_extracted = True
        upload.ocr_data = ocr_data
        upload.updated_at = datetime.utcnow()
        
        session.commit()
        logger.info(f"Updated ClientUpload {upload_id} with OCR data")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating ClientUpload OCR data: {e}")
        return False
    finally:
        session.close()


def process_upload_for_ocr(
    upload_id: int,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a ClientUpload for OCR extraction based on its category.
    Automatically determines the appropriate extraction function to use.
    
    Args:
        upload_id: ID of the ClientUpload record
        category: Optional category override
    
    Returns:
        Dictionary with processing results
    """
    session = SessionLocal()
    try:
        upload = session.query(ClientUpload).filter(
            ClientUpload.id == upload_id
        ).first()
        
        if not upload:
            return {
                "success": False,
                "error": f"ClientUpload {upload_id} not found"
            }
        
        file_path = upload.file_path
        file_type = upload.file_type or (file_path.split('.')[-1] if file_path else 'pdf')
        doc_category = category or upload.category
        
        if not file_path or not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        if doc_category in ['cra_response', 'bureau_response', 'dispute_result']:
            result = extract_cra_response_data(
                file_path=file_path,
                file_type=file_type,
                bureau=upload.bureau
            )
        elif doc_category in ['collection_letter', 'debt_collection', 'collection']:
            result = analyze_collection_letter(
                file_path=file_path,
                file_type=file_type
            )
        else:
            result = extract_cra_response_data(
                file_path=file_path,
                file_type=file_type,
                bureau=upload.bureau
            )
        
        if result.get("success") and result.get("data"):
            ocr_data = {
                "extracted_at": datetime.utcnow().isoformat(),
                "category": doc_category,
                "extraction_result": result["data"],
                "tokens_used": result.get("tokens_used", 0)
            }
            
            if doc_category in ['cra_response', 'bureau_response', 'dispute_result']:
                violations_result = detect_fcra_violations(
                    document_data=result["data"],
                    document_type="cra_response"
                )
                if violations_result.get("success"):
                    ocr_data["violations_analysis"] = {
                        "violations": violations_result.get("violations", []),
                        "overall_count": violations_result.get("overall_count", 0),
                        "highest_severity": violations_result.get("highest_severity", "none"),
                        "potential_damages": violations_result.get("potential_damages", {}),
                        "recommended_actions": violations_result.get("recommended_actions", []),
                        "litigation_worthiness": violations_result.get("litigation_worthiness", {})
                    }
            
            update_success = update_client_upload_ocr(upload_id, ocr_data)
            
            return {
                "success": True,
                "upload_id": upload_id,
                "data": ocr_data,
                "db_updated": update_success
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown extraction error"),
                "upload_id": upload_id
            }
            
    except Exception as e:
        logger.error(f"Error processing upload for OCR: {e}")
        return {
            "success": False,
            "error": str(e),
            "upload_id": upload_id
        }
    finally:
        session.close()


def batch_process_uploads(
    upload_ids: List[int],
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process multiple ClientUploads for OCR extraction.
    
    Args:
        upload_ids: List of ClientUpload IDs to process
        category: Optional category override for all uploads
    
    Returns:
        Dictionary with batch processing results
    """
    results = {
        "total": len(upload_ids),
        "successful": 0,
        "failed": 0,
        "results": []
    }
    
    for upload_id in upload_ids:
        result = process_upload_for_ocr(upload_id, category)
        results["results"].append(result)
        
        if result.get("success"):
            results["successful"] += 1
        else:
            results["failed"] += 1
    
    return results
