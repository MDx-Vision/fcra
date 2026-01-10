"""
Comprehensive Unit Tests for SendCertified SFTP Integration Service.

Tests cover:
- SFTP connection establishment
- Batch upload functionality
- Letter batch creation and sending
- Tracking status retrieval
- Batch status updates
- Bureau address lookup
- Error handling and edge cases
"""

import pytest
import os
import sys
import io
import csv
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock paramiko before importing the service module
sys.modules['paramiko'] = MagicMock()

from services.sendcertified_sftp_service import (
    get_sftp_connection,
    upload_batch,
    send_letter_batch,
    check_tracking,
    update_batch_status,
    get_bureau_address,
    BUREAU_ADDRESSES,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.flush = MagicMock()
    session.refresh = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_sftp():
    """Create a mock SFTP client."""
    sftp = MagicMock()
    sftp.mkdir = MagicMock()
    sftp.putfo = MagicMock()
    sftp.put = MagicMock()
    sftp.getfo = MagicMock()
    sftp.close = MagicMock()
    return sftp


@pytest.fixture
def mock_transport():
    """Create a mock transport object."""
    transport = MagicMock()
    transport.connect = MagicMock()
    transport.close = MagicMock()
    return transport


@pytest.fixture
def sample_letters():
    """Create sample letter data for batch uploads."""
    return [
        {
            "letter_id": 1,
            "recipient_name": "Equifax Information Services LLC",
            "address1": "P.O. Box 740256",
            "address2": "",
            "city": "Atlanta",
            "state": "GA",
            "zip": "30374-0256",
            "pdf_path": "/tmp/letter_1.pdf",
            "tracking_number": "SCM000001",
        },
        {
            "letter_id": 2,
            "recipient_name": "Experian",
            "address1": "P.O. Box 4500",
            "address2": "",
            "city": "Allen",
            "state": "TX",
            "zip": "75013",
            "pdf_path": "/tmp/letter_2.pdf",
            "tracking_number": "SCM000002",
        },
    ]


@pytest.fixture
def mock_dispute_letter():
    """Create a mock DisputeLetter object."""
    letter = MagicMock()
    letter.id = 1
    letter.client_id = 100
    letter.bureau = "Equifax"
    letter.round_number = 1
    letter.file_path = "/tmp/dispute_letter_1.pdf"
    letter.sent_via_letterstream = False
    letter.sent_at = None
    letter.tracking_number = None
    return letter


@pytest.fixture
def mock_letter_batch():
    """Create a mock LetterBatch object."""
    batch = MagicMock()
    batch.id = 1
    batch.batch_id = "BATCH_20250115_120000"
    batch.letter_count = 2
    batch.cost_cents = 2200
    batch.status = "uploaded"
    batch.uploaded_at = datetime.utcnow()
    batch.tracking_received_at = None
    return batch


# =============================================================================
# Test Class: Constants and Bureau Addresses
# =============================================================================

class TestBureauAddresses:
    """Tests for BUREAU_ADDRESSES dictionary."""

    def test_bureau_addresses_contains_equifax(self):
        """Test Equifax address is present."""
        assert "Equifax" in BUREAU_ADDRESSES
        equifax = BUREAU_ADDRESSES["Equifax"]
        assert equifax["name"] == "Equifax Information Services LLC"
        assert equifax["city"] == "Atlanta"
        assert equifax["state"] == "GA"

    def test_bureau_addresses_contains_experian(self):
        """Test Experian address is present."""
        assert "Experian" in BUREAU_ADDRESSES
        experian = BUREAU_ADDRESSES["Experian"]
        assert experian["name"] == "Experian"
        assert experian["city"] == "Allen"
        assert experian["state"] == "TX"

    def test_bureau_addresses_contains_transunion(self):
        """Test TransUnion address is present."""
        assert "TransUnion" in BUREAU_ADDRESSES
        transunion = BUREAU_ADDRESSES["TransUnion"]
        assert transunion["name"] == "TransUnion LLC"
        assert transunion["city"] == "Chester"
        assert transunion["state"] == "PA"

    def test_transunion_has_address2(self):
        """Test TransUnion has address2 field."""
        transunion = BUREAU_ADDRESSES["TransUnion"]
        assert "address2" in transunion
        assert transunion["address2"] == "P.O. Box 2000"


# =============================================================================
# Test Class: get_bureau_address Function
# =============================================================================

class TestGetBureauAddress:
    """Tests for get_bureau_address function."""

    def test_get_bureau_address_equifax(self):
        """Test getting Equifax address."""
        result = get_bureau_address("Equifax")
        assert result["name"] == "Equifax Information Services LLC"
        assert result["state"] == "GA"

    def test_get_bureau_address_experian(self):
        """Test getting Experian address."""
        result = get_bureau_address("Experian")
        assert result["name"] == "Experian"
        assert result["state"] == "TX"

    def test_get_bureau_address_transunion(self):
        """Test getting TransUnion address."""
        result = get_bureau_address("TransUnion")
        assert result["name"] == "TransUnion LLC"
        assert result["state"] == "PA"

    def test_get_bureau_address_unknown_returns_equifax(self):
        """Test unknown bureau returns Equifax as default."""
        result = get_bureau_address("UnknownBureau")
        assert result["name"] == "Equifax Information Services LLC"
        assert result["state"] == "GA"

    def test_get_bureau_address_empty_returns_equifax(self):
        """Test empty bureau name returns Equifax as default."""
        result = get_bureau_address("")
        assert result["name"] == "Equifax Information Services LLC"

    def test_get_bureau_address_none_returns_equifax(self):
        """Test None bureau returns Equifax as default."""
        result = get_bureau_address(None)
        assert result["name"] == "Equifax Information Services LLC"


# =============================================================================
# Test Class: get_sftp_connection Function
# =============================================================================

class TestGetSftpConnection:
    """Tests for get_sftp_connection function."""

    @patch.dict(os.environ, {
        "SENDCERTIFIED_SFTP_HOST": "sftp.sendcertified.com",
        "SENDCERTIFIED_SFTP_USERNAME": "testuser",
        "SENDCERTIFIED_SFTP_PASSWORD": "testpass",
        "SENDCERTIFIED_SFTP_PORT": "22"
    })
    @patch('services.sendcertified_sftp_service.paramiko')
    def test_get_sftp_connection_success(self, mock_paramiko):
        """Test successful SFTP connection."""
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        sftp, transport = get_sftp_connection()

        mock_paramiko.Transport.assert_called_once_with(("sftp.sendcertified.com", 22))
        mock_transport.connect.assert_called_once_with(username="testuser", password="testpass")
        assert sftp == mock_sftp
        assert transport == mock_transport

    @patch.dict(os.environ, {
        "SENDCERTIFIED_SFTP_HOST": "sftp.sendcertified.com",
        "SENDCERTIFIED_SFTP_USERNAME": "testuser",
        "SENDCERTIFIED_SFTP_PASSWORD": "testpass"
    })
    @patch('services.sendcertified_sftp_service.paramiko')
    def test_get_sftp_connection_default_port(self, mock_paramiko):
        """Test SFTP connection with default port 22."""
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        sftp, transport = get_sftp_connection()

        mock_paramiko.Transport.assert_called_once_with(("sftp.sendcertified.com", 22))

    @patch.dict(os.environ, {
        "SENDCERTIFIED_SFTP_HOST": "sftp.sendcertified.com",
        "SENDCERTIFIED_SFTP_USERNAME": "testuser",
        "SENDCERTIFIED_SFTP_PASSWORD": "testpass",
        "SENDCERTIFIED_SFTP_PORT": "2222"
    })
    @patch('services.sendcertified_sftp_service.paramiko')
    def test_get_sftp_connection_custom_port(self, mock_paramiko):
        """Test SFTP connection with custom port."""
        mock_transport = MagicMock()
        mock_sftp = MagicMock()
        mock_paramiko.Transport.return_value = mock_transport
        mock_paramiko.SFTPClient.from_transport.return_value = mock_sftp

        sftp, transport = get_sftp_connection()

        mock_paramiko.Transport.assert_called_once_with(("sftp.sendcertified.com", 2222))

    @patch.dict(os.environ, {}, clear=True)
    def test_get_sftp_connection_missing_host(self):
        """Test connection fails with missing host."""
        # Remove specific vars if they exist
        for key in ["SENDCERTIFIED_SFTP_HOST", "SENDCERTIFIED_SFTP_USERNAME", "SENDCERTIFIED_SFTP_PASSWORD"]:
            os.environ.pop(key, None)

        with pytest.raises(ValueError, match="Missing SendCertified SFTP credentials"):
            get_sftp_connection()

    @patch.dict(os.environ, {
        "SENDCERTIFIED_SFTP_HOST": "sftp.sendcertified.com"
    }, clear=True)
    def test_get_sftp_connection_missing_username(self):
        """Test connection fails with missing username."""
        with pytest.raises(ValueError, match="Missing SendCertified SFTP credentials"):
            get_sftp_connection()

    @patch.dict(os.environ, {
        "SENDCERTIFIED_SFTP_HOST": "sftp.sendcertified.com",
        "SENDCERTIFIED_SFTP_USERNAME": "testuser"
    }, clear=True)
    def test_get_sftp_connection_missing_password(self):
        """Test connection fails with missing password."""
        with pytest.raises(ValueError, match="Missing SendCertified SFTP credentials"):
            get_sftp_connection()


# =============================================================================
# Test Class: upload_batch Function
# =============================================================================

class TestUploadBatch:
    """Tests for upload_batch function."""

    def test_upload_batch_empty_letters_raises_error(self):
        """Test upload_batch raises error with empty letters list."""
        with pytest.raises(ValueError, match="No letters provided"):
            upload_batch([])

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_success(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test successful batch upload."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        result = upload_batch(sample_letters)

        assert result["status"] == "uploaded"
        assert result["letter_count"] == 2
        assert "batch_id" in result
        assert result["batch_id"].startswith("BATCH_")
        assert "timestamp" in result

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_creates_directory(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test batch upload creates batch directory."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        result = upload_batch(sample_letters)

        mock_sftp.mkdir.assert_called_once()
        mkdir_call = mock_sftp.mkdir.call_args[0][0]
        assert mkdir_call.startswith("/uploads/BATCH_")

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_uploads_csv_manifest(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test batch upload creates and uploads CSV manifest."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        upload_batch(sample_letters)

        # Verify putfo was called (for CSV manifest upload)
        assert mock_sftp.putfo.call_count >= 1
        csv_call = mock_sftp.putfo.call_args_list[0]
        csv_path = csv_call[0][1]
        assert csv_path.endswith("/manifest.csv")

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_uploads_pdf_files(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test batch upload uploads PDF files."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        upload_batch(sample_letters)

        # Should upload 2 PDFs
        assert mock_sftp.put.call_count == 2

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_skips_missing_pdf(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test batch upload skips PDFs that don't exist."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = False  # All PDFs don't exist

        letters = [
            {
                "letter_id": 1,
                "recipient_name": "Test",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "pdf_path": "/nonexistent/letter.pdf",
            }
        ]

        result = upload_batch(letters)

        # Should not call put for PDFs
        mock_sftp.put.assert_not_called()
        assert result["letter_count"] == 1

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_handles_empty_pdf_path(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test batch upload handles empty pdf_path."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = False

        letters = [
            {
                "letter_id": 1,
                "recipient_name": "Test",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "pdf_path": "",
            }
        ]

        result = upload_batch(letters)

        mock_sftp.put.assert_not_called()
        assert result["status"] == "uploaded"

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_handles_none_pdf_path(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test batch upload handles None pdf_path."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)

        letters = [
            {
                "letter_id": 1,
                "recipient_name": "Test",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                "pdf_path": None,
            }
        ]

        result = upload_batch(letters)

        mock_sftp.put.assert_not_called()
        assert result["status"] == "uploaded"

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_handles_mkdir_ioerror(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test batch upload handles IOError when directory exists."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True
        mock_sftp.mkdir.side_effect = IOError("Directory exists")

        # Should not raise exception - IOError is caught
        result = upload_batch(sample_letters)

        assert result["status"] == "uploaded"

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_closes_connections_on_success(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test SFTP connections are closed after successful upload."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        upload_batch(sample_letters)

        mock_sftp.close.assert_called_once()
        mock_transport.close.assert_called_once()

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_closes_connections_on_error(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test SFTP connections are closed even on error."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True
        mock_sftp.putfo.side_effect = Exception("Upload failed")

        with pytest.raises(Exception, match="Upload failed"):
            upload_batch(sample_letters)

        mock_sftp.close.assert_called_once()
        mock_transport.close.assert_called_once()

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_csv_contains_correct_fields(self, mock_exists, mock_get_connection, sample_letters, mock_sftp, mock_transport):
        """Test CSV manifest contains correct fields."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        captured_csv = None
        def capture_csv(file_obj, path):
            nonlocal captured_csv
            captured_csv = file_obj.read().decode('utf-8')
        mock_sftp.putfo.side_effect = capture_csv

        upload_batch(sample_letters)

        assert captured_csv is not None
        reader = csv.DictReader(io.StringIO(captured_csv))
        rows = list(reader)
        assert len(rows) == 2
        assert "letter_id" in reader.fieldnames
        assert "recipient_name" in reader.fieldnames
        assert "address1" in reader.fieldnames
        assert "city" in reader.fieldnames
        assert "state" in reader.fieldnames
        assert "zip" in reader.fieldnames
        assert "pdf_filename" in reader.fieldnames
        assert "tracking_number" in reader.fieldnames

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_optional_fields_default_to_empty(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test optional fields default to empty string."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = False

        letters = [
            {
                "letter_id": 1,
                "recipient_name": "Test",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "zip": "12345",
                # No address2, pdf_path, or tracking_number
            }
        ]

        captured_csv = None
        def capture_csv(file_obj, path):
            nonlocal captured_csv
            captured_csv = file_obj.read().decode('utf-8')
        mock_sftp.putfo.side_effect = capture_csv

        upload_batch(letters)

        reader = csv.DictReader(io.StringIO(captured_csv))
        rows = list(reader)
        assert rows[0]["address2"] == ""
        assert rows[0]["pdf_filename"] == ""
        assert rows[0]["tracking_number"] == ""


# =============================================================================
# Test Class: send_letter_batch Function
# =============================================================================

class TestSendLetterBatch:
    """Tests for send_letter_batch function."""

    @patch('services.sendcertified_sftp_service.upload_batch')
    def test_send_letter_batch_no_letters_raises_error(self, mock_upload, mock_db_session):
        """Test send_letter_batch raises error when no letters found."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        with pytest.raises(ValueError, match="No letters found"):
            send_letter_batch(mock_db_session, [1, 2, 3])

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_success(self, MockDeadline, MockBatch, mock_upload, mock_db_session, mock_dispute_letter):
        """Test successful letter batch sending."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_dispute_letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = send_letter_batch(mock_db_session, [1])

        assert result["batch_id"] == "BATCH_20250115_120000"
        assert result["letter_count"] == 1
        assert result["cost_cents"] == 1100  # 1 letter * 1100 cents
        assert "deadline_ids" in result
        mock_db_session.commit.assert_called_once()

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_calculates_correct_cost(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test cost calculation for multiple letters."""
        letter1 = MagicMock()
        letter1.id = 1
        letter1.client_id = 100
        letter1.bureau = "Equifax"
        letter1.round_number = 1
        letter1.file_path = "/tmp/letter1.pdf"

        letter2 = MagicMock()
        letter2.id = 2
        letter2.client_id = 100
        letter2.bureau = "Experian"
        letter2.round_number = 1
        letter2.file_path = "/tmp/letter2.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter1, letter2]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 2,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = send_letter_batch(mock_db_session, [1, 2])

        assert result["cost_cents"] == 2200  # 2 letters * 1100 cents

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_creates_deadlines(self, MockDeadline, MockBatch, mock_upload, mock_db_session, mock_dispute_letter):
        """Test that deadlines are created for sent letters."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_dispute_letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Mock deadline ID assignment via flush
        deadline_instance = MagicMock()
        deadline_instance.id = 500
        MockDeadline.return_value = deadline_instance

        result = send_letter_batch(mock_db_session, [1])

        MockDeadline.assert_called_once()
        deadline_call_kwargs = MockDeadline.call_args[1]
        assert deadline_call_kwargs["client_id"] == 100
        assert deadline_call_kwargs["deadline_type"] == "cra_response"
        assert deadline_call_kwargs["related_bureau"] == "Equifax"
        assert deadline_call_kwargs["round_number"] == 1
        assert "deadline_ids" in result

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_updates_letter_status(self, MockDeadline, MockBatch, mock_upload, mock_db_session, mock_dispute_letter):
        """Test that letters are marked as sent."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_dispute_letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        send_letter_batch(mock_db_session, [1])

        assert mock_dispute_letter.sent_via_letterstream is True
        assert mock_dispute_letter.sent_at is not None
        assert mock_dispute_letter.tracking_number == "SCM000001"

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_skips_unknown_bureau(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test that letters with unknown bureau are skipped."""
        letter = MagicMock()
        letter.id = 1
        letter.client_id = 100
        letter.bureau = "UnknownBureau"
        letter.round_number = 1
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 0,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = send_letter_batch(mock_db_session, [1])

        # Letter count should be 0 since unknown bureau was skipped
        assert result["letter_count"] == 0

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_handles_none_bureau(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test that letters with None bureau default to Equifax."""
        letter = MagicMock()
        letter.id = 1
        letter.client_id = 100
        letter.bureau = None
        letter.round_number = 1
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = send_letter_batch(mock_db_session, [1])

        # Should have processed 1 letter (defaulted to Equifax)
        assert result["letter_count"] == 1

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_handles_none_round_number(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test that letters with None round_number default to 1."""
        letter = MagicMock()
        letter.id = 1
        letter.client_id = 100
        letter.bureau = "Equifax"
        letter.round_number = None
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        deadline_instance = MagicMock()
        deadline_instance.id = 500
        MockDeadline.return_value = deadline_instance

        send_letter_batch(mock_db_session, [1])

        # Deadline should be created with round_number 1
        deadline_call_kwargs = MockDeadline.call_args[1]
        assert deadline_call_kwargs["round_number"] == 1

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_creates_letter_batch_record(self, MockDeadline, MockBatch, mock_upload, mock_db_session, mock_dispute_letter):
        """Test that LetterBatch record is created."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_dispute_letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        send_letter_batch(mock_db_session, [1])

        MockBatch.assert_called_once()
        batch_call_kwargs = MockBatch.call_args[1]
        assert batch_call_kwargs["batch_id"] == "BATCH_20250115_120000"
        assert batch_call_kwargs["letter_count"] == 1
        assert batch_call_kwargs["cost_cents"] == 1100
        assert batch_call_kwargs["status"] == "uploaded"
        mock_db_session.add.assert_called()

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_returns_sent_at(self, MockDeadline, MockBatch, mock_upload, mock_db_session, mock_dispute_letter):
        """Test that sent_at timestamp is returned."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_dispute_letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = send_letter_batch(mock_db_session, [1])

        assert "sent_at" in result


# =============================================================================
# Test Class: check_tracking Function
# =============================================================================

class TestCheckTracking:
    """Tests for check_tracking function."""

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    def test_check_tracking_success(self, mock_get_connection, mock_sftp, mock_transport):
        """Test successful tracking data retrieval."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)

        # Create mock tracking CSV data
        tracking_csv = "letter_id,status,delivered_at\n1,delivered,2025-01-15\n"

        def mock_getfo(remote_path, file_obj):
            file_obj.write(tracking_csv.encode('utf-8'))
        mock_sftp.getfo.side_effect = mock_getfo

        result = check_tracking("BATCH_20250115_120000")

        assert result["tracking_available"] is True
        assert result["batch_id"] == "BATCH_20250115_120000"
        assert "tracking_data" in result
        assert "retrieved_at" in result

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    def test_check_tracking_not_available(self, mock_get_connection, mock_sftp, mock_transport):
        """Test tracking when file not yet available."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_sftp.getfo.side_effect = IOError("File not found")

        result = check_tracking("BATCH_20250115_120000")

        assert result["tracking_available"] is False
        assert result["batch_id"] == "BATCH_20250115_120000"
        assert result["message"] == "Tracking data not yet available"
        assert "retrieved_at" in result

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    def test_check_tracking_closes_connections(self, mock_get_connection, mock_sftp, mock_transport):
        """Test connections are closed after tracking check."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_sftp.getfo.side_effect = IOError("File not found")

        check_tracking("BATCH_20250115_120000")

        mock_sftp.close.assert_called_once()
        mock_transport.close.assert_called_once()

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    def test_check_tracking_parses_csv_data(self, mock_get_connection, mock_sftp, mock_transport):
        """Test tracking CSV data is properly parsed."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)

        tracking_csv = "letter_id,status,tracking_number\n1,delivered,9400111899223334445566\n2,in_transit,9400111899223334445567\n"

        def mock_getfo(remote_path, file_obj):
            file_obj.write(tracking_csv.encode('utf-8'))
        mock_sftp.getfo.side_effect = mock_getfo

        result = check_tracking("BATCH_20250115_120000")

        assert len(result["tracking_data"]) == 2
        assert result["tracking_data"][0]["letter_id"] == "1"
        assert result["tracking_data"][0]["status"] == "delivered"

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    def test_check_tracking_correct_file_path(self, mock_get_connection, mock_sftp, mock_transport):
        """Test tracking uses correct file path."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_sftp.getfo.side_effect = IOError("File not found")

        check_tracking("BATCH_20250115_120000")

        mock_sftp.getfo.assert_called_once()
        call_args = mock_sftp.getfo.call_args[0]
        assert call_args[0] == "/tracking/BATCH_20250115_120000_tracking.csv"


# =============================================================================
# Test Class: update_batch_status Function
# =============================================================================

class TestUpdateBatchStatus:
    """Tests for update_batch_status function."""

    @patch('services.sendcertified_sftp_service.check_tracking')
    def test_update_batch_status_batch_not_found(self, mock_check_tracking, mock_db_session):
        """Test update returns None when batch not found."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        result = update_batch_status(mock_db_session, "BATCH_NONEXISTENT")

        assert result is None
        mock_check_tracking.assert_not_called()

    @patch('services.sendcertified_sftp_service.check_tracking')
    def test_update_batch_status_tracking_available(self, mock_check_tracking, mock_db_session, mock_letter_batch):
        """Test batch status updated when tracking available."""
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_letter_batch
        mock_check_tracking.return_value = {
            "tracking_available": True,
            "tracking_data": [{"letter_id": "1", "status": "delivered"}]
        }

        result = update_batch_status(mock_db_session, "BATCH_20250115_120000")

        assert result == mock_letter_batch
        assert mock_letter_batch.status == "complete"
        assert mock_letter_batch.tracking_received_at is not None
        mock_db_session.commit.assert_called_once()

    @patch('services.sendcertified_sftp_service.check_tracking')
    def test_update_batch_status_tracking_not_available(self, mock_check_tracking, mock_db_session, mock_letter_batch):
        """Test batch status not changed when tracking not available."""
        original_status = mock_letter_batch.status
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_letter_batch
        mock_check_tracking.return_value = {
            "tracking_available": False,
            "message": "Tracking data not yet available"
        }

        result = update_batch_status(mock_db_session, "BATCH_20250115_120000")

        assert result == mock_letter_batch
        assert mock_letter_batch.status == original_status
        # commit should not be called since status wasn't updated
        mock_db_session.commit.assert_not_called()


# =============================================================================
# Test Class: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_single_letter(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test batch upload with single letter."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = True

        letters = [{
            "letter_id": 1,
            "recipient_name": "Test Recipient",
            "address1": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345",
            "pdf_path": "/tmp/test.pdf"
        }]

        result = upload_batch(letters)

        assert result["letter_count"] == 1

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_generates_unique_batch_ids(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test batch IDs contain timestamp for uniqueness."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = False

        letters = [{"letter_id": 1, "recipient_name": "Test"}]

        result = upload_batch(letters)

        assert result["batch_id"].startswith("BATCH_")
        # Format should be BATCH_YYYYMMDD_HHMMSS
        batch_parts = result["batch_id"].split("_")
        assert len(batch_parts) == 3
        assert len(batch_parts[1]) == 8  # Date part
        assert len(batch_parts[2]) == 6  # Time part

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_deadline_30_days(self, MockDeadline, MockBatch, mock_upload, mock_db_session, mock_dispute_letter):
        """Test deadline is set to 30 days from now."""
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_dispute_letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        deadline_instance = MagicMock()
        deadline_instance.id = 500
        MockDeadline.return_value = deadline_instance

        send_letter_batch(mock_db_session, [1])

        deadline_call_kwargs = MockDeadline.call_args[1]
        deadline_date = deadline_call_kwargs["deadline_date"]
        expected_date = datetime.utcnow() + timedelta(days=30)
        # Check that dates are approximately equal (within 1 second)
        assert abs((deadline_date - expected_date).total_seconds()) < 1

    def test_bureau_addresses_all_have_required_fields(self):
        """Test all bureau addresses have required fields."""
        required_fields = ["name", "address1", "city", "state", "zip"]

        for bureau_name, address in BUREAU_ADDRESSES.items():
            for field in required_fields:
                assert field in address, f"{bureau_name} missing {field}"

    @patch('services.sendcertified_sftp_service.get_sftp_connection')
    @patch('services.sendcertified_sftp_service.os.path.exists')
    def test_upload_batch_handles_special_characters_in_recipient(self, mock_exists, mock_get_connection, mock_sftp, mock_transport):
        """Test batch upload handles special characters in recipient name."""
        mock_get_connection.return_value = (mock_sftp, mock_transport)
        mock_exists.return_value = False

        letters = [{
            "letter_id": 1,
            "recipient_name": "Test & Company, LLC",
            "address1": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "zip": "12345"
        }]

        captured_csv = None
        def capture_csv(file_obj, path):
            nonlocal captured_csv
            captured_csv = file_obj.read().decode('utf-8')
        mock_sftp.putfo.side_effect = capture_csv

        result = upload_batch(letters)

        assert result["status"] == "uploaded"
        assert "Test & Company, LLC" in captured_csv

    @patch.dict(os.environ, {
        "SENDCERTIFIED_SFTP_HOST": "sftp.sendcertified.com",
        "SENDCERTIFIED_SFTP_USERNAME": "testuser",
        "SENDCERTIFIED_SFTP_PASSWORD": "testpass"
    })
    @patch('services.sendcertified_sftp_service.paramiko')
    def test_get_sftp_connection_transport_error(self, mock_paramiko):
        """Test connection handles transport error."""
        mock_paramiko.Transport.side_effect = Exception("Connection refused")

        with pytest.raises(Exception, match="Connection refused"):
            get_sftp_connection()

    @patch('services.sendcertified_sftp_service.upload_batch')
    def test_send_letter_batch_with_empty_file_path(self, mock_upload, mock_db_session):
        """Test send_letter_batch handles letter with empty file_path."""
        letter = MagicMock()
        letter.id = 1
        letter.client_id = 100
        letter.bureau = "Equifax"
        letter.round_number = 1
        letter.file_path = ""  # Empty file path

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        # This tests that the function doesn't crash with empty file_path
        with patch('services.sendcertified_sftp_service.LetterBatch'):
            with patch('services.sendcertified_sftp_service.CaseDeadline'):
                result = send_letter_batch(mock_db_session, [1])
                assert result["letter_count"] == 1


# =============================================================================
# Test Class: Integration with Database Models
# =============================================================================

class TestDatabaseIntegration:
    """Tests for integration with database models."""

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_creates_deadline_with_correct_description(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test deadline description is correctly formatted."""
        letter = MagicMock()
        letter.id = 1
        letter.client_id = 100
        letter.bureau = "TransUnion"
        letter.round_number = 2
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        deadline_instance = MagicMock()
        deadline_instance.id = 500
        MockDeadline.return_value = deadline_instance

        send_letter_batch(mock_db_session, [1])

        deadline_call_kwargs = MockDeadline.call_args[1]
        assert "TransUnion Response Deadline" in deadline_call_kwargs["description"]
        assert "Round 2" in deadline_call_kwargs["description"]

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_send_letter_batch_flush_and_get_deadline_ids(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test flush is called to get deadline IDs."""
        letter = MagicMock()
        letter.id = 1
        letter.client_id = 100
        letter.bureau = "Equifax"
        letter.round_number = 1
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        deadline_instance = MagicMock()
        deadline_instance.id = 999
        MockDeadline.return_value = deadline_instance

        result = send_letter_batch(mock_db_session, [1])

        mock_db_session.flush.assert_called()
        assert 999 in result["deadline_ids"]


# =============================================================================
# Test Class: Tracking Number Generation
# =============================================================================

class TestTrackingNumberGeneration:
    """Tests for tracking number generation."""

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_tracking_number_format(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test tracking number follows SCM format."""
        letter = MagicMock()
        letter.id = 123
        letter.client_id = 100
        letter.bureau = "Equifax"
        letter.round_number = 1
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        send_letter_batch(mock_db_session, [123])

        # Tracking number should be SCM + 6 digit letter ID
        assert letter.tracking_number == "SCM000123"

    @patch('services.sendcertified_sftp_service.upload_batch')
    @patch('services.sendcertified_sftp_service.LetterBatch')
    @patch('services.sendcertified_sftp_service.CaseDeadline')
    def test_tracking_number_large_id(self, MockDeadline, MockBatch, mock_upload, mock_db_session):
        """Test tracking number with large letter ID."""
        letter = MagicMock()
        letter.id = 999999
        letter.client_id = 100
        letter.bureau = "Equifax"
        letter.round_number = 1
        letter.file_path = "/tmp/letter.pdf"

        mock_db_session.query.return_value.filter.return_value.all.return_value = [letter]
        mock_upload.return_value = {
            "batch_id": "BATCH_20250115_120000",
            "letter_count": 1,
            "status": "uploaded",
            "timestamp": datetime.utcnow().isoformat()
        }

        send_letter_batch(mock_db_session, [999999])

        assert letter.tracking_number == "SCM999999"
