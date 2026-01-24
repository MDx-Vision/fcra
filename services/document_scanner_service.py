"""
Document Scanner Service
Handles multi-page document scanning, image-to-PDF conversion, and OCR processing.
Uses Claude Vision for high-accuracy OCR of credit reports and legal documents.
"""

import base64
import io
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import anthropic
from fpdf import FPDF
from PIL import Image

from database import Client, Document, get_db

UPLOAD_FOLDER = "uploads/scans"
OUTPUT_FOLDER = "generated_documents/scanned_pdfs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

DOCUMENT_TYPES = {
    "cra_response_r1": {
        "name": "CRA Response - Round 1",
        "description": "First dispute round response from CRA",
        "round": 1,
        "ocr_prompt": "Extract all text from this credit reporting agency Round 1 response letter. Include dates, case numbers, bureau name, and detailed statements about investigation results for each disputed item.",
    },
    "cra_response_r2": {
        "name": "CRA Response - Round 2",
        "description": "Second dispute round response from CRA",
        "round": 2,
        "ocr_prompt": "Extract all text from this credit reporting agency Round 2 response letter. Include dates, case numbers, bureau name, and detailed statements about re-investigation results. Note any items that were verified vs deleted.",
    },
    "cra_response_r3": {
        "name": "CRA Response - Round 3",
        "description": "Third dispute round response from CRA",
        "round": 3,
        "ocr_prompt": "Extract all text from this credit reporting agency Round 3 response letter. Include dates, case numbers, bureau name, and detailed statements. Note any frivolous dispute claims or continued verification statements.",
    },
    "cra_response_r4": {
        "name": "CRA Response - Round 4",
        "description": "Fourth dispute round (Method of Verification)",
        "round": 4,
        "ocr_prompt": "Extract all text from this credit reporting agency Round 4/MOV response letter. Include dates, case numbers, bureau name, method of verification details, and any compliance statements.",
    },
    "collection_letter": {
        "name": "Collection Letter",
        "description": "Letter from debt collector",
        "ocr_prompt": "Extract all text from this collection letter. Include creditor name, original creditor, account numbers, amounts claimed, dates, and any legal notices or validation information.",
    },
    "creditor_response": {
        "name": "Creditor/Furnisher Response",
        "description": "Response from creditor or data furnisher",
        "ocr_prompt": "Extract all text from this creditor/furnisher response. Include company name, account details, dates, and their position on the dispute.",
    },
    "court_document": {
        "name": "Court Document",
        "description": "Lawsuit, summons, or court filing",
        "ocr_prompt": "Extract all text from this court document. Include case numbers, party names, court name, dates, claims, and any legal language or deadlines.",
    },
    "id_document": {
        "name": "ID Document",
        "description": "Driver license, passport, or other ID",
        "ocr_prompt": "Extract the name, address, date of birth, and document number from this ID document. Do not include the full ID number for security.",
    },
    "proof_of_address": {
        "name": "Proof of Address",
        "description": "Utility bill, bank statement for address verification",
        "ocr_prompt": "Extract the name, address, and date from this proof of address document. Include the type of document (utility bill, bank statement, etc.).",
    },
    "other": {
        "name": "Other Document",
        "description": "Any other document type",
        "ocr_prompt": "Extract all text from this document, preserving the structure and formatting as much as possible.",
    },
}


class DocumentScanner:
    """Handles document scanning, PDF creation, and OCR processing"""

    def __init__(self):
        self.client = None
        try:
            api_key = os.environ.get("FCRA Automation Secure") or os.environ.get(
                "ANTHROPIC_API_KEY"
            )
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
            else:
                self.client = anthropic.Anthropic()
        except Exception as e:
            print(f"Warning: Anthropic client not initialized: {e}")

    def process_uploaded_image(
        self, image_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """
        Process a single uploaded image - validate, optimize, and save.

        Args:
            image_data: Raw image bytes
            filename: Original filename

        Returns:
            dict with image info including path, dimensions, size
        """
        try:
            img = Image.open(io.BytesIO(image_data))

            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background  # type: ignore[assignment]
            elif img.mode != "RGB":
                img = img.convert("RGB")  # type: ignore[assignment]

            max_dimension = 2000
            if img.width > max_dimension or img.height > max_dimension:
                ratio = min(max_dimension / img.width, max_dimension / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)  # type: ignore[assignment]

            image_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"scan_{timestamp}_{image_id}.jpg"
            filepath = os.path.join(UPLOAD_FOLDER, safe_filename)

            img.save(filepath, "JPEG", quality=85, optimize=True)

            file_size = os.path.getsize(filepath)

            return {
                "success": True,
                "image_id": image_id,
                "filepath": filepath,
                "filename": safe_filename,
                "original_filename": filename,
                "width": img.width,
                "height": img.height,
                "file_size": file_size,
                "file_size_kb": round(file_size / 1024, 2),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def combine_images_to_pdf(
        self,
        image_paths: List[str],
        output_filename: Optional[str] = None,
        client_name: Optional[str] = None,
        document_type: str = "other",
    ) -> Dict[str, Any]:
        """
        Combine multiple images into a single PDF document.

        Args:
            image_paths: List of paths to images
            output_filename: Optional custom filename
            client_name: Client name for filename
            document_type: Type of document for naming

        Returns:
            dict with PDF info including path and page count
        """
        try:
            if not image_paths:
                return {"success": False, "error": "No images provided"}

            pdf = FPDF()
            pdf.set_auto_page_break(auto=False)

            for img_path in image_paths:
                if not os.path.exists(img_path):
                    continue

                img = Image.open(img_path)
                img_width, img_height = img.size

                if img_width > img_height:
                    pdf.add_page(orientation="L")
                    page_width, page_height = 297, 210
                else:
                    pdf.add_page(orientation="P")
                    page_width, page_height = 210, 297

                margin = 10
                available_width = page_width - (2 * margin)
                available_height = page_height - (2 * margin)

                width_ratio = available_width / img_width
                height_ratio = available_height / img_height
                scale = min(width_ratio, height_ratio)

                final_width = img_width * scale
                final_height = img_height * scale

                x = margin + (available_width - final_width) / 2
                y = margin + (available_height - final_height) / 2

                pdf.image(img_path, x=x, y=y, w=final_width, h=final_height)

            if output_filename:
                pdf_filename = output_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                client_safe = (client_name or "unknown").replace(" ", "_")[:30]
                doc_type = document_type.replace("_", "-")
                pdf_filename = f"{client_safe}_{doc_type}_{timestamp}.pdf"

            pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
            pdf.output(pdf_path)

            return {
                "success": True,
                "pdf_path": pdf_path,
                "pdf_filename": pdf_filename,
                "page_count": len(image_paths),
                "file_size": os.path.getsize(pdf_path),
                "file_size_kb": round(os.path.getsize(pdf_path) / 1024, 2),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_text_from_image(
        self, image_path: str, document_type: str = "other"
    ) -> Dict[str, Any]:
        """
        Extract text from a single image using Claude Vision OCR.

        Args:
            image_path: Path to image file
            document_type: Type of document for optimized extraction

        Returns:
            dict with extracted text and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "Anthropic client not initialized",
                "text": "",
                "mock": True,
            }

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            base64_image = base64.standard_b64encode(image_data).decode("utf-8")

            ext = os.path.splitext(image_path)[1].lower()
            media_type = "image/jpeg"
            if ext == ".png":
                media_type = "image/png"
            elif ext == ".gif":
                media_type = "image/gif"
            elif ext == ".webp":
                media_type = "image/webp"

            doc_config = DOCUMENT_TYPES.get(document_type, DOCUMENT_TYPES["other"])
            ocr_prompt: str = doc_config["ocr_prompt"]  # type: ignore[index]

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image,
                                },
                            },
                            {"type": "text", "text": ocr_prompt},
                        ],
                    }
                ],
            )

            extracted_text = response.content[0].text if response.content else ""

            input_tokens = (
                response.usage.input_tokens if hasattr(response, "usage") else 0
            )
            output_tokens = (
                response.usage.output_tokens if hasattr(response, "usage") else 0
            )

            return {
                "success": True,
                "text": extracted_text,
                "char_count": len(extracted_text),
                "word_count": len(extracted_text.split()),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": round(
                    (input_tokens * 0.003 + output_tokens * 0.015) / 1000, 4
                ),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "text": ""}

    def process_multi_page_document(
        self,
        image_paths: List[str],
        document_type: str = "credit_report",
        client_id: Optional[int] = None,
        client_name: Optional[str] = None,
        run_ocr: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a multi-page document: combine to PDF and optionally run OCR.

        Args:
            image_paths: List of image file paths
            document_type: Type of document
            client_id: Client ID for database storage
            client_name: Client name for filename
            run_ocr: Whether to run OCR on all pages

        Returns:
            dict with PDF path, OCR results, and metadata
        """
        pdf_result = self.combine_images_to_pdf(
            image_paths=image_paths,
            client_name=client_name,
            document_type=document_type,
        )

        if not pdf_result["success"]:
            return pdf_result

        result = {
            "success": True,
            "pdf_path": pdf_result["pdf_path"],
            "pdf_filename": pdf_result["pdf_filename"],
            "page_count": pdf_result["page_count"],
            "document_type": document_type,
            "client_id": client_id,
        }

        if run_ocr:
            all_text = []
            page_results = []
            total_cost = 0

            for i, img_path in enumerate(image_paths):
                ocr_result = self.extract_text_from_image(img_path, document_type)

                page_results.append(
                    {
                        "page": i + 1,
                        "success": ocr_result["success"],
                        "char_count": ocr_result.get("char_count", 0),
                        "word_count": ocr_result.get("word_count", 0),
                    }
                )

                if ocr_result["success"]:
                    all_text.append(f"--- PAGE {i + 1} ---\n{ocr_result['text']}")
                    total_cost += ocr_result.get("estimated_cost", 0)

            result["ocr_completed"] = True
            result["extracted_text"] = "\n\n".join(all_text)
            result["total_chars"] = len(result["extracted_text"])
            result["total_words"] = len(result["extracted_text"].split())
            result["page_results"] = page_results
            result["estimated_ocr_cost"] = round(total_cost, 4)

            text_filename = pdf_result["pdf_filename"].replace(".pdf", "_text.txt")
            text_path = os.path.join(OUTPUT_FOLDER, text_filename)
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(result["extracted_text"])
            result["text_file_path"] = text_path
        else:
            result["ocr_completed"] = False

        if client_id:
            try:
                db = get_db()
                doc = Document(
                    client_id=client_id,
                    document_type=document_type,
                    file_path=pdf_result["pdf_path"],
                    file_name=pdf_result["pdf_filename"],
                    status="processed" if run_ocr else "uploaded",
                    uploaded_at=datetime.utcnow(),
                )
                db.add(doc)
                db.commit()
                result["document_id"] = doc.id
                db.close()
            except Exception as e:
                result["database_error"] = str(e)

        return result

    def cleanup_temp_images(self, image_paths: List[str]) -> int:
        """Remove temporary image files after processing"""
        removed = 0
        for path in image_paths:
            try:
                if os.path.exists(path) and UPLOAD_FOLDER in path:
                    os.remove(path)
                    removed += 1
            except:
                pass
        return removed


class ScanSession:
    """Manages a multi-page scanning session"""

    def __init__(
        self,
        client_id: Optional[int] = None,
        client_name: Optional[str] = None,
        document_type: str = "credit_report",
    ):
        self.session_id = str(uuid.uuid4())
        self.client_id = client_id
        self.client_name = client_name
        self.document_type = document_type
        self.images: List[Dict[str, Any]] = []
        self.created_at = datetime.utcnow()
        self.scanner = DocumentScanner()

    def add_image(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """Add an image to the session"""
        result = self.scanner.process_uploaded_image(image_data, filename)

        if result["success"]:
            self.images.append(
                {
                    "image_id": result["image_id"],
                    "filepath": result["filepath"],
                    "filename": result["filename"],
                    "page_number": len(self.images) + 1,
                    "width": result["width"],
                    "height": result["height"],
                    "file_size_kb": result["file_size_kb"],
                }
            )
            result["page_number"] = len(self.images)
            result["total_pages"] = len(self.images)

        return result

    def remove_image(self, page_number: int) -> bool:
        """Remove an image from the session by page number"""
        if 1 <= page_number <= len(self.images):
            removed = self.images.pop(page_number - 1)
            try:
                if os.path.exists(removed["filepath"]):
                    os.remove(removed["filepath"])
            except:
                pass
            for i, img in enumerate(self.images):
                img["page_number"] = i + 1
            return True
        return False

    def reorder_images(self, new_order: List[int]) -> bool:
        """Reorder images based on new page order"""
        if sorted(new_order) != list(range(1, len(self.images) + 1)):
            return False

        new_images = []
        for page_num in new_order:
            new_images.append(self.images[page_num - 1])

        for i, img in enumerate(new_images):
            img["page_number"] = i + 1

        self.images = new_images
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current session status"""
        return {
            "session_id": self.session_id,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "document_type": self.document_type,
            "page_count": len(self.images),
            "images": self.images,
            "created_at": self.created_at.isoformat(),
        }

    def finalize(self, run_ocr: bool = True) -> Dict[str, Any]:
        """Finalize the session - create PDF and optionally run OCR"""
        if not self.images:
            return {"success": False, "error": "No images in session"}

        image_paths = [img["filepath"] for img in self.images]

        result = self.scanner.process_multi_page_document(
            image_paths=image_paths,
            document_type=self.document_type,
            client_id=self.client_id,
            client_name=self.client_name,
            run_ocr=run_ocr,
        )

        result["session_id"] = self.session_id

        return result

    def cancel(self) -> int:
        """Cancel the session and cleanup images"""
        image_paths = [img["filepath"] for img in self.images]
        removed = self.scanner.cleanup_temp_images(image_paths)
        self.images = []
        return removed


scan_sessions: Dict[str, ScanSession] = {}


def create_scan_session(
    client_id: Optional[int] = None,
    client_name: Optional[str] = None,
    document_type: str = "credit_report",
) -> Dict[str, Any]:
    """Create a new scanning session"""
    session = ScanSession(client_id, client_name, document_type)
    scan_sessions[session.session_id] = session
    return {
        "success": True,
        "session_id": session.session_id,
        "document_type": document_type,
        "client_id": client_id,
        "message": "Scan session created. Add images using the session ID.",
    }


def get_scan_session(session_id: str) -> Optional[ScanSession]:
    """Get an existing scan session"""
    return scan_sessions.get(session_id)


def cleanup_old_sessions(max_age_hours: int = 24) -> int:
    """Remove sessions older than max_age_hours"""
    now = datetime.utcnow()
    removed = 0
    to_remove = []

    for session_id, session in scan_sessions.items():
        age = (now - session.created_at).total_seconds() / 3600
        if age > max_age_hours:
            session.cancel()
            to_remove.append(session_id)
            removed += 1

    for session_id in to_remove:
        del scan_sessions[session_id]

    return removed


def get_document_types() -> List[Dict[str, Any]]:
    """Get list of supported document types"""
    return [
        {"id": k, "name": str(v["name"]), "description": str(v["description"])}  # type: ignore[index]
        for k, v in DOCUMENT_TYPES.items()
    ]
