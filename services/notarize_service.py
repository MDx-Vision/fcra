"""
Notarize.com Integration Service
Remote Online Notarization (RON) API integration using class-based approach.
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from database import (
    IntegrationConnection,
    IntegrationEvent,
    NotarizeTransaction,
    SessionLocal,
)

logger = logging.getLogger(__name__)

PRODUCTION_BASE_URL = "https://api.notarize.com/v1"
SANDBOX_BASE_URL = "https://api.sandbox.notarize.com/v1"
SERVICE_NAME = "notarize"


class NotarizeService:
    """
    Notarize.com API client for Remote Online Notarization services.

    Usage:
        service = NotarizeService(api_key='your_key', sandbox=True)
        if service.test_connection():
            result = service.create_transaction(
                signer_email='john@example.com',
                signer_first_name='John',
                signer_last_name='Doe',
                document_url='https://example.com/document.pdf'
            )
    """

    def __init__(self, api_key: Optional[str] = None, sandbox: bool = True):
        """
        Initialize NotarizeService with API credentials.

        Args:
            api_key: Notarize.com API key. If None, will try environment variables.
            sandbox: If True, use sandbox environment. Default True.
        """
        self.api_key = (
            api_key
            or os.environ.get("NOTARIZE_API_KEY")
            or os.environ.get("PROOF_API_KEY")
        )
        self.sandbox = sandbox
        self.base_url = SANDBOX_BASE_URL if sandbox else PRODUCTION_BASE_URL
        self._integration_id: Optional[int] = None

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and len(self.api_key) > 10)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        if not self.is_configured:
            raise ValueError("Notarize.com API key is not configured")
        return {
            "ApiKey": self.api_key or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_integration_id(self, db=None) -> Optional[int]:
        """Get or create the integration connection record ID."""
        if self._integration_id:
            return self._integration_id

        session = db or SessionLocal()
        try:
            connection = (
                session.query(IntegrationConnection)
                .filter_by(service_name=SERVICE_NAME)
                .first()
            )

            if not connection:
                connection = IntegrationConnection(
                    service_name=SERVICE_NAME,
                    display_name="Notarize.com",
                    base_url=self.base_url,
                    is_active=self.is_configured,
                    is_sandbox=self.sandbox,
                    connection_status=(
                        "configured" if self.is_configured else "not_configured"
                    ),
                )
                session.add(connection)
                session.commit()
                session.refresh(connection)

            self._integration_id = int(connection.id)
            return self._integration_id
        except Exception as e:
            logger.error(f"Error getting integration ID: {e}")
            return None
        finally:
            if not db:
                session.close()

    def _log_event(
        self,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        client_id: Optional[int] = None,
        request_id: Optional[str] = None,
        response_status: Optional[int] = None,
        error_message: Optional[str] = None,
        cost_cents: int = 0,
        db: Any = None,
    ) -> None:
        """Log an integration event for audit trail."""
        session = db or SessionLocal()
        try:
            integration_id = self._get_integration_id(session)
            if not integration_id:
                logger.warning("Could not log event: no integration ID")
                return

            event = IntegrationEvent(
                integration_id=integration_id,
                event_type=event_type,
                event_data=event_data,
                client_id=client_id,
                request_id=request_id,
                response_status=response_status,
                error_message=error_message,
                cost_cents=cost_cents,
            )
            session.add(event)
            session.commit()
        except Exception as e:
            logger.error(f"Error logging integration event: {e}")
        finally:
            if not db:
                session.close()

    def test_connection(self) -> bool:
        """
        Test the API connection by making a simple request.

        Returns:
            True if connection is successful, False otherwise.
        """
        if not self.is_configured:
            logger.warning("Notarize.com API key not configured")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/transactions",
                headers=self._get_headers(),
                params={"limit": 1},
                timeout=15,
            )

            self._log_event(
                event_type="test_connection",
                response_status=response.status_code,
                error_message=None if response.ok else str(response.text[:500]),
            )

            if response.status_code in [200, 201]:
                logger.info("Notarize.com connection test successful")
                return True
            elif response.status_code == 401:
                logger.error("Notarize.com authentication failed - check API key")
                return False
            else:
                logger.warning(
                    f"Notarize.com connection test returned {response.status_code}"
                )
                return response.status_code < 500

        except requests.RequestException as e:
            logger.error(f"Notarize.com connection test failed: {e}")
            self._log_event(event_type="test_connection", error_message=str(e))
            return False

    def create_transaction(
        self,
        signer_email: str,
        signer_first_name: str,
        signer_last_name: str,
        document_url: str,
        requirement: str = "notarization",
        client_id: Optional[int] = None,
        document_id: Optional[int] = None,
        document_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new notarization transaction.

        Args:
            signer_email: Email address of the signer
            signer_first_name: Signer's first name
            signer_last_name: Signer's last name
            document_url: URL to the document to be notarized (must be publicly accessible)
            requirement: Type of requirement ('notarization', 'esignature', 'witness')
            client_id: Optional client ID for database tracking
            document_id: Optional document ID for database tracking
            document_name: Optional document display name

        Returns:
            Dict with keys:
                - success: bool
                - transaction_id: External Notarize.com transaction ID
                - access_link: URL for signer to access notarization session
                - internal_id: Our database record ID
                - error: Error message if failed
        """
        if not self.is_configured:
            return {
                "success": False,
                "transaction_id": None,
                "access_link": None,
                "internal_id": None,
                "error": "Notarize.com API key not configured",
            }

        signer_name = f"{signer_first_name} {signer_last_name}"

        payload = {
            "signers": [
                {
                    "email": signer_email,
                    "first_name": signer_first_name,
                    "last_name": signer_last_name,
                    "name": signer_name,
                }
            ],
            "documents": [
                {
                    "resource": document_url,
                    "requirement": requirement,
                    "name": document_name or "Document",
                }
            ],
        }

        session = SessionLocal()
        try:
            logger.info(f"Creating notarization transaction for {signer_email}")

            response = requests.post(
                f"{self.base_url}/transactions",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            self._log_event(
                event_type="create_transaction",
                event_data={"signer_email": signer_email, "requirement": requirement},
                client_id=client_id,
                response_status=response.status_code,
                error_message=None if response.ok else str(response.text[:500]),
                db=session,
            )

            if response.status_code not in [200, 201]:
                error_msg = f"API request failed with status {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "transaction_id": None,
                    "access_link": None,
                    "internal_id": None,
                    "error": error_msg,
                }

            response_data = response.json()

            transaction_id = (
                response_data.get("id")
                or response_data.get("transaction_id")
                or response_data.get("transactionId")
            )
            access_link = (
                response_data.get("access_link")
                or response_data.get("session_link")
                or response_data.get("signerUrl")
                or response_data.get("url")
            )

            transaction = NotarizeTransaction(
                client_id=client_id,
                document_id=document_id,
                external_transaction_id=transaction_id,
                transaction_type=requirement,
                status="created",
                access_link=access_link,
                signer_email=signer_email,
                signer_name=signer_name,
                document_name=document_name or "Document",
                original_document_path=document_url,
                webhook_events=[
                    {"event": "created", "timestamp": datetime.utcnow().isoformat()}
                ],
            )

            session.add(transaction)
            session.commit()
            session.refresh(transaction)

            logger.info(
                f"Created notarization transaction {transaction.id} with external ID {transaction_id}"
            )

            return {
                "success": True,
                "transaction_id": transaction_id,
                "access_link": access_link,
                "internal_id": transaction.id,
                "error": None,
            }

        except requests.RequestException as e:
            error_msg = f"Network error connecting to Notarize.com API: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "transaction_id": None,
                "access_link": None,
                "internal_id": None,
                "error": error_msg,
            }
        except Exception as e:
            session.rollback()
            error_msg = f"Error creating notarization transaction: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "transaction_id": None,
                "access_link": None,
                "internal_id": None,
                "error": error_msg,
            }
        finally:
            session.close()

    def get_transaction_status(self, transaction_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get the current status of a notarization transaction.

        Args:
            transaction_id: External Notarize.com transaction ID or internal database ID

        Returns:
            Dict with keys:
                - success: bool
                - status: Current transaction status
                - events: List of status change events
                - transaction_data: Full API response data
                - internal_id: Our database record ID
                - error: Error message if failed
        """
        if not self.is_configured:
            return {
                "success": False,
                "status": None,
                "events": [],
                "transaction_data": None,
                "internal_id": None,
                "error": "Notarize.com API key not configured",
            }

        session = SessionLocal()
        try:
            if isinstance(transaction_id, int) or (
                isinstance(transaction_id, str) and transaction_id.isdigit()
            ):
                transaction = (
                    session.query(NotarizeTransaction)
                    .filter_by(id=int(transaction_id))
                    .first()
                )
            else:
                transaction = (
                    session.query(NotarizeTransaction)
                    .filter_by(external_transaction_id=str(transaction_id))
                    .first()
                )

            if not transaction:
                return {
                    "success": False,
                    "status": None,
                    "events": [],
                    "transaction_data": None,
                    "internal_id": None,
                    "error": f"Transaction {transaction_id} not found",
                }

            external_id = transaction.external_transaction_id

            if not external_id:
                return {
                    "success": False,
                    "status": transaction.status,
                    "events": transaction.webhook_events or [],
                    "transaction_data": None,
                    "internal_id": transaction.id,
                    "error": "No external transaction ID",
                }

            logger.info(
                f"Getting status for transaction {transaction.id}, external ID: {external_id}"
            )

            response = requests.get(
                f"{self.base_url}/transactions/{external_id}",
                headers=self._get_headers(),
                timeout=30,
            )

            self._log_event(
                event_type="get_transaction_status",
                event_data={"external_id": external_id},
                client_id=int(transaction.client_id) if transaction.client_id else None,
                request_id=str(external_id) if external_id else None,
                response_status=response.status_code,
                error_message=None if response.ok else str(response.text[:500]),
                db=session,
            )

            if response.status_code == 404:
                return {
                    "success": False,
                    "status": "not_found",
                    "events": transaction.webhook_events or [],
                    "transaction_data": None,
                    "internal_id": transaction.id,
                    "error": "Transaction not found in Notarize.com",
                }

            if response.status_code != 200:
                return {
                    "success": False,
                    "status": transaction.status,
                    "events": transaction.webhook_events or [],
                    "transaction_data": None,
                    "internal_id": transaction.id,
                    "error": f"API error: {response.status_code}",
                }

            response_data = response.json()
            api_status = response_data.get("status", "").lower()

            status_mapping = {
                "created": "created",
                "pending": "pending",
                "in_progress": "in_progress",
                "in progress": "in_progress",
                "scheduled": "scheduled",
                "completed": "completed",
                "complete": "completed",
                "cancelled": "cancelled",
                "canceled": "cancelled",
                "expired": "expired",
                "failed": "failed",
            }
            normalized_status = status_mapping.get(api_status, api_status)

            events: List[Any] = list(transaction.webhook_events) if transaction.webhook_events else []
            if normalized_status != transaction.status:
                events.append(
                    {
                        "event": f"status_changed_to_{normalized_status}",
                        "previous_status": transaction.status,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            transaction.status = normalized_status
            transaction.webhook_events = events  # type: ignore[assignment]
            transaction.updated_at = datetime.utcnow()  # type: ignore[assignment]

            if normalized_status == "completed" and not transaction.completed_at:
                transaction.completed_at = datetime.utcnow()  # type: ignore[assignment]

            session.commit()

            logger.info(f"Transaction {transaction.id} status: {normalized_status}")

            return {
                "success": True,
                "status": normalized_status,
                "events": events,
                "transaction_data": response_data,
                "internal_id": transaction.id,
                "error": None,
            }

        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "status": None,
                "events": [],
                "transaction_data": None,
                "internal_id": None,
                "error": error_msg,
            }
        except Exception as e:
            session.rollback()
            error_msg = f"Error getting transaction status: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "status": None,
                "events": [],
                "transaction_data": None,
                "internal_id": None,
                "error": error_msg,
            }
        finally:
            session.close()

    def download_completed_document(
        self, transaction_id: Union[str, int], document_index: int = 0
    ) -> Union[bytes, Dict[str, Any]]:
        """
        Download the completed notarized document.

        Args:
            transaction_id: External Notarize.com transaction ID or internal database ID
            document_index: Index of document to download (default 0 for first)

        Returns:
            bytes: PDF content of the notarized document
            OR Dict with error information if failed
        """
        if not self.is_configured:
            return {"success": False, "error": "Notarize.com API key not configured"}

        session = SessionLocal()
        try:
            if isinstance(transaction_id, int) or (
                isinstance(transaction_id, str) and transaction_id.isdigit()
            ):
                transaction = (
                    session.query(NotarizeTransaction)
                    .filter_by(id=int(transaction_id))
                    .first()
                )
            else:
                transaction = (
                    session.query(NotarizeTransaction)
                    .filter_by(external_transaction_id=str(transaction_id))
                    .first()
                )

            if not transaction:
                return {
                    "success": False,
                    "error": f"Transaction {transaction_id} not found",
                }

            external_id = transaction.external_transaction_id

            status_result = self.get_transaction_status(int(transaction.id))
            if status_result.get("status") != "completed":
                return {
                    "success": False,
                    "error": f"Transaction not completed. Current status: {status_result.get('status')}",
                }

            logger.info(
                f"Downloading notarized document for transaction {transaction.id}"
            )

            docs_response = requests.get(
                f"{self.base_url}/transactions/{external_id}/documents",
                headers=self._get_headers(),
                timeout=30,
            )

            if docs_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get documents: {docs_response.status_code}",
                }

            documents = docs_response.json()
            if isinstance(documents, dict):
                documents = documents.get("documents", [])

            if not documents or len(documents) <= document_index:
                return {
                    "success": False,
                    "error": "No documents available for download",
                }

            doc = documents[document_index]
            doc_id = doc.get("id") or doc.get("document_id")
            doc_url = doc.get("url") or doc.get("download_url") or doc.get("resource")

            if doc_url:
                doc_response = requests.get(doc_url, timeout=120)
            elif doc_id:
                doc_response = requests.get(
                    f"{self.base_url}/transactions/{external_id}/documents/{doc_id}",
                    headers=self._get_headers(),
                    timeout=120,
                )
            else:
                return {"success": False, "error": "No document URL or ID found"}

            if doc_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download document: {doc_response.status_code}",
                }

            self._log_event(
                event_type="download_document",
                event_data={
                    "external_id": external_id,
                    "document_index": document_index,
                },
                client_id=int(transaction.client_id) if transaction.client_id else None,
                request_id=str(external_id) if external_id else None,
                response_status=200,
                db=session,
            )

            logger.info(
                f"Successfully downloaded document for transaction {transaction.id}"
            )

            return doc_response.content

        except requests.RequestException as e:
            error_msg = f"Network error downloading document: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error downloading document: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            session.close()

    def verify_webhook_signature(
        self, payload: Union[str, bytes], signature: str, secret: Optional[str] = None
    ) -> bool:
        """
        Verify the webhook signature from Notarize.com.

        Args:
            payload: Raw request body (string or bytes)
            signature: Signature from the webhook header
            secret: Webhook secret key. If None, reads from environment.

        Returns:
            True if signature is valid, False otherwise.
        """
        webhook_secret = secret or os.environ.get("NOTARIZE_WEBHOOK_SECRET")

        if not webhook_secret:
            logger.warning(
                "No webhook secret configured, skipping signature verification"
            )
            return True

        if not signature:
            logger.warning("No signature provided in webhook request")
            return False

        try:
            if isinstance(payload, str):
                payload_bytes = payload.encode("utf-8")
            else:
                payload_bytes = payload

            expected_signature = hmac.new(
                webhook_secret.encode("utf-8"), payload_bytes, hashlib.sha256
            ).hexdigest()

            signature_clean = signature.replace("sha256=", "").strip()

            is_valid = hmac.compare_digest(expected_signature, signature_clean)

            if not is_valid:
                logger.warning("Webhook signature verification failed")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    def handle_webhook(
        self,
        webhook_data: Dict[str, Any],
        raw_payload: Optional[Union[str, bytes]] = None,
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook notifications from Notarize.com.

        Args:
            webhook_data: Parsed JSON webhook payload
            raw_payload: Raw request body for signature verification
            signature: Signature header value

        Returns:
            Dict with keys:
                - success: bool
                - internal_id: Our database record ID (if found)
                - action_taken: Description of what was done
                - error: Error message if failed
        """
        if raw_payload and signature:
            if not self.verify_webhook_signature(raw_payload, signature):
                return {
                    "success": False,
                    "internal_id": None,
                    "action_taken": None,
                    "error": "Invalid webhook signature",
                }

        session = SessionLocal()
        try:
            transaction_id = (
                webhook_data.get("transaction_id")
                or webhook_data.get("id")
                or webhook_data.get("transactionId")
            )
            event_type = (
                webhook_data.get("event")
                or webhook_data.get("type")
                or webhook_data.get("status")
            )

            logger.info(
                f"Received webhook for transaction {transaction_id}, event: {event_type}"
            )

            if not transaction_id:
                return {
                    "success": False,
                    "internal_id": None,
                    "action_taken": None,
                    "error": "No transaction_id in webhook data",
                }

            transaction = (
                session.query(NotarizeTransaction)
                .filter_by(external_transaction_id=transaction_id)
                .first()
            )

            if not transaction:
                logger.warning(f"No transaction found for external ID {transaction_id}")
                return {
                    "success": False,
                    "internal_id": None,
                    "action_taken": None,
                    "error": f"No transaction found for ID {transaction_id}",
                }

            status_mapping = {
                "transaction.created": "created",
                "transaction.started": "in_progress",
                "transaction.scheduled": "scheduled",
                "transaction.completed": "completed",
                "transaction.cancelled": "cancelled",
                "transaction.expired": "expired",
                "transaction.failed": "failed",
                "created": "created",
                "started": "in_progress",
                "in_progress": "in_progress",
                "scheduled": "scheduled",
                "completed": "completed",
                "complete": "completed",
                "cancelled": "cancelled",
                "canceled": "cancelled",
                "expired": "expired",
                "failed": "failed",
            }

            event_lower = str(event_type).lower() if event_type else ""
            new_status = status_mapping.get(event_lower, transaction.status)

            events: List[Any] = list(transaction.webhook_events) if transaction.webhook_events else []
            events.append(
                {
                    "event": event_type,
                    "status": new_status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": webhook_data,
                }
            )

            transaction.status = new_status  # type: ignore[assignment]
            transaction.webhook_events = events  # type: ignore[assignment]
            transaction.updated_at = datetime.utcnow()  # type: ignore[assignment]

            action_taken = f"Updated status to {new_status}"

            if new_status == "completed":
                transaction.completed_at = datetime.utcnow()  # type: ignore[assignment]
                action_taken = f"Updated status to completed"

            self._log_event(
                event_type="webhook_received",
                event_data=webhook_data,
                client_id=int(transaction.client_id) if transaction.client_id else None,
                request_id=str(transaction_id) if transaction_id else None,
                db=session,
            )

            session.commit()

            logger.info(
                f"Webhook processed for transaction {transaction.id}: {action_taken}"
            )

            return {
                "success": True,
                "internal_id": transaction.id,
                "action_taken": action_taken,
                "error": None,
            }

        except Exception as e:
            session.rollback()
            error_msg = f"Error processing webhook: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "internal_id": None,
                "action_taken": None,
                "error": error_msg,
            }
        finally:
            session.close()


def get_notarize_service(sandbox: Optional[bool] = None) -> NotarizeService:
    """
    Factory function to create a NotarizeService instance with default configuration.

    Args:
        sandbox: Override sandbox mode. If None, uses environment variable or defaults to True.

    Returns:
        Configured NotarizeService instance
    """
    if sandbox is None:
        env_sandbox = os.environ.get("NOTARIZE_SANDBOX", "true").lower()
        sandbox = env_sandbox in ("true", "1", "yes")

    return NotarizeService(sandbox=sandbox)


def is_notarize_configured() -> bool:
    """Check if Notarize.com API is configured."""
    service = get_notarize_service()
    return service.is_configured


def test_notarize_connection() -> bool:
    """Test connection to Notarize.com API."""
    service = get_notarize_service()
    return service.test_connection()
