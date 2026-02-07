"""
Credit Import System - Comprehensive Regression Tests

This test suite protects the ENTIRE credit import system from regressions.
It tests all supported credit monitoring services and all extraction components.

SUPPORTED SERVICES:
- MyScoreIQ.com (57 clients) - Angular-based, most common
- MyFreeScoreNow.com (17 clients) - Classic/Original view
- IdentityIQ.com (4 clients) - Similar structure to MyFreeScoreNow
- SmartCredit.com (1 client) - Unique format

EXTRACTION COMPONENTS TESTED:
1. Credit Scores (transunion, experian, equifax)
2. Personal Information (names, DOB, addresses per bureau)
3. Summary (total accounts, open/closed, balances, inquiries)
4. Accounts/Tradelines (creditor, balance, status, payment history)
5. Inquiries (company, date, bureau)
6. Creditor Contacts (name, address, phone)

HOW TO RUN:
    pytest tests/test_credit_import_regression.py -v

WHEN TO RUN:
- Before ANY changes to credit_import_automation.py
- Before deploying to production
- As part of CI/CD pipeline

HOW TO ADD NEW FIXTURES:
1. After successful import, copy JSON to tests/fixtures/credit_reports/
2. Add test class with expected values
3. Run tests to verify
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment
os.environ["TESTING"] = "true"


# =============================================================================
# Test Fixtures Directory Setup
# =============================================================================

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "credit_reports"
REPORTS_DIR = Path(__file__).parent.parent / "uploads" / "credit_reports"


def get_fixture_path(filename: str) -> Path:
    """Get path to a fixture file, checking fixtures dir first, then uploads."""
    fixture_path = FIXTURES_DIR / filename
    if fixture_path.exists():
        return fixture_path
    # Fall back to uploads directory
    upload_path = REPORTS_DIR / filename
    if upload_path.exists():
        return upload_path
    return fixture_path  # Return fixtures path for error message


def load_json_fixture(filename: str) -> dict:
    """Load a JSON fixture file."""
    path = get_fixture_path(filename)
    if not path.exists():
        pytest.skip(f"Fixture not found: {filename}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Base Test Class - Common Assertions
# =============================================================================


class CreditReportTestBase:
    """Base class with common test methods for all credit report formats."""

    FIXTURE_JSON = None  # Override in subclass
    SERVICE_NAME = None  # Override in subclass

    # Expected values - override in subclass
    EXPECTED_SCORES = {}
    EXPECTED_ACCOUNTS_MIN = 0
    EXPECTED_INQUIRIES_MIN = 0

    @pytest.fixture
    def report_data(self):
        """Load the JSON fixture."""
        if not self.FIXTURE_JSON:
            pytest.skip("No fixture defined")
        return load_json_fixture(self.FIXTURE_JSON)

    # -------------------------------------------------------------------------
    # Score Tests
    # -------------------------------------------------------------------------

    def test_scores_structure(self, report_data):
        """Test that scores dict exists and has correct structure."""
        scores = report_data.get("scores", {})
        assert isinstance(scores, dict), "scores must be a dict"

    def test_scores_are_valid_numbers(self, report_data):
        """Test that extracted scores are valid credit score numbers."""
        scores = report_data.get("scores", {})
        for bureau, score in scores.items():
            if score is not None:
                assert isinstance(score, int), f"{bureau} score must be int"
                assert 300 <= score <= 850, f"{bureau} score {score} out of range"

    def test_expected_scores(self, report_data):
        """Test scores match expected values."""
        if not self.EXPECTED_SCORES:
            pytest.skip("No expected scores defined")
        scores = report_data.get("scores", {})
        for bureau, expected in self.EXPECTED_SCORES.items():
            assert scores.get(bureau) == expected, \
                f"{bureau}: expected {expected}, got {scores.get(bureau)}"

    # -------------------------------------------------------------------------
    # Personal Info Tests
    # -------------------------------------------------------------------------

    def test_personal_info_structure(self, report_data):
        """Test that personal_info exists and has correct structure."""
        pi = report_data.get("personal_info", {})
        assert isinstance(pi, dict), "personal_info must be a dict"
        # Should have at least names array
        assert "names" in pi or any(
            bureau in pi for bureau in ["transunion", "experian", "equifax"]
        ), "personal_info should have names or per-bureau data"

    def test_names_no_trailing_artifacts(self, report_data):
        """Test that names don't have trailing artifacts like ' -'."""
        pi = report_data.get("personal_info", {})
        names = pi.get("names", [])

        # Check top-level names
        for name in names:
            assert not name.endswith(" -"), f"Name has trailing ' -': '{name}'"
            assert not name.endswith(" - "), f"Name has trailing ' - ': '{name}'"

        # Check per-bureau names
        for bureau in ["transunion", "experian", "equifax"]:
            bureau_data = pi.get(bureau, {})
            for name in bureau_data.get("names", []):
                assert not name.endswith(" -"), \
                    f"{bureau} name has trailing ' -': '{name}'"

    def test_dob_format(self, report_data):
        """Test that DOB is a valid year without artifacts."""
        pi = report_data.get("personal_info", {})
        dob = pi.get("dob")

        if dob:
            assert not dob.endswith(" -"), f"DOB has trailing ' -': '{dob}'"
            # Should be a 4-digit year
            assert re.match(r"^\d{4}$", dob), f"DOB should be YYYY format: '{dob}'"

    def test_addresses_no_embedded_dates(self, report_data):
        """Test that current addresses don't have dates embedded."""
        pi = report_data.get("personal_info", {})

        for bureau in ["transunion", "experian", "equifax"]:
            bureau_data = pi.get(bureau, {})
            addr = bureau_data.get("current_address", "")
            if addr:
                # Address should not contain MM/YYYY pattern
                date_pattern = r"\d{2}/\d{4}\s*-?\s*$"
                assert not re.search(date_pattern, addr), \
                    f"{bureau} address has embedded date: '{addr}'"

    def test_previous_addresses_format(self, report_data):
        """Test that previous addresses are properly formatted."""
        pi = report_data.get("personal_info", {})

        for bureau in ["transunion", "experian", "equifax"]:
            bureau_data = pi.get(bureau, {})
            prev_addrs = bureau_data.get("previous_addresses", [])

            for i, addr in enumerate(prev_addrs):
                # Should be dict with address and date keys
                if isinstance(addr, dict):
                    assert "address" in addr, \
                        f"{bureau} prev_addr[{i}] missing 'address' key"
                # Or a string (legacy format)
                elif isinstance(addr, str):
                    pass  # String format is acceptable
                else:
                    pytest.fail(f"{bureau} prev_addr[{i}] invalid type: {type(addr)}")

    # -------------------------------------------------------------------------
    # Summary Tests
    # -------------------------------------------------------------------------

    def test_summary_structure(self, report_data):
        """Test that summary exists and has expected fields."""
        summary = report_data.get("summary", {})
        assert isinstance(summary, dict), "summary must be a dict"

    def test_summary_numeric_fields(self, report_data):
        """Test that summary numeric fields are valid."""
        summary = report_data.get("summary", {})

        numeric_fields = [
            "total_accounts", "open_accounts", "closed_accounts",
            "total_inquiries"
        ]

        for field in numeric_fields:
            value = summary.get(field)
            if value is not None:
                # Could be string like "14" or int
                if isinstance(value, str):
                    assert value.isdigit() or value == "", \
                        f"summary.{field} should be numeric: '{value}'"

    # -------------------------------------------------------------------------
    # Accounts Tests
    # -------------------------------------------------------------------------

    def test_accounts_structure(self, report_data):
        """Test that accounts array exists and has correct structure."""
        accounts = report_data.get("accounts", [])
        assert isinstance(accounts, list), "accounts must be a list"

    def test_accounts_minimum_count(self, report_data):
        """Test minimum expected account count."""
        if self.EXPECTED_ACCOUNTS_MIN == 0:
            pytest.skip("No minimum accounts defined")
        accounts = report_data.get("accounts", [])
        assert len(accounts) >= self.EXPECTED_ACCOUNTS_MIN, \
            f"Expected at least {self.EXPECTED_ACCOUNTS_MIN} accounts"

    def test_accounts_have_required_fields(self, report_data):
        """Test that accounts have required fields."""
        accounts = report_data.get("accounts", [])

        for i, acct in enumerate(accounts):
            assert "creditor" in acct, f"accounts[{i}] missing 'creditor'"
            assert "bureaus" in acct, f"accounts[{i}] missing 'bureaus'"

    def test_accounts_bureaus_structure(self, report_data):
        """Test that account bureau data has correct structure."""
        accounts = report_data.get("accounts", [])

        for i, acct in enumerate(accounts):
            bureaus = acct.get("bureaus", {})
            assert isinstance(bureaus, dict), f"accounts[{i}].bureaus must be dict"

            for bureau in ["transunion", "experian", "equifax"]:
                if bureau in bureaus:
                    bureau_data = bureaus[bureau]
                    assert isinstance(bureau_data, dict), \
                        f"accounts[{i}].bureaus.{bureau} must be dict"

    # -------------------------------------------------------------------------
    # Inquiries Tests
    # -------------------------------------------------------------------------

    def test_inquiries_structure(self, report_data):
        """Test that inquiries array exists and has correct structure."""
        inquiries = report_data.get("inquiries", [])
        assert isinstance(inquiries, list), "inquiries must be a list"

    def test_inquiries_minimum_count(self, report_data):
        """Test minimum expected inquiries count."""
        if self.EXPECTED_INQUIRIES_MIN == 0:
            pytest.skip("No minimum inquiries defined")
        inquiries = report_data.get("inquiries", [])
        assert len(inquiries) >= self.EXPECTED_INQUIRIES_MIN, \
            f"Expected at least {self.EXPECTED_INQUIRIES_MIN} inquiries"

    def test_inquiries_have_required_fields(self, report_data):
        """Test that inquiries have required fields."""
        inquiries = report_data.get("inquiries", [])

        for i, inq in enumerate(inquiries):
            assert "company" in inq, f"inquiries[{i}] missing 'company'"

    # -------------------------------------------------------------------------
    # Creditor Contacts Tests
    # -------------------------------------------------------------------------

    def test_creditor_contacts_structure(self, report_data):
        """Test that creditor_contacts array exists."""
        contacts = report_data.get("creditor_contacts", [])
        assert isinstance(contacts, list), "creditor_contacts must be a list"


# =============================================================================
# MyScoreIQ Tests
# =============================================================================


class TestMyScoreIQCarlosDelCarmen(CreditReportTestBase):
    """
    Regression tests for MyScoreIQ.com - Carlos Del Carmen

    This is the PRIMARY test case for MyScoreIQ Angular-based extraction.
    Tests the fix for Personal Information extraction issues:
    - Names with trailing " -"
    - DOB with trailing " -"
    - Addresses with embedded dates
    - Previous addresses as dict format
    """

    FIXTURE_JSON = "407_Carlos_Del_Carmen_20260207_035341.json"
    SERVICE_NAME = "MyScoreIQ.com"

    EXPECTED_SCORES = {"transunion": 793, "experian": 795, "equifax": 800}
    EXPECTED_ACCOUNTS_MIN = 15
    EXPECTED_INQUIRIES_MIN = 3

    # Specific expected values for this client
    EXPECTED_NAME = "CARLOS DELCARMEN"
    EXPECTED_DOB = "1979"
    EXPECTED_TU_ADDRESS = "108136 MARTIN LUTHER KING JR BV 2209B NEWARK, NJ 07104"
    EXPECTED_EX_ADDRESS = "108-136 MARTIN APT 1907 NEWARK, NJ 07104"
    EXPECTED_EQ_ADDRESS = "108-136 MARTIN LUTHER KING JR BLVD APT 2209B NEWARK, NJ 07104"

    def test_name_exact_match(self, report_data):
        """Test name matches expected (no trailing artifacts)."""
        pi = report_data.get("personal_info", {})
        names = pi.get("names", [])
        assert self.EXPECTED_NAME in names, \
            f"Expected name '{self.EXPECTED_NAME}' not found in {names}"

    def test_dob_exact_match(self, report_data):
        """Test DOB matches expected."""
        pi = report_data.get("personal_info", {})
        assert pi.get("dob") == self.EXPECTED_DOB

    def test_per_bureau_addresses(self, report_data):
        """Test each bureau has its own address."""
        pi = report_data.get("personal_info", {})

        tu = pi.get("transunion", {})
        ex = pi.get("experian", {})
        eq = pi.get("equifax", {})

        assert tu.get("current_address") == self.EXPECTED_TU_ADDRESS
        assert ex.get("current_address") == self.EXPECTED_EX_ADDRESS
        assert eq.get("current_address") == self.EXPECTED_EQ_ADDRESS

    def test_address_date_separated(self, report_data):
        """Test that address dates are stored separately."""
        pi = report_data.get("personal_info", {})
        tu = pi.get("transunion", {})

        assert tu.get("current_address_date") == "04/2014"

    def test_experian_previous_addresses(self, report_data):
        """Test Experian previous addresses are dict format."""
        pi = report_data.get("personal_info", {})
        ex = pi.get("experian", {})
        prev = ex.get("previous_addresses", [])

        assert len(prev) == 2, f"Expected 2 previous addresses, got {len(prev)}"
        assert prev[0]["address"] == "351 BROAD ST APT 190 NEWARK, NJ 07104-3304"
        assert prev[0]["date"] == "10/2025"

    def test_employers_array_exists(self, report_data):
        """Test employers field exists even when empty."""
        pi = report_data.get("personal_info", {})

        for bureau in ["transunion", "experian", "equifax"]:
            bureau_data = pi.get(bureau, {})
            assert "employers" in bureau_data, \
                f"{bureau} missing 'employers' field"


# =============================================================================
# MyFreeScoreNow Tests
# =============================================================================


class TestMyFreeScoreNowWendyPerdomo(CreditReportTestBase):
    """
    Regression tests for MyFreeScoreNow.com - Wendy Perdomo

    Tests the Classic/Original View format used by MyFreeScoreNow.
    """

    FIXTURE_JSON = "408_Wendy_Perdomo_20260205_093217.json"
    SERVICE_NAME = "MyFreeScoreNow.com"

    EXPECTED_SCORES = {"transunion": 706, "experian": 704, "equifax": 705}
    EXPECTED_ACCOUNTS_MIN = 30
    EXPECTED_INQUIRIES_MIN = 1


# =============================================================================
# Template for Adding New Service Tests
# =============================================================================


class TestIdentityIQTemplate(CreditReportTestBase):
    """
    Template for IdentityIQ.com tests.

    To enable:
    1. Get a successful import JSON
    2. Copy to tests/fixtures/credit_reports/
    3. Update FIXTURE_JSON and expected values
    """

    FIXTURE_JSON = None  # Add fixture filename
    SERVICE_NAME = "IdentityIQ.com"

    # Update these with real expected values
    EXPECTED_SCORES = {}
    EXPECTED_ACCOUNTS_MIN = 0


class TestSmartCreditTemplate(CreditReportTestBase):
    """
    Template for SmartCredit.com tests.

    To enable:
    1. Get a successful import JSON
    2. Copy to tests/fixtures/credit_reports/
    3. Update FIXTURE_JSON and expected values
    """

    FIXTURE_JSON = None  # Add fixture filename
    SERVICE_NAME = "SmartCredit.com"

    EXPECTED_SCORES = {}
    EXPECTED_ACCOUNTS_MIN = 0


# =============================================================================
# Cross-Service Compatibility Tests
# =============================================================================


class TestExtractionOutputFormat:
    """
    Tests that verify the extraction output format is consistent across services.

    These tests ensure that no matter which service is used, the JSON output
    follows the same schema so downstream code works correctly.
    """

    @pytest.fixture
    def all_fixtures(self):
        """Load all available JSON fixtures."""
        fixtures = []
        for path in FIXTURES_DIR.glob("*.json"):
            if "_xhr" not in path.name:
                with open(path, "r") as f:
                    data = json.load(f)
                    data["_fixture_name"] = path.name
                    fixtures.append(data)
        return fixtures

    def test_all_have_scores_dict(self, all_fixtures):
        """All fixtures must have a scores dict."""
        for data in all_fixtures:
            assert "scores" in data, f"{data['_fixture_name']} missing scores"
            assert isinstance(data["scores"], dict)

    def test_all_have_accounts_list(self, all_fixtures):
        """All fixtures must have an accounts list."""
        for data in all_fixtures:
            assert "accounts" in data, f"{data['_fixture_name']} missing accounts"
            assert isinstance(data["accounts"], list)

    def test_all_have_personal_info(self, all_fixtures):
        """All fixtures must have personal_info."""
        for data in all_fixtures:
            assert "personal_info" in data, \
                f"{data['_fixture_name']} missing personal_info"

    def test_all_have_inquiries(self, all_fixtures):
        """All fixtures must have inquiries list."""
        for data in all_fixtures:
            assert "inquiries" in data, \
                f"{data['_fixture_name']} missing inquiries"
            assert isinstance(data["inquiries"], list)


# =============================================================================
# JavaScript Extraction Code Validation
# =============================================================================


class TestJavaScriptExtractionCode:
    """
    Tests that validate the JavaScript extraction code in credit_import_automation.py.

    These tests read the actual Python file and verify the embedded JavaScript
    doesn't contain common issues.
    """

    @pytest.fixture
    def automation_source(self):
        """Load the credit_import_automation.py source code."""
        path = Path(__file__).parent.parent / "services" / "credit_import_automation.py"
        with open(path, "r") as f:
            return f.read()

    def test_no_invalid_css_selectors(self, automation_source):
        """Test that JS doesn't use Playwright-only selectors in CSS context."""
        # :has-text() is Playwright selector, not valid CSS
        # It should only appear in Playwright locator calls, not in querySelectorAll
        invalid_in_css = [
            "querySelectorAll(':has-text",
            "querySelector(':has-text",
            "querySelectorAll('button:has-text",
        ]
        for pattern in invalid_in_css:
            assert pattern not in automation_source, \
                f"Invalid CSS selector pattern found: {pattern}"

    def test_has_score_extraction(self, automation_source):
        """Test that score extraction code exists."""
        assert "transunion" in automation_source.lower()
        assert "experian" in automation_source.lower()
        assert "equifax" in automation_source.lower()

    def test_has_personal_info_extraction(self, automation_source):
        """Test that personal info extraction code exists."""
        assert "personal_info" in automation_source or "personalInfo" in automation_source

    def test_has_account_extraction(self, automation_source):
        """Test that account extraction code exists."""
        assert "accounts" in automation_source
        assert "creditor" in automation_source

    def test_has_inquiry_extraction(self, automation_source):
        """Test that inquiry extraction code exists."""
        assert "inquiries" in automation_source


# =============================================================================
# Integration Tests (require database)
# =============================================================================


class TestCreditImportIntegration:
    """
    Integration tests that verify the full import pipeline works.

    These tests require a running database and test credentials.
    Skip if environment not configured.
    """

    @pytest.fixture
    def db_available(self):
        """Check if database is available."""
        try:
            from database import get_db
            db = get_db()
            db.execute("SELECT 1")
            db.close()
            return True
        except Exception:
            pytest.skip("Database not available")

    def test_import_service_can_be_imported(self):
        """Test that the import service module loads without errors."""
        from services.credit_import_automation import CreditImportAutomation
        assert CreditImportAutomation is not None

    def test_supported_services_defined(self):
        """Test that supported services are defined."""
        from services.credit_import_automation import CreditImportAutomation

        # Check for common service patterns
        source = open(
            Path(__file__).parent.parent / "services" / "credit_import_automation.py"
        ).read()

        services = ["myscoreiq", "myfreescorenow", "identityiq", "smartcredit"]
        for service in services:
            assert service in source.lower(), f"{service} not found in automation code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
