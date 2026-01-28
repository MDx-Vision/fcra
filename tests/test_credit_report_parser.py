"""
Comprehensive Unit Tests for CreditReportParser

Tests cover:
- parse() - Main parsing entry point
- _extract_scores() - Credit score extraction
- _extract_personal_info() - Personal information parsing
- _extract_accounts() - Account data extraction
- _extract_inquiries() - Inquiry record parsing
- _extract_collections() - Collection account extraction
- _extract_summary_counts() - Summary counts
- Edge cases and error handling
"""

import pytest
from services.credit_report_parser import CreditReportParser, parse_credit_report


# =============================================================================
# Fixtures - HTML Templates for Testing
# =============================================================================

@pytest.fixture
def minimal_html():
    """Minimal valid HTML structure."""
    return "<html><body></body></html>"


@pytest.fixture
def empty_html():
    """Empty HTML content."""
    return ""


@pytest.fixture
def full_credit_report_html():
    """Complete credit report HTML with all sections."""
    return """
    <html>
    <body>
        <div id="Summary">
            <table>
                <tr>
                    <td class="label">Collections:</td>
                    <td class="info1">2</td>
                    <td class="info2">2</td>
                    <td class="info3">1</td>
                </tr>
                <tr>
                    <td class="label">Public Records:</td>
                    <td class="info1">1</td>
                    <td class="info2">-</td>
                    <td class="info3">1</td>
                </tr>
                <tr>
                    <td class="label">Open Accounts:</td>
                    <td class="info1">5</td>
                    <td class="info2">5</td>
                    <td class="info3">5</td>
                </tr>
            </table>
        </div>

        <div id="CreditScore">
            <table class="rpt_content_table">
                <tr>
                    <td class="label">FICO Score 8:</td>
                    <td class="info1">720</td>
                    <td class="info2">715</td>
                    <td class="info3">725</td>
                </tr>
            </table>
        </div>

        <div id="PersonalInformation">
            <table>
                <tr>
                    <td>Name:</td>
                    <td class="info1">John Doe</td>
                    <td class="info2">John Doe</td>
                    <td class="info3">John A Doe</td>
                </tr>
            </table>
        </div>

        <div class="rpt_content_wrapper">
            <div id="AccountHistory">
                <table class="crPrint">
                    <div class="sub_header ng-binding">CHASE CREDIT CARD</div>
                    <table class="rpt_content_table">
                        <tr>
                            <td class="label">Account #:</td>
                            <td class="info1">****1234</td>
                            <td class="info2">****1234</td>
                            <td class="info3">****1234</td>
                        </tr>
                        <tr>
                            <td class="label">Account Type:</td>
                            <td class="info1">Revolving</td>
                            <td class="info2">Revolving</td>
                            <td class="info3">Revolving</td>
                        </tr>
                        <tr>
                            <td class="label">Balance:</td>
                            <td class="info1">$5,000</td>
                            <td class="info2">$5,000</td>
                            <td class="info3">$5,000</td>
                        </tr>
                        <tr>
                            <td class="label">Credit Limit:</td>
                            <td class="info1">$10,000</td>
                            <td class="info2">$10,000</td>
                            <td class="info3">$10,000</td>
                        </tr>
                        <tr>
                            <td class="label">Date Opened:</td>
                            <td class="info1">01/15/2020</td>
                            <td class="info2">01/15/2020</td>
                            <td class="info3">01/15/2020</td>
                        </tr>
                        <tr>
                            <td class="label">Status:</td>
                            <td class="info1">Open</td>
                            <td class="info2">Open</td>
                            <td class="info3">Open</td>
                        </tr>
                    </table>
                </table>
            </div>
        </div>

        <div id="Inquiries">
            <table>
                <tr class="ng-scope">
                    <td class="info1">BANK OF AMERICA</td>
                    <td class="info2">Hard Inquiry</td>
                    <td class="info3">12/01/2023</td>
                    <td class="info4">TransUnion</td>
                </tr>
            </table>
        </div>

        <div id="PublicRecords">
            <div class="sub_header">BANKRUPTCY - CHAPTER 7</div>
            <table class="rpt_content_table">
                <tr>
                    <td class="label">Date Filed:</td>
                    <td class="info1">06/15/2019</td>
                    <td class="info2">-</td>
                    <td class="info3">06/15/2019</td>
                </tr>
            </table>
        </div>

        <div id="CreditorContacts">
            <table class="rpt_content_table">
                <tr class="ng-scope">
                    <td class="info1">CHASE</td>
                    <td class="info2">123 Main St, New York, NY 10001</td>
                    <td class="info3">800-555-1234</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def scores_html():
    """HTML with credit scores section."""
    return """
    <html>
    <body>
        <div id="CreditScore">
            <table class="rpt_content_table">
                <tr>
                    <td class="label">FICO Score 8:</td>
                    <td class="info1">750</td>
                    <td class="info2">740</td>
                    <td class="info3">745</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def accounts_html():
    """HTML with account history section."""
    return """
    <html>
    <body>
        <div class="rpt_content_wrapper">
            <div id="AccountHistory">
                <table class="crPrint">
                    <div class="sub_header ng-binding">CAPITAL ONE</div>
                    <table class="rpt_content_table">
                        <tr>
                            <td class="label">Account #:</td>
                            <td class="info1">****5678</td>
                            <td class="info2">****5678</td>
                            <td class="info3">****5678</td>
                        </tr>
                        <tr>
                            <td class="label">Account Type:</td>
                            <td class="info1">Revolving</td>
                            <td class="info2">Revolving</td>
                            <td class="info3">Revolving</td>
                        </tr>
                        <tr>
                            <td class="label">Balance:</td>
                            <td class="info1">$2,500</td>
                            <td class="info2">$2,500</td>
                            <td class="info3">$2,500</td>
                        </tr>
                        <tr>
                            <td class="label">Status:</td>
                            <td class="info1">Open</td>
                            <td class="info2">Open</td>
                            <td class="info3">Open</td>
                        </tr>
                        <tr>
                            <td class="label">Times 30 Days Late:</td>
                            <td class="info1">0</td>
                            <td class="info2">0</td>
                            <td class="info3">0</td>
                        </tr>
                        <tr>
                            <td class="label">Times 60 Days Late:</td>
                            <td class="info1">1</td>
                            <td class="info2">1</td>
                            <td class="info3">1</td>
                        </tr>
                        <tr>
                            <td class="label">Times 90 Days Late:</td>
                            <td class="info1">0</td>
                            <td class="info2">0</td>
                            <td class="info3">0</td>
                        </tr>
                    </table>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def collections_html():
    """HTML with collection accounts."""
    return """
    <html>
    <body>
        <div id="Summary">
            <table>
                <tr>
                    <td class="label">Collections:</td>
                    <td class="info1">1</td>
                    <td class="info2">1</td>
                    <td class="info3">1</td>
                </tr>
            </table>
        </div>
        <div class="rpt_content_wrapper">
            <div id="AccountHistory">
                <table class="crPrint">
                    <div class="sub_header ng-binding">MIDLAND CREDIT (Original Creditor: AT&T)</div>
                    <table class="rpt_content_table">
                        <tr>
                            <td class="label">Account Type:</td>
                            <td class="info1">Collection</td>
                            <td class="info2">Collection</td>
                            <td class="info3">Collection</td>
                        </tr>
                        <tr>
                            <td class="label">Balance:</td>
                            <td class="info1">$500</td>
                            <td class="info2">$500</td>
                            <td class="info3">$500</td>
                        </tr>
                        <tr>
                            <td class="label">Status:</td>
                            <td class="info1">Collection</td>
                            <td class="info2">Collection</td>
                            <td class="info3">Collection</td>
                        </tr>
                    </table>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def inquiries_html():
    """HTML with inquiries section."""
    return """
    <html>
    <body>
        <div id="Inquiries">
            <table>
                <tr class="ng-scope">
                    <td class="info1">WELLS FARGO</td>
                    <td class="info2">Hard Inquiry</td>
                    <td class="info3">11/15/2023</td>
                    <td class="info4">Experian</td>
                </tr>
                <tr class="ng-scope">
                    <td class="info1">CITIBANK</td>
                    <td class="info2">Hard Inquiry</td>
                    <td class="info3">10/01/2023</td>
                    <td class="info4">Equifax</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """


# =============================================================================
# Test Class: Basic Initialization
# =============================================================================

class TestCreditReportParserInit:
    """Tests for CreditReportParser initialization."""

    def test_init_with_valid_html(self, minimal_html):
        """Test parser initializes with valid HTML."""
        parser = CreditReportParser(minimal_html)
        assert parser.html == minimal_html
        assert parser.service == "unknown"
        assert parser.soup is not None

    def test_init_with_service_name(self, minimal_html):
        """Test parser initializes with custom service name."""
        parser = CreditReportParser(minimal_html, service_name="myscoreiq")
        assert parser.service == "myscoreiq"

    def test_init_with_empty_html(self, empty_html):
        """Test parser handles empty HTML."""
        parser = CreditReportParser(empty_html)
        assert parser.html == ""
        assert parser.soup is not None

    def test_init_summary_counts_none(self, minimal_html):
        """Test _summary_counts is None before parse()."""
        parser = CreditReportParser(minimal_html)
        assert parser._summary_counts is None


# =============================================================================
# Test Class: parse() Method
# =============================================================================

class TestParseMethod:
    """Tests for the main parse() method."""

    def test_parse_returns_dict(self, minimal_html):
        """Test parse() returns a dictionary."""
        parser = CreditReportParser(minimal_html)
        result = parser.parse()
        assert isinstance(result, dict)

    def test_parse_contains_required_keys(self, minimal_html):
        """Test parse() result contains all required keys."""
        parser = CreditReportParser(minimal_html)
        result = parser.parse()
        required_keys = [
            "scores", "personal_info", "accounts", "inquiries",
            "public_records", "collections", "creditor_contacts", "summary"
        ]
        for key in required_keys:
            assert key in result

    def test_parse_summary_counts(self, full_credit_report_html):
        """Test parse() correctly counts items in summary."""
        parser = CreditReportParser(full_credit_report_html)
        result = parser.parse()
        assert "total_accounts" in result["summary"]
        assert "total_inquiries" in result["summary"]
        assert "total_collections" in result["summary"]
        assert "total_public_records" in result["summary"]

    def test_parse_empty_html_returns_empty_collections(self, empty_html):
        """Test parse() with empty HTML returns empty collections."""
        parser = CreditReportParser(empty_html)
        result = parser.parse()
        assert result["accounts"] == []
        assert result["inquiries"] == []
        assert result["collections"] == []

    def test_parse_sets_summary_counts(self, full_credit_report_html):
        """Test parse() sets _summary_counts attribute."""
        parser = CreditReportParser(full_credit_report_html)
        parser.parse()
        assert parser._summary_counts is not None


# =============================================================================
# Test Class: _extract_scores() Method
# =============================================================================

class TestExtractScores:
    """Tests for credit score extraction."""

    def test_extract_scores_returns_dict(self, minimal_html):
        """Test _extract_scores returns a dictionary."""
        parser = CreditReportParser(minimal_html)
        scores = parser._extract_scores()
        assert isinstance(scores, dict)

    def test_extract_scores_has_three_bureaus(self, minimal_html):
        """Test scores dict has all three bureaus."""
        parser = CreditReportParser(minimal_html)
        scores = parser._extract_scores()
        assert "transunion" in scores
        assert "experian" in scores
        assert "equifax" in scores

    def test_extract_scores_valid_scores(self, scores_html):
        """Test extraction of valid credit scores."""
        parser = CreditReportParser(scores_html)
        scores = parser._extract_scores()
        assert scores["transunion"] == 750
        assert scores["experian"] == 740
        assert scores["equifax"] == 745

    def test_extract_scores_none_when_missing(self, minimal_html):
        """Test scores are None when not found."""
        parser = CreditReportParser(minimal_html)
        scores = parser._extract_scores()
        assert scores["transunion"] is None
        assert scores["experian"] is None
        assert scores["equifax"] is None

    def test_extract_scores_valid_range(self):
        """Test scores outside 300-850 range are rejected."""
        html = """
        <html>
        <body>
            <div id="CreditScore">
                <table class="rpt_content_table">
                    <tr>
                        <td class="label">FICO Score 8:</td>
                        <td class="info1">200</td>
                        <td class="info2">900</td>
                        <td class="info3">750</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        scores = parser._extract_scores()
        assert scores["transunion"] is None  # 200 is too low
        assert scores["experian"] is None  # 900 is too high
        assert scores["equifax"] == 750  # Valid score

    def test_extract_scores_handles_dash(self):
        """Test scores with dash values are handled."""
        html = """
        <html>
        <body>
            <div id="CreditScore">
                <table class="rpt_content_table">
                    <tr>
                        <td class="label">FICO Score 8:</td>
                        <td class="info1">720</td>
                        <td class="info2">-</td>
                        <td class="info3">-</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        scores = parser._extract_scores()
        assert scores["transunion"] == 720
        assert scores["experian"] is None
        assert scores["equifax"] is None

    def test_extract_scores_fallback_regex(self):
        """Test fallback regex extraction method."""
        html = """
        <html>
        <body>
            <p>TransUnion: 720</p>
            <p>Experian: 715</p>
            <p>Equifax: 710</p>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        scores = parser._extract_scores()
        assert scores["transunion"] == 720
        assert scores["experian"] == 715
        assert scores["equifax"] == 710

    def test_extract_scores_handles_non_numeric(self):
        """Test scores handle non-numeric values gracefully."""
        html = """
        <html>
        <body>
            <div id="CreditScore">
                <table class="rpt_content_table">
                    <tr>
                        <td class="label">FICO Score 8:</td>
                        <td class="info1">N/A</td>
                        <td class="info2">Unknown</td>
                        <td class="info3">720</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        scores = parser._extract_scores()
        assert scores["transunion"] is None
        assert scores["experian"] is None
        assert scores["equifax"] == 720


# =============================================================================
# Test Class: _extract_personal_info() Method
# =============================================================================

class TestExtractPersonalInfo:
    """Tests for personal information extraction."""

    def test_extract_personal_info_returns_dict(self, minimal_html):
        """Test _extract_personal_info returns a dictionary."""
        parser = CreditReportParser(minimal_html)
        info = parser._extract_personal_info()
        assert isinstance(info, dict)

    def test_extract_personal_info_has_required_keys(self, minimal_html):
        """Test personal info dict has required keys."""
        parser = CreditReportParser(minimal_html)
        info = parser._extract_personal_info()
        assert "name" in info
        assert "address" in info
        assert "ssn_last4" in info
        assert "dob" in info

    def test_extract_personal_info_name(self):
        """Test extraction of name from personal info."""
        html = """
        <html>
        <body>
            <div id="PersonalInformation">
                <table>
                    <tr>
                        <td>Name:</td>
                        <td class="info1">Jane Smith</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        info = parser._extract_personal_info()
        assert info["name"] == "Jane Smith"

    def test_extract_personal_info_missing_section(self, minimal_html):
        """Test personal info when section is missing."""
        parser = CreditReportParser(minimal_html)
        info = parser._extract_personal_info()
        assert info["name"] is None
        assert info["address"] is None

    def test_extract_personal_info_handles_dash(self):
        """Test personal info handles dash values."""
        html = """
        <html>
        <body>
            <div id="PersonalInformation">
                <table>
                    <tr>
                        <td>Name:</td>
                        <td class="info1">-</td>
                        <td class="info2">John Doe</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        info = parser._extract_personal_info()
        assert info["name"] == "John Doe"

    def test_extract_personal_info_myfreescorenow_format(self):
        """Test personal info extraction from MyFreeScoreNow format.

        CRITICAL: This tests the fix where we must iterate through ALL h2.headline
        elements to find 'Personal Information', not just use soup.find() which
        returns the first one (Credit Scores).
        """
        html = """
        <html>
        <body>
            <!-- Credit Scores headline comes FIRST -->
            <h2 class="headline">Credit Scores</h2>
            <div class="attribute-collection">
                <div class="attribute-row">
                    <p class="text-gray-900">TransUnion</p>
                    <div class="display-attribute"><p class="fw-semi">720</p></div>
                </div>
            </div>

            <!-- Personal Information headline comes SECOND -->
            <h2 class="headline">Personal Information</h2>
            <div class="attribute-collection">
                <div class="attribute-row">
                    <p class="text-gray-900">Name</p>
                    <div class="display-attribute"><p class="fw-semi">JENNIFER A NIEVES</p></div>
                </div>
                <div class="attribute-row">
                    <p class="text-gray-900">Date of Birth</p>
                    <div class="display-attribute"><p class="fw-semi">07/15/1976</p></div>
                </div>
                <div class="attribute-row">
                    <p class="text-gray-900">Current Address</p>
                    <div class="display-attribute"><p class="fw-semi">111 LOCUST AVE, MAYWOOD, NJ 07607</p></div>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html, service_name="myfreescorenow")
        info = parser._extract_personal_info()

        # Should find Personal Information, NOT return None because Credit Scores was first
        assert info["name"] is not None, "Name should be extracted from Personal Information section"
        assert "JENNIFER" in info["name"].upper() or "Jennifer" in info["name"]
        assert info["dob"] == "07/15/1976"
        assert info["address"] is not None

    def test_extract_personal_info_myfreescorenow_no_personal_headline(self):
        """Test graceful handling when only Credit Scores headline exists."""
        html = """
        <html>
        <body>
            <h2 class="headline">Credit Scores</h2>
            <div class="attribute-collection">
                <div class="attribute-row">
                    <p class="text-gray-900">TransUnion</p>
                    <div class="display-attribute"><p class="fw-semi">720</p></div>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        info = parser._extract_personal_info()

        # Should return None for all fields, not crash
        assert info["name"] is None
        assert info["dob"] is None
        assert info["address"] is None

    def test_extract_personal_info_myfreescorenow_multiple_headlines(self):
        """Test extraction with multiple h2.headline elements (real-world scenario)."""
        html = """
        <html>
        <body>
            <h2 class="headline">Credit Scores</h2>
            <div class="score-section"><!-- scores here --></div>

            <h2 class="headline">Summary</h2>
            <div class="summary-section"><!-- summary here --></div>

            <h2 class="headline">Personal Information</h2>
            <div class="attribute-collection">
                <div class="attribute-row">
                    <p class="text-gray-900">Name</p>
                    <div class="display-attribute"><p class="fw-semi">Test User</p></div>
                </div>
            </div>

            <h2 class="headline">Account History</h2>
            <div class="accounts-section"><!-- accounts here --></div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        info = parser._extract_personal_info()

        # Should correctly find the 3rd headline (Personal Information)
        assert info["name"] is not None
        assert "Test" in info["name"]


# =============================================================================
# Test Class: _extract_accounts() Method
# =============================================================================

class TestExtractAccounts:
    """Tests for account extraction."""

    def test_extract_accounts_returns_list(self, minimal_html):
        """Test _extract_accounts returns a list."""
        parser = CreditReportParser(minimal_html)
        accounts = parser._extract_accounts()
        assert isinstance(accounts, list)

    def test_extract_accounts_empty_when_no_section(self, minimal_html):
        """Test accounts list is empty when no account section."""
        parser = CreditReportParser(minimal_html)
        accounts = parser._extract_accounts()
        assert len(accounts) == 0

    def test_extract_accounts_creditor_name(self, accounts_html):
        """Test extraction of creditor name."""
        parser = CreditReportParser(accounts_html)
        accounts = parser._extract_accounts()
        assert len(accounts) >= 1
        assert accounts[0]["creditor"] == "CAPITAL ONE"

    def test_extract_accounts_account_number(self, accounts_html):
        """Test extraction of account number."""
        parser = CreditReportParser(accounts_html)
        accounts = parser._extract_accounts()
        assert accounts[0]["account_number"] == "****5678"

    def test_extract_accounts_balance(self, accounts_html):
        """Test extraction of account balance."""
        parser = CreditReportParser(accounts_html)
        accounts = parser._extract_accounts()
        assert accounts[0]["balance"] == "$2,500"

    def test_extract_accounts_status(self, accounts_html):
        """Test extraction of account status."""
        parser = CreditReportParser(accounts_html)
        accounts = parser._extract_accounts()
        assert accounts[0]["status"] == "Open"

    def test_extract_accounts_late_payments(self, accounts_html):
        """Test extraction of late payment counts."""
        parser = CreditReportParser(accounts_html)
        accounts = parser._extract_accounts()
        assert accounts[0]["times_30_late"] == "0"
        assert accounts[0]["times_60_late"] == "1"
        assert accounts[0]["times_90_late"] == "0"

    def test_extract_accounts_bureau_data(self, accounts_html):
        """Test extraction of bureau-specific data."""
        parser = CreditReportParser(accounts_html)
        accounts = parser._extract_accounts()
        bureaus = accounts[0]["bureaus"]
        assert bureaus["transunion"]["present"] == True
        assert bureaus["experian"]["present"] == True
        assert bureaus["equifax"]["present"] == True

    def test_extract_accounts_original_creditor(self, collections_html):
        """Test extraction of original creditor."""
        parser = CreditReportParser(collections_html)
        accounts = parser._extract_accounts()
        assert len(accounts) >= 1
        assert accounts[0]["original_creditor"] == "AT&T"

    def test_extract_accounts_skips_invalid_headers(self):
        """Test that invalid creditor names are skipped."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">CREDIT REPORT</div>
                    </table>
                    <table class="crPrint">
                        <div class="sub_header ng-binding">VALID CREDITOR NAME</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Balance:</td>
                                <td class="info1">$1,000</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert len(accounts) == 1
        assert accounts[0]["creditor"] == "VALID CREDITOR NAME"

    def test_extract_accounts_deduplication(self):
        """Test that duplicate accounts are not added."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">SAME CREDITOR</div>
                        <table class="rpt_content_table">
                            <tr><td class="label">Balance:</td><td class="info1">$100</td></tr>
                        </table>
                    </table>
                    <table class="crPrint">
                        <div class="sub_header ng-binding">SAME CREDITOR</div>
                        <table class="rpt_content_table">
                            <tr><td class="label">Balance:</td><td class="info1">$200</td></tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        # First occurrence should be kept
        assert len(accounts) == 1
        assert accounts[0]["balance"] == "$100"

    def test_extract_accounts_credit_limit(self):
        """Test extraction of credit limit."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">TEST BANK</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Credit Limit:</td>
                                <td class="info1">$15,000</td>
                                <td class="info2">$15,000</td>
                                <td class="info3">$15,000</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert accounts[0]["credit_limit"] == "$15,000"

    def test_extract_accounts_date_opened(self):
        """Test extraction of date opened."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">TEST BANK</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Date Opened:</td>
                                <td class="info1">03/15/2018</td>
                                <td class="info2">03/15/2018</td>
                                <td class="info3">03/15/2018</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert accounts[0]["date_opened"] == "03/15/2018"

    def test_extract_accounts_authorized_user(self):
        """Test detection of authorized user accounts."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">FAMILY MEMBER CARD</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Responsibility:</td>
                                <td class="info1">Authorized User</td>
                                <td class="info2">Authorized User</td>
                                <td class="info3">Auth User</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert accounts[0]["is_authorized_user"] == True


# =============================================================================
# Test Class: _extract_inquiries() Method
# =============================================================================

class TestExtractInquiries:
    """Tests for inquiry extraction."""

    def test_extract_inquiries_returns_list(self, minimal_html):
        """Test _extract_inquiries returns a list."""
        parser = CreditReportParser(minimal_html)
        inquiries = parser._extract_inquiries()
        assert isinstance(inquiries, list)

    def test_extract_inquiries_empty_when_no_section(self, minimal_html):
        """Test inquiries list is empty when no section."""
        parser = CreditReportParser(minimal_html)
        inquiries = parser._extract_inquiries()
        assert len(inquiries) == 0

    def test_extract_inquiries_creditor(self, inquiries_html):
        """Test extraction of inquiry creditor."""
        parser = CreditReportParser(inquiries_html)
        inquiries = parser._extract_inquiries()
        assert len(inquiries) >= 1
        assert inquiries[0]["creditor"] == "WELLS FARGO"

    def test_extract_inquiries_type(self, inquiries_html):
        """Test extraction of inquiry type."""
        parser = CreditReportParser(inquiries_html)
        inquiries = parser._extract_inquiries()
        assert inquiries[0]["type"] == "Hard Inquiry"

    def test_extract_inquiries_date(self, inquiries_html):
        """Test extraction of inquiry date."""
        parser = CreditReportParser(inquiries_html)
        inquiries = parser._extract_inquiries()
        assert inquiries[0]["date"] == "11/15/2023"

    def test_extract_inquiries_bureau(self, inquiries_html):
        """Test extraction of inquiry bureau."""
        parser = CreditReportParser(inquiries_html)
        inquiries = parser._extract_inquiries()
        assert inquiries[0]["bureau"] == "Experian"

    def test_extract_inquiries_multiple(self, inquiries_html):
        """Test extraction of multiple inquiries."""
        parser = CreditReportParser(inquiries_html)
        inquiries = parser._extract_inquiries()
        assert len(inquiries) == 2

    def test_extract_inquiries_deduplication(self):
        """Test that duplicate inquiries are not added."""
        html = """
        <html>
        <body>
            <div id="Inquiries">
                <table>
                    <tr class="ng-scope">
                        <td class="info1">SAME COMPANY</td>
                        <td class="info2">Hard Inquiry</td>
                        <td class="info3">01/01/2024</td>
                        <td class="info4">TransUnion</td>
                    </tr>
                    <tr class="ng-scope">
                        <td class="info1">SAME COMPANY</td>
                        <td class="info2">Hard Inquiry</td>
                        <td class="info3">01/01/2024</td>
                        <td class="info4">Experian</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        inquiries = parser._extract_inquiries()
        assert len(inquiries) == 1


# =============================================================================
# Test Class: _extract_collections() Method
# =============================================================================

class TestExtractCollections:
    """Tests for collection account extraction."""

    def test_extract_collections_returns_list(self, minimal_html):
        """Test _extract_collections returns a list."""
        parser = CreditReportParser(minimal_html)
        parser._summary_counts = {"collections": 0}
        collections = parser._extract_collections()
        assert isinstance(collections, list)

    def test_extract_collections_empty_when_no_summary(self, minimal_html):
        """Test collections empty when summary shows zero."""
        parser = CreditReportParser(minimal_html)
        parser._summary_counts = {"collections": 0}
        collections = parser._extract_collections()
        assert len(collections) == 0

    def test_extract_collections_from_accounts(self, collections_html):
        """Test extraction of collection accounts."""
        parser = CreditReportParser(collections_html)
        parser._summary_counts = parser._extract_summary_counts()
        collections = parser._extract_collections()
        assert len(collections) >= 1

    def test_extract_collections_agency(self, collections_html):
        """Test extraction of collection agency name."""
        parser = CreditReportParser(collections_html)
        parser._summary_counts = parser._extract_summary_counts()
        collections = parser._extract_collections()
        assert collections[0]["agency"] == "MIDLAND CREDIT"

    def test_extract_collections_original_creditor(self, collections_html):
        """Test extraction of original creditor in collections."""
        parser = CreditReportParser(collections_html)
        parser._summary_counts = parser._extract_summary_counts()
        collections = parser._extract_collections()
        assert collections[0]["original_creditor"] == "AT&T"

    def test_extract_collections_amount(self, collections_html):
        """Test extraction of collection amount."""
        parser = CreditReportParser(collections_html)
        parser._summary_counts = parser._extract_summary_counts()
        collections = parser._extract_collections()
        assert collections[0]["amount"] == "$500"


# =============================================================================
# Test Class: _extract_summary_counts() Method
# =============================================================================

class TestExtractSummaryCounts:
    """Tests for summary counts extraction."""

    def test_extract_summary_counts_returns_dict(self, minimal_html):
        """Test _extract_summary_counts returns a dictionary."""
        parser = CreditReportParser(minimal_html)
        counts = parser._extract_summary_counts()
        assert isinstance(counts, dict)

    def test_extract_summary_counts_has_required_keys(self, minimal_html):
        """Test summary counts has required keys."""
        parser = CreditReportParser(minimal_html)
        counts = parser._extract_summary_counts()
        assert "collections" in counts
        assert "public_records" in counts
        assert "open_accounts" in counts
        assert "closed_accounts" in counts

    def test_extract_summary_counts_collections(self, full_credit_report_html):
        """Test extraction of collections count."""
        parser = CreditReportParser(full_credit_report_html)
        counts = parser._extract_summary_counts()
        assert counts["collections"] == 2

    def test_extract_summary_counts_public_records(self, full_credit_report_html):
        """Test extraction of public records count."""
        parser = CreditReportParser(full_credit_report_html)
        counts = parser._extract_summary_counts()
        assert counts["public_records"] == 1

    def test_extract_summary_counts_handles_dash(self):
        """Test summary counts handles dash values."""
        html = """
        <html>
        <body>
            <div id="Summary">
                <table>
                    <tr>
                        <td class="label">Collections:</td>
                        <td class="info1">-</td>
                        <td class="info2">-</td>
                        <td class="info3">-</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        counts = parser._extract_summary_counts()
        assert counts["collections"] == 0

    def test_extract_summary_counts_uses_first_valid(self):
        """Test summary counts uses first valid value found."""
        html = """
        <html>
        <body>
            <div id="Summary">
                <table>
                    <tr>
                        <td class="label">Collections:</td>
                        <td class="info1">1</td>
                        <td class="info2">3</td>
                        <td class="info3">2</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        counts = parser._extract_summary_counts()
        # Implementation breaks after finding first valid value
        assert counts["collections"] == 1

    def test_extract_summary_counts_skips_empty_finds_next(self):
        """Test summary counts skips dash and finds next valid value."""
        html = """
        <html>
        <body>
            <div id="Summary">
                <table>
                    <tr>
                        <td class="label">Collections:</td>
                        <td class="info1">-</td>
                        <td class="info2">5</td>
                        <td class="info3">2</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        counts = parser._extract_summary_counts()
        # Should skip dash and find the next valid value
        assert counts["collections"] == 5


# =============================================================================
# Test Class: _is_valid_creditor_name() Method
# =============================================================================

class TestIsValidCreditorName:
    """Tests for creditor name validation."""

    def test_valid_creditor_name(self, minimal_html):
        """Test valid creditor names return True."""
        parser = CreditReportParser(minimal_html)
        assert parser._is_valid_creditor_name("CHASE BANK") == True
        assert parser._is_valid_creditor_name("CAPITAL ONE") == True
        assert parser._is_valid_creditor_name("WELLS FARGO MORTGAGE") == True

    def test_invalid_short_name(self, minimal_html):
        """Test short names are invalid."""
        parser = CreditReportParser(minimal_html)
        assert parser._is_valid_creditor_name("AB") == False
        assert parser._is_valid_creditor_name("") == False

    def test_invalid_skip_headers(self, minimal_html):
        """Test skip headers are invalid."""
        parser = CreditReportParser(minimal_html)
        assert parser._is_valid_creditor_name("CREDIT REPORT") == False
        assert parser._is_valid_creditor_name("SUMMARY") == False
        assert parser._is_valid_creditor_name("INQUIRIES") == False

    def test_invalid_angular_template(self, minimal_html):
        """Test Angular templates are invalid."""
        parser = CreditReportParser(minimal_html)
        assert parser._is_valid_creditor_name("{{creditor.name}}") == False
        assert parser._is_valid_creditor_name("Name: {{name}}") == False

    def test_invalid_single_letters(self, minimal_html):
        """Test single letter codes are invalid."""
        parser = CreditReportParser(minimal_html)
        assert parser._is_valid_creditor_name("TU") == False
        assert parser._is_valid_creditor_name("EX") == False
        assert parser._is_valid_creditor_name("EQ") == False


# =============================================================================
# Test Class: _extract_public_records() Method
# =============================================================================

class TestExtractPublicRecords:
    """Tests for public records extraction."""

    def test_extract_public_records_returns_list(self, minimal_html):
        """Test _extract_public_records returns a list."""
        parser = CreditReportParser(minimal_html)
        parser._summary_counts = {"public_records": 0}
        records = parser._extract_public_records()
        assert isinstance(records, list)

    def test_extract_public_records_empty_when_none(self, minimal_html):
        """Test public records empty when summary shows zero."""
        parser = CreditReportParser(minimal_html)
        parser._summary_counts = {"public_records": 0}
        records = parser._extract_public_records()
        assert len(records) == 0

    def test_extract_public_records_bankruptcy(self, full_credit_report_html):
        """Test extraction of bankruptcy record."""
        parser = CreditReportParser(full_credit_report_html)
        parser._summary_counts = {"public_records": 1}
        records = parser._extract_public_records()
        assert len(records) >= 1
        assert records[0]["type"] == "Bankruptcy"

    def test_extract_public_records_filed_date(self, full_credit_report_html):
        """Test extraction of filed date."""
        parser = CreditReportParser(full_credit_report_html)
        parser._summary_counts = {"public_records": 1}
        records = parser._extract_public_records()
        assert records[0]["date"] == "06/15/2019"


# =============================================================================
# Test Class: _extract_creditor_contacts() Method
# =============================================================================

class TestExtractCreditorContacts:
    """Tests for creditor contacts extraction."""

    def test_extract_creditor_contacts_returns_list(self, minimal_html):
        """Test _extract_creditor_contacts returns a list."""
        parser = CreditReportParser(minimal_html)
        contacts = parser._extract_creditor_contacts()
        assert isinstance(contacts, list)

    def test_extract_creditor_contacts_empty_when_no_section(self, minimal_html):
        """Test contacts empty when section missing."""
        parser = CreditReportParser(minimal_html)
        contacts = parser._extract_creditor_contacts()
        assert len(contacts) == 0

    def test_extract_creditor_contacts_name(self, full_credit_report_html):
        """Test extraction of creditor name."""
        parser = CreditReportParser(full_credit_report_html)
        contacts = parser._extract_creditor_contacts()
        assert len(contacts) >= 1
        assert contacts[0]["creditor"] == "CHASE"

    def test_extract_creditor_contacts_address(self, full_credit_report_html):
        """Test extraction of creditor address."""
        parser = CreditReportParser(full_credit_report_html)
        contacts = parser._extract_creditor_contacts()
        assert "123 Main St" in contacts[0]["address"]

    def test_extract_creditor_contacts_phone(self, full_credit_report_html):
        """Test extraction of creditor phone."""
        parser = CreditReportParser(full_credit_report_html)
        contacts = parser._extract_creditor_contacts()
        assert contacts[0]["phone"] == "800-555-1234"


# =============================================================================
# Test Class: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_html(self):
        """Test parser handles malformed HTML."""
        html = "<html><body><div>Unclosed div<p>Unclosed paragraph"
        parser = CreditReportParser(html)
        result = parser.parse()
        assert isinstance(result, dict)

    def test_unicode_characters(self):
        """Test parser handles unicode characters."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">BANCO NACIONAL</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Balance:</td>
                                <td class="info1">$1,000</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert len(accounts) == 1
        assert accounts[0]["creditor"] == "BANCO NACIONAL"

    def test_whitespace_handling(self):
        """Test parser handles excessive whitespace."""
        html = """
        <html>
        <body>
            <div id="CreditScore">
                <table class="rpt_content_table">
                    <tr>
                        <td class="label">   FICO Score 8:   </td>
                        <td class="info1">   720   </td>
                        <td class="info2">   715   </td>
                        <td class="info3">   710   </td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        scores = parser._extract_scores()
        assert scores["transunion"] == 720
        assert scores["experian"] == 715
        assert scores["equifax"] == 710

    def test_special_characters_in_creditor_name(self):
        """Test parser handles special characters in names."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">AT&amp;T MOBILITY</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Balance:</td>
                                <td class="info1">$500</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert len(accounts) == 1
        assert "AT&T" in accounts[0]["creditor"]

    def test_nested_tables(self):
        """Test parser handles deeply nested tables."""
        html = """
        <html>
        <body>
            <div id="CreditScore">
                <table>
                    <tr>
                        <td>
                            <table class="rpt_content_table">
                                <tr>
                                    <td class="label">FICO Score 8:</td>
                                    <td class="info1">700</td>
                                    <td class="info2">705</td>
                                    <td class="info3">710</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        scores = parser._extract_scores()
        assert scores["transunion"] == 700

    def test_empty_cells(self):
        """Test parser handles empty table cells."""
        html = """
        <html>
        <body>
            <div id="Inquiries">
                <table>
                    <tr class="ng-scope">
                        <td class="info1"></td>
                        <td class="info2"></td>
                        <td class="info3"></td>
                        <td class="info4"></td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        inquiries = parser._extract_inquiries()
        # Empty creditor should be skipped
        assert len(inquiries) == 0


# =============================================================================
# Test Class: Payment History Extraction
# =============================================================================

class TestPaymentHistoryExtraction:
    """Tests for payment history extraction."""

    def test_extract_payment_history(self):
        """Test extraction of payment history grid."""
        html = """
        <html>
        <body>
            <div class="rpt_content_wrapper">
                <div id="AccountHistory">
                    <table class="crPrint">
                        <div class="sub_header ng-binding">TEST ACCOUNT</div>
                        <table class="rpt_content_table">
                            <tr>
                                <td class="label">Balance:</td>
                                <td class="info1">$1,000</td>
                            </tr>
                        </table>
                        <table class="addr_hsrty">
                            <tr>
                                <td>Month:</td>
                                <td>Jan</td>
                                <td>Feb</td>
                                <td>Mar</td>
                            </tr>
                            <tr>
                                <td>Year:</td>
                                <td>2024</td>
                                <td>2024</td>
                                <td>2024</td>
                            </tr>
                            <tr>
                                <td>TransUnion:</td>
                                <td>OK</td>
                                <td>OK</td>
                                <td>30</td>
                            </tr>
                            <tr>
                                <td>Experian:</td>
                                <td>OK</td>
                                <td>OK</td>
                                <td>30</td>
                            </tr>
                            <tr>
                                <td>Equifax:</td>
                                <td>OK</td>
                                <td>OK</td>
                                <td>30</td>
                            </tr>
                        </table>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        parser = CreditReportParser(html)
        accounts = parser._extract_accounts()
        assert len(accounts) >= 1
        history = accounts[0]["payment_history"]
        assert len(history) == 3
        assert history[0]["month"] == "Jan"
        assert history[0]["year"] == "2024"
        assert history[0]["transunion"] == "OK"


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for full parsing workflow."""

    def test_full_parse_workflow(self, full_credit_report_html):
        """Test complete parsing workflow."""
        parser = CreditReportParser(full_credit_report_html, service_name="myscoreiq")
        result = parser.parse()

        # Check scores
        assert result["scores"]["transunion"] == 720
        assert result["scores"]["experian"] == 715
        assert result["scores"]["equifax"] == 725

        # Check accounts exist
        assert len(result["accounts"]) >= 1

        # Check inquiries exist
        assert len(result["inquiries"]) >= 1

        # Check summary
        assert result["summary"]["total_accounts"] >= 1
        assert result["summary"]["total_inquiries"] >= 1

    def test_parse_preserves_all_data_types(self, full_credit_report_html):
        """Test that parse preserves correct data types."""
        parser = CreditReportParser(full_credit_report_html)
        result = parser.parse()

        # Scores should be int or None
        for bureau in ["transunion", "experian", "equifax"]:
            assert result["scores"][bureau] is None or isinstance(result["scores"][bureau], int)

        # Accounts should be list of dicts
        assert isinstance(result["accounts"], list)
        for account in result["accounts"]:
            assert isinstance(account, dict)

        # Summary should be dict with int/bool values
        assert isinstance(result["summary"], dict)
        for key, value in result["summary"].items():
            assert isinstance(value, (int, bool))


# =============================================================================
# Error Recovery Tests
# =============================================================================


class TestErrorRecovery:
    """Tests for parser error recovery - partial data on section failures."""

    def test_parse_returns_partial_data_on_section_failure(self):
        """If one section fails, others should still return data."""
        from unittest.mock import patch

        parser = CreditReportParser("<html><body></body></html>")

        # Make _extract_scores raise, everything else should still work
        with patch.object(parser, "_extract_scores", side_effect=ValueError("bad score")):
            result = parser.parse()

        assert result["scores"] == {}
        assert isinstance(result["accounts"], list)
        assert isinstance(result["inquiries"], list)
        assert result["summary"]["had_errors"] is True
        assert result["summary"]["error_count"] >= 1
        assert len(result["parse_errors"]) >= 1
        assert result["parse_errors"][0]["section"] == "scores"

    def test_parse_returns_all_defaults_on_total_failure(self):
        """If all sections fail, result should have all defaults."""
        from unittest.mock import patch

        parser = CreditReportParser("<html><body></body></html>")

        methods = [
            "_extract_summary_counts",
            "_extract_scores",
            "_extract_personal_info",
            "_extract_accounts",
            "_extract_inquiries",
            "_extract_public_records",
            "_extract_collections",
            "_extract_creditor_contacts",
        ]
        patches = {m: patch.object(parser, m, side_effect=Exception("fail")) for m in methods}

        with patches["_extract_summary_counts"], patches["_extract_scores"], \
             patches["_extract_personal_info"], patches["_extract_accounts"], \
             patches["_extract_inquiries"], patches["_extract_public_records"], \
             patches["_extract_collections"], patches["_extract_creditor_contacts"]:
            result = parser.parse()

        assert result["scores"] == {}
        assert result["personal_info"] == {}
        assert result["accounts"] == []
        assert result["inquiries"] == []
        assert result["public_records"] == []
        assert result["collections"] == []
        assert result["creditor_contacts"] == []
        assert result["summary"]["had_errors"] is True
        assert result["summary"]["error_count"] == 8

    def test_parse_no_errors_on_valid_html(self):
        """Normal parse with empty HTML should have no errors."""
        parser = CreditReportParser("<html><body></body></html>")
        result = parser.parse()

        assert result["summary"]["had_errors"] is False
        assert result["summary"]["error_count"] == 0
        assert result["parse_errors"] == []

    def test_safe_extract_logs_error(self):
        """_safe_extract should log errors."""
        from unittest.mock import patch
        import logging

        parser = CreditReportParser("<html></html>")
        parser._parse_errors = []

        with patch.object(parser, "_extract_scores", side_effect=TypeError("test error")):
            with patch("services.credit_report_parser.logger") as mock_logger:
                result = parser._safe_extract("_extract_scores", default={})

        assert result == {}
        mock_logger.error.assert_called_once()
        assert len(parser._parse_errors) == 1
        assert parser._parse_errors[0]["error_type"] == "TypeError"

    def test_parse_errors_include_context(self):
        """Parse errors should include section name, error message, and type."""
        from unittest.mock import patch

        parser = CreditReportParser("<html></html>")

        with patch.object(parser, "_extract_accounts", side_effect=AttributeError("no attr")):
            result = parser.parse()

        errors = result["parse_errors"]
        account_error = next(e for e in errors if e["section"] == "accounts")
        assert account_error["error"] == "no attr"
        assert account_error["error_type"] == "AttributeError"


class TestFailureTracking:
    """Tests for the failure tracking and admin alert system."""

    def test_record_parse_failure_tracks_count(self):
        """Failures should be tracked per service."""
        from services.credit_report_parser import _record_parse_failure, _failure_counts

        # Clear state
        _failure_counts.clear()

        _record_parse_failure("test_service", [{"section": "scores", "error": "test"}])

        assert "test_service" in _failure_counts
        assert len(_failure_counts["test_service"]) == 1

        # Cleanup
        _failure_counts.clear()

    def test_get_parse_failure_stats(self):
        """Stats should return current failure counts."""
        from services.credit_report_parser import (
            _record_parse_failure, get_parse_failure_stats, _failure_counts
        )

        _failure_counts.clear()

        _record_parse_failure("svc_a", [{"section": "scores", "error": "fail"}])
        _record_parse_failure("svc_a", [{"section": "accounts", "error": "fail"}])

        stats = get_parse_failure_stats()
        assert "svc_a" in stats
        assert stats["svc_a"]["count"] == 2

        _failure_counts.clear()

    def test_alert_triggered_at_threshold(self):
        """Admin alert should fire after threshold failures."""
        from unittest.mock import patch
        from services.credit_report_parser import (
            _record_parse_failure, _failure_counts, _FAILURE_ALERT_THRESHOLD
        )

        _failure_counts.clear()

        with patch("services.credit_report_parser.logger") as mock_logger:
            for i in range(_FAILURE_ALERT_THRESHOLD):
                _record_parse_failure("alert_test", [{"section": "scores", "error": f"fail {i}"}])

            # Should have triggered critical log
            mock_logger.critical.assert_called_once()

        _failure_counts.clear()
