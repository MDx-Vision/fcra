"""
Credit Pull Integration Service
Provider-agnostic abstraction for pulling credit reports from various providers.
Supports SmartCredit, IdentityIQ, and Experian Connect APIs.
"""

import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from database import (
    Analysis,
    Client,
    CreditPullRequest,
    CreditReport,
    IntegrationConnection,
    IntegrationEvent,
    SessionLocal,
)

logger = logging.getLogger(__name__)

SERVICE_NAME = "credit_pull"
DISPLAY_NAME = "Credit Pull Service"


class BaseCreditAdapter(ABC):
    """Abstract base class for credit provider adapters."""

    PROVIDER_NAME = "base"
    SANDBOX_BASE_URL = ""
    PRODUCTION_BASE_URL = ""

    def __init__(self, api_key: Optional[str] = None, sandbox: bool = True):
        self.api_key = api_key
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_BASE_URL if sandbox else self.PRODUCTION_BASE_URL

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and len(self.api_key) > 10)

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the API connection."""
        pass

    @abstractmethod
    def request_report(
        self,
        ssn_last4: str,
        dob: str,
        full_ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Request a credit report pull."""
        pass

    @abstractmethod
    def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a credit report request."""
        pass

    @abstractmethod
    def get_report(self, request_id: str) -> Dict[str, Any]:
        """Get the full credit report data."""
        pass

    @abstractmethod
    def parse_report(self, raw_data: Any) -> Dict[str, Any]:
        """Parse raw report data into structured format."""
        pass


class SmartCreditAdapter(BaseCreditAdapter):
    """
    SmartCredit API adapter.
    Documentation: https://smartcredit.com/api/docs (requires B2B partnership)
    """

    PROVIDER_NAME = "smartcredit"
    SANDBOX_BASE_URL = "https://api.sandbox.smartcredit.com/v1"
    PRODUCTION_BASE_URL = "https://api.smartcredit.com/v1"

    def __init__(self, api_key: Optional[str] = None, sandbox: bool = True):
        super().__init__(api_key, sandbox)
        if not api_key:
            self.api_key = os.environ.get("SMARTCREDIT_API_KEY")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def test_connection(self) -> bool:
        """Test SmartCredit API connection."""
        if not self.is_configured:
            logger.warning("SmartCredit API key not configured")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/health", headers=self._get_headers(), timeout=15
            )
            return response.status_code in [200, 201, 401]
        except requests.RequestException as e:
            logger.error(f"SmartCredit connection test failed: {e}")
            return False

    def request_report(
        self,
        ssn_last4: str,
        dob: str,
        full_ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Request a credit report from SmartCredit."""
        if not self.is_configured:
            return {
                "success": False,
                "request_id": None,
                "status": "error",
                "error": "SmartCredit API key not configured. Please add SMARTCREDIT_API_KEY to your environment.",
            }

        payload = {
            "ssn_last4": ssn_last4,
            "date_of_birth": dob,
            "report_type": "tri-merge",
            "bureaus": ["experian", "equifax", "transunion"],
        }

        if full_ssn:
            payload["ssn"] = full_ssn
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if address:
            payload["address"] = address

        try:
            response = requests.post(
                f"{self.base_url}/reports/request",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "request_id": data.get("request_id") or data.get("id"),
                    "status": data.get("status", "pending"),
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "request_id": None,
                    "status": "error",
                    "error": f"API error: {response.status_code} - {response.text[:200]}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "request_id": None,
                "status": "error",
                "error": f"Network error: {str(e)}",
            }

    def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a SmartCredit report request."""
        if not self.is_configured:
            return {
                "success": False,
                "status": "error",
                "scores": None,
                "error": "SmartCredit API key not configured",
            }

        try:
            response = requests.get(
                f"{self.base_url}/reports/{request_id}/status",
                headers=self._get_headers(),
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status", "pending"),
                    "scores": (
                        {
                            "experian": data.get("experian_score"),
                            "equifax": data.get("equifax_score"),
                            "transunion": data.get("transunion_score"),
                        }
                        if data.get("status") == "complete"
                        else None
                    ),
                    "report_ready": data.get("status") == "complete",
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "scores": None,
                    "error": f"API error: {response.status_code}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "status": "error",
                "scores": None,
                "error": f"Network error: {str(e)}",
            }

    def get_report(self, request_id: str) -> Dict[str, Any]:
        """Get the full report from SmartCredit."""
        if not self.is_configured:
            return {
                "success": False,
                "raw_data": None,
                "error": "SmartCredit API key not configured",
            }

        try:
            response = requests.get(
                f"{self.base_url}/reports/{request_id}",
                headers=self._get_headers(),
                timeout=60,
            )

            if response.status_code == 200:
                return {"success": True, "raw_data": response.json(), "error": None}
            else:
                return {
                    "success": False,
                    "raw_data": None,
                    "error": f"API error: {response.status_code}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "raw_data": None,
                "error": f"Network error: {str(e)}",
            }

    def parse_report(self, raw_data: Any) -> Dict[str, Any]:
        """Parse SmartCredit report into structured format."""
        if not raw_data:
            return {"success": False, "error": "No data to parse"}

        try:
            parsed = {
                "provider": self.PROVIDER_NAME,
                "report_date": raw_data.get("report_date"),
                "consumer": {
                    "name": raw_data.get("consumer_name"),
                    "addresses": raw_data.get("addresses", []),
                    "employers": raw_data.get("employers", []),
                },
                "scores": {
                    "experian": raw_data.get("experian_score"),
                    "equifax": raw_data.get("equifax_score"),
                    "transunion": raw_data.get("transunion_score"),
                },
                "tradelines": [],
                "inquiries": [],
                "public_records": [],
                "collections": [],
            }

            for tradeline in raw_data.get("tradelines", []):
                parsed["tradelines"].append(
                    {
                        "creditor": tradeline.get("creditor_name"),
                        "account_number": tradeline.get("account_number_masked"),
                        "account_type": tradeline.get("account_type"),
                        "balance": tradeline.get("balance"),
                        "credit_limit": tradeline.get("credit_limit"),
                        "payment_status": tradeline.get("payment_status"),
                        "date_opened": tradeline.get("date_opened"),
                        "date_closed": tradeline.get("date_closed"),
                        "bureaus_reporting": tradeline.get("bureaus", []),
                    }
                )

            for inquiry in raw_data.get("inquiries", []):
                parsed["inquiries"].append(
                    {
                        "creditor": inquiry.get("creditor_name"),
                        "date": inquiry.get("inquiry_date"),
                        "type": inquiry.get("inquiry_type"),
                        "bureau": inquiry.get("bureau"),
                    }
                )

            for record in raw_data.get("public_records", []):
                parsed["public_records"].append(
                    {
                        "type": record.get("record_type"),
                        "court": record.get("court_name"),
                        "filed_date": record.get("filed_date"),
                        "status": record.get("status"),
                        "amount": record.get("amount"),
                    }
                )

            for collection in raw_data.get("collections", []):
                parsed["collections"].append(
                    {
                        "creditor": collection.get("creditor_name"),
                        "original_creditor": collection.get("original_creditor"),
                        "account_number": collection.get("account_number_masked"),
                        "balance": collection.get("balance"),
                        "date_reported": collection.get("date_reported"),
                        "status": collection.get("status"),
                    }
                )

            return {"success": True, "parsed_data": parsed, "error": None}

        except Exception as e:
            return {
                "success": False,
                "parsed_data": None,
                "error": f"Parse error: {str(e)}",
            }


class IdentityIQAdapter(BaseCreditAdapter):
    """
    IdentityIQ API adapter.
    Requires B2B partnership agreement.
    Documentation: Contact IdentityIQ for API access.
    """

    PROVIDER_NAME = "identityiq"
    SANDBOX_BASE_URL = "https://api.sandbox.identityiq.com/v1"
    PRODUCTION_BASE_URL = "https://api.identityiq.com/v1"

    def __init__(self, api_key: Optional[str] = None, sandbox: bool = True):
        super().__init__(api_key, sandbox)
        if not api_key:
            self.api_key = os.environ.get("IDENTITYIQ_API_KEY")
        self.api_secret = os.environ.get("IDENTITYIQ_API_SECRET")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "X-Api-Key": self.api_key or "",
            "X-Api-Secret": self.api_secret or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def test_connection(self) -> bool:
        """Test IdentityIQ API connection."""
        if not self.is_configured:
            logger.warning("IdentityIQ API credentials not configured")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/ping", headers=self._get_headers(), timeout=15
            )
            return response.status_code in [200, 201]
        except requests.RequestException as e:
            logger.error(f"IdentityIQ connection test failed: {e}")
            return False

    def request_report(
        self,
        ssn_last4: str,
        dob: str,
        full_ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Request a credit report from IdentityIQ."""
        if not self.is_configured:
            return {
                "success": False,
                "request_id": None,
                "status": "error",
                "error": "IdentityIQ API credentials not configured. Please add IDENTITYIQ_API_KEY and IDENTITYIQ_API_SECRET to your environment.",
            }

        payload = {
            "consumer": {
                "ssn_last4": ssn_last4,
                "dob": dob,
                "first_name": first_name,
                "last_name": last_name,
            },
            "product": "3B",
            "bureaus": ["EX", "EQ", "TU"],
        }

        if full_ssn:
            payload["consumer"]["ssn"] = full_ssn
        if address:
            payload["consumer"]["address"] = address

        try:
            response = requests.post(
                f"{self.base_url}/credit/pull",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "request_id": data.get("transaction_id") or data.get("id"),
                    "status": data.get("status", "pending"),
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "request_id": None,
                    "status": "error",
                    "error": f"API error: {response.status_code} - {response.text[:200]}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "request_id": None,
                "status": "error",
                "error": f"Network error: {str(e)}",
            }

    def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of an IdentityIQ report request."""
        if not self.is_configured:
            return {
                "success": False,
                "status": "error",
                "scores": None,
                "error": "IdentityIQ API credentials not configured",
            }

        try:
            response = requests.get(
                f"{self.base_url}/credit/{request_id}/status",
                headers=self._get_headers(),
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status", "pending"),
                    "scores": (
                        {
                            "experian": data.get("scores", {}).get("EX"),
                            "equifax": data.get("scores", {}).get("EQ"),
                            "transunion": data.get("scores", {}).get("TU"),
                        }
                        if data.get("status") == "complete"
                        else None
                    ),
                    "report_ready": data.get("status") == "complete",
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "scores": None,
                    "error": f"API error: {response.status_code}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "status": "error",
                "scores": None,
                "error": f"Network error: {str(e)}",
            }

    def get_report(self, request_id: str) -> Dict[str, Any]:
        """Get the full report from IdentityIQ."""
        if not self.is_configured:
            return {
                "success": False,
                "raw_data": None,
                "error": "IdentityIQ API credentials not configured",
            }

        try:
            response = requests.get(
                f"{self.base_url}/credit/{request_id}/report",
                headers=self._get_headers(),
                timeout=60,
            )

            if response.status_code == 200:
                return {"success": True, "raw_data": response.json(), "error": None}
            else:
                return {
                    "success": False,
                    "raw_data": None,
                    "error": f"API error: {response.status_code}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "raw_data": None,
                "error": f"Network error: {str(e)}",
            }

    def parse_report(self, raw_data: Any) -> Dict[str, Any]:
        """Parse IdentityIQ report into structured format."""
        if not raw_data:
            return {"success": False, "error": "No data to parse"}

        try:
            parsed = {
                "provider": self.PROVIDER_NAME,
                "report_date": raw_data.get("pull_date"),
                "consumer": {
                    "name": raw_data.get("consumer", {}).get("name"),
                    "addresses": raw_data.get("consumer", {}).get("addresses", []),
                    "employers": raw_data.get("consumer", {}).get("employers", []),
                },
                "scores": {
                    "experian": raw_data.get("scores", {}).get("EX"),
                    "equifax": raw_data.get("scores", {}).get("EQ"),
                    "transunion": raw_data.get("scores", {}).get("TU"),
                },
                "tradelines": [],
                "inquiries": [],
                "public_records": [],
                "collections": [],
            }

            for tradeline in raw_data.get("trade_lines", []):
                parsed["tradelines"].append(
                    {
                        "creditor": tradeline.get("subscriber_name"),
                        "account_number": tradeline.get("account_number"),
                        "account_type": tradeline.get("type"),
                        "balance": tradeline.get("current_balance"),
                        "credit_limit": tradeline.get("high_credit"),
                        "payment_status": tradeline.get("payment_pattern"),
                        "date_opened": tradeline.get("open_date"),
                        "date_closed": tradeline.get("close_date"),
                        "bureaus_reporting": tradeline.get("bureaus", []),
                    }
                )

            return {"success": True, "parsed_data": parsed, "error": None}

        except Exception as e:
            return {
                "success": False,
                "parsed_data": None,
                "error": f"Parse error: {str(e)}",
            }


class ExperianConnectAdapter(BaseCreditAdapter):
    """
    Experian Connect API adapter.
    Documentation: https://developer.experian.com/
    Requires Experian developer account and approved application.
    """

    PROVIDER_NAME = "experian_connect"
    SANDBOX_BASE_URL = "https://sandbox.experian.com/consumerservices/v2"
    PRODUCTION_BASE_URL = "https://api.experian.com/consumerservices/v2"

    def __init__(self, api_key: Optional[str] = None, sandbox: bool = True):
        super().__init__(api_key, sandbox)
        if not api_key:
            self.api_key = os.environ.get("EXPERIAN_API_KEY")
        self.client_id = os.environ.get("EXPERIAN_CLIENT_ID")
        self.client_secret = os.environ.get("EXPERIAN_CLIENT_SECRET")
        self._access_token = None
        self._token_expires_at = None

    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token from Experian."""
        if self._access_token and self._token_expires_at:
            if datetime.utcnow().timestamp() < self._token_expires_at:
                return self._access_token

        if not self.client_id or not self.client_secret:
            return None

        try:
            token_url = f"{'https://sandbox.experian.com' if self.sandbox else 'https://api.experian.com'}/oauth2/v1/token"
            response = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                self._token_expires_at = (
                    datetime.utcnow().timestamp() + data.get("expires_in", 3600) - 60
                )
                return self._access_token
        except Exception as e:
            logger.error(f"Failed to get Experian access token: {e}")

        return None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}" if token else "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(
            (self.api_key and len(self.api_key) > 10)
            or (self.client_id and self.client_secret)
        )

    def test_connection(self) -> bool:
        """Test Experian Connect API connection."""
        if not self.is_configured:
            logger.warning("Experian Connect API credentials not configured")
            return False

        try:
            token = self._get_access_token()
            return token is not None
        except Exception as e:
            logger.error(f"Experian connection test failed: {e}")
            return False

    def request_report(
        self,
        ssn_last4: str,
        dob: str,
        full_ssn: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Request a credit report from Experian Connect."""
        if not self.is_configured:
            return {
                "success": False,
                "request_id": None,
                "status": "error",
                "error": "Experian Connect API credentials not configured. Please add EXPERIAN_CLIENT_ID and EXPERIAN_CLIENT_SECRET to your environment.",
            }

        payload = {
            "consumerPii": {
                "primaryApplicant": {
                    "name": {
                        "firstName": first_name or "",
                        "lastName": last_name or "",
                    },
                    "dob": {"dob": dob},
                    "ssn": {"ssn": full_ssn or ("XXXXX" + ssn_last4)},
                }
            },
            "requestor": {
                "subscriberCode": os.environ.get("EXPERIAN_SUBSCRIBER_CODE", "")
            },
            "productCodes": ["3B"],
        }

        if address:
            payload["consumerPii"]["primaryApplicant"]["currentAddress"] = {
                "line1": address.get("street", ""),
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "zipCode": address.get("zip", ""),
            }

        try:
            response = requests.post(
                f"{self.base_url}/credit/profile",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "request_id": data.get("reportId")
                    or data.get("transactionId")
                    or str(uuid.uuid4()),
                    "status": "complete" if data.get("creditProfile") else "pending",
                    "raw_data": data,
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "request_id": None,
                    "status": "error",
                    "error": f"API error: {response.status_code} - {response.text[:200]}",
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "request_id": None,
                "status": "error",
                "error": f"Network error: {str(e)}",
            }

    def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of an Experian report request."""
        return {
            "success": True,
            "status": "complete",
            "scores": None,
            "report_ready": True,
            "error": None,
        }

    def get_report(self, request_id: str) -> Dict[str, Any]:
        """Get the full report from Experian."""
        if not self.is_configured:
            return {
                "success": False,
                "raw_data": None,
                "error": "Experian Connect API credentials not configured",
            }

        return {
            "success": False,
            "raw_data": None,
            "error": "Experian Connect returns report data synchronously in request_report response",
        }

    def parse_report(self, raw_data: Any) -> Dict[str, Any]:
        """Parse Experian Connect report into structured format."""
        if not raw_data:
            return {"success": False, "error": "No data to parse"}

        try:
            credit_profile = raw_data.get("creditProfile", {})

            parsed = {
                "provider": self.PROVIDER_NAME,
                "report_date": datetime.utcnow().isoformat(),
                "consumer": {"name": None, "addresses": [], "employers": []},
                "scores": {
                    "experian": credit_profile.get("riskModel", {}).get("score"),
                    "equifax": None,
                    "transunion": None,
                },
                "tradelines": [],
                "inquiries": [],
                "public_records": [],
                "collections": [],
            }

            for tradeline in credit_profile.get("tradeline", []):
                parsed["tradelines"].append(
                    {
                        "creditor": tradeline.get("subscriberName"),
                        "account_number": tradeline.get("accountNumber"),
                        "account_type": tradeline.get("accountType"),
                        "balance": tradeline.get("balance"),
                        "credit_limit": tradeline.get("creditLimit"),
                        "payment_status": tradeline.get("paymentStatus"),
                        "date_opened": tradeline.get("openDate"),
                        "date_closed": tradeline.get("closeDate"),
                        "bureaus_reporting": ["experian"],
                    }
                )

            for inquiry in credit_profile.get("inquiry", []):
                parsed["inquiries"].append(
                    {
                        "creditor": inquiry.get("subscriberName"),
                        "date": inquiry.get("inquiryDate"),
                        "type": inquiry.get("inquiryType"),
                        "bureau": "experian",
                    }
                )

            return {"success": True, "parsed_data": parsed, "error": None}

        except Exception as e:
            return {
                "success": False,
                "parsed_data": None,
                "error": f"Parse error: {str(e)}",
            }


PROVIDER_ADAPTERS = {
    "smartcredit": SmartCreditAdapter,
    "identityiq": IdentityIQAdapter,
    "experian_connect": ExperianConnectAdapter,
}


class CreditPullService:
    """
    Provider-agnostic credit report pull service.

    Usage:
        service = CreditPullService(provider='smartcredit', sandbox=True)
        if service.test_connection():
            result = service.request_credit_report(
                client_id=123,
                ssn_last4='1234',
                dob='1990-01-15'
            )
    """

    def __init__(
        self,
        provider: str = "smartcredit",
        api_key: Optional[str] = None,
        sandbox: bool = True,
    ):
        """
        Initialize CreditPullService.

        Args:
            provider: Credit provider to use ('smartcredit', 'identityiq', 'experian_connect')
            api_key: API key for the provider. If None, will try environment variables.
            sandbox: If True, use sandbox environment. Default True.
        """
        self.sandbox = sandbox
        self.provider_name = provider
        self._integration_id = None

        self.set_provider(provider, api_key)

    def set_provider(self, provider_name: str, api_key: Optional[str] = None) -> bool:
        """
        Switch to a different credit provider.

        Args:
            provider_name: Name of the provider
            api_key: Optional API key override

        Returns:
            True if provider was set successfully
        """
        if provider_name not in PROVIDER_ADAPTERS:
            logger.error(
                f"Unknown provider: {provider_name}. Available: {list(PROVIDER_ADAPTERS.keys())}"
            )
            return False

        self.provider_name = provider_name
        adapter_class = PROVIDER_ADAPTERS[provider_name]
        self.adapter = adapter_class(api_key=api_key, sandbox=self.sandbox)

        logger.info(f"Set credit provider to: {provider_name}")
        return True

    @property
    def is_configured(self) -> bool:
        """Check if the current provider is configured."""
        return self.adapter.is_configured if hasattr(self, "adapter") else False

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
                    display_name=DISPLAY_NAME,
                    is_active=self.is_configured,
                    is_sandbox=self.sandbox,
                    connection_status=(
                        "configured" if self.is_configured else "not_configured"
                    ),
                    config_json={"provider": self.provider_name},
                )
                session.add(connection)
                session.commit()
                session.refresh(connection)

            self._integration_id = connection.id
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
        event_data: Dict = None,
        client_id: int = None,
        request_id: str = None,
        response_status: int = None,
        error_message: str = None,
        cost_cents: int = 0,
        db=None,
    ) -> None:
        """Log an integration event for audit trail."""
        session = db or SessionLocal()
        try:
            integration_id = self._get_integration_id(session)
            if not integration_id:
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
        Test connection to the credit provider API.

        Returns:
            True if connection is successful
        """
        if not hasattr(self, "adapter"):
            logger.error("No adapter configured")
            return False

        result = self.adapter.test_connection()

        self._log_event(
            event_type="test_connection",
            event_data={"provider": self.provider_name, "sandbox": self.sandbox},
            response_status=200 if result else 500,
            error_message=None if result else "Connection test failed",
        )

        return result

    def request_credit_report(
        self,
        client_id: int,
        ssn_last4: str,
        dob: str,
        full_ssn_encrypted: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request a credit report pull for a client.

        Args:
            client_id: Database ID of the client
            ssn_last4: Last 4 digits of SSN
            dob: Date of birth (YYYY-MM-DD format)
            full_ssn_encrypted: Optional encrypted full SSN for identity verification

        Returns:
            Dict with:
                - success: bool
                - request_id: Database ID of the pull request
                - external_id: Provider's request ID
                - status: Current status
                - error: Error message if failed
        """
        if not hasattr(self, "adapter"):
            return {
                "success": False,
                "request_id": None,
                "external_id": None,
                "status": "error",
                "error": "No credit provider configured",
            }

        session = SessionLocal()
        try:
            client = session.query(Client).filter_by(id=client_id).first()
            if not client:
                return {
                    "success": False,
                    "request_id": None,
                    "external_id": None,
                    "status": "error",
                    "error": f"Client {client_id} not found",
                }

            full_ssn = None
            if full_ssn_encrypted:
                from services.encryption import decrypt_value

                try:
                    full_ssn = decrypt_value(full_ssn_encrypted)
                except Exception as e:
                    logger.warning(f"Could not decrypt SSN: {e}")

            address = None
            if client.address_street:
                address = {
                    "street": client.address_street,
                    "city": client.address_city,
                    "state": client.address_state,
                    "zip": client.address_zip,
                }

            logger.info(
                f"Requesting credit report for client {client_id} via {self.provider_name}"
            )

            result = self.adapter.request_report(
                ssn_last4=ssn_last4,
                dob=dob,
                full_ssn=full_ssn,
                first_name=client.first_name,
                last_name=client.last_name,
                address=address,
            )

            pull_request = CreditPullRequest(
                client_id=client_id,
                provider=self.provider_name,
                external_request_id=result.get("request_id"),
                status=result.get("status", "pending"),
                bureaus_requested=["experian", "equifax", "transunion"],
                report_type="tri-merge",
                error_message=result.get("error"),
            )
            session.add(pull_request)
            session.commit()
            session.refresh(pull_request)

            self._log_event(
                event_type="request_credit_report",
                event_data={
                    "provider": self.provider_name,
                    "client_id": client_id,
                    "external_id": result.get("request_id"),
                },
                client_id=client_id,
                request_id=str(pull_request.id),
                response_status=200 if result.get("success") else 400,
                error_message=result.get("error"),
                db=session,
            )

            return {
                "success": result.get("success", False),
                "request_id": pull_request.id,
                "external_id": result.get("request_id"),
                "status": result.get("status", "pending"),
                "error": result.get("error"),
            }

        except Exception as e:
            session.rollback()
            error_msg = f"Error requesting credit report: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "request_id": None,
                "external_id": None,
                "status": "error",
                "error": error_msg,
            }
        finally:
            session.close()

    def get_report_status(self, request_id: int) -> Dict[str, Any]:
        """
        Get the status of a credit report pull request.

        Args:
            request_id: Database ID of the pull request

        Returns:
            Dict with:
                - success: bool
                - status: Current status
                - scores: Dict with bureau scores if complete
                - report_path: Path to saved report if available
                - error: Error message if failed
        """
        session = SessionLocal()
        try:
            pull_request = (
                session.query(CreditPullRequest).filter_by(id=request_id).first()
            )
            if not pull_request:
                return {
                    "success": False,
                    "status": "not_found",
                    "scores": None,
                    "report_path": None,
                    "error": f"Pull request {request_id} not found",
                }

            if pull_request.status == "complete":
                return {
                    "success": True,
                    "status": "complete",
                    "scores": {
                        "experian": pull_request.score_experian,
                        "equifax": pull_request.score_equifax,
                        "transunion": pull_request.score_transunion,
                    },
                    "report_path": pull_request.raw_response_path,
                    "parsed_data": pull_request.parsed_data,
                    "error": None,
                }

            if not pull_request.external_request_id:
                return {
                    "success": True,
                    "status": pull_request.status,
                    "scores": None,
                    "report_path": None,
                    "error": pull_request.error_message,
                }

            self.set_provider(pull_request.provider)
            status_result = self.adapter.get_status(pull_request.external_request_id)

            if (
                status_result.get("success")
                and status_result.get("status") == "complete"
            ):
                pull_request.status = "complete"
                if status_result.get("scores"):
                    scores = status_result["scores"]
                    pull_request.score_experian = scores.get("experian")
                    pull_request.score_equifax = scores.get("equifax")
                    pull_request.score_transunion = scores.get("transunion")
                pull_request.pulled_at = datetime.utcnow()
                pull_request.updated_at = datetime.utcnow()
                session.commit()

            return {
                "success": True,
                "status": status_result.get("status", pull_request.status),
                "scores": status_result.get("scores"),
                "report_path": pull_request.raw_response_path,
                "parsed_data": pull_request.parsed_data,
                "error": status_result.get("error"),
            }

        except Exception as e:
            error_msg = f"Error getting report status: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "status": "error",
                "scores": None,
                "report_path": None,
                "error": error_msg,
            }
        finally:
            session.close()

    def get_parsed_report(self, request_id: int) -> Dict[str, Any]:
        """
        Get the parsed credit report data.

        Args:
            request_id: Database ID of the pull request

        Returns:
            Dict with parsed report data
        """
        session = SessionLocal()
        try:
            pull_request = (
                session.query(CreditPullRequest).filter_by(id=request_id).first()
            )
            if not pull_request:
                return {
                    "success": False,
                    "parsed_data": None,
                    "error": f"Pull request {request_id} not found",
                }

            if pull_request.parsed_data:
                return {
                    "success": True,
                    "parsed_data": pull_request.parsed_data,
                    "error": None,
                }

            if not pull_request.external_request_id:
                return {
                    "success": False,
                    "parsed_data": None,
                    "error": "No external request ID - report not fetched from provider",
                }

            self.set_provider(pull_request.provider)
            report_result = self.adapter.get_report(pull_request.external_request_id)

            if not report_result.get("success"):
                return {
                    "success": False,
                    "parsed_data": None,
                    "error": report_result.get("error"),
                }

            parse_result = self.adapter.parse_report(report_result.get("raw_data"))

            if parse_result.get("success"):
                pull_request.parsed_data = parse_result.get("parsed_data")
                pull_request.updated_at = datetime.utcnow()
                session.commit()

            return parse_result

        except Exception as e:
            error_msg = f"Error getting parsed report: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "parsed_data": None, "error": error_msg}
        finally:
            session.close()

    def parse_credit_report(self, raw_data: Any) -> Dict[str, Any]:
        """
        Parse raw credit report data into structured format.

        Args:
            raw_data: Raw response data from credit provider

        Returns:
            Dict with parsed data
        """
        if not hasattr(self, "adapter"):
            return {
                "success": False,
                "parsed_data": None,
                "error": "No adapter configured",
            }

        return self.adapter.parse_report(raw_data)

    def get_client_pulls(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Get all credit pull requests for a client.

        Args:
            client_id: Database ID of the client

        Returns:
            List of pull request dicts
        """
        session = SessionLocal()
        try:
            pulls = (
                session.query(CreditPullRequest)
                .filter_by(client_id=client_id)
                .order_by(CreditPullRequest.created_at.desc())
                .all()
            )

            return [
                {
                    "id": pull.id,
                    "provider": pull.provider,
                    "status": pull.status,
                    "report_type": pull.report_type,
                    "scores": {
                        "experian": pull.score_experian,
                        "equifax": pull.score_equifax,
                        "transunion": pull.score_transunion,
                    },
                    "pulled_at": pull.pulled_at.isoformat() if pull.pulled_at else None,
                    "created_at": (
                        pull.created_at.isoformat() if pull.created_at else None
                    ),
                    "error_message": pull.error_message,
                }
                for pull in pulls
            ]
        except Exception as e:
            logger.error(f"Error getting client pulls: {e}")
            return []
        finally:
            session.close()

    def import_to_analysis(self, request_id: int) -> Dict[str, Any]:
        """
        Import a completed credit pull into the analysis pipeline.

        Args:
            request_id: Database ID of the pull request

        Returns:
            Dict with analysis_id if successful
        """
        session = SessionLocal()
        try:
            pull_request = (
                session.query(CreditPullRequest).filter_by(id=request_id).first()
            )
            if not pull_request:
                return {
                    "success": False,
                    "analysis_id": None,
                    "credit_report_id": None,
                    "error": f"Pull request {request_id} not found",
                }

            if pull_request.status != "complete":
                return {
                    "success": False,
                    "analysis_id": None,
                    "credit_report_id": None,
                    "error": f"Pull request not complete. Current status: {pull_request.status}",
                }

            client = session.query(Client).filter_by(id=pull_request.client_id).first()
            if not client:
                return {
                    "success": False,
                    "analysis_id": None,
                    "credit_report_id": None,
                    "error": "Client not found",
                }

            credit_report = CreditReport(
                client_id=client.id,
                client_name=client.name,
                credit_provider=pull_request.provider,
                report_html=(
                    str(pull_request.parsed_data) if pull_request.parsed_data else None
                ),
                report_date=pull_request.pulled_at or datetime.utcnow(),
            )
            session.add(credit_report)
            session.commit()
            session.refresh(credit_report)

            dispute_round = (client.current_dispute_round or 0) + 1

            analysis = Analysis(
                credit_report_id=credit_report.id,
                client_id=client.id,
                client_name=client.name,
                dispute_round=dispute_round,
                stage=1,
                analysis_mode="automated",
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)

            self._log_event(
                event_type="import_to_analysis",
                event_data={
                    "pull_request_id": request_id,
                    "credit_report_id": credit_report.id,
                    "analysis_id": analysis.id,
                },
                client_id=client.id,
                request_id=str(request_id),
                db=session,
            )

            return {
                "success": True,
                "analysis_id": analysis.id,
                "credit_report_id": credit_report.id,
                "error": None,
            }

        except Exception as e:
            session.rollback()
            error_msg = f"Error importing to analysis: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "analysis_id": None,
                "credit_report_id": None,
                "error": error_msg,
            }
        finally:
            session.close()

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of available credit providers and their configuration status.

        Returns:
            List of provider info dicts
        """
        providers = []

        for name, adapter_class in PROVIDER_ADAPTERS.items():
            adapter = adapter_class(sandbox=self.sandbox)
            providers.append(
                {
                    "name": name,
                    "display_name": name.replace("_", " ").title(),
                    "configured": adapter.is_configured,
                    "sandbox_url": adapter.SANDBOX_BASE_URL,
                    "production_url": adapter.PRODUCTION_BASE_URL,
                    "env_vars_required": self._get_required_env_vars(name),
                }
            )

        return providers

    def _get_required_env_vars(self, provider: str) -> List[str]:
        """Get list of required environment variables for a provider."""
        env_vars = {
            "smartcredit": ["SMARTCREDIT_API_KEY"],
            "identityiq": ["IDENTITYIQ_API_KEY", "IDENTITYIQ_API_SECRET"],
            "experian_connect": [
                "EXPERIAN_CLIENT_ID",
                "EXPERIAN_CLIENT_SECRET",
                "EXPERIAN_SUBSCRIBER_CODE",
            ],
        }
        return env_vars.get(provider, [])


def get_credit_pull_service(
    provider: str = "smartcredit", sandbox: bool = True
) -> CreditPullService:
    """
    Factory function to get a configured CreditPullService instance.

    Args:
        provider: Credit provider name
        sandbox: Whether to use sandbox mode

    Returns:
        Configured CreditPullService instance
    """
    return CreditPullService(provider=provider, sandbox=sandbox)
