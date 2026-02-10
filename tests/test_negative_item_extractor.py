"""
Unit tests for NegativeItemExtractor service.
"""

import pytest
from services.negative_item_extractor import (
    NegativeItemExtractor,
    extract_negative_items_from_report,
)


class TestNegativeItemExtractor:
    """Tests for NegativeItemExtractor class."""

    def test_init_with_parsed_report(self):
        """Test initialization with parsed report."""
        report = {
            "client_id": 1,
            "client_name": "Test Client",
            "accounts": [],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        assert extractor.client_id == 1
        assert extractor.client_name == "Test Client"

    def test_extract_all_negative_items_empty_report(self):
        """Test extraction with empty report."""
        report = {
            "accounts": [],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert items == []

    def test_detect_late_payment_30_days(self):
        """Test detection of 30 days late payment."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "payment_status": "30 days past due",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "late_payment"
        assert "30 day" in str(items[0]["negative_reasons"]).lower()

    def test_detect_late_payment_90_days(self):
        """Test detection of 90 days late payment."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "payment_status": "90 days past due",
                "bureaus": {"equifax": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] in ["late_payment", "settled"]

    def test_detect_charge_off(self):
        """Test detection of charge-off accounts."""
        report = {
            "accounts": [{
                "creditor": "Credit Card Co",
                "status": "Charged off as bad debt",
                "bureaus": {
                    "transunion": {"present": True, "status": "Charged off"},
                    "experian": {"present": True},
                    "equifax": {"present": True},
                },
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "charge_off"
        assert items[0]["creditor_name"] == "Credit Card Co"

    def test_detect_collection(self):
        """Test detection of collection accounts from status."""
        report = {
            "accounts": [{
                "creditor": "Collection Agency",
                "status": "Account in collection",
                "bureaus": {"equifax": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "collection"

    def test_detect_settled_account(self):
        """Test detection of settled accounts."""
        report = {
            "accounts": [{
                "creditor": "Loan Company",
                "comments": "Settled; less than full balance",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "settled"

    def test_skip_positive_accounts(self):
        """Test that positive accounts are skipped."""
        report = {
            "accounts": [{
                "creditor": "Good Bank",
                "status": "Pays as agreed",
                "payment_status": "Current",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 0

    def test_extract_bureaus_from_bureaus_dict(self):
        """Test bureau extraction from bureaus dictionary."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "status": "30 days late",
                "bureaus": {
                    "transunion": {"present": True},
                    "experian": {"present": True},
                    "equifax": {"present": False},
                },
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert "TransUnion" in items[0]["bureaus"]
        assert "Experian" in items[0]["bureaus"]
        assert "Equifax" not in items[0]["bureaus"]

    def test_extract_account_number(self):
        """Test account number extraction."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "account_number": "1234XXXX",
                "status": "Charge off",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert items[0]["account_id"] == "1234XXXX"

    def test_extract_inquiries(self):
        """Test inquiry extraction."""
        report = {
            "accounts": [],
            "inquiries": [{
                "creditor": "Auto Dealer",
                "date": "01/15/2024",
                "type": "Hard Inquiry",
                "bureau": "Experian",
            }],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "inquiry"
        assert items[0]["creditor_name"] == "Auto Dealer"

    def test_skip_soft_inquiries(self):
        """Test that soft inquiries are skipped."""
        report = {
            "accounts": [],
            "inquiries": [{
                "creditor": "Marketing Company",
                "date": "01/15/2024",
                "type": "Soft Inquiry - Promotional",
            }],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 0

    def test_extract_collections_section(self):
        """Test extraction from collections section."""
        report = {
            "accounts": [],
            "inquiries": [],
            "collections": [{
                "creditor": "Collection Agency XYZ",
                "balance": "$500.00",
                "original_creditor": "Original Bank",
                "date_assigned": "03/01/2024",
            }],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "collection"
        assert items[0]["balance"] == 500.0

    def test_extract_public_records_bankruptcy(self):
        """Test extraction of bankruptcy public record."""
        report = {
            "accounts": [],
            "inquiries": [],
            "collections": [],
            "public_records": [{
                "type": "Bankruptcy Chapter 7",
                "court": "US Bankruptcy Court",
                "case_number": "12-34567",
                "filed_date": "01/01/2020",
                "status": "Discharged",
            }],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "bankruptcy"
        assert items[0]["account_id"] == "12-34567"

    def test_extract_public_records_judgment(self):
        """Test extraction of judgment public record."""
        report = {
            "accounts": [],
            "inquiries": [],
            "collections": [],
            "public_records": [{
                "type": "Civil Judgment",
                "amount": "$5,000",
            }],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "judgment"
        assert items[0]["balance"] == 5000.0

    def test_extract_public_records_tax_lien(self):
        """Test extraction of tax lien public record."""
        report = {
            "accounts": [],
            "inquiries": [],
            "collections": [],
            "public_records": [{
                "type": "Tax Lien",
                "amount": "$10,000",
            }],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "tax_lien"

    def test_parse_currency_string(self):
        """Test currency parsing."""
        extractor = NegativeItemExtractor({})
        assert extractor._parse_currency("$1,234.56") == 1234.56
        assert extractor._parse_currency("$0.00") == 0.0
        assert extractor._parse_currency(500) == 500.0
        assert extractor._parse_currency(None) is None
        assert extractor._parse_currency("N/A") is None

    def test_high_utilization_detection(self):
        """Test detection of high credit utilization."""
        report = {
            "accounts": [{
                "creditor": "Credit Card",
                "status": "Open",  # Not explicitly positive
                "balance": "$950.00",
                "credit_limit": "$1000.00",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "high_utilization"
        assert "utilization" in str(items[0]["negative_reasons"]).lower()

    def test_multiple_negative_items(self):
        """Test extraction of multiple negative items."""
        report = {
            "accounts": [
                {
                    "creditor": "Bank A",
                    "status": "Charge off",
                    "bureaus": {"transunion": {"present": True}},
                },
                {
                    "creditor": "Bank B",
                    "status": "30 days late",
                    "bureaus": {"experian": {"present": True}},
                },
            ],
            "inquiries": [{
                "creditor": "Auto Dealer",
                "date": "01/15/2024",
            }],
            "collections": [{
                "creditor": "Collection Co",
                "balance": "$100",
            }],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 4

    def test_bureau_specific_status_detection(self):
        """Test detection of negative status in bureau-specific data."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "status": "Open",  # Looks positive at top level
                "bureaus": {
                    "transunion": {"present": True, "status": "Current"},
                    "experian": {"present": True, "status": "Charged off"},  # Negative!
                    "equifax": {"present": True, "status": "Current"},
                },
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert "Bureau experian: charged off" in items[0]["negative_reasons"]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_extract_negative_items_from_report(self):
        """Test the convenience function."""
        report = {
            "accounts": [{
                "creditor": "Test",
                "status": "Collection",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        items = extract_negative_items_from_report(report)
        assert len(items) == 1
        assert items[0]["item_type"] == "collection"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_bureaus_dict(self):
        """Test handling of missing bureaus dictionary."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "status": "Charge off",
                # No bureaus dict
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        # Should default to all bureaus
        assert len(items[0]["bureaus"]) == 3

    def test_null_account_number(self):
        """Test handling of null account number."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "account_number": None,
                "status": "Charge off",
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert items[0]["account_id"] == "N/A"

    def test_empty_status_fields(self):
        """Test handling of empty status fields."""
        report = {
            "accounts": [{
                "creditor": "Test Bank",
                "status": "",
                "payment_status": "",
                "comments": "Settled for less",  # Only negative indicator
                "bureaus": {"transunion": {"present": True}},
            }],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["item_type"] == "settled"

    def test_mixed_positive_negative_accounts(self):
        """Test report with mix of positive and negative accounts."""
        report = {
            "accounts": [
                {
                    "creditor": "Good Bank",
                    "status": "Pays as agreed",
                    "bureaus": {"transunion": {"present": True}},
                },
                {
                    "creditor": "Bad Bank",
                    "status": "Charge off",
                    "bureaus": {"transunion": {"present": True}},
                },
                {
                    "creditor": "Another Good Bank",
                    "status": "Current",
                    "payment_status": "On time payments",  # Avoid "never late" which contains "late"
                    "bureaus": {"experian": {"present": True}},
                },
            ],
            "inquiries": [],
            "collections": [],
            "public_records": [],
        }
        extractor = NegativeItemExtractor(report)
        items = extractor.extract_all_negative_items()
        assert len(items) == 1
        assert items[0]["creditor_name"] == "Bad Bank"
