"""
OCR Service for extracting data from CRA response documents and collection letters.
Uses Claude (Anthropic API) for document analysis and data extraction.
Includes CRA response analysis and reinsertion violation detection.
"""

import base64
import json
import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union, cast

from anthropic import Anthropic
from anthropic.types import TextBlock

from database import (
    Client,
    ClientUpload,
    CRAResponse,
    CRAResponseOCR,
    DisputeItem,
    SessionLocal,
    Violation,
)

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("FCRA Automation Secure", "")
if not ANTHROPIC_API_KEY or len(ANTHROPIC_API_KEY) < 20:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

_anthropic_client = None


def get_anthropic_client() -> Optional[Anthropic]:
    """Get or create Anthropic client instance."""
    global _anthropic_client
    if _anthropic_client is None:
        if (
            ANTHROPIC_API_KEY
            and len(ANTHROPIC_API_KEY) >= 20
            and "invalid" not in ANTHROPIC_API_KEY.lower()
        ):
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
        with open(file_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to load image {file_path}: {e}")
        return None


def _get_media_type(file_path: str, file_type: str) -> str:
    """Determine the media type for an image file."""
    ext = file_type.lower() if file_type else file_path.lower().split(".")[-1]
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    return media_types.get(ext, "image/jpeg")


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

            with open(file_path, "rb") as f:
                reader_pyp2: Any = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader_pyp2.pages:
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
        import tempfile

        from pdf2image import convert_from_path

        images = convert_from_path(file_path, dpi=150, first_page=1, last_page=5)
        base64_images = []

        for i, img in enumerate(images):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                img.save(tmp.name, "PNG")
                with open(tmp.name, "rb") as f:
                    base64_images.append(
                        base64.standard_b64encode(f.read()).decode("utf-8")
                    )
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

This is a response from a credit bureau after a dispute was submitted. Common document types include:
- "Results of Investigation" letters
- "Reinvestigation Results"
- Account status update notices
- Frivolous dispute notifications

Extract:
{
    "bureau_name": "Equifax" | "Experian" | "TransUnion" | null,
    "response_type": "Results of Investigation" | "Verification Passed" | "Item Deleted" | "Account Updated" | "Dispute Processed" | "Frivolous" | "Other",
    "response_type_detail": "detailed description of the response type",
    "response_date": "YYYY-MM-DD format or null",
    "acdv_reference_number": "reference number if present or null",
    "confirmation_number": "dispute confirmation/reference number if present",
    "consumer_name": "name of the consumer if visible",
    "items": [
        {
            "creditor_name": "exact name of the creditor/furnisher as shown",
            "account_number": "masked/partial account number (e.g., XXXX1234)",
            "account_type": "credit card" | "auto loan" | "mortgage" | "collection" | "student loan" | "personal loan" | "other",
            "result": "deleted" | "verified" | "updated" | "investigating" | "remains",
            "result_detail": "specific outcome description (e.g., 'Account deleted per your request')",
            "reason": "reason given by bureau for the result",
            "original_dispute_reason": "what was originally disputed if mentioned",
            "changes_made": "specific changes if the item was updated (null if not updated)",
            "balance": "balance amount if shown",
            "date_opened": "account open date if shown",
            "status_before": "account status before dispute if shown",
            "status_after": "account status after dispute if shown"
        }
    ],
    "summary_counts": {
        "total_items_disputed": 0,
        "items_deleted": 0,
        "items_verified": 0,
        "items_updated": 0,
        "items_investigating": 0
    },
    "investigation_summary": "brief summary of the investigation results",
    "frivolous_warning": true | false,
    "frivolous_reason": "reason if frivolous warning present",
    "next_dispute_allowed_date": "date consumer can submit next dispute if mentioned",
    "next_steps_recommended": ["recommended actions based on this response"],
    "raw_text_extracted": "all key text from the document for reference",
    "confidence_score": 0.0 to 1.0
}

IMPORTANT EXTRACTION RULES:
1. For each account/item mentioned, extract the EXACT creditor name as shown
2. Include partial account numbers to help match with existing records
3. The "result" field must be one of: deleted, verified, updated, investigating, remains
4. If an item says "information verified as accurate" or "verified", result = "verified"
5. If an item says "deleted", "removed", or "will no longer appear", result = "deleted"
6. If an item shows changes were made but not deleted, result = "updated"
7. Extract ALL items mentioned, even if outcome is unclear

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
    file_path: str, file_type: str, bureau: Optional[str] = None
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
            "data": None,
        }

    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}", "data": None}

    try:
        file_type_lower = (
            file_type.lower() if file_type else file_path.lower().split(".")[-1]
        )
        bureau_hint = (
            f"Bureau: {bureau}"
            if bureau
            else "Bureau not specified - detect from document"
        )
        prompt = CRA_RESPONSE_PROMPT.replace("{bureau_hint}", bureau_hint)

        messages_content: List[Dict[str, Any]] = []

        if file_type_lower == "pdf":
            pdf_images = _convert_pdf_to_images(file_path)
            if pdf_images:
                for img_base64 in pdf_images:
                    messages_content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64,
                            },
                        }
                    )
            else:
                pdf_text = _extract_text_from_pdf(file_path)
                if pdf_text:
                    messages_content.append(
                        {
                            "type": "text",
                            "text": f"Document Text Content:\n\n{pdf_text}",
                        }
                    )
                else:
                    return {
                        "success": False,
                        "error": "Could not extract content from PDF",
                        "data": None,
                    }
        else:
            image_base64 = _load_image_as_base64(file_path)
            if not image_base64:
                return {
                    "success": False,
                    "error": "Could not load image file",
                    "data": None,
                }
            messages_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": _get_media_type(file_path, file_type),
                        "data": image_base64,
                    },
                }
            )

        messages_content.append({"type": "text", "text": prompt})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": messages_content}],  # type: ignore[arg-type,typeddict-item]
        )

        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            return {"success": False, "error": "Unexpected response type", "data": None}
        response_text = first_block.text.strip()

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
                "confidence_score": 0.5,
            }

        return {
            "success": True,
            "error": None,
            "data": extracted_data,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        }

    except Exception as e:
        logger.error(f"Error extracting CRA response data: {e}")
        return {"success": False, "error": str(e), "data": None}


def analyze_collection_letter(file_path: str, file_type: str) -> Dict[str, Any]:
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
            "data": None,
        }

    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}", "data": None}

    try:
        file_type_lower = (
            file_type.lower() if file_type else file_path.lower().split(".")[-1]
        )

        messages_content: List[Dict[str, Any]] = []

        if file_type_lower == "pdf":
            pdf_images = _convert_pdf_to_images(file_path)
            if pdf_images:
                for img_base64 in pdf_images:
                    messages_content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64,
                            },
                        }
                    )
            else:
                pdf_text = _extract_text_from_pdf(file_path)
                if pdf_text:
                    messages_content.append(
                        {
                            "type": "text",
                            "text": f"Collection Letter Text Content:\n\n{pdf_text}",
                        }
                    )
                else:
                    return {
                        "success": False,
                        "error": "Could not extract content from PDF",
                        "data": None,
                    }
        else:
            image_base64 = _load_image_as_base64(file_path)
            if not image_base64:
                return {
                    "success": False,
                    "error": "Could not load image file",
                    "data": None,
                }
            messages_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": _get_media_type(file_path, file_type),
                        "data": image_base64,
                    },
                }
            )

        messages_content.append({"type": "text", "text": COLLECTION_LETTER_PROMPT})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": messages_content}],  # type: ignore[arg-type,typeddict-item]
        )

        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            return {"success": False, "error": "Unexpected response type", "data": None}
        response_text = first_block.text.strip()

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
                "confidence_score": 0.5,
            }

        return {
            "success": True,
            "error": None,
            "data": extracted_data,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        }

    except Exception as e:
        logger.error(f"Error analyzing collection letter: {e}")
        return {"success": False, "error": str(e), "data": None}


def detect_fcra_violations(
    document_data: Dict[str, Any], document_type: str
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
            "violations": [],
        }

    if not document_data:
        return {
            "success": False,
            "error": "No document data provided",
            "violations": [],
        }

    try:
        prompt = FCRA_VIOLATION_ANALYSIS_PROMPT.format(
            document_type=document_type,
            document_data=json.dumps(document_data, indent=2),
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            return {
                "success": False,
                "error": "Unexpected response type",
                "violations": [],
            }
        response_text = first_block.text.strip()

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
                "violations_detected": [],
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
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
        }

    except Exception as e:
        logger.error(f"Error detecting FCRA violations: {e}")
        return {"success": False, "error": str(e), "violations": []}


def update_client_upload_ocr(upload_id: int, ocr_data: Dict[str, Any]) -> bool:
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
        upload = (
            session.query(ClientUpload).filter(ClientUpload.id == upload_id).first()
        )

        if not upload:
            logger.error(f"ClientUpload {upload_id} not found")
            return False

        upload.ocr_extracted = True  # type: ignore[assignment]
        upload.ocr_data = ocr_data  # type: ignore[assignment]
        upload.updated_at = datetime.utcnow()  # type: ignore[assignment]

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
    upload_id: int, category: Optional[str] = None
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
        upload = (
            session.query(ClientUpload).filter(ClientUpload.id == upload_id).first()
        )

        if not upload:
            return {"success": False, "error": f"ClientUpload {upload_id} not found"}

        file_path_val: str = str(upload.file_path) if upload.file_path else ""
        file_type_val: str = (
            str(upload.file_type)
            if upload.file_type
            else (file_path_val.split(".")[-1] if file_path_val else "pdf")
        )
        bureau_val: Optional[str] = str(upload.bureau) if upload.bureau else None
        doc_category = category or (str(upload.category) if upload.category else None)

        if not file_path_val or not os.path.exists(file_path_val):
            return {"success": False, "error": f"File not found: {file_path_val}"}

        if doc_category in ["cra_response", "bureau_response", "dispute_result"]:
            result = extract_cra_response_data(
                file_path=file_path_val, file_type=file_type_val, bureau=bureau_val
            )
        elif doc_category in ["collection_letter", "debt_collection", "collection"]:
            result = analyze_collection_letter(
                file_path=file_path_val, file_type=file_type_val
            )
        else:
            result = extract_cra_response_data(
                file_path=file_path_val, file_type=file_type_val, bureau=bureau_val
            )

        if result.get("success") and result.get("data"):
            ocr_data = {
                "extracted_at": datetime.utcnow().isoformat(),
                "category": doc_category,
                "extraction_result": result["data"],
                "tokens_used": result.get("tokens_used", 0),
            }

            if doc_category in ["cra_response", "bureau_response", "dispute_result"]:
                violations_result = detect_fcra_violations(
                    document_data=result["data"], document_type="cra_response"
                )
                if violations_result.get("success"):
                    ocr_data["violations_analysis"] = {
                        "violations": violations_result.get("violations", []),
                        "overall_count": violations_result.get("overall_count", 0),
                        "highest_severity": violations_result.get(
                            "highest_severity", "none"
                        ),
                        "potential_damages": violations_result.get(
                            "potential_damages", {}
                        ),
                        "recommended_actions": violations_result.get(
                            "recommended_actions", []
                        ),
                        "litigation_worthiness": violations_result.get(
                            "litigation_worthiness", {}
                        ),
                    }

            update_success = update_client_upload_ocr(upload_id, ocr_data)

            return {
                "success": True,
                "upload_id": upload_id,
                "data": ocr_data,
                "db_updated": update_success,
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown extraction error"),
                "upload_id": upload_id,
            }

    except Exception as e:
        logger.error(f"Error processing upload for OCR: {e}")
        return {"success": False, "error": str(e), "upload_id": upload_id}
    finally:
        session.close()


def batch_process_uploads(
    upload_ids: List[int], category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process multiple ClientUploads for OCR extraction.

    Args:
        upload_ids: List of ClientUpload IDs to process
        category: Optional category override for all uploads

    Returns:
        Dictionary with batch processing results
    """
    results: Dict[str, Any] = {
        "total": len(upload_ids),
        "successful": 0,
        "failed": 0,
        "results": [],
    }

    for upload_id in upload_ids:
        result = process_upload_for_ocr(upload_id, category)
        results["results"].append(result)

        if result.get("success"):
            results["successful"] += 1
        else:
            results["failed"] += 1

    return results


def analyze_cra_response(cra_response_id: int) -> Dict[str, Any]:
    """
    Analyze a CRA response document using Claude Vision.
    Extracts items, matches to existing DisputeItems, and detects reinsertion violations.

    Args:
        cra_response_id: ID of the CRAResponse record

    Returns:
        Dictionary with analysis results including matched items and reinsertion flags
    """
    session = SessionLocal()
    try:
        cra_response = (
            session.query(CRAResponse).filter(CRAResponse.id == cra_response_id).first()
        )

        if not cra_response:
            return {
                "success": False,
                "error": f"CRA Response {cra_response_id} not found",
            }

        cra_file_path: str = (
            str(cra_response.file_path) if cra_response.file_path else ""
        )
        cra_bureau: Optional[str] = (
            str(cra_response.bureau) if cra_response.bureau else None
        )
        cra_client_id: int = (
            int(cra_response.client_id) if cra_response.client_id else 0
        )
        cra_dispute_round: int = (
            int(cra_response.dispute_round) if cra_response.dispute_round else 0
        )

        if not cra_file_path or not os.path.exists(cra_file_path):
            return {
                "success": False,
                "error": f"File not found: {cra_file_path}",
            }

        file_type = cra_file_path.split(".")[-1].lower()

        extraction_result = extract_cra_response_data(
            file_path=cra_file_path,
            file_type=file_type,
            bureau=cra_bureau,
        )

        if not extraction_result.get("success"):
            return {
                "success": False,
                "error": extraction_result.get("error", "Extraction failed"),
            }

        extracted_data = extraction_result.get("data", {})
        extracted_items = extracted_data.get("items", [])

        dispute_items = (
            session.query(DisputeItem)
            .filter(
                DisputeItem.client_id == cra_client_id,
                DisputeItem.bureau == cra_bureau,
            )
            .all()
        )

        matched_items = []
        reinsertion_violations = []

        for ext_item in extracted_items:
            creditor_name = ext_item.get("creditor_name", "").lower().strip()
            account_number = ext_item.get("account_number", "").strip()
            result = ext_item.get("result", "").lower()

            best_match: Optional[DisputeItem] = None
            best_score: float = 0.0

            for di in dispute_items:
                di_creditor: str = str(di.creditor_name) if di.creditor_name else ""
                di_account: str = str(di.account_id) if di.account_id else ""
                score = _calculate_match_score(ext_item, di_creditor, di_account)
                if score > best_score and score >= 0.5:
                    best_score = score
                    best_match = di

            status_map = {
                "deleted": "deleted",
                "verified": "verified",
                "updated": "updated",
                "investigating": "investigating",
                "remains": "verified",
            }
            new_status = status_map.get(result, None)

            match_info = {
                "extracted_creditor": ext_item.get("creditor_name"),
                "extracted_account": account_number,
                "extracted_result": result,
                "extracted_reason": ext_item.get("reason"),
                "extracted_changes": ext_item.get("changes_made"),
                "match_score": best_score,
                "new_status": new_status,
            }

            if best_match:
                match_info["dispute_item_id"] = best_match.id
                match_info["current_status"] = best_match.status
                match_info["matched_creditor"] = best_match.creditor_name
                match_info["matched_account"] = best_match.account_id

                best_match_creditor: str = (
                    str(best_match.creditor_name) if best_match.creditor_name else ""
                )
                if new_status == "verified" and best_match.status == "deleted":
                    reinsertion = _check_reinsertion_violation(
                        session,
                        cra_client_id,
                        best_match_creditor,
                        cra_bureau or "",
                        cra_dispute_round,
                    )
                    if reinsertion.get("is_reinsertion"):
                        reinsertion_violations.append(
                            {
                                "dispute_item_id": best_match.id,
                                "creditor_name": best_match.creditor_name,
                                "deleted_in_round": reinsertion.get("deleted_round"),
                                "reappeared_in_round": cra_dispute_round,
                                "fcra_section": "611(a)(5)",
                                "violation_type": "reinsertion",
                            }
                        )
                        match_info["reinsertion_detected"] = True
            else:
                match_info["dispute_item_id"] = None
                match_info["current_status"] = None
                match_info["match_warning"] = "No matching dispute item found"

            matched_items.append(match_info)

        summary_counts = extracted_data.get("summary_counts", {})

        cra_case_id: Optional[int] = (
            int(cra_response.case_id) if cra_response.case_id else None
        )
        ocr_record = CRAResponseOCR(
            client_id=cra_client_id,
            case_id=cra_case_id,
            bureau=cra_bureau,
            document_type="cra_response",
            document_date=_parse_date(extracted_data.get("response_date")),
            response_date=_parse_date(extracted_data.get("response_date")),
            raw_text=extracted_data.get("raw_text_extracted", ""),
            structured_data={
                "extracted_data": extracted_data,
                "matched_items": matched_items,
                "reinsertion_violations": reinsertion_violations,
            },
            items_verified=[
                m for m in matched_items if m.get("extracted_result") == "verified"
            ],
            items_deleted=[
                m for m in matched_items if m.get("extracted_result") == "deleted"
            ],
            items_updated=[
                m for m in matched_items if m.get("extracted_result") == "updated"
            ],
            items_reinvestigated=[
                m for m in matched_items if m.get("extracted_result") == "investigating"
            ],
            new_violations_detected=(
                reinsertion_violations if reinsertion_violations else None
            ),
            reinvestigation_complete=(
                extracted_data.get("response_type") == "Results of Investigation"
            ),
            frivolous_claim=extracted_data.get("frivolous_warning", False),
            ocr_confidence=extracted_data.get("confidence_score", 0.7),
            extraction_method="claude_vision",
            processed_at=datetime.utcnow(),
        )

        session.add(ocr_record)
        session.commit()

        return {
            "success": True,
            "cra_response_id": cra_response_id,
            "ocr_record_id": ocr_record.id,
            "bureau": cra_bureau,
            "response_date": extracted_data.get("response_date"),
            "confidence_score": extracted_data.get("confidence_score", 0.7),
            "summary": {
                "total_items_found": len(extracted_items),
                "items_matched": len(
                    [m for m in matched_items if m.get("dispute_item_id")]
                ),
                "items_unmatched": len(
                    [m for m in matched_items if not m.get("dispute_item_id")]
                ),
                "items_deleted": summary_counts.get("items_deleted", 0),
                "items_verified": summary_counts.get("items_verified", 0),
                "items_updated": summary_counts.get("items_updated", 0),
                "reinsertion_violations": len(reinsertion_violations),
            },
            "matched_items": matched_items,
            "reinsertion_violations": reinsertion_violations,
            "frivolous_warning": extracted_data.get("frivolous_warning", False),
            "investigation_summary": extracted_data.get("investigation_summary"),
            "tokens_used": extraction_result.get("tokens_used", 0),
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error analyzing CRA response: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        session.close()


def _calculate_match_score(
    extracted_item: Dict[str, Any], db_creditor: str, db_account: str
) -> float:
    """Calculate similarity score between extracted item and database record."""
    score = 0.0

    ext_creditor = (extracted_item.get("creditor_name") or "").lower().strip()
    ext_account = (extracted_item.get("account_number") or "").strip()
    db_creditor_lower = db_creditor.lower().strip()
    db_account_clean = db_account.strip()

    if ext_creditor and db_creditor_lower:
        ext_words = set(ext_creditor.replace(",", " ").replace(".", " ").split())
        db_words = set(db_creditor_lower.replace(",", " ").replace(".", " ").split())

        if ext_creditor == db_creditor_lower:
            score += 0.6
        elif ext_words & db_words:
            overlap = len(ext_words & db_words) / max(len(ext_words), len(db_words))
            score += 0.4 * overlap
        elif ext_creditor in db_creditor_lower or db_creditor_lower in ext_creditor:
            score += 0.5

    if ext_account and db_account_clean:
        ext_digits = "".join(filter(str.isdigit, ext_account))[-4:]
        db_digits = "".join(filter(str.isdigit, db_account_clean))[-4:]

        if ext_digits and db_digits and ext_digits == db_digits:
            score += 0.4
        elif ext_digits and db_digits:
            matching = sum(a == b for a, b in zip(ext_digits, db_digits))
            score += 0.2 * (matching / max(len(ext_digits), len(db_digits)))

    return min(score, 1.0)


def _check_reinsertion_violation(
    session, client_id: int, creditor_name: str, bureau: str, current_round: int
) -> Dict[str, Any]:
    """Check if an item was previously deleted and is now reappearing (reinsertion)."""
    prior_deleted_items = (
        session.query(DisputeItem)
        .filter(
            DisputeItem.client_id == client_id,
            DisputeItem.bureau == bureau,
            DisputeItem.status == "deleted",
            DisputeItem.dispute_round < current_round,
        )
        .all()
    )

    creditor_lower = creditor_name.lower().strip() if creditor_name else ""

    for item in prior_deleted_items:
        item_creditor = (item.creditor_name or "").lower().strip()
        if (
            item_creditor == creditor_lower
            or creditor_lower in item_creditor
            or item_creditor in creditor_lower
        ):
            return {
                "is_reinsertion": True,
                "deleted_round": item.dispute_round,
                "deleted_item_id": item.id,
                "deleted_creditor": item.creditor_name,
            }

    return {"is_reinsertion": False}


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except:
        try:
            for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
        except:
            pass
    return None


def apply_analysis_updates(
    ocr_record_id: int,
    reviewed_items: Optional[List[Dict[str, Any]]] = None,
    create_violations: bool = True,
    staff_user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply the analysis results to update DisputeItem statuses.

    Args:
        ocr_record_id: ID of the CRAResponseOCR record
        reviewed_items: Optional list of reviewed/edited items (if None, uses stored data)
        create_violations: Whether to create Violation records for reinsertion
        staff_user: Name/email of the staff member applying changes

    Returns:
        Dictionary with update results
    """
    session = SessionLocal()
    try:
        ocr_record = (
            session.query(CRAResponseOCR)
            .filter(CRAResponseOCR.id == ocr_record_id)
            .first()
        )

        if not ocr_record:
            return {"success": False, "error": f"OCR record {ocr_record_id} not found"}

        structured_data: Dict[str, Any] = (
            cast(Dict[str, Any], ocr_record.structured_data)
            if ocr_record.structured_data
            else {}
        )
        items_to_update = reviewed_items or structured_data.get("matched_items", [])
        reinsertion_violations = structured_data.get("reinsertion_violations", [])

        updates_made = []
        violations_created = []

        for item in items_to_update:
            dispute_item_id = item.get("dispute_item_id")
            new_status = item.get("new_status")

            if not dispute_item_id or not new_status:
                continue

            dispute_item = (
                session.query(DisputeItem)
                .filter(DisputeItem.id == dispute_item_id)
                .first()
            )

            if dispute_item:
                old_status = dispute_item.status
                dispute_item.status = new_status  # type: ignore[assignment]
                dispute_item.response_date = date.today()  # type: ignore[assignment]
                dispute_item.response_notes = (  # type: ignore[assignment]
                    f"Auto-updated from CRA response analysis. Previous: {old_status}"
                )

                updates_made.append(
                    {
                        "dispute_item_id": dispute_item_id,
                        "creditor_name": dispute_item.creditor_name,
                        "old_status": old_status,
                        "new_status": new_status,
                    }
                )

        if create_violations and reinsertion_violations:
            for rv in reinsertion_violations:
                violation = Violation(
                    analysis_id=None,
                    client_id=ocr_record.client_id,
                    bureau=ocr_record.bureau,
                    account_name=rv.get("creditor_name"),
                    fcra_section="611(a)(5)",
                    violation_type="reinsertion",
                    description=f"Item previously deleted in round {rv.get('deleted_in_round')} reappeared in round {rv.get('reappeared_in_round')}. Under FCRA 611(a)(5), credit bureaus must follow reasonable procedures to prevent reinsertion of previously deleted information.",
                    statutory_damages_min=100,
                    statutory_damages_max=1000,
                    is_willful=True,
                    willfulness_notes="Reinsertion of deleted information indicates failure to implement proper procedures",
                )
                session.add(violation)
                violations_created.append(
                    {
                        "creditor_name": rv.get("creditor_name"),
                        "fcra_section": "611(a)(5)",
                        "violation_type": "reinsertion",
                    }
                )

        ocr_record.reviewed = True  # type: ignore[assignment]
        ocr_record.reviewed_by = staff_user  # type: ignore[assignment]
        ocr_record.reviewed_at = datetime.utcnow()  # type: ignore[assignment]
        current_notes: str = str(ocr_record.notes) if ocr_record.notes else ""
        new_notes: str = (
            current_notes
            + f"\nApplied {len(updates_made)} updates on {datetime.utcnow().isoformat()}"
        )
        ocr_record.notes = new_notes  # type: ignore[assignment]

        session.commit()

        return {
            "success": True,
            "ocr_record_id": ocr_record_id,
            "updates_applied": len(updates_made),
            "updates_made": updates_made,
            "violations_created": len(violations_created),
            "violations": violations_created,
            "reviewed_by": staff_user,
            "reviewed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error applying analysis updates: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        session.close()


def get_analysis_for_review(ocr_record_id: int) -> Dict[str, Any]:
    """
    Get analysis data formatted for staff review.

    Args:
        ocr_record_id: ID of the CRAResponseOCR record

    Returns:
        Dictionary with analysis data ready for review
    """
    session = SessionLocal()
    try:
        ocr_record = (
            session.query(CRAResponseOCR)
            .filter(CRAResponseOCR.id == ocr_record_id)
            .first()
        )

        if not ocr_record:
            return {"success": False, "error": f"OCR record {ocr_record_id} not found"}

        structured_data: Dict[str, Any] = (
            cast(Dict[str, Any], ocr_record.structured_data)
            if ocr_record.structured_data
            else {}
        )
        extracted_data = structured_data.get("extracted_data", {})
        matched_items = structured_data.get("matched_items", [])
        reinsertion_violations = structured_data.get("reinsertion_violations", [])

        return {
            "success": True,
            "ocr_record_id": ocr_record_id,
            "client_id": ocr_record.client_id,
            "bureau": ocr_record.bureau,
            "response_date": (
                ocr_record.response_date.isoformat()
                if ocr_record.response_date
                else None
            ),
            "confidence_score": ocr_record.ocr_confidence,
            "reviewed": ocr_record.reviewed,
            "reviewed_by": ocr_record.reviewed_by,
            "reviewed_at": (
                ocr_record.reviewed_at.isoformat() if ocr_record.reviewed_at else None
            ),
            "frivolous_claim": ocr_record.frivolous_claim,
            "investigation_summary": extracted_data.get("investigation_summary"),
            "matched_items": matched_items,
            "reinsertion_violations": reinsertion_violations,
            "summary_counts": extracted_data.get("summary_counts", {}),
            "raw_text": ocr_record.raw_text[:2000] if ocr_record.raw_text else None,
        }

    except Exception as e:
        logger.error(f"Error getting analysis for review: {e}")
        return {"success": False, "error": str(e)}
    finally:
        session.close()
