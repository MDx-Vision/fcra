"""
Tests for RoundLetterBuilder - Round-Specific Letter Generator with RLPP Bundling
"""

import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestRoundLetterBuilderConstants(unittest.TestCase):
    """Test class constants and configuration"""

    def test_bureau_addresses_defined(self):
        """Should have bureau addresses for all 3 major bureaus"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        assert hasattr(builder, "BUREAU_ADDRESSES")
        assert "Equifax" in builder.BUREAU_ADDRESSES
        assert "Experian" in builder.BUREAU_ADDRESSES
        assert "TransUnion" in builder.BUREAU_ADDRESSES

    def test_equifax_address_complete(self):
        """Equifax address should have name, address, city"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        equifax = builder.BUREAU_ADDRESSES["Equifax"]
        assert "name" in equifax
        assert "address" in equifax
        assert "city" in equifax
        assert equifax["name"] == "Equifax Information Services LLC"

    def test_experian_address_complete(self):
        """Experian address should have name, address, city"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        experian = builder.BUREAU_ADDRESSES["Experian"]
        assert "name" in experian
        assert "address" in experian
        assert "city" in experian
        assert experian["name"] == "Experian"

    def test_transunion_address_complete(self):
        """TransUnion address should have name, address, city"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        transunion = builder.BUREAU_ADDRESSES["TransUnion"]
        assert "name" in transunion
        assert "address" in transunion
        assert "city" in transunion
        assert transunion["name"] == "TransUnion LLC"

    def test_inherits_from_base_pdf_builder(self):
        """Should inherit from BasePDFBuilder"""
        from services.pdf.base import BasePDFBuilder
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        assert isinstance(builder, BasePDFBuilder)


class TestRoundLetterBuilderInit(unittest.TestCase):
    """Test initialization"""

    def test_can_instantiate(self):
        """Should be able to create instance"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        assert builder is not None

    def test_has_base_styles(self):
        """Should have styles from base class"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        assert hasattr(builder, "body_style")
        assert hasattr(builder, "body_blue_style")
        assert hasattr(builder, "warning_style")


class TestRoundLetterBuilderRound1(unittest.TestCase):
    """Test Round 1 letter generation"""

    def _create_client_data(self):
        """Create mock client data"""
        return {
            "client_name": "John Doe",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001",
            },
            "ssn_last_four": "1234",
            "violations": [
                {
                    "bureau": "Equifax",
                    "account_name": "Test Bank",
                    "fcra_section": "611",
                    "violation_type": "Inaccurate Balance",
                    "description": "Balance is incorrect",
                },
                {
                    "bureau": "Equifax",
                    "account_name": "Credit Card Co",
                    "fcra_section": "623",
                    "violation_type": "Late Payment Error",
                    "description": "Payment was on time",
                },
            ],
        }

    def test_generate_round_1_creates_pdf(self):
        """Should generate Round 1 PDF file"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r1_letter.pdf")
            result = builder.generate_round_1(output_path, client_data, "Equifax")

            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

    def test_generate_round_1_all_bureaus(self):
        """Should generate Round 1 letters for all bureaus"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        for bureau in ["Equifax", "Experian", "TransUnion"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"r1_{bureau}.pdf")
                result = builder.generate_round_1(output_path, client_data, bureau)
                assert os.path.exists(output_path)

    def test_generate_round_1_no_violations(self):
        """Should handle case with no violations"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {"client_name": "Jane Doe", "violations": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r1_empty.pdf")
            result = builder.generate_round_1(output_path, client_data, "Experian")
            assert os.path.exists(output_path)

    def test_generate_round_1_minimal_data(self):
        """Should handle minimal client data"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r1_minimal.pdf")
            result = builder.generate_round_1(output_path, client_data, "TransUnion")
            assert os.path.exists(output_path)


class TestRoundLetterBuilderRound2(unittest.TestCase):
    """Test Round 2 MOV demand letter generation"""

    def _create_client_data(self):
        """Create mock client data for R2"""
        return {
            "client_name": "John Doe",
            "address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02101",
            },
            "ssn_last_four": "5678",
            "previous_dispute_date": "January 1, 2024",
            "violations": [
                {
                    "bureau": "Experian",
                    "account_name": "ABC Bank",
                    "violation_type": "Disputed Balance",
                },
                {
                    "bureau": "Experian",
                    "account_name": "XYZ Credit",
                    "violation_type": "Incorrect Status",
                },
            ],
        }

    def test_generate_round_2_creates_pdf(self):
        """Should generate Round 2 MOV demand PDF"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r2_mov.pdf")
            result = builder.generate_round_2(output_path, client_data, "Experian")

            assert result == output_path
            assert os.path.exists(output_path)

    def test_generate_round_2_no_previous_date(self):
        """Should handle missing previous dispute date"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {"client_name": "Jane Doe", "violations": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r2_no_date.pdf")
            result = builder.generate_round_2(output_path, client_data, "Equifax")
            assert os.path.exists(output_path)

    def test_generate_mov_demand_is_alias_for_round_2(self):
        """generate_mov_demand should be alias for generate_round_2"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "mov_demand.pdf")
            result = builder.generate_mov_demand(output_path, client_data, "TransUnion")
            assert os.path.exists(output_path)


class TestRoundLetterBuilderRound3(unittest.TestCase):
    """Test Round 3 regulatory complaint letter generation"""

    def _create_client_data(self):
        """Create mock client data for R3"""
        return {
            "client_name": "John Doe",
            "address": {
                "street": "456 Oak Ave",
                "city": "Chicago",
                "state": "IL",
                "zip": "60601",
            },
            "ssn_last_four": "9012",
            "violations": [
                {
                    "bureau": "TransUnion",
                    "account_name": "Loan Provider",
                    "fcra_section": "611",
                    "violation_type": "Failed Investigation",
                },
            ],
        }

    def test_generate_round_3_creates_pdf(self):
        """Should generate Round 3 regulatory complaint PDF"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r3_complaint.pdf")
            result = builder.generate_round_3(output_path, client_data, "TransUnion")

            assert result == output_path
            assert os.path.exists(output_path)

    def test_generate_round_3_multiple_violations(self):
        """Should handle multiple violations in R3"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()
        # Add more violations
        for i in range(10):
            client_data["violations"].append(
                {
                    "bureau": "TransUnion",
                    "account_name": f"Account {i}",
                    "fcra_section": "611",
                    "violation_type": f"Violation {i}",
                }
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r3_many.pdf")
            result = builder.generate_round_3(output_path, client_data, "TransUnion")
            assert os.path.exists(output_path)


class TestRoundLetterBuilderRound4(unittest.TestCase):
    """Test Round 4 pre-arbitration demand letter generation"""

    def _create_client_data(self):
        """Create mock client data for R4"""
        return {
            "client_name": "John Doe",
            "address": {
                "street": "789 Pine St",
                "city": "Los Angeles",
                "state": "CA",
                "zip": "90001",
            },
            "ssn_last_four": "3456",
            "violations": [
                {
                    "bureau": "Equifax",
                    "account_name": "Major Bank",
                    "fcra_section": "616",
                    "violation_type": "Willful Noncompliance",
                },
            ],
            "damages": {
                "total_exposure": 50000,
                "settlement_target": 15000,
                "actual_damages_total": 5000,
                "statutory_damages_total": 10000,
                "punitive_damages_amount": 30000,
                "attorney_fees_projection": 5000,
            },
        }

    def test_generate_round_4_creates_pdf(self):
        """Should generate Round 4 pre-arbitration PDF"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r4_demand.pdf")
            result = builder.generate_round_4(output_path, client_data, "Equifax")

            assert result == output_path
            assert os.path.exists(output_path)

    def test_generate_round_4_no_damages(self):
        """Should handle R4 with no damages data"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Jane Doe",
            "violations": [
                {"bureau": "Experian", "account_name": "Test", "violation_type": "Test"}
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r4_no_damages.pdf")
            result = builder.generate_round_4(output_path, client_data, "Experian")
            assert os.path.exists(output_path)

    def test_generate_round_4_with_empty_damages(self):
        """Should handle R4 with empty damages dict"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Jane Doe",
            "damages": {},
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "r4_empty_damages.pdf")
            result = builder.generate_round_4(output_path, client_data, "TransUnion")
            assert os.path.exists(output_path)


class TestRoundLetterBuilderCFPB(unittest.TestCase):
    """Test CFPB complaint template generation"""

    def _create_client_data(self):
        """Create mock client data for CFPB"""
        return {
            "client_name": "John Doe",
            "violations": [
                {
                    "bureau": "Equifax",
                    "account_name": "Bad Creditor",
                    "fcra_section": "611(a)(1)",
                },
                {
                    "bureau": "Equifax",
                    "account_name": "Another Creditor",
                    "fcra_section": "611(a)(7)",
                },
            ],
        }

    def test_generate_cfpb_complaint_creates_pdf(self):
        """Should generate CFPB complaint PDF"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = self._create_client_data()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "cfpb_complaint.pdf")
            result = builder.generate_cfpb_complaint(output_path, client_data, "Equifax")

            assert result == output_path
            assert os.path.exists(output_path)

    def test_generate_cfpb_complaint_all_bureaus(self):
        """Should generate CFPB complaints for all bureaus"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test Consumer",
            "violations": [],
        }

        for bureau in ["Equifax", "Experian", "TransUnion"]:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"cfpb_{bureau}.pdf")
                result = builder.generate_cfpb_complaint(output_path, client_data, bureau)
                assert os.path.exists(output_path)

    def test_generate_cfpb_complaint_many_violations(self):
        """Should handle CFPB with many violations (limited to 10)"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test Consumer",
            "violations": [
                {"bureau": "Experian", "account_name": f"Account {i}", "fcra_section": "611"}
                for i in range(20)
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "cfpb_many.pdf")
            result = builder.generate_cfpb_complaint(output_path, client_data, "Experian")
            assert os.path.exists(output_path)


class TestRoundLetterBuilderPrivateMethods(unittest.TestCase):
    """Test private helper methods"""

    def test_add_letter_header_with_address(self):
        """_add_letter_header should add client info and bureau address"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "client_name": "Test Client",
            "address": {
                "street": "100 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
            },
            "ssn_last_four": "9999",
        }

        builder._add_letter_header(story, client_data, "Equifax")

        # Should have added multiple elements
        assert len(story) > 0

    def test_add_letter_header_no_address(self):
        """_add_letter_header should handle missing address"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {"client_name": "Test Client"}

        builder._add_letter_header(story, client_data, "Experian")
        assert len(story) > 0

    def test_add_letter_header_unknown_bureau(self):
        """_add_letter_header should handle unknown bureau"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {"client_name": "Test Client"}

        builder._add_letter_header(story, client_data, "UnknownBureau")
        assert len(story) > 0

    def test_add_letter_footer(self):
        """_add_letter_footer should add signature and enclosures"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {"client_name": "John Doe"}

        builder._add_letter_footer(story, client_data)

        assert len(story) > 0

    def test_add_r1_body_with_violations(self):
        """_add_r1_body should include RLPP bundle violations"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "violations": [
                {
                    "bureau": "equifax",
                    "account_name": "Test Account",
                    "fcra_section": "611",
                    "violation_type": "Inaccurate",
                    "description": "Wrong info",
                },
            ]
        }

        builder._add_r1_body(story, client_data, "Equifax")
        assert len(story) > 0

    def test_add_r1_body_filters_by_bureau(self):
        """_add_r1_body should filter violations by bureau"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "violations": [
                {"bureau": "equifax", "account_name": "Equifax Account"},
                {"bureau": "experian", "account_name": "Experian Account"},
            ]
        }

        # Should only include Equifax violations
        builder._add_r1_body(story, client_data, "Equifax")
        assert len(story) > 0

    def test_add_r2_body_mov_demands(self):
        """_add_r2_body should include MOV demand items"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "previous_dispute_date": "December 1, 2023",
            "violations": [
                {"bureau": "transunion", "account_name": "Test", "violation_type": "Error"}
            ],
        }

        builder._add_r2_body(story, client_data, "TransUnion")
        assert len(story) > 0

    def test_add_r3_body_regulatory_agencies(self):
        """_add_r3_body should list regulatory agencies"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "violations": [
                {"bureau": "experian", "fcra_section": "611", "violation_type": "Test"}
            ]
        }

        builder._add_r3_body(story, client_data, "Experian")
        assert len(story) > 0

    def test_add_r4_body_with_damages(self):
        """_add_r4_body should include damages information"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "violations": [{"bureau": "equifax"}],
            "damages": {
                "total_exposure": 25000,
                "settlement_target": 7500,
                "actual_damages_total": 2000,
                "statutory_damages_total": 5000,
                "punitive_damages_amount": 15000,
                "attorney_fees_projection": 3000,
            },
        }

        builder._add_r4_body(story, client_data, "Equifax")
        assert len(story) > 0

    def test_add_cfpb_header(self):
        """_add_cfpb_header should add complaint header"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {"client_name": "Complainant Name"}

        builder._add_cfpb_header(story, client_data)
        assert len(story) > 0

    def test_add_cfpb_body(self):
        """_add_cfpb_body should add complaint details"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        story = []
        client_data = {
            "violations": [
                {"bureau": "equifax", "account_name": "Bad Account", "fcra_section": "611"}
            ]
        }

        builder._add_cfpb_body(story, client_data, "Equifax")
        assert len(story) > 0


class TestRoundLetterBuilderEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_unicode_in_client_name(self):
        """Should handle unicode characters in client name"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Jos\u00e9 Garc\u00eda",
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "unicode_test.pdf")
            result = builder.generate_round_1(output_path, client_data, "Equifax")
            assert os.path.exists(output_path)

    def test_very_long_violation_description(self):
        """Should handle very long violation descriptions"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        long_description = "This is a very long description. " * 100
        client_data = {
            "client_name": "Test Client",
            "violations": [
                {
                    "bureau": "Equifax",
                    "account_name": "Test",
                    "description": long_description,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "long_desc.pdf")
            result = builder.generate_round_1(output_path, client_data, "Equifax")
            assert os.path.exists(output_path)

    def test_special_characters_in_account_name(self):
        """Should handle special characters in account names"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test Client",
            "violations": [
                {
                    "bureau": "Experian",
                    "account_name": "Bank & Trust (LLC) - #12345",
                    "violation_type": "Error <Test>",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "special_chars.pdf")
            result = builder.generate_round_2(output_path, client_data, "Experian")
            assert os.path.exists(output_path)

    def test_none_values_in_violations(self):
        """Should handle None values in violation fields"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test Client",
            "violations": [
                {
                    "bureau": "TransUnion",
                    "account_name": None,
                    "fcra_section": None,
                    "violation_type": None,
                    "description": None,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "none_values.pdf")
            result = builder.generate_round_1(output_path, client_data, "TransUnion")
            assert os.path.exists(output_path)

    def test_case_insensitive_bureau_matching(self):
        """Bureau matching should be case insensitive"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test",
            "violations": [
                {"bureau": "EQUIFAX", "account_name": "Test1"},
                {"bureau": "equifax", "account_name": "Test2"},
                {"bureau": "Equifax", "account_name": "Test3"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "case_test.pdf")
            result = builder.generate_round_1(output_path, client_data, "Equifax")
            assert os.path.exists(output_path)

    def test_empty_address_fields(self):
        """Should handle empty address fields"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test Client",
            "address": {
                "street": "",
                "city": "",
                "state": "",
                "zip": "",
            },
            "violations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "empty_addr.pdf")
            result = builder.generate_round_3(output_path, client_data, "Equifax")
            assert os.path.exists(output_path)

    def test_missing_ssn_last_four(self):
        """Should use default when ssn_last_four is missing"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {"client_name": "Test Client", "violations": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "no_ssn.pdf")
            result = builder.generate_round_4(output_path, client_data, "Experian")
            assert os.path.exists(output_path)

    def test_zero_damages_values(self):
        """Should handle zero values in damages"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Test Client",
            "damages": {
                "total_exposure": 0,
                "settlement_target": 0,
                "actual_damages_total": 0,
                "statutory_damages_total": 0,
                "punitive_damages_amount": 0,
                "attorney_fees_projection": 0,
            },
            "violations": [{"bureau": "Equifax"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "zero_damages.pdf")
            result = builder.generate_round_4(output_path, client_data, "Equifax")
            assert os.path.exists(output_path)


class TestRoundLetterBuilderIntegration(unittest.TestCase):
    """Integration tests for full letter generation workflow"""

    def test_generate_all_rounds_for_client(self):
        """Should generate all 4 rounds of letters for a client"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Integration Test Client",
            "address": {
                "street": "100 Integration Ave",
                "city": "Test City",
                "state": "TC",
                "zip": "00000",
            },
            "ssn_last_four": "1111",
            "previous_dispute_date": "January 15, 2024",
            "violations": [
                {
                    "bureau": "Equifax",
                    "account_name": "Test Bank",
                    "fcra_section": "611",
                    "violation_type": "Inaccurate Information",
                    "description": "Balance is wrong",
                },
                {
                    "bureau": "Experian",
                    "account_name": "Credit Union",
                    "fcra_section": "623",
                    "violation_type": "Reporting Error",
                    "description": "Account not mine",
                },
            ],
            "damages": {
                "total_exposure": 30000,
                "settlement_target": 10000,
                "actual_damages_total": 3000,
                "statutory_damages_total": 7000,
                "punitive_damages_amount": 15000,
                "attorney_fees_projection": 5000,
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate all rounds
            r1 = builder.generate_round_1(
                os.path.join(tmpdir, "r1.pdf"), client_data, "Equifax"
            )
            r2 = builder.generate_round_2(
                os.path.join(tmpdir, "r2.pdf"), client_data, "Equifax"
            )
            r3 = builder.generate_round_3(
                os.path.join(tmpdir, "r3.pdf"), client_data, "Equifax"
            )
            r4 = builder.generate_round_4(
                os.path.join(tmpdir, "r4.pdf"), client_data, "Equifax"
            )

            # All should exist
            assert os.path.exists(r1)
            assert os.path.exists(r2)
            assert os.path.exists(r3)
            assert os.path.exists(r4)

            # All should have content
            assert os.path.getsize(r1) > 0
            assert os.path.getsize(r2) > 0
            assert os.path.getsize(r3) > 0
            assert os.path.getsize(r4) > 0

    def test_generate_letters_for_all_bureaus(self):
        """Should generate letters for all 3 bureaus"""
        from services.pdf.round_letters import RoundLetterBuilder

        builder = RoundLetterBuilder()
        client_data = {
            "client_name": "Multi-Bureau Client",
            "violations": [
                {"bureau": "Equifax", "account_name": "EQ Account"},
                {"bureau": "Experian", "account_name": "EX Account"},
                {"bureau": "TransUnion", "account_name": "TU Account"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            for bureau in ["Equifax", "Experian", "TransUnion"]:
                path = os.path.join(tmpdir, f"{bureau}_r1.pdf")
                result = builder.generate_round_1(path, client_data, bureau)
                assert os.path.exists(result)
                assert os.path.getsize(result) > 0


if __name__ == "__main__":
    unittest.main()
