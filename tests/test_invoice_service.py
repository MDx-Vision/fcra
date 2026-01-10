"""
Unit tests for Invoice Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta


class TestInvoiceConstants:
    """Test invoice constants and configuration"""

    def test_invoice_prefix_exists(self):
        from services.invoice_service import INVOICE_PREFIX
        assert INVOICE_PREFIX is not None
        assert len(INVOICE_PREFIX) > 0

    def test_default_due_days(self):
        from services.invoice_service import DEFAULT_DUE_DAYS
        assert DEFAULT_DUE_DAYS >= 0
        assert DEFAULT_DUE_DAYS == 30  # Default is 30 days

    def test_default_tax_rate(self):
        from services.invoice_service import DEFAULT_TAX_RATE
        assert DEFAULT_TAX_RATE >= 0.0
        assert DEFAULT_TAX_RATE <= 1.0

    def test_invoice_statuses_defined(self):
        from database import INVOICE_STATUSES
        assert isinstance(INVOICE_STATUSES, dict)
        assert 'draft' in INVOICE_STATUSES
        assert 'sent' in INVOICE_STATUSES
        assert 'paid' in INVOICE_STATUSES
        assert 'overdue' in INVOICE_STATUSES
        assert 'cancelled' in INVOICE_STATUSES

    def test_invoice_item_types_defined(self):
        from database import INVOICE_ITEM_TYPES
        assert isinstance(INVOICE_ITEM_TYPES, dict)
        assert 'service' in INVOICE_ITEM_TYPES
        assert 'analysis' in INVOICE_ITEM_TYPES
        assert 'round' in INVOICE_ITEM_TYPES
        assert 'discount' in INVOICE_ITEM_TYPES


class TestInvoiceNumberGeneration:
    """Test invoice number generation"""

    @patch('services.invoice_service.SessionLocal')
    def test_generate_invoice_number_format(self, mock_session_local):
        from services.invoice_service import _generate_invoice_number, INVOICE_PREFIX

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        number = _generate_invoice_number()

        year = datetime.utcnow().year
        assert number.startswith(f"{INVOICE_PREFIX}-{year}-")
        assert len(number.split('-')) == 3

    @patch('services.invoice_service.SessionLocal')
    def test_generate_invoice_number_increments(self, mock_session_local):
        from services.invoice_service import _generate_invoice_number, INVOICE_PREFIX

        year = datetime.utcnow().year

        # Mock existing invoice
        mock_invoice = Mock()
        mock_invoice.invoice_number = f"{INVOICE_PREFIX}-{year}-00005"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        number = _generate_invoice_number()

        assert number == f"{INVOICE_PREFIX}-{year}-00006"


class TestCreateInvoice:
    """Test invoice creation"""

    @patch('services.invoice_service.SessionLocal')
    @patch('services.invoice_service._generate_invoice_number')
    def test_create_invoice_success(self, mock_gen_number, mock_session_local):
        from services.invoice_service import create_invoice

        mock_gen_number.return_value = 'INV-2026-00001'

        mock_client = Mock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.email = 'test@example.com'
        mock_client.address_street = '123 Main St'
        mock_client.address_city = 'New York'
        mock_client.address_state = 'NY'
        mock_client.address_zip = '10001'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.invoice_number = 'INV-2026-00001'
        mock_invoice.to_dict.return_value = {'id': 1, 'invoice_number': 'INV-2026-00001'}

        def mock_add(obj):
            if hasattr(obj, 'invoice_number'):
                obj.id = 1
        mock_db.add = mock_add
        mock_db.refresh = lambda x: None

        mock_session_local.return_value = mock_db

        result = create_invoice(
            client_id=1,
            items=[{
                'description': 'Test Service',
                'unit_price': 10000,  # $100.00
                'quantity': 1,
            }],
        )

        assert result.get('success') is True
        mock_db.commit.assert_called()

    @patch('services.invoice_service.SessionLocal')
    def test_create_invoice_client_not_found(self, mock_session_local):
        from services.invoice_service import create_invoice

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = create_invoice(
            client_id=999,
            items=[{'description': 'Test', 'unit_price': 1000}],
        )

        assert result.get('success') is False
        assert 'not found' in result.get('error', '').lower()

    @patch('services.invoice_service.SessionLocal')
    def test_create_invoice_no_items(self, mock_session_local):
        from services.invoice_service import create_invoice

        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        result = create_invoice(
            client_id=1,
            items=[],
        )

        assert result.get('success') is False
        assert 'item' in result.get('error', '').lower()


class TestGetInvoice:
    """Test getting invoices"""

    @patch('services.invoice_service.SessionLocal')
    def test_get_invoice_success(self, mock_session_local):
        from services.invoice_service import get_invoice

        mock_invoice = Mock()
        mock_invoice.to_dict.return_value = {'id': 1, 'invoice_number': 'INV-2026-00001'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = get_invoice(1)

        assert result.get('success') is True
        assert result.get('invoice') is not None

    @patch('services.invoice_service.SessionLocal')
    def test_get_invoice_not_found(self, mock_session_local):
        from services.invoice_service import get_invoice

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = get_invoice(999)

        assert result.get('success') is False
        assert 'not found' in result.get('error', '').lower()

    @patch('services.invoice_service.SessionLocal')
    def test_get_invoice_by_number(self, mock_session_local):
        from services.invoice_service import get_invoice_by_number

        mock_invoice = Mock()
        mock_invoice.to_dict.return_value = {'id': 1, 'invoice_number': 'INV-2026-00001'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = get_invoice_by_number('INV-2026-00001')

        assert result.get('success') is True


class TestListInvoices:
    """Test listing invoices"""

    @patch('services.invoice_service.SessionLocal')
    def test_list_invoices_empty(self, mock_session_local):
        from services.invoice_service import list_invoices

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_session_local.return_value = mock_db

        result = list_invoices()

        assert result.get('success') is True
        assert result.get('invoices') == []
        assert result.get('total') == 0

    @patch('services.invoice_service.SessionLocal')
    def test_list_invoices_with_filters(self, mock_session_local):
        from services.invoice_service import list_invoices

        mock_invoice = Mock()
        mock_invoice.to_dict.return_value = {'id': 1, 'status': 'paid'}

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_invoice]
        mock_session_local.return_value = mock_db

        result = list_invoices(status='paid', limit=10)

        assert result.get('success') is True
        assert result.get('limit') == 10


class TestUpdateInvoice:
    """Test updating invoices"""

    @patch('services.invoice_service.SessionLocal')
    def test_update_invoice_success(self, mock_session_local):
        from services.invoice_service import update_invoice

        mock_invoice = Mock()
        mock_invoice.status = 'draft'
        mock_invoice.subtotal = 10000
        mock_invoice.discount_amount = 0
        mock_invoice.tax_rate = 0.0
        mock_invoice.to_dict.return_value = {'id': 1, 'title': 'Updated Title'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = update_invoice(1, title='Updated Title')

        assert result.get('success') is True
        assert mock_invoice.title == 'Updated Title'

    @patch('services.invoice_service.SessionLocal')
    def test_update_invoice_not_found(self, mock_session_local):
        from services.invoice_service import update_invoice

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_local.return_value = mock_db

        result = update_invoice(999, title='Test')

        assert result.get('success') is False

    @patch('services.invoice_service.SessionLocal')
    def test_update_invoice_paid_not_allowed(self, mock_session_local):
        from services.invoice_service import update_invoice

        mock_invoice = Mock()
        mock_invoice.status = 'paid'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = update_invoice(1, title='Test')

        assert result.get('success') is False
        assert 'paid' in result.get('error', '').lower()


class TestLineItems:
    """Test line item operations"""

    @patch('services.invoice_service.SessionLocal')
    @patch('services.invoice_service._recalculate_invoice_totals')
    def test_add_item_success(self, mock_recalc, mock_session_local):
        from services.invoice_service import add_item

        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.status = 'draft'
        mock_invoice.to_dict.return_value = {'id': 1}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_session_local.return_value = mock_db

        result = add_item(
            invoice_id=1,
            description='New Service',
            unit_price=5000,
        )

        assert result.get('success') is True
        mock_db.add.assert_called()

    @patch('services.invoice_service.SessionLocal')
    @patch('services.invoice_service._recalculate_invoice_totals')
    def test_remove_item_success(self, mock_recalc, mock_session_local):
        from services.invoice_service import remove_item

        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.status = 'draft'
        mock_invoice.to_dict.return_value = {'id': 1}

        mock_item = Mock()
        mock_item.id = 1
        mock_item.invoice_id = 1

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_invoice, mock_item]
        mock_session_local.return_value = mock_db

        result = remove_item(1, 1)

        assert result.get('success') is True
        mock_db.delete.assert_called_with(mock_item)


class TestPayments:
    """Test payment recording"""

    @patch('services.invoice_service.SessionLocal')
    def test_record_payment_success(self, mock_session_local):
        from services.invoice_service import record_payment

        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.status = 'sent'
        mock_invoice.total = 10000
        mock_invoice.amount_paid = 0
        mock_invoice.amount_due = 10000
        mock_invoice.to_dict.return_value = {'id': 1, 'amount_due': 0}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = record_payment(
            invoice_id=1,
            amount=10000,
            payment_method='stripe',
        )

        assert result.get('success') is True
        assert result.get('fully_paid') is True
        assert mock_invoice.status == 'paid'

    @patch('services.invoice_service.SessionLocal')
    def test_record_partial_payment(self, mock_session_local):
        from services.invoice_service import record_payment

        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.status = 'sent'
        mock_invoice.total = 10000
        mock_invoice.amount_paid = 0
        mock_invoice.amount_due = 10000
        mock_invoice.to_dict.return_value = {'id': 1, 'amount_due': 5000}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = record_payment(
            invoice_id=1,
            amount=5000,
            payment_method='cash',
        )

        assert result.get('success') is True
        assert result.get('fully_paid') is False
        assert mock_invoice.status == 'partial'

    @patch('services.invoice_service.SessionLocal')
    def test_record_payment_exceeds_due(self, mock_session_local):
        from services.invoice_service import record_payment

        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.status = 'sent'
        mock_invoice.amount_due = 5000

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = record_payment(
            invoice_id=1,
            amount=10000,  # Exceeds amount due
            payment_method='cash',
        )

        assert result.get('success') is False
        assert 'exceeds' in result.get('error', '').lower()

    @patch('services.invoice_service.SessionLocal')
    def test_record_payment_zero_amount(self, mock_session_local):
        from services.invoice_service import record_payment

        mock_invoice = Mock()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = record_payment(
            invoice_id=1,
            amount=0,
            payment_method='cash',
        )

        assert result.get('success') is False
        assert 'positive' in result.get('error', '').lower()


class TestVoidInvoice:
    """Test voiding invoices"""

    @patch('services.invoice_service.SessionLocal')
    def test_void_invoice_success(self, mock_session_local):
        from services.invoice_service import void_invoice

        mock_invoice = Mock()
        mock_invoice.status = 'sent'
        mock_invoice.internal_notes = ''
        mock_invoice.to_dict.return_value = {'id': 1, 'status': 'cancelled'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = void_invoice(1, reason='Customer cancelled')

        assert result.get('success') is True
        assert mock_invoice.status == 'cancelled'

    @patch('services.invoice_service.SessionLocal')
    def test_void_paid_invoice_not_allowed(self, mock_session_local):
        from services.invoice_service import void_invoice

        mock_invoice = Mock()
        mock_invoice.status = 'paid'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = void_invoice(1)

        assert result.get('success') is False
        assert 'refund' in result.get('error', '').lower()


class TestMarkSentViewed:
    """Test marking invoices sent/viewed"""

    @patch('services.invoice_service.SessionLocal')
    def test_mark_sent(self, mock_session_local):
        from services.invoice_service import mark_sent

        mock_invoice = Mock()
        mock_invoice.status = 'draft'
        mock_invoice.email_sent_count = 0
        mock_invoice.to_dict.return_value = {'id': 1, 'status': 'sent'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = mark_sent(1)

        assert result.get('success') is True
        assert mock_invoice.status == 'sent'
        assert mock_invoice.email_sent_count == 1

    @patch('services.invoice_service.SessionLocal')
    def test_mark_viewed(self, mock_session_local):
        from services.invoice_service import mark_viewed

        mock_invoice = Mock()
        mock_invoice.status = 'sent'
        mock_invoice.viewed_at = None
        mock_invoice.to_dict.return_value = {'id': 1, 'status': 'viewed'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = mark_viewed(1)

        assert result.get('success') is True
        assert mock_invoice.status == 'viewed'
        assert mock_invoice.viewed_at is not None


class TestCheckOverdue:
    """Test overdue invoice checking"""

    @patch('services.invoice_service.SessionLocal')
    def test_check_overdue_invoices(self, mock_session_local):
        from services.invoice_service import check_overdue_invoices

        mock_invoice1 = Mock()
        mock_invoice1.id = 1
        mock_invoice1.status = 'sent'

        mock_invoice2 = Mock()
        mock_invoice2.id = 2
        mock_invoice2.status = 'viewed'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_invoice1, mock_invoice2]
        mock_session_local.return_value = mock_db

        result = check_overdue_invoices()

        assert result.get('success') is True
        assert result.get('updated_count') == 2
        assert mock_invoice1.status == 'overdue'
        assert mock_invoice2.status == 'overdue'


class TestDeleteInvoice:
    """Test invoice deletion"""

    @patch('services.invoice_service.SessionLocal')
    def test_delete_draft_invoice(self, mock_session_local):
        from services.invoice_service import delete_invoice

        mock_invoice = Mock()
        mock_invoice.status = 'draft'
        mock_invoice.pdf_filename = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = delete_invoice(1)

        assert result.get('success') is True
        mock_db.delete.assert_called_with(mock_invoice)

    @patch('services.invoice_service.SessionLocal')
    def test_delete_non_draft_not_allowed(self, mock_session_local):
        from services.invoice_service import delete_invoice

        mock_invoice = Mock()
        mock_invoice.status = 'sent'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_session_local.return_value = mock_db

        result = delete_invoice(1)

        assert result.get('success') is False
        assert 'draft' in result.get('error', '').lower()


class TestInvoiceStats:
    """Test invoice statistics"""

    @patch('services.invoice_service.SessionLocal')
    def test_get_invoice_stats(self, mock_session_local):
        from services.invoice_service import get_invoice_stats

        mock_invoice1 = Mock()
        mock_invoice1.status = 'paid'
        mock_invoice1.total = 10000
        mock_invoice1.amount_paid = 10000
        mock_invoice1.amount_due = 0

        mock_invoice2 = Mock()
        mock_invoice2.status = 'sent'
        mock_invoice2.total = 5000
        mock_invoice2.amount_paid = 0
        mock_invoice2.amount_due = 5000

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [mock_invoice1, mock_invoice2]
        mock_session_local.return_value = mock_db

        result = get_invoice_stats()

        assert result.get('success') is True
        stats = result.get('stats')
        assert stats['total_invoices'] == 2
        assert stats['total_invoiced'] == 15000
        assert stats['total_paid'] == 10000
        assert stats['total_outstanding'] == 5000


class TestConvenienceFunctions:
    """Test convenience functions for common invoice types"""

    @patch('services.invoice_service.create_invoice')
    def test_create_invoice_for_round(self, mock_create):
        from services.invoice_service import create_invoice_for_round

        mock_create.return_value = {'success': True, 'invoice_id': 1}

        result = create_invoice_for_round(
            client_id=1,
            round_number=2,
            amount=29700,
        )

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['client_id'] == 1
        assert 'Round 2' in call_args[1]['title']

    @patch('services.invoice_service.create_invoice')
    def test_create_invoice_for_analysis(self, mock_create):
        from services.invoice_service import create_invoice_for_analysis

        mock_create.return_value = {'success': True, 'invoice_id': 1}

        result = create_invoice_for_analysis(
            client_id=1,
            analysis_id=5,
        )

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['client_id'] == 1
        assert 'Analysis' in call_args[1]['title']

    @patch('services.invoice_service.create_invoice')
    def test_create_invoice_for_settlement(self, mock_create):
        from services.invoice_service import create_invoice_for_settlement

        mock_create.return_value = {'success': True, 'invoice_id': 1}

        result = create_invoice_for_settlement(
            client_id=1,
            settlement_id=10,
            settlement_amount=100000,  # $1000
            fee_rate=0.30,
        )

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]['client_id'] == 1
        # 30% of $1000 = $300
        assert call_args[1]['items'][0]['unit_price'] == 30000


class TestPdfGeneration:
    """Test PDF generation"""

    @patch('services.invoice_service.WEASYPRINT_AVAILABLE', False)
    def test_generate_pdf_no_weasyprint(self):
        from services.invoice_service import generate_invoice_pdf

        result = generate_invoice_pdf(1)

        assert result.get('success') is False
        assert 'weasyprint' in result.get('error', '').lower()

    def test_build_invoice_html(self):
        from services.invoice_service import _build_invoice_html
        from database import INVOICE_STATUSES

        mock_invoice = Mock()
        mock_invoice.invoice_number = 'INV-2026-00001'
        mock_invoice.status = 'sent'
        mock_invoice.company_name = 'Test Company'
        mock_invoice.company_address = '123 Test St'
        mock_invoice.company_phone = '555-1234'
        mock_invoice.company_email = 'test@company.com'
        mock_invoice.billing_name = 'John Doe'
        mock_invoice.billing_email = 'john@example.com'
        mock_invoice.billing_address = '456 Client Ave'
        mock_invoice.invoice_date = date(2026, 1, 3)
        mock_invoice.due_date = date(2026, 2, 2)
        mock_invoice.subtotal = 10000
        mock_invoice.discount_amount = 0
        mock_invoice.tax_rate = 0.0
        mock_invoice.tax_amount = 0
        mock_invoice.total = 10000
        mock_invoice.amount_paid = 0
        mock_invoice.amount_due = 10000
        mock_invoice.notes = 'Test notes'

        mock_item = Mock()
        mock_item.description = 'Test Service'
        mock_item.quantity = 1.0
        mock_item.unit_price = 10000
        mock_item.amount = 10000

        mock_invoice.items = [mock_item]

        html = _build_invoice_html(mock_invoice)

        assert 'INV-2026-00001' in html
        assert 'Test Company' in html
        assert 'John Doe' in html
        assert '$100.00' in html
