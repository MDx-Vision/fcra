"""
Invoice Service - Generate and manage client invoices

Features:
- Create, update, delete invoices
- Add/remove line items
- Record payments (full or partial)
- Generate PDF invoices
- Send invoices via email
- Track invoice status
- Auto-generate invoice numbers
"""

import os
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

# PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from database import (
    SessionLocal, Invoice, InvoiceItem, InvoicePayment, Client,
    INVOICE_STATUSES, INVOICE_ITEM_TYPES
)


# Service configuration
INVOICE_PREFIX = os.getenv('INVOICE_PREFIX', 'INV')
INVOICE_PDF_DIR = os.getenv('INVOICE_PDF_DIR', 'static/invoices')
DEFAULT_DUE_DAYS = int(os.getenv('INVOICE_DUE_DAYS', '30'))
DEFAULT_TAX_RATE = float(os.getenv('INVOICE_TAX_RATE', '0.0'))

# Company defaults (can be overridden per invoice)
DEFAULT_COMPANY_NAME = os.getenv('COMPANY_NAME', 'Brightpath Ascend Group')
DEFAULT_COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
DEFAULT_COMPANY_PHONE = os.getenv('COMPANY_PHONE', '')
DEFAULT_COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', '')


def _generate_invoice_number(session=None) -> str:
    """Generate unique invoice number: INV-YYYY-NNNNN"""
    year = datetime.utcnow().year

    if session is None:
        db = SessionLocal()
        close_db = True
    else:
        db = session
        close_db = False

    try:
        # Find the highest invoice number for this year
        prefix = f"{INVOICE_PREFIX}-{year}-"
        latest = db.query(Invoice).filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(Invoice.id.desc()).first()

        if latest:
            try:
                last_num = int(latest.invoice_number.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:05d}"
    finally:
        if close_db:
            db.close()


def create_invoice(
    client_id: int,
    items: List[Dict[str, Any]],
    invoice_date: Optional[date] = None,
    due_date: Optional[date] = None,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    internal_notes: Optional[str] = None,
    tax_rate: Optional[float] = None,
    company_name: Optional[str] = None,
    company_address: Optional[str] = None,
    company_phone: Optional[str] = None,
    company_email: Optional[str] = None,
    company_logo_url: Optional[str] = None,
    tenant_id: Optional[int] = None,
    created_by_id: Optional[int] = None,
    status: str = 'draft',
) -> Dict[str, Any]:
    """
    Create a new invoice with line items.

    Args:
        client_id: Client to invoice
        items: List of line item dicts with keys:
            - description (required)
            - quantity (default 1.0)
            - unit_price (in cents, required)
            - item_type (default 'service')
            - reference_type (optional)
            - reference_id (optional)
        invoice_date: Date of invoice (default today)
        due_date: Payment due date (default 30 days from invoice_date)
        title: Invoice title/description
        notes: Client-visible notes
        internal_notes: Staff-only notes
        tax_rate: Tax rate (0.0 to 1.0)
        company_*: Company branding fields
        tenant_id: White label tenant ID
        created_by_id: Staff ID who created
        status: Initial status (default 'draft')

    Returns:
        Dict with success status and invoice data
    """
    db = SessionLocal()
    try:
        # Validate client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'success': False, 'error': 'Client not found'}

        # Validate items
        if not items or len(items) == 0:
            return {'success': False, 'error': 'At least one line item is required'}

        # Generate invoice number
        invoice_number = _generate_invoice_number(db)

        # Set dates
        if invoice_date is None:
            invoice_date = date.today()
        if due_date is None:
            due_date = invoice_date + timedelta(days=DEFAULT_DUE_DAYS)

        # Use defaults for company info
        if company_name is None:
            company_name = DEFAULT_COMPANY_NAME
        if company_address is None:
            company_address = DEFAULT_COMPANY_ADDRESS
        if company_phone is None:
            company_phone = DEFAULT_COMPANY_PHONE
        if company_email is None:
            company_email = DEFAULT_COMPANY_EMAIL

        # Build billing address from client
        billing_parts = []
        if client.address_street:
            billing_parts.append(client.address_street)
        if client.address_city or client.address_state or client.address_zip:
            city_state_zip = ', '.join(filter(None, [
                client.address_city,
                f"{client.address_state} {client.address_zip}".strip() if client.address_state or client.address_zip else None
            ]))
            billing_parts.append(city_state_zip)

        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            client_id=client_id,
            title=title,
            notes=notes,
            internal_notes=internal_notes,
            tax_rate=tax_rate if tax_rate is not None else DEFAULT_TAX_RATE,
            invoice_date=invoice_date,
            due_date=due_date,
            status=status,
            billing_name=client.name,
            billing_email=client.email,
            billing_address='\n'.join(billing_parts) if billing_parts else None,
            company_name=company_name,
            company_address=company_address,
            company_phone=company_phone,
            company_email=company_email,
            company_logo_url=company_logo_url,
            tenant_id=tenant_id,
            created_by_id=created_by_id,
        )
        db.add(invoice)
        db.flush()  # Get invoice ID

        # Add line items
        subtotal = 0
        discount_total = 0

        for i, item_data in enumerate(items):
            description = item_data.get('description')
            if not description:
                db.rollback()
                return {'success': False, 'error': f'Item {i+1} missing description'}

            quantity = float(item_data.get('quantity', 1.0))
            unit_price = int(item_data.get('unit_price', 0))
            amount = int(quantity * unit_price)
            item_type = item_data.get('item_type', 'service')

            # Track discounts/credits separately
            if item_type in ('discount', 'credit'):
                discount_total += abs(amount)
                amount = -abs(amount)  # Ensure negative
            else:
                subtotal += amount

            item = InvoiceItem(
                invoice_id=invoice.id,
                item_type=item_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                reference_type=item_data.get('reference_type'),
                reference_id=item_data.get('reference_id'),
                sort_order=i,
            )
            db.add(item)

        # Calculate totals
        invoice.subtotal = subtotal
        invoice.discount_amount = discount_total
        invoice.tax_amount = int((subtotal - discount_total) * invoice.tax_rate)
        invoice.total = subtotal - discount_total + invoice.tax_amount
        invoice.amount_due = invoice.total

        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(),
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
        }

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def get_invoice(invoice_id: int, include_payments: bool = False) -> Dict[str, Any]:
    """Get invoice by ID"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        return {
            'success': True,
            'invoice': invoice.to_dict(include_items=True, include_payments=include_payments),
        }
    finally:
        db.close()


def get_invoice_by_number(invoice_number: str, include_payments: bool = False) -> Dict[str, Any]:
    """Get invoice by invoice number"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        return {
            'success': True,
            'invoice': invoice.to_dict(include_items=True, include_payments=include_payments),
        }
    finally:
        db.close()


def list_invoices(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    tenant_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """List invoices with optional filters"""
    db = SessionLocal()
    try:
        query = db.query(Invoice)

        if client_id:
            query = query.filter(Invoice.client_id == client_id)
        if status:
            query = query.filter(Invoice.status == status)
        if tenant_id:
            query = query.filter(Invoice.tenant_id == tenant_id)
        if from_date:
            query = query.filter(Invoice.invoice_date >= from_date)
        if to_date:
            query = query.filter(Invoice.invoice_date <= to_date)

        total = query.count()
        invoices = query.order_by(Invoice.invoice_date.desc(), Invoice.id.desc())\
            .offset(offset).limit(limit).all()

        return {
            'success': True,
            'invoices': [inv.to_dict(include_items=False) for inv in invoices],
            'total': total,
            'limit': limit,
            'offset': offset,
        }
    finally:
        db.close()


def update_invoice(
    invoice_id: int,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    internal_notes: Optional[str] = None,
    due_date: Optional[date] = None,
    tax_rate: Optional[float] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Update invoice fields (not line items - use add/remove item methods)"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        # Don't allow editing paid/cancelled invoices
        if invoice.status in ('paid', 'cancelled', 'refunded'):
            return {'success': False, 'error': f'Cannot edit invoice with status: {invoice.status}'}

        if title is not None:
            invoice.title = title
        if notes is not None:
            invoice.notes = notes
        if internal_notes is not None:
            invoice.internal_notes = internal_notes
        if due_date is not None:
            invoice.due_date = due_date
        if tax_rate is not None:
            invoice.tax_rate = tax_rate
            # Recalculate tax
            invoice.tax_amount = int((invoice.subtotal - invoice.discount_amount) * invoice.tax_rate)
            invoice.total = invoice.subtotal - invoice.discount_amount + invoice.tax_amount
            invoice.amount_due = invoice.total - invoice.amount_paid
        if status is not None:
            if status not in INVOICE_STATUSES:
                return {'success': False, 'error': f'Invalid status: {status}'}
            invoice.status = status

        invoice.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(),
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def add_item(
    invoice_id: int,
    description: str,
    unit_price: int,
    quantity: float = 1.0,
    item_type: str = 'service',
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Add a line item to an invoice"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if invoice.status in ('paid', 'cancelled', 'refunded'):
            return {'success': False, 'error': f'Cannot modify invoice with status: {invoice.status}'}

        # Get next sort order
        max_order = db.query(InvoiceItem).filter(
            InvoiceItem.invoice_id == invoice_id
        ).count()

        amount = int(quantity * unit_price)

        # Handle discounts/credits
        if item_type in ('discount', 'credit'):
            amount = -abs(amount)

        item = InvoiceItem(
            invoice_id=invoice_id,
            item_type=item_type,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            sort_order=max_order,
        )
        db.add(item)

        # Recalculate totals
        _recalculate_invoice_totals(invoice, db)

        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(),
            'item': item.to_dict(),
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def remove_item(invoice_id: int, item_id: int) -> Dict[str, Any]:
    """Remove a line item from an invoice"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if invoice.status in ('paid', 'cancelled', 'refunded'):
            return {'success': False, 'error': f'Cannot modify invoice with status: {invoice.status}'}

        item = db.query(InvoiceItem).filter(
            InvoiceItem.id == item_id,
            InvoiceItem.invoice_id == invoice_id
        ).first()
        if not item:
            return {'success': False, 'error': 'Item not found'}

        db.delete(item)

        # Recalculate totals
        _recalculate_invoice_totals(invoice, db)

        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(),
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def _recalculate_invoice_totals(invoice: Invoice, db) -> None:
    """Recalculate invoice totals from line items"""
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).all()

    subtotal = 0
    discount_total = 0

    for item in items:
        if item.item_type in ('discount', 'credit'):
            discount_total += abs(item.amount)
        else:
            subtotal += item.amount

    invoice.subtotal = subtotal
    invoice.discount_amount = discount_total
    invoice.tax_amount = int((subtotal - discount_total) * invoice.tax_rate)
    invoice.total = subtotal - discount_total + invoice.tax_amount
    invoice.amount_due = invoice.total - invoice.amount_paid
    invoice.updated_at = datetime.utcnow()


def record_payment(
    invoice_id: int,
    amount: int,
    payment_method: str = 'other',
    stripe_payment_intent_id: Optional[str] = None,
    stripe_charge_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    notes: Optional[str] = None,
    recorded_by_id: Optional[int] = None,
    paid_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Record a payment against an invoice"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if invoice.status in ('cancelled', 'refunded'):
            return {'success': False, 'error': f'Cannot pay invoice with status: {invoice.status}'}

        if amount <= 0:
            return {'success': False, 'error': 'Payment amount must be positive'}

        if amount > invoice.amount_due:
            return {'success': False, 'error': f'Payment amount ({amount}) exceeds amount due ({invoice.amount_due})'}

        payment = InvoicePayment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_charge_id=stripe_charge_id,
            transaction_id=transaction_id,
            notes=notes,
            recorded_by_id=recorded_by_id,
            paid_at=paid_at or datetime.utcnow(),
            status='completed',
        )
        db.add(payment)

        # Update invoice
        invoice.amount_paid += amount
        invoice.amount_due = invoice.total - invoice.amount_paid
        invoice.payment_method = payment_method

        if stripe_payment_intent_id:
            invoice.stripe_payment_intent_id = stripe_payment_intent_id

        # Update status based on payment
        if invoice.amount_due <= 0:
            invoice.status = 'paid'
            invoice.paid_at = payment.paid_at
        elif invoice.amount_paid > 0:
            invoice.status = 'partial'

        invoice.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(include_payments=True),
            'payment': payment.to_dict(),
            'fully_paid': invoice.amount_due <= 0,
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def void_invoice(invoice_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
    """Void/cancel an invoice"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if invoice.status == 'paid':
            return {'success': False, 'error': 'Cannot void a paid invoice - use refund instead'}

        if invoice.status == 'cancelled':
            return {'success': False, 'error': 'Invoice already cancelled'}

        invoice.status = 'cancelled'
        if reason:
            invoice.internal_notes = (invoice.internal_notes or '') + f'\n\nVoided: {reason}'
        invoice.updated_at = datetime.utcnow()

        db.commit()

        return {
            'success': True,
            'invoice': invoice.to_dict(),
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def mark_sent(invoice_id: int) -> Dict[str, Any]:
    """Mark invoice as sent"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if invoice.status == 'draft':
            invoice.status = 'sent'
        invoice.sent_at = datetime.utcnow()
        invoice.email_sent_count = (invoice.email_sent_count or 0) + 1
        invoice.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(),
        }
    finally:
        db.close()


def mark_viewed(invoice_id: int) -> Dict[str, Any]:
    """Mark invoice as viewed by client"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if not invoice.viewed_at:
            invoice.viewed_at = datetime.utcnow()
        if invoice.status == 'sent':
            invoice.status = 'viewed'
        invoice.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(invoice)

        return {
            'success': True,
            'invoice': invoice.to_dict(),
        }
    finally:
        db.close()


def check_overdue_invoices() -> Dict[str, Any]:
    """Check for overdue invoices and update their status"""
    db = SessionLocal()
    try:
        today = date.today()

        # Find invoices that are overdue
        overdue_invoices = db.query(Invoice).filter(
            Invoice.status.in_(['sent', 'viewed', 'partial']),
            Invoice.due_date < today,
            Invoice.amount_due > 0,
        ).all()

        updated = 0
        for invoice in overdue_invoices:
            invoice.status = 'overdue'
            invoice.updated_at = datetime.utcnow()
            updated += 1

        db.commit()

        return {
            'success': True,
            'updated_count': updated,
            'overdue_invoice_ids': [inv.id for inv in overdue_invoices],
        }
    finally:
        db.close()


def generate_invoice_pdf(invoice_id: int) -> Dict[str, Any]:
    """Generate PDF for an invoice"""
    if not WEASYPRINT_AVAILABLE:
        return {'success': False, 'error': 'WeasyPrint not installed'}

    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        # Build HTML
        html_content = _build_invoice_html(invoice)

        # Ensure directory exists
        os.makedirs(INVOICE_PDF_DIR, exist_ok=True)

        # Generate PDF
        filename = f"{invoice.invoice_number}.pdf"
        filepath = os.path.join(INVOICE_PDF_DIR, filename)

        HTML(string=html_content).write_pdf(filepath)

        # Update invoice
        invoice.pdf_filename = filename
        invoice.pdf_generated_at = datetime.utcnow()
        invoice.updated_at = datetime.utcnow()

        db.commit()

        return {
            'success': True,
            'pdf_filename': filename,
            'pdf_path': filepath,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def _build_invoice_html(invoice: Invoice) -> str:
    """Build HTML content for invoice PDF"""

    # Format currency helper
    def fmt_currency(cents: int) -> str:
        return f"${cents / 100:,.2f}"

    # Build items HTML
    items_html = ""
    for item in invoice.items:
        items_html += f"""
        <tr>
            <td>{item.description}</td>
            <td class="text-right">{item.quantity}</td>
            <td class="text-right">{fmt_currency(item.unit_price)}</td>
            <td class="text-right">{fmt_currency(item.amount)}</td>
        </tr>
        """

    # Status badge color
    status_colors = {
        'draft': '#6b7280',
        'sent': '#3b82f6',
        'viewed': '#8b5cf6',
        'paid': '#22c55e',
        'partial': '#f59e0b',
        'overdue': '#ef4444',
        'cancelled': '#6b7280',
        'refunded': '#6b7280',
    }
    status_color = status_colors.get(invoice.status, '#6b7280')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Invoice {invoice.invoice_number}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 12px;
                line-height: 1.5;
                color: #1f2937;
                padding: 40px;
            }}
            .header {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
            .company {{ }}
            .company-name {{ font-size: 24px; font-weight: bold; color: #111827; }}
            .company-details {{ color: #6b7280; margin-top: 5px; }}
            .invoice-info {{ text-align: right; }}
            .invoice-title {{ font-size: 28px; font-weight: bold; color: #111827; }}
            .invoice-number {{ color: #6b7280; margin-top: 5px; }}
            .status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 9999px;
                color: white;
                background-color: {status_color};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                margin-top: 10px;
            }}
            .addresses {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .address-block {{ }}
            .address-label {{ font-size: 10px; color: #6b7280; text-transform: uppercase; margin-bottom: 5px; }}
            .address-name {{ font-weight: 600; }}
            .dates {{ margin-bottom: 30px; }}
            .date-row {{ display: flex; gap: 40px; }}
            .date-item {{ }}
            .date-label {{ font-size: 10px; color: #6b7280; text-transform: uppercase; }}
            .date-value {{ font-weight: 600; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th {{
                text-align: left;
                padding: 12px 8px;
                border-bottom: 2px solid #e5e7eb;
                font-size: 10px;
                text-transform: uppercase;
                color: #6b7280;
            }}
            td {{ padding: 12px 8px; border-bottom: 1px solid #f3f4f6; }}
            .text-right {{ text-align: right; }}
            .totals {{ margin-left: auto; width: 300px; }}
            .totals-row {{ display: flex; justify-content: space-between; padding: 8px 0; }}
            .totals-row.total {{
                border-top: 2px solid #e5e7eb;
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                padding-top: 15px;
            }}
            .totals-row.due {{
                background: #fef3c7;
                padding: 15px;
                border-radius: 8px;
                margin-top: 10px;
            }}
            .totals-row.paid {{ color: #22c55e; }}
            .notes {{
                margin-top: 40px;
                padding: 20px;
                background: #f9fafb;
                border-radius: 8px;
            }}
            .notes-label {{ font-size: 10px; color: #6b7280; text-transform: uppercase; margin-bottom: 5px; }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                color: #9ca3af;
                font-size: 11px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="company">
                <div class="company-name">{invoice.company_name or DEFAULT_COMPANY_NAME}</div>
                <div class="company-details">
                    {invoice.company_address or ''}<br>
                    {invoice.company_phone or ''}<br>
                    {invoice.company_email or ''}
                </div>
            </div>
            <div class="invoice-info">
                <div class="invoice-title">INVOICE</div>
                <div class="invoice-number">{invoice.invoice_number}</div>
                <div class="status">{INVOICE_STATUSES.get(invoice.status, invoice.status)}</div>
            </div>
        </div>

        <div class="addresses">
            <div class="address-block">
                <div class="address-label">Bill To</div>
                <div class="address-name">{invoice.billing_name}</div>
                <div>{invoice.billing_email or ''}</div>
                <div>{(invoice.billing_address or '').replace(chr(10), '<br>')}</div>
            </div>
        </div>

        <div class="dates">
            <div class="date-row">
                <div class="date-item">
                    <div class="date-label">Invoice Date</div>
                    <div class="date-value">{invoice.invoice_date.strftime('%B %d, %Y') if invoice.invoice_date else ''}</div>
                </div>
                <div class="date-item">
                    <div class="date-label">Due Date</div>
                    <div class="date-value">{invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else ''}</div>
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th class="text-right">Qty</th>
                    <th class="text-right">Unit Price</th>
                    <th class="text-right">Amount</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div class="totals">
            <div class="totals-row">
                <span>Subtotal</span>
                <span>{fmt_currency(invoice.subtotal)}</span>
            </div>
            {"<div class='totals-row'><span>Discount</span><span>-" + fmt_currency(invoice.discount_amount) + "</span></div>" if invoice.discount_amount else ""}
            {"<div class='totals-row'><span>Tax (" + str(int(invoice.tax_rate * 100)) + "%)</span><span>" + fmt_currency(invoice.tax_amount) + "</span></div>" if invoice.tax_amount else ""}
            <div class="totals-row total">
                <span>Total</span>
                <span>{fmt_currency(invoice.total)}</span>
            </div>
            {"<div class='totals-row paid'><span>Amount Paid</span><span>" + fmt_currency(invoice.amount_paid) + "</span></div>" if invoice.amount_paid else ""}
            {"<div class='totals-row due'><span>Amount Due</span><span>" + fmt_currency(invoice.amount_due) + "</span></div>" if invoice.amount_due else ""}
        </div>

        {f"<div class='notes'><div class='notes-label'>Notes</div>{invoice.notes}</div>" if invoice.notes else ""}

        <div class="footer">
            Thank you for your business!<br>
            {invoice.company_name or DEFAULT_COMPANY_NAME}
        </div>
    </body>
    </html>
    """

    return html


def send_invoice_email(invoice_id: int) -> Dict[str, Any]:
    """Send invoice to client via email"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if not invoice.billing_email:
            return {'success': False, 'error': 'Client has no email address'}

        # Generate PDF if not already generated
        if not invoice.pdf_filename:
            pdf_result = generate_invoice_pdf(invoice_id)
            if not pdf_result.get('success'):
                return pdf_result

        # Import email service
        try:
            from services.email_service import send_email_with_attachment
        except ImportError:
            return {'success': False, 'error': 'Email service not available'}

        # Build email
        subject = f"Invoice {invoice.invoice_number} from {invoice.company_name or DEFAULT_COMPANY_NAME}"

        def fmt_currency(cents: int) -> str:
            return f"${cents / 100:,.2f}"

        body = f"""
Dear {invoice.billing_name},

Please find attached invoice {invoice.invoice_number}.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Invoice Date: {invoice.invoice_date.strftime('%B %d, %Y') if invoice.invoice_date else 'N/A'}
- Due Date: {invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'N/A'}
- Amount Due: {fmt_currency(invoice.amount_due)}

{f"Notes: {invoice.notes}" if invoice.notes else ""}

Thank you for your business!

{invoice.company_name or DEFAULT_COMPANY_NAME}
{invoice.company_email or ''}
"""

        # Send email
        pdf_path = os.path.join(INVOICE_PDF_DIR, invoice.pdf_filename)
        result = send_email_with_attachment(
            to_email=invoice.billing_email,
            subject=subject,
            body=body,
            attachment_path=pdf_path,
            attachment_name=invoice.pdf_filename,
        )

        if result.get('success'):
            # Mark as sent
            mark_sent(invoice_id)

        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def get_invoice_stats(
    client_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get invoice statistics"""
    db = SessionLocal()
    try:
        query = db.query(Invoice)

        if client_id:
            query = query.filter(Invoice.client_id == client_id)
        if tenant_id:
            query = query.filter(Invoice.tenant_id == tenant_id)

        invoices = query.all()

        stats = {
            'total_invoices': len(invoices),
            'total_invoiced': 0,
            'total_paid': 0,
            'total_outstanding': 0,
            'by_status': {},
        }

        for inv in invoices:
            stats['total_invoiced'] += inv.total
            stats['total_paid'] += inv.amount_paid
            stats['total_outstanding'] += inv.amount_due

            status = inv.status
            if status not in stats['by_status']:
                stats['by_status'][status] = {'count': 0, 'total': 0}
            stats['by_status'][status]['count'] += 1
            stats['by_status'][status]['total'] += inv.total

        return {
            'success': True,
            'stats': stats,
        }
    finally:
        db.close()


def get_client_invoices(client_id: int) -> Dict[str, Any]:
    """Get all invoices for a client (for portal)"""
    return list_invoices(client_id=client_id)


def delete_invoice(invoice_id: int) -> Dict[str, Any]:
    """Delete a draft invoice"""
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {'success': False, 'error': 'Invoice not found'}

        if invoice.status != 'draft':
            return {'success': False, 'error': 'Only draft invoices can be deleted'}

        # Delete PDF if exists
        if invoice.pdf_filename:
            pdf_path = os.path.join(INVOICE_PDF_DIR, invoice.pdf_filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        db.delete(invoice)
        db.commit()

        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def create_invoice_for_round(
    client_id: int,
    round_number: int,
    amount: int,
    created_by_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an invoice for a dispute round"""
    return create_invoice(
        client_id=client_id,
        items=[{
            'description': f'Dispute Round {round_number} Services',
            'item_type': 'round',
            'unit_price': amount,
            'quantity': 1,
            'reference_type': 'dispute_round',
            'reference_id': round_number,
        }],
        title=f'Dispute Round {round_number}',
        created_by_id=created_by_id,
    )


def create_invoice_for_analysis(
    client_id: int,
    analysis_id: int,
    amount: int = 19900,  # $199 default
    created_by_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an invoice for credit analysis"""
    return create_invoice(
        client_id=client_id,
        items=[{
            'description': 'Full Credit Analysis',
            'item_type': 'analysis',
            'unit_price': amount,
            'quantity': 1,
            'reference_type': 'analysis',
            'reference_id': analysis_id,
        }],
        title='Credit Analysis',
        created_by_id=created_by_id,
    )


def create_invoice_for_settlement(
    client_id: int,
    settlement_id: int,
    settlement_amount: int,
    fee_rate: float = 0.30,  # 30% default
    created_by_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create an invoice for settlement fee"""
    fee_amount = int(settlement_amount * fee_rate)

    return create_invoice(
        client_id=client_id,
        items=[{
            'description': f'Settlement Fee (30% of ${settlement_amount / 100:,.2f})',
            'item_type': 'settlement',
            'unit_price': fee_amount,
            'quantity': 1,
            'reference_type': 'settlement',
            'reference_id': settlement_id,
        }],
        title='Settlement Fee',
        created_by_id=created_by_id,
    )
