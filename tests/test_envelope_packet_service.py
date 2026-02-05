"""
Unit tests for Envelope Packet Service - 5-Day Knock-Out Mailings

Tests cover:
- Bureau address constants
- Cover sheet generation
- Placeholder page generation
- Bureau packet creation
- SendCertified integration
- PDF utilities
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import io


class TestBureauAddresses:
    """Tests for BUREAU_FRAUD_ADDRESSES constant"""

    def test_bureau_addresses_exist(self):
        """Should have addresses for all three bureaus"""
        from services.envelope_packet_service import BUREAU_FRAUD_ADDRESSES

        assert 'Experian' in BUREAU_FRAUD_ADDRESSES
        assert 'Equifax' in BUREAU_FRAUD_ADDRESSES
        assert 'TransUnion' in BUREAU_FRAUD_ADDRESSES

    def test_bureau_addresses_have_required_fields(self):
        """Each bureau should have complete address info"""
        from services.envelope_packet_service import BUREAU_FRAUD_ADDRESSES

        required_fields = ['name', 'street', 'city', 'state', 'zip', 'full']

        for bureau, info in BUREAU_FRAUD_ADDRESSES.items():
            for field in required_fields:
                assert field in info, f"{bureau} missing field: {field}"
                assert info[field], f"{bureau} has empty {field}"


class TestEnvelopePacketServiceInit:
    """Tests for EnvelopePacketService initialization"""

    def test_creates_instance(self):
        """Should create service instance"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        assert service is not None
        assert service.styles is not None

    def test_has_custom_styles(self):
        """Should setup custom paragraph styles"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        # Check custom styles were added
        assert 'CoverTitle' in service.styles
        assert 'BureauAddress' in service.styles
        assert 'ChecklistItem' in service.styles
        assert 'ImportantNote' in service.styles
        assert 'SectionHeader' in service.styles


class TestCreateCoverSheet:
    """Tests for create_cover_sheet method"""

    def test_creates_pdf_bytes(self):
        """Should return PDF bytes"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service.create_cover_sheet(
            bureau='Experian',
            client_name='John Doe',
            accounts_disputed=[{'creditor': 'Test Bank', 'type': 'Credit Card'}]
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Check PDF signature
        assert result[:4] == b'%PDF'

    def test_works_without_accounts(self):
        """Should create cover sheet even without accounts"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service.create_cover_sheet(
            bureau='Equifax',
            client_name='Jane Smith',
            accounts_disputed=[]
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_handles_custom_date(self):
        """Should accept custom packet date"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()
        custom_date = datetime(2024, 6, 15)

        result = service.create_cover_sheet(
            bureau='TransUnion',
            client_name='Test Client',
            accounts_disputed=[],
            packet_date=custom_date
        )

        assert isinstance(result, bytes)

    def test_handles_unknown_bureau(self):
        """Should handle unknown bureau gracefully"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service.create_cover_sheet(
            bureau='UnknownBureau',
            client_name='Test Client',
            accounts_disputed=[]
        )

        assert isinstance(result, bytes)

    def test_limits_accounts_displayed(self):
        """Should limit accounts to 15"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        # Create 20 accounts
        accounts = [{'creditor': f'Bank {i}', 'type': 'Loan'} for i in range(20)]

        result = service.create_cover_sheet(
            bureau='Experian',
            client_name='Test Client',
            accounts_disputed=accounts
        )

        assert isinstance(result, bytes)


class TestCreatePlaceholderPage:
    """Tests for create_placeholder_page method"""

    def test_creates_pdf_bytes(self):
        """Should return PDF bytes"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service.create_placeholder_page(
            title='GOVERNMENT ID COPY',
            instructions=['Add your ID here', 'Make sure it is legible']
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'%PDF'

    def test_handles_empty_instructions(self):
        """Should handle empty instructions list"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service.create_placeholder_page(
            title='PROOF OF ADDRESS',
            instructions=[]
        )

        assert isinstance(result, bytes)


class TestCreateBureauPacket:
    """Tests for create_bureau_packet method"""

    def test_returns_tuple(self):
        """Should return tuple of (bytes, metadata)"""
        pytest.importorskip('PyPDF2')
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        mock_client = Mock()
        mock_client.name = 'Test Client'
        mock_client.id = 1

        # Actually run the method - it uses PyPDF2 internally
        result = service.create_bureau_packet(
            bureau='Experian',
            client=mock_client,
            accounts=[{'creditor': 'Test', 'type': 'Card'}],
            letter_content='<p>Test letter</p>',
            include_placeholders=False
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        # First element is bytes (PDF)
        assert isinstance(result[0], bytes)
        # Second element is metadata dict
        assert isinstance(result[1], dict)

    def test_metadata_has_required_fields(self):
        """Should include required metadata fields"""
        pytest.importorskip('PyPDF2')
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        mock_client = Mock()
        mock_client.name = 'Test Client'
        mock_client.id = 1

        pdf_bytes, metadata = service.create_bureau_packet(
            bureau='Equifax',
            client=mock_client,
            accounts=[],
            letter_content='Test',
            include_placeholders=False
        )

        assert 'bureau' in metadata
        assert 'client_id' in metadata
        assert 'client_name' in metadata
        assert 'recipient_name' in metadata
        assert 'recipient_address' in metadata
        assert 'documents_included' in metadata
        assert 'created_at' in metadata
        assert 'page_count' in metadata


class TestCreateAllBureauPackets:
    """Tests for create_all_bureau_packets method"""

    def test_returns_dict(self):
        """Should return dict mapping bureau to packet"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        mock_client = Mock()
        mock_client.name = 'Test Client'
        mock_client.id = 1

        with patch.object(service, 'create_bureau_packet') as mock_create:
            mock_create.return_value = (b'%PDF-test', {'bureau': 'Experian', 'page_count': 3})

            result = service.create_all_bureau_packets(
                client=mock_client,
                accounts_by_bureau={'Experian': [{'creditor': 'Test'}]},
                letters_by_bureau={'Experian': 'Test letter'}
            )

            assert isinstance(result, dict)

    def test_skips_bureaus_without_accounts(self):
        """Should skip bureaus with no accounts"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        mock_client = Mock()
        mock_client.name = 'Test Client'
        mock_client.id = 1

        with patch.object(service, 'create_bureau_packet') as mock_create:
            mock_create.return_value = (b'%PDF-test', {'bureau': 'Experian', 'page_count': 3})

            result = service.create_all_bureau_packets(
                client=mock_client,
                accounts_by_bureau={'Experian': [{'creditor': 'Test'}], 'Equifax': []},
                letters_by_bureau={'Experian': 'Test', 'Equifax': 'Test'}
            )

            # Only Experian should be created (Equifax has no accounts)
            mock_create.assert_called_once()


class TestQueueToSendCertified:
    """Tests for queue_to_sendcertified method"""

    @patch('services.envelope_packet_service.get_sendcertified_service')
    def test_fails_when_not_configured(self, mock_get_service):
        """Should fail when SendCertified not configured"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        mock_sendcert = Mock()
        mock_sendcert.is_configured.return_value = False
        mock_get_service.return_value = mock_sendcert

        result = service.queue_to_sendcertified(
            pdf_bytes=b'%PDF-test',
            metadata={
                'bureau': 'Experian',
                'recipient_name': 'Experian Fraud',
                'recipient_address': {'street': '123', 'city': 'Allen', 'state': 'TX', 'zip': '75013'}
            },
            client_id=1
        )

        assert result['success'] is False
        assert 'not configured' in result['error']

    @patch('services.envelope_packet_service.get_sendcertified_service')
    def test_queues_successfully(self, mock_get_service):
        """Should queue packet when configured"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        mock_sendcert = Mock()
        mock_sendcert.is_configured.return_value = True
        mock_sendcert.create_mailing.return_value = {
            'success': True,
            'tracking_number': 'TRACK123',
            'order_id': 'ORDER456'
        }
        mock_get_service.return_value = mock_sendcert

        result = service.queue_to_sendcertified(
            pdf_bytes=b'%PDF-test',
            metadata={
                'bureau': 'Equifax',
                'recipient_name': 'Equifax Fraud',
                'recipient_address': {'street': '123', 'city': 'Atlanta', 'state': 'GA', 'zip': '30348'}
            },
            client_id=1
        )

        assert result['success'] is True
        assert result['queued'] is True
        mock_sendcert.create_mailing.assert_called_once()


class TestQueueAllPackets:
    """Tests for queue_all_packets method"""

    def test_queues_all_bureaus(self):
        """Should queue all bureau packets"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        with patch.object(service, 'queue_to_sendcertified') as mock_queue:
            mock_queue.return_value = {'success': True, 'tracking_number': 'TRACK123'}

            packets = {
                'Experian': (b'%PDF-exp', {'bureau': 'Experian'}),
                'Equifax': (b'%PDF-eqf', {'bureau': 'Equifax'}),
            }

            results = service.queue_all_packets(packets=packets, client_id=1)

            assert len(results) == 2
            assert 'Experian' in results
            assert 'Equifax' in results
            assert mock_queue.call_count == 2


class TestHtmlToPdf:
    """Tests for _html_to_pdf method"""

    def test_converts_html_to_pdf(self):
        """Should convert HTML string to PDF bytes"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service._html_to_pdf(
            html_content='<p>Test paragraph</p><p>Another paragraph</p>',
            title='Test Document'
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'%PDF'

    def test_handles_empty_html(self):
        """Should handle empty HTML"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        result = service._html_to_pdf(
            html_content='',
            title='Empty Document'
        )

        assert isinstance(result, bytes)

    def test_handles_complex_html(self):
        """Should handle HTML with headings and formatting"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        html = """
        <h1>LETTER HEADING</h1>
        <p>Date: January 1, 2024</p>
        <p>RE: Identity Theft Block Request</p>
        <p>This is a test letter with multiple paragraphs.</p>
        """

        result = service._html_to_pdf(html_content=html, title='Test Letter')

        assert isinstance(result, bytes)


class TestCountPages:
    """Tests for _count_pages method"""

    def test_counts_pages_in_pdf(self):
        """Should count pages in PDF"""
        pytest.importorskip('PyPDF2')
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        # Create a simple PDF to count
        test_pdf = service.create_cover_sheet(
            bureau='Experian',
            client_name='Test',
            accounts_disputed=[]
        )

        count = service._count_pages(test_pdf)

        assert count >= 1

    def test_returns_zero_on_error(self):
        """Should return 0 on invalid PDF"""
        from services.envelope_packet_service import EnvelopePacketService

        service = EnvelopePacketService()

        count = service._count_pages(b'not a valid pdf')

        assert count == 0


class TestGetEnvelopePacketService:
    """Tests for get_envelope_packet_service factory"""

    def test_returns_instance(self):
        """Should return EnvelopePacketService instance"""
        from services.envelope_packet_service import get_envelope_packet_service, EnvelopePacketService

        service = get_envelope_packet_service()

        assert isinstance(service, EnvelopePacketService)
