"""
SendCertified Integration Service
Provides certified mail with return receipt tracking through SendCertified API.
Supports both sandbox and production environments.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests  # type: ignore[import-untyped]

from database import (
    CertifiedMailOrder,
    Client,
    IntegrationConnection,
    IntegrationEvent,
    SessionLocal,
)

logger = logging.getLogger(__name__)

SANDBOX_BASE_URL = "https://sandbox.sendcertified.com/api/v1"
PRODUCTION_BASE_URL = "https://api.sendcertified.com/api/v1"
SERVICE_NAME = "sendcertified"
DISPLAY_NAME = "SendCertified"


class SendCertifiedService:
    """
    SendCertified API integration service.
    Handles certified mail creation, tracking, and return receipt downloads.
    """

    def __init__(
        self, api_key: Optional[str] = None, api_secret: Optional[str] = None, sandbox: bool = True
    ):
        """
        Initialize SendCertified service.

        Args:
            api_key: SendCertified API key (or loaded from IntegrationConnection)
            api_secret: SendCertified API secret (or loaded from IntegrationConnection)
            sandbox: Whether to use sandbox environment (default True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.base_url = SANDBOX_BASE_URL if sandbox else PRODUCTION_BASE_URL
        self._integration_id = None

        if not api_key or not api_secret:
            self._load_credentials_from_db()

    def _load_credentials_from_db(self):
        """Load API credentials from IntegrationConnection table."""
        from services.encryption import decrypt_value

        session = SessionLocal()
        try:
            connection = (
                session.query(IntegrationConnection)
                .filter_by(service_name=SERVICE_NAME)
                .first()
            )

            if connection:
                self._integration_id = connection.id
                if connection.api_key_encrypted:
                    self.api_key = decrypt_value(connection.api_key_encrypted)
                if connection.api_secret_encrypted:
                    self.api_secret = decrypt_value(connection.api_secret_encrypted)
                self.sandbox = connection.is_sandbox
                self.base_url = (
                    SANDBOX_BASE_URL if self.sandbox else PRODUCTION_BASE_URL
                )
        except Exception as e:
            logger.error(f"Error loading SendCertified credentials: {e}")
        finally:
            session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key or ''}",
            "X-API-Secret": self.api_secret or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _log_event(
        self,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        client_id: Optional[int] = None,
        request_id: Optional[str] = None,
        response_status: Optional[int] = None,
        error_message: Optional[str] = None,
        cost_cents: int = 0,
    ) -> None:
        """Log an integration event to the database."""
        if not self._integration_id:
            return

        session = SessionLocal()
        try:
            event = IntegrationEvent(
                integration_id=self._integration_id,
                event_type=event_type,
                event_data=event_data or {},
                client_id=client_id,
                request_id=request_id or str(uuid.uuid4()),
                response_status=response_status,
                error_message=error_message,
                cost_cents=cost_cents,
                created_at=datetime.utcnow(),
            )
            session.add(event)
            session.commit()
        except Exception as e:
            logger.error(f"Error logging integration event: {e}")
            session.rollback()
        finally:
            session.close()

    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.api_key and self.api_secret)

    def test_connection(self) -> bool:
        """
        Test connection to SendCertified API.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("SendCertified credentials not configured")
            self._log_event(
                event_type="connection_test",
                event_data={"success": False, "reason": "credentials_not_configured"},
                response_status=0,
                error_message="API credentials not configured",
            )
            return False

        request_id = str(uuid.uuid4())

        try:
            response = requests.get(
                f"{self.base_url}/account/status",
                headers=self._get_headers(),
                timeout=15,
            )

            success = response.status_code == 200

            self._log_event(
                event_type="connection_test",
                event_data={
                    "success": success,
                    "sandbox": self.sandbox,
                    "response_code": response.status_code,
                },
                request_id=request_id,
                response_status=response.status_code,
            )

            if success:
                self._update_connection_status("connected")
            else:
                self._update_connection_status("error", f"HTTP {response.status_code}")

            return success

        except requests.Timeout:
            self._log_event(
                event_type="connection_test",
                event_data={"success": False, "reason": "timeout"},
                request_id=request_id,
                error_message="Connection timeout",
            )
            self._update_connection_status("error", "Connection timeout")
            return False

        except requests.RequestException as e:
            error_msg = str(e)
            self._log_event(
                event_type="connection_test",
                event_data={"success": False, "reason": "request_error"},
                request_id=request_id,
                error_message=error_msg,
            )
            self._update_connection_status("error", error_msg[:200])
            return False

    def _update_connection_status(self, status: str, error: Optional[str] = None) -> None:
        """Update connection status in IntegrationConnection table."""
        session = SessionLocal()
        try:
            connection = (
                session.query(IntegrationConnection)
                .filter_by(service_name=SERVICE_NAME)
                .first()
            )

            if connection:
                connection.connection_status = status  # type: ignore[assignment]
                connection.last_connected_at = (
                    datetime.utcnow() if status == "connected" else None  # type: ignore[assignment]
                )
                connection.last_error = error  # type: ignore[assignment]
                connection.updated_at = datetime.utcnow()  # type: ignore[assignment]
                session.commit()
        except Exception as e:
            logger.error(f"Error updating connection status: {e}")
            session.rollback()
        finally:
            session.close()

    def create_mailing(
        self,
        recipient: str,
        address: Dict[str, str],
        document_content: bytes,
        mail_class: str = "certified",
        client_id: Optional[int] = None,
        dispute_id: Optional[int] = None,
        letter_type: Optional[str] = None,
        bureau: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a certified mailing through SendCertified API.

        Args:
            recipient: Recipient name
            address: Dict with street, city, state, zip fields
            document_content: PDF document as bytes
            mail_class: Mail class ('certified', 'certified_return_receipt', 'priority')
            client_id: Optional client ID for tracking
            dispute_id: Optional dispute ID for tracking
            letter_type: Type of letter (dispute_round_1, etc.)
            bureau: Credit bureau name if applicable

        Returns:
            dict with:
                - success: bool
                - label_id: SendCertified label/order ID
                - tracking_number: USPS tracking number
                - estimated_delivery: Estimated delivery date
                - cost: Cost in dollars
                - error: Error message if failed
        """
        if not self.is_configured():
            return {
                "success": False,
                "label_id": None,
                "tracking_number": None,
                "estimated_delivery": None,
                "cost": None,
                "error": "SendCertified API credentials not configured",
            }

        request_id = str(uuid.uuid4())

        formatted_address = self._format_address(address)

        payload = {
            "recipient": {
                "name": recipient,
                "address_line_1": address.get(
                    "street", address.get("address_line_1", "")
                ),
                "address_line_2": address.get("address_line_2", ""),
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "zip_code": address.get("zip", address.get("zip_code", "")),
                "country": address.get("country", "US"),
            },
            "mail_class": mail_class,
            "return_receipt": "return" in mail_class.lower(),
            "metadata": {
                "request_id": request_id,
                "client_id": client_id,
                "dispute_id": dispute_id,
                "letter_type": letter_type,
                "bureau": bureau,
            },
        }

        session = SessionLocal()
        try:
            import base64

            files_payload = {
                "document": base64.b64encode(document_content).decode("utf-8")
            }
            payload["document"] = files_payload

            response = requests.post(
                f"{self.base_url}/mailings",
                headers=self._get_headers(),
                json=payload,
                timeout=60,
            )

            if response.status_code in [200, 201]:
                data = response.json()

                label_id = (
                    data.get("label_id") or data.get("id") or data.get("mailing_id")
                )
                tracking_number = data.get("tracking_number")
                cost = data.get("cost", 0)
                estimated_delivery = data.get("estimated_delivery")

                order = CertifiedMailOrder(
                    client_id=client_id,
                    external_order_id=label_id,
                    tracking_number=tracking_number,
                    recipient_name=recipient,
                    recipient_address=formatted_address,
                    recipient_type="credit_bureau" if bureau else "other",
                    document_type=letter_type or "general",
                    letter_type=letter_type,
                    dispute_round=None,
                    bureau=bureau,
                    status="submitted",
                    cost=cost,
                    submitted_at=datetime.utcnow(),
                    webhook_data=data,
                )
                session.add(order)
                session.commit()
                session.refresh(order)

                self._log_event(
                    event_type="mailing_created",
                    event_data={
                        "label_id": label_id,
                        "tracking_number": tracking_number,
                        "mail_class": mail_class,
                        "recipient": recipient,
                        "order_id": order.id,
                    },
                    client_id=client_id,
                    request_id=request_id,
                    response_status=response.status_code,
                    cost_cents=int(cost * 100),
                )

                return {
                    "success": True,
                    "label_id": label_id,
                    "tracking_number": tracking_number,
                    "order_id": order.id,
                    "estimated_delivery": estimated_delivery,
                    "cost": cost,
                    "error": None,
                }
            else:
                error_msg = (
                    f"API returned status {response.status_code}: {response.text[:200]}"
                )

                self._log_event(
                    event_type="mailing_failed",
                    event_data={"mail_class": mail_class, "recipient": recipient},
                    client_id=client_id,
                    request_id=request_id,
                    response_status=response.status_code,
                    error_message=error_msg,
                )

                return {
                    "success": False,
                    "label_id": None,
                    "tracking_number": None,
                    "estimated_delivery": None,
                    "cost": None,
                    "error": error_msg,
                }

        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            self._log_event(
                event_type="mailing_failed",
                event_data={"mail_class": mail_class, "recipient": recipient},
                client_id=client_id,
                request_id=request_id,
                error_message=error_msg,
            )
            return {
                "success": False,
                "label_id": None,
                "tracking_number": None,
                "estimated_delivery": None,
                "cost": None,
                "error": error_msg,
            }

        except Exception as e:
            session.rollback()
            error_msg = f"Error creating mailing: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "label_id": None,
                "tracking_number": None,
                "estimated_delivery": None,
                "cost": None,
                "error": error_msg,
            }

        finally:
            session.close()

    def _format_address(self, address: Dict[str, str]) -> str:
        """Format address dict into single string."""
        parts: List[str] = []
        street = address.get("street") or address.get("address_line_1")
        if street:
            parts.append(street)
        if address.get("address_line_2"):
            parts.append(address["address_line_2"])

        city_state_zip: List[str] = []
        if address.get("city"):
            city_state_zip.append(address["city"])
        if address.get("state"):
            city_state_zip.append(address["state"])
        zip_val = address.get("zip") or address.get("zip_code")
        if zip_val:
            city_state_zip.append(zip_val)

        if city_state_zip:
            parts.append(", ".join(city_state_zip))

        return "\n".join(parts)

    def get_tracking_status(
        self, tracking_number: Optional[str] = None, order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get tracking status for a certified mailing.

        Args:
            tracking_number: USPS tracking number
            order_id: Internal order ID (alternative to tracking number)

        Returns:
            dict with:
                - success: bool
                - status: Current status string
                - events: List of tracking events
                - delivered_at: Delivery timestamp (if delivered)
                - signed_by: Signature name (if available)
                - error: Error message if failed
        """
        session = SessionLocal()
        try:
            if order_id:
                order = session.query(CertifiedMailOrder).filter_by(id=order_id).first()
                if order and order.tracking_number:
                    tracking_number = str(order.tracking_number)

            if not tracking_number:
                return {
                    "success": False,
                    "status": None,
                    "events": [],
                    "delivered_at": None,
                    "signed_by": None,
                    "error": "No tracking number provided",
                }

            if not self.is_configured():
                order = (
                    session.query(CertifiedMailOrder)
                    .filter_by(tracking_number=tracking_number)
                    .first()
                )

                if order:
                    return {
                        "success": True,
                        "status": order.status,
                        "events": (
                            order.webhook_data.get("events", [])
                            if order.webhook_data
                            else []
                        ),
                        "delivered_at": (
                            order.delivered_at.isoformat()
                            if order.delivered_at
                            else None
                        ),
                        "signed_by": (
                            order.webhook_data.get("signed_by")
                            if order.webhook_data
                            else None
                        ),
                        "error": None,
                        "cached": True,
                    }

                return {
                    "success": False,
                    "status": None,
                    "events": [],
                    "delivered_at": None,
                    "signed_by": None,
                    "error": "API credentials not configured",
                }

            request_id = str(uuid.uuid4())

            response = requests.get(
                f"{self.base_url}/tracking/{tracking_number}",
                headers=self._get_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()

                status = data.get("status", "unknown")
                events = data.get("events", data.get("tracking_events", []))
                delivered_at = data.get("delivered_at")
                signed_by = data.get("signed_by", data.get("signature_name"))

                order = (
                    session.query(CertifiedMailOrder)
                    .filter_by(tracking_number=tracking_number)
                    .first()
                )

                if order:
                    order.status = status
                    order.webhook_data = data
                    if status == "delivered" and delivered_at:
                        try:
                            order.delivered_at = datetime.fromisoformat(  # type: ignore[assignment]
                                delivered_at.replace("Z", "+00:00")
                            )
                        except:
                            order.delivered_at = datetime.utcnow()  # type: ignore[assignment]
                    session.commit()

                self._log_event(
                    event_type="tracking_checked",
                    event_data={
                        "tracking_number": tracking_number,
                        "status": status,
                        "event_count": len(events),
                    },
                    request_id=request_id,
                    response_status=response.status_code,
                )

                return {
                    "success": True,
                    "status": status,
                    "events": events,
                    "delivered_at": delivered_at,
                    "signed_by": signed_by,
                    "error": None,
                }
            else:
                error_msg = f"API returned status {response.status_code}"
                return {
                    "success": False,
                    "status": None,
                    "events": [],
                    "delivered_at": None,
                    "signed_by": None,
                    "error": error_msg,
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "status": None,
                "events": [],
                "delivered_at": None,
                "signed_by": None,
                "error": f"Network error: {str(e)}",
            }

        except Exception as e:
            logger.error(f"Error getting tracking status: {e}")
            return {
                "success": False,
                "status": None,
                "events": [],
                "delivered_at": None,
                "signed_by": None,
                "error": str(e),
            }

        finally:
            session.close()

    def download_return_receipt(
        self, tracking_number: Optional[str] = None, order_id: Optional[int] = None
    ) -> Optional[bytes]:
        """
        Download return receipt (green card) as PDF.

        Args:
            tracking_number: USPS tracking number
            order_id: Internal order ID (alternative to tracking number)

        Returns:
            bytes: PDF document bytes, or None if not available
        """
        session = SessionLocal()
        try:
            if order_id:
                order = session.query(CertifiedMailOrder).filter_by(id=order_id).first()
                if order and order.tracking_number:
                    tracking_number = str(order.tracking_number)

            if not tracking_number:
                logger.warning(
                    "No tracking number provided for return receipt download"
                )
                return None

            if not self.is_configured():
                logger.warning("SendCertified credentials not configured")
                return None

            request_id = str(uuid.uuid4())

            response = requests.get(
                f"{self.base_url}/receipts/{tracking_number}/download",
                headers=self._get_headers(),
                timeout=60,
            )

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if (
                    "pdf" in content_type.lower()
                    or "octet-stream" in content_type.lower()
                ):
                    self._log_event(
                        event_type="receipt_downloaded",
                        event_data={"tracking_number": tracking_number},
                        request_id=request_id,
                        response_status=response.status_code,
                    )
                    return response.content
                else:
                    logger.warning(
                        f"Unexpected content type for receipt: {content_type}"
                    )
                    return None
            elif response.status_code == 404:
                logger.info(f"Return receipt not yet available for {tracking_number}")
                return None
            else:
                logger.error(f"Error downloading receipt: {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"Network error downloading receipt: {e}")
            return None

        except Exception as e:
            logger.error(f"Error downloading return receipt: {e}")
            return None

        finally:
            session.close()

    def get_account_balance(self) -> Dict[str, Any]:
        """
        Get current account balance and usage statistics.

        Returns:
            dict with balance, credits, usage stats
        """
        if not self.is_configured():
            return {
                "success": False,
                "balance": 0,
                "credits": 0,
                "error": "API credentials not configured",
            }

        try:
            response = requests.get(
                f"{self.base_url}/account/balance",
                headers=self._get_headers(),
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "balance": data.get("balance", 0),
                    "credits": data.get("credits", 0),
                    "monthly_usage": data.get("monthly_usage", 0),
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "balance": 0,
                    "credits": 0,
                    "error": f"API returned status {response.status_code}",
                }

        except Exception as e:
            return {"success": False, "balance": 0, "credits": 0, "error": str(e)}


def get_sendcertified_service() -> SendCertifiedService:
    """Factory function to get a configured SendCertified service instance."""
    return SendCertifiedService()


def configure_sendcertified(
    api_key: str, api_secret: str, sandbox: bool = True
) -> Dict[str, Any]:
    """
    Configure SendCertified integration with API credentials.

    Args:
        api_key: SendCertified API key
        api_secret: SendCertified API secret
        sandbox: Whether to use sandbox environment

    Returns:
        dict with success status and any errors
    """
    from services.encryption import encrypt_value

    session = SessionLocal()
    try:
        connection = (
            session.query(IntegrationConnection)
            .filter_by(service_name=SERVICE_NAME)
            .first()
        )

        if not connection:
            connection = IntegrationConnection(
                service_name=SERVICE_NAME,
                display_name=DISPLAY_NAME,
                base_url=SANDBOX_BASE_URL if sandbox else PRODUCTION_BASE_URL,
                is_sandbox=sandbox,
                connection_status="not_tested",
                created_at=datetime.utcnow(),
            )
            session.add(connection)

        connection.api_key_encrypted = encrypt_value(api_key)  # type: ignore[assignment]
        connection.api_secret_encrypted = encrypt_value(api_secret)  # type: ignore[assignment]
        connection.is_sandbox = sandbox  # type: ignore[assignment]
        connection.base_url = SANDBOX_BASE_URL if sandbox else PRODUCTION_BASE_URL  # type: ignore[assignment]
        connection.is_active = True  # type: ignore[assignment]
        connection.connection_status = "configured"  # type: ignore[assignment]
        connection.updated_at = datetime.utcnow()  # type: ignore[assignment]

        session.commit()

        service = SendCertifiedService(
            api_key=api_key, api_secret=api_secret, sandbox=sandbox
        )
        test_result = service.test_connection()

        return {
            "success": True,
            "configured": True,
            "connection_test": test_result,
            "sandbox": sandbox,
            "error": None,
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error configuring SendCertified: {e}")
        return {
            "success": False,
            "configured": False,
            "connection_test": False,
            "error": str(e),
        }

    finally:
        session.close()


def get_sendcertified_status() -> Dict[str, Any]:
    """
    Get current SendCertified integration status.

    Returns:
        dict with configuration and connection status
    """
    session = SessionLocal()
    try:
        connection = (
            session.query(IntegrationConnection)
            .filter_by(service_name=SERVICE_NAME)
            .first()
        )

        if not connection:
            return {
                "configured": False,
                "connected": False,
                "status": "not_configured",
                "sandbox": True,
                "last_connected": None,
                "last_error": None,
            }

        return {
            "configured": bool(connection.api_key_encrypted),
            "connected": connection.connection_status == "connected",
            "status": connection.connection_status,
            "sandbox": connection.is_sandbox,
            "last_connected": (
                connection.last_connected_at.isoformat()
                if connection.last_connected_at
                else None
            ),
            "last_error": connection.last_error,
        }

    except Exception as e:
        logger.error(f"Error getting SendCertified status: {e}")
        return {
            "configured": False,
            "connected": False,
            "status": "error",
            "sandbox": True,
            "last_connected": None,
            "last_error": str(e),
        }

    finally:
        session.close()


def get_mailing_statistics() -> Dict[str, Any]:
    """
    Get certified mail usage statistics.

    Returns:
        dict with counts of mailings by status
    """
    session = SessionLocal()
    try:
        from sqlalchemy import func

        total = session.query(func.count(CertifiedMailOrder.id)).scalar() or 0

        submitted = (
            session.query(func.count(CertifiedMailOrder.id))
            .filter(CertifiedMailOrder.status == "submitted")
            .scalar()
            or 0
        )

        in_transit = (
            session.query(func.count(CertifiedMailOrder.id))
            .filter(
                CertifiedMailOrder.status.in_(
                    ["mailed", "in_transit", "out_for_delivery"]
                )
            )
            .scalar()
            or 0
        )

        delivered = (
            session.query(func.count(CertifiedMailOrder.id))
            .filter(CertifiedMailOrder.status == "delivered")
            .scalar()
            or 0
        )

        returned = (
            session.query(func.count(CertifiedMailOrder.id))
            .filter(CertifiedMailOrder.status == "returned")
            .scalar()
            or 0
        )

        from datetime import timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        this_month = (
            session.query(func.count(CertifiedMailOrder.id))
            .filter(CertifiedMailOrder.created_at >= thirty_days_ago)
            .scalar()
            or 0
        )

        total_cost = session.query(func.sum(CertifiedMailOrder.cost)).scalar() or 0

        return {
            "total": total,
            "submitted": submitted,
            "in_transit": in_transit,
            "delivered": delivered,
            "returned": returned,
            "this_month": this_month,
            "total_cost": round(total_cost, 2),
        }

    except Exception as e:
        logger.error(f"Error getting mailing statistics: {e}")
        return {
            "total": 0,
            "submitted": 0,
            "in_transit": 0,
            "delivered": 0,
            "returned": 0,
            "this_month": 0,
            "total_cost": 0,
        }

    finally:
        session.close()
