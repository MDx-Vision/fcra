"""
USPS Address Validation Service

Uses the NEW USPS APIs (OAuth2) to validate and standardize addresses.
The old Web Tools API is being shut down January 25, 2026.

Features:
- Validates addresses exist and are deliverable
- Standardizes formatting (proper case, abbreviations)
- Returns ZIP+4 codes
- Flags undeliverable addresses before letters are sent
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import requests

from services.activity_logger import log_api_call

# USPS API Configuration (New OAuth2 API)
USPS_CLIENT_ID = os.environ.get(
    "USPS_CLIENT_ID", "rgAdfxqZRgogGP93LTV25vguQ2PGqrTvJK1gthUtCpjKAb8B"
)
USPS_CLIENT_SECRET = os.environ.get(
    "USPS_CLIENT_SECRET",
    "BA5JBMoQKMNdPgnq7GGqQ4p2gHSkXGGwU01ybmRkfon3glkj5Y90WPOYlKbuyPvh",
)

# API Endpoints
USPS_OAUTH_URL = "https://apis.usps.com/oauth2/v3/token"
USPS_ADDRESS_URL = "https://apis.usps.com/addresses/v3/address"

# For testing, use TEM (Testing Environment for Mailers)
# USPS_OAUTH_URL = "https://apis-tem.usps.com/oauth2/v3/token"
# USPS_ADDRESS_URL = "https://apis-tem.usps.com/addresses/v3/address"


@dataclass
class ValidatedAddress:
    """Represents a validated/standardized address"""

    street: str
    street2: str  # Apt, Suite, Unit, etc.
    city: str
    state: str
    zip5: str
    zip4: str  # +4 extension
    is_valid: bool
    error_message: str
    return_text: str  # USPS return text/footnotes
    was_corrected: bool  # True if USPS made corrections
    original: Dict[str, str]  # Original input for comparison


class AddressValidationService:
    """Service for validating addresses via USPS API"""

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or USPS_CLIENT_ID
        self.client_secret = client_secret or USPS_CLIENT_SECRET
        self.is_configured = bool(self.client_id and self.client_secret)
        self._access_token = None
        self._token_expires_at = None

    def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token, refreshing if needed"""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token

        # Request new token
        try:
            start_time = time.time()
            response = requests.post(
                USPS_OAUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            duration_ms = (time.time() - start_time) * 1000
            log_api_call("USPS", "/oauth2/v3/token", response.status_code, duration_ms)
            response.raise_for_status()
            data = response.json()

            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)  # Default 1 hour
            self._token_expires_at = datetime.now() + timedelta(
                seconds=expires_in - 60
            )  # Refresh 1 min early

            return self._access_token

        except requests.RequestException as e:
            print(f"USPS OAuth error: {e}")
            return None

    def validate_address(
        self, street: str, city: str, state: str, zip_code: str = "", street2: str = ""
    ) -> ValidatedAddress:
        """
        Validate and standardize an address using USPS API.

        Args:
            street: Street address (e.g., "123 Main St")
            city: City name
            state: 2-letter state code
            zip_code: 5 or 9 digit ZIP code (optional but recommended)
            street2: Apartment, Suite, Unit number (optional)

        Returns:
            ValidatedAddress with standardized data and validation status
        """
        original = {
            "street": street,
            "street2": street2,
            "city": city,
            "state": state,
            "zip_code": zip_code,
        }

        # If USPS not configured, return as-is with warning
        if not self.is_configured:
            return ValidatedAddress(
                street=street,
                street2=street2,
                city=city,
                state=state,
                zip5=zip_code[:5] if zip_code else "",
                zip4="",
                is_valid=True,  # Assume valid if can't verify
                error_message="USPS API not configured - address not verified",
                return_text="",
                was_corrected=False,
                original=original,
            )

        # Get OAuth token
        token = self._get_access_token()
        if not token:
            return ValidatedAddress(
                street=street,
                street2=street2,
                city=city,
                state=state,
                zip5=zip_code[:5] if zip_code else "",
                zip4="",
                is_valid=True,  # Assume valid if can't verify
                error_message="Could not authenticate with USPS API",
                return_text="",
                was_corrected=False,
                original=original,
            )

        # Build request payload
        # Combine street and street2 for the API
        street_address = street
        if street2:
            street_address = f"{street}, {street2}"

        # Clean ZIP code
        zip_clean = "".join(c for c in (zip_code or "") if c.isdigit())
        zip5 = zip_clean[:5] if len(zip_clean) >= 5 else zip_clean
        zip4 = zip_clean[5:9] if len(zip_clean) > 5 else ""

        params = {"streetAddress": street_address, "city": city, "state": state.upper()}
        if zip5:
            params["ZIPCode"] = zip5
        if zip4:
            params["ZIPPlus4"] = zip4

        try:
            start_time = time.time()
            response = requests.get(
                USPS_ADDRESS_URL,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            duration_ms = (time.time() - start_time) * 1000
            log_api_call(
                "USPS", "/addresses/v3/address", response.status_code, duration_ms
            )

            if response.status_code == 404:
                return ValidatedAddress(
                    street=street,
                    street2=street2,
                    city=city,
                    state=state,
                    zip5=zip5,
                    zip4="",
                    is_valid=False,
                    error_message="Address not found - please verify the address is correct",
                    return_text="",
                    was_corrected=False,
                    original=original,
                )

            response.raise_for_status()
            data = response.json()

            return self._parse_response(data, original)

        except requests.RequestException as e:
            return ValidatedAddress(
                street=street,
                street2=street2,
                city=city,
                state=state,
                zip5=zip5,
                zip4="",
                is_valid=False,
                error_message=f"USPS API error: {str(e)}",
                return_text="",
                was_corrected=False,
                original=original,
            )

    def _parse_response(self, data: Dict, original: Dict) -> ValidatedAddress:
        """Parse USPS API response"""
        try:
            address = data.get("address", {})

            # Extract validated fields
            street_address = address.get("streetAddress", "")
            secondary_address = address.get("secondaryAddress", "")
            city = address.get("city", "")
            state = address.get("state", "")
            zip5 = address.get("ZIPCode", "")
            zip4 = address.get("ZIPPlus4", "")

            # Check for delivery point validation
            # additionalInfo may contain warnings or notes
            additional_info = data.get("additionalInfo", {})
            delivery_point = additional_info.get("deliveryPoint", "")
            dpv_confirmation = additional_info.get("DPVConfirmation", "")

            # DPV codes: Y = confirmed, N = not confirmed, S = secondary missing, D = secondary not confirmed
            is_valid = dpv_confirmation in ("Y", "D", "") or not dpv_confirmation

            # Build return text from any warnings
            return_text = ""
            if additional_info.get("footnotes"):
                return_text = additional_info.get("footnotes", "")

            error_message = ""
            if not is_valid:
                error_message = "Address not confirmed as deliverable"
            elif dpv_confirmation == "S":
                error_message = (
                    "Secondary address (apt/unit) is missing - please add unit number"
                )
            elif dpv_confirmation == "D":
                error_message = "Secondary address exists but could not be confirmed"

            # Check if address was corrected
            was_corrected = (
                street_address.upper() != original["street"].upper()
                or city.upper() != original["city"].upper()
                or state.upper() != original["state"].upper()
            )

            return ValidatedAddress(
                street=street_address,
                street2=secondary_address,
                city=city,
                state=state,
                zip5=zip5,
                zip4=zip4,
                is_valid=is_valid,
                error_message=error_message,
                return_text=return_text,
                was_corrected=was_corrected,
                original=original,
            )

        except Exception as e:
            return ValidatedAddress(
                street=original["street"],
                street2=original["street2"],
                city=original["city"],
                state=original["state"],
                zip5=original["zip_code"][:5] if original["zip_code"] else "",
                zip4="",
                is_valid=False,
                error_message=f"Failed to parse USPS response: {str(e)}",
                return_text="",
                was_corrected=False,
                original=original,
            )

    def format_full_address(self, validated: ValidatedAddress) -> str:
        """Format validated address as single string"""
        parts = [validated.street]
        if validated.street2:
            parts.append(validated.street2)

        zip_full = validated.zip5
        if validated.zip4:
            zip_full = f"{validated.zip5}-{validated.zip4}"

        parts.append(f"{validated.city}, {validated.state} {zip_full}")
        return "\n".join(parts)

    def compare_addresses(self, validated: ValidatedAddress) -> Dict[str, Any]:
        """
        Compare original and validated addresses, highlighting differences.
        Useful for showing clients what was corrected.
        """
        original = validated.original

        corrections = []

        if validated.street.upper() != original["street"].upper():
            corrections.append(
                {
                    "field": "Street",
                    "original": original["street"],
                    "corrected": validated.street,
                }
            )

        if validated.city.upper() != original["city"].upper():
            corrections.append(
                {
                    "field": "City",
                    "original": original["city"],
                    "corrected": validated.city,
                }
            )

        if validated.state.upper() != original["state"].upper():
            corrections.append(
                {
                    "field": "State",
                    "original": original["state"],
                    "corrected": validated.state,
                }
            )

        orig_zip = original["zip_code"][:5] if original["zip_code"] else ""
        if validated.zip5 != orig_zip:
            corrections.append(
                {"field": "ZIP Code", "original": orig_zip, "corrected": validated.zip5}
            )

        # Check if apartment/unit was added
        if validated.street2 and not original["street2"]:
            corrections.append(
                {
                    "field": "Unit/Apt",
                    "original": "(none)",
                    "corrected": validated.street2,
                }
            )

        return {
            "was_corrected": len(corrections) > 0,
            "corrections": corrections,
            "is_valid": validated.is_valid,
            "error_message": validated.error_message,
            "formatted_address": self.format_full_address(validated),
        }


# Singleton instance
_service_instance = None


def get_address_validation_service() -> AddressValidationService:
    """Get or create the address validation service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AddressValidationService()
    return _service_instance


def validate_client_address(
    street: str, city: str, state: str, zip_code: str = "", street2: str = ""
) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to validate a client address.

    Returns:
        Tuple of (is_valid, result_dict)
        result_dict contains validated address and any corrections
    """
    service = get_address_validation_service()
    validated = service.validate_address(street, city, state, zip_code, street2)
    comparison = service.compare_addresses(validated)

    return validated.is_valid, {
        "is_valid": validated.is_valid,
        "validated_address": {
            "street": validated.street,
            "street2": validated.street2,
            "city": validated.city,
            "state": validated.state,
            "zip5": validated.zip5,
            "zip4": validated.zip4,
            "full_zip": (
                f"{validated.zip5}-{validated.zip4}"
                if validated.zip4
                else validated.zip5
            ),
        },
        "original_address": validated.original,
        "was_corrected": comparison["was_corrected"],
        "corrections": comparison["corrections"],
        "error_message": validated.error_message,
        "formatted_address": comparison["formatted_address"],
    }
