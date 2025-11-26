"""
SendCertifiedMail.com Integration Service
Provides certified mail with return receipt for legal proof of delivery
"""
import os
import logging
import requests
import uuid
from datetime import datetime
from database import SessionLocal, CertifiedMailOrder

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.sendcertifiedmail.com/v1"
PROVIDER_NAME = "sendcertifiedmail.com"

VALID_LETTER_TYPES = [
    'dispute_round_1',
    'dispute_round_2',
    'dispute_round_3',
    'dispute_round_4',
    'freeze_request',
    'intent_to_sue',
    'validation_request'
]

COST_BASE = 8.50
COST_PER_PAGE = 0.50
COST_RETURN_RECEIPT = 3.50


def is_certified_mail_configured():
    """
    Check if SendCertifiedMail.com API key is configured.
    Returns True if API key exists, False otherwise.
    """
    api_key = os.environ.get('SENDCERTIFIEDMAIL_API_KEY')
    return bool(api_key)


def _get_api_key():
    """
    Get SendCertifiedMail.com API key from environment variable.
    Returns None if not configured (mock mode).
    """
    return os.environ.get('SENDCERTIFIEDMAIL_API_KEY')


def _get_headers():
    """Get headers for API requests."""
    api_key = _get_api_key()
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }


def _get_multipart_headers():
    """Get headers for multipart file uploads."""
    api_key = _get_api_key()
    return {
        'Authorization': f'Bearer {api_key}'
    }


def _get_client_delivery_folder(client_id):
    """Get or create client's delivery proof folder."""
    folder_path = f"static/client_uploads/{client_id}/certified_mail"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def _generate_mock_tracking():
    """Generate a mock USPS tracking number for testing."""
    return f"MOCK{uuid.uuid4().hex[:16].upper()}"


def _generate_mock_order_id():
    """Generate a mock order ID for testing."""
    return f"mock_{uuid.uuid4().hex[:12]}"


def get_mailing_cost(pages, mail_class='certified'):
    """
    Calculate estimated cost for certified mail.
    
    Args:
        pages: Number of pages in the document
        mail_class: Type of mail ('certified' or 'certified_return_receipt')
        
    Returns:
        dict with:
            - base_cost: Base mailing cost
            - page_cost: Cost for additional pages
            - return_receipt_cost: Cost for return receipt (if applicable)
            - total_cost: Total estimated cost
    """
    if pages < 1:
        pages = 1
    
    base_cost = COST_BASE
    page_cost = max(0, (pages - 1)) * COST_PER_PAGE
    
    return_receipt_cost = COST_RETURN_RECEIPT if 'return' in mail_class.lower() else 0
    
    total_cost = base_cost + page_cost + return_receipt_cost
    
    return {
        'base_cost': round(base_cost, 2),
        'page_cost': round(page_cost, 2),
        'return_receipt_cost': round(return_receipt_cost, 2),
        'total_cost': round(total_cost, 2),
        'pages': pages,
        'mail_class': mail_class
    }


def send_certified_letter(client_id, recipient_name, recipient_address, document_path, 
                          letter_type, bureau=None, dispute_round=None):
    """
    Send a document via certified mail with return receipt.
    
    Args:
        client_id: ID of the client in our database
        recipient_name: Name of the recipient
        recipient_address: Full mailing address of recipient
        document_path: Path to the document to mail (PDF)
        letter_type: Type of letter (dispute_round_1-4, freeze_request, intent_to_sue, validation_request)
        bureau: Credit bureau name (optional, for dispute letters)
        dispute_round: Dispute round number (optional)
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID
            - external_order_id: SendCertifiedMail.com order ID
            - tracking_number: USPS tracking number
            - estimated_cost: Estimated mailing cost
            - mock_mode: True if using mock mode
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        if letter_type not in VALID_LETTER_TYPES:
            return {
                'success': False,
                'order_id': None,
                'external_order_id': None,
                'tracking_number': None,
                'estimated_cost': None,
                'mock_mode': False,
                'error': f'Invalid letter_type. Must be one of: {", ".join(VALID_LETTER_TYPES)}'
            }
        
        if not os.path.exists(document_path):
            return {
                'success': False,
                'order_id': None,
                'external_order_id': None,
                'tracking_number': None,
                'estimated_cost': None,
                'mock_mode': False,
                'error': f'Document not found: {document_path}'
            }
        
        file_size = os.path.getsize(document_path)
        estimated_pages = max(1, file_size // 50000)
        cost_info = get_mailing_cost(estimated_pages, 'certified_return_receipt')
        
        if not is_certified_mail_configured():
            logger.warning("SENDCERTIFIEDMAIL_API_KEY not configured - using mock mode")
            
            mock_order_id = _generate_mock_order_id()
            mock_tracking = _generate_mock_tracking()
            
            order = CertifiedMailOrder(
                client_id=client_id,
                external_order_id=mock_order_id,
                tracking_number=mock_tracking,
                recipient_name=recipient_name,
                recipient_address=recipient_address,
                recipient_type='credit_bureau' if bureau else 'other',
                document_type=letter_type,
                document_path=document_path,
                letter_type=letter_type,
                dispute_round=dispute_round,
                bureau=bureau,
                status='mock_pending',
                cost=cost_info['total_cost'],
                submitted_at=datetime.utcnow(),
                webhook_data={'mock_mode': True, 'note': 'API key not configured'}
            )
            
            session.add(order)
            session.commit()
            session.refresh(order)
            
            logger.info(f"Created mock certified mail order {order.id} for client {client_id}")
            
            return {
                'success': True,
                'order_id': order.id,
                'external_order_id': mock_order_id,
                'tracking_number': mock_tracking,
                'estimated_cost': cost_info['total_cost'],
                'mock_mode': True,
                'error': None
            }
        
        logger.info(f"Uploading document for certified mail: {document_path}")
        
        with open(document_path, 'rb') as f:
            files = {'document': (os.path.basename(document_path), f, 'application/pdf')}
            upload_response = requests.post(
                f"{API_BASE_URL}/documents/upload",
                headers=_get_multipart_headers(),
                files=files,
                timeout=60
            )
        
        if upload_response.status_code not in [200, 201]:
            error_msg = f"Document upload failed: {upload_response.status_code} - {upload_response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': None,
                'external_order_id': None,
                'tracking_number': None,
                'estimated_cost': None,
                'mock_mode': False,
                'error': error_msg
            }
        
        upload_data = upload_response.json()
        document_id = upload_data.get('document_id') or upload_data.get('id')
        
        order_payload = {
            'document_id': document_id,
            'recipient': {
                'name': recipient_name,
                'address': recipient_address
            },
            'mail_class': 'certified',
            'return_receipt': True,
            'metadata': {
                'client_id': client_id,
                'letter_type': letter_type,
                'bureau': bureau,
                'dispute_round': dispute_round
            }
        }
        
        logger.info(f"Creating certified mail order for client {client_id}")
        
        order_response = requests.post(
            f"{API_BASE_URL}/orders",
            headers=_get_headers(),
            json=order_payload,
            timeout=30
        )
        
        if order_response.status_code not in [200, 201]:
            error_msg = f"Order creation failed: {order_response.status_code} - {order_response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': None,
                'external_order_id': None,
                'tracking_number': None,
                'estimated_cost': None,
                'mock_mode': False,
                'error': error_msg
            }
        
        order_data = order_response.json()
        external_order_id = order_data.get('order_id') or order_data.get('id')
        tracking_number = order_data.get('tracking_number')
        api_cost = order_data.get('cost') or cost_info['total_cost']
        
        order = CertifiedMailOrder(
            client_id=client_id,
            external_order_id=external_order_id,
            tracking_number=tracking_number,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            recipient_type='credit_bureau' if bureau else 'other',
            document_type=letter_type,
            document_path=document_path,
            letter_type=letter_type,
            dispute_round=dispute_round,
            bureau=bureau,
            status='submitted',
            cost=api_cost,
            submitted_at=datetime.utcnow(),
            webhook_data=order_data
        )
        
        session.add(order)
        session.commit()
        session.refresh(order)
        
        logger.info(f"Created certified mail order {order.id} with tracking {tracking_number}")
        
        return {
            'success': True,
            'order_id': order.id,
            'external_order_id': external_order_id,
            'tracking_number': tracking_number,
            'estimated_cost': api_cost,
            'mock_mode': False,
            'error': None
        }
        
    except requests.RequestException as e:
        error_msg = f"Network error connecting to SendCertifiedMail.com API: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': None,
            'external_order_id': None,
            'tracking_number': None,
            'estimated_cost': None,
            'mock_mode': False,
            'error': error_msg
        }
    except Exception as e:
        session.rollback()
        error_msg = f"Error creating certified mail order: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': None,
            'external_order_id': None,
            'tracking_number': None,
            'estimated_cost': None,
            'mock_mode': False,
            'error': error_msg
        }
    finally:
        session.close()


def check_delivery_status(order_id):
    """
    Check the delivery status of a certified mail order.
    
    Args:
        order_id: Our internal CertifiedMailOrder ID
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID
            - external_order_id: SendCertifiedMail.com order ID
            - tracking_number: USPS tracking number
            - status: current status
            - delivered_at: delivery timestamp (if delivered)
            - api_response: full API response data
            - mock_mode: True if using mock mode
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        order = session.query(CertifiedMailOrder).filter(
            CertifiedMailOrder.id == order_id
        ).first()
        
        if not order:
            return {
                'success': False,
                'order_id': order_id,
                'external_order_id': None,
                'tracking_number': None,
                'status': None,
                'delivered_at': None,
                'api_response': None,
                'mock_mode': False,
                'error': f'Certified mail order {order_id} not found'
            }
        
        if order.status and order.status.startswith('mock_'):
            logger.info(f"Returning mock status for order {order_id}")
            return {
                'success': True,
                'order_id': order_id,
                'external_order_id': order.external_order_id,
                'tracking_number': order.tracking_number,
                'status': order.status,
                'delivered_at': order.delivered_at,
                'api_response': order.webhook_data,
                'mock_mode': True,
                'error': None
            }
        
        if not is_certified_mail_configured():
            logger.warning("SENDCERTIFIEDMAIL_API_KEY not configured - cannot check live status")
            return {
                'success': True,
                'order_id': order_id,
                'external_order_id': order.external_order_id,
                'tracking_number': order.tracking_number,
                'status': order.status,
                'delivered_at': order.delivered_at,
                'api_response': order.webhook_data,
                'mock_mode': True,
                'error': None
            }
        
        if not order.external_order_id:
            return {
                'success': False,
                'order_id': order_id,
                'external_order_id': None,
                'tracking_number': order.tracking_number,
                'status': order.status,
                'delivered_at': None,
                'api_response': None,
                'mock_mode': False,
                'error': 'No external order ID found for this order'
            }
        
        logger.info(f"Checking status for order {order_id}, external ID: {order.external_order_id}")
        
        response = requests.get(
            f"{API_BASE_URL}/orders/{order.external_order_id}",
            headers=_get_headers(),
            timeout=30
        )
        
        if response.status_code == 404:
            return {
                'success': False,
                'order_id': order_id,
                'external_order_id': order.external_order_id,
                'tracking_number': order.tracking_number,
                'status': 'not_found',
                'delivered_at': None,
                'api_response': None,
                'mock_mode': False,
                'error': 'Order not found in SendCertifiedMail.com'
            }
        
        if response.status_code != 200:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': order_id,
                'external_order_id': order.external_order_id,
                'tracking_number': order.tracking_number,
                'status': None,
                'delivered_at': None,
                'api_response': None,
                'mock_mode': False,
                'error': error_msg
            }
        
        response_data = response.json()
        api_status = response_data.get('status', '').lower()
        
        status_mapping = {
            'pending': 'pending',
            'processing': 'processing',
            'printed': 'printed',
            'mailed': 'mailed',
            'in_transit': 'in_transit',
            'in transit': 'in_transit',
            'out_for_delivery': 'out_for_delivery',
            'delivered': 'delivered',
            'returned': 'returned',
            'failed': 'failed',
            'cancelled': 'cancelled',
            'canceled': 'cancelled'
        }
        normalized_status = status_mapping.get(api_status, api_status)
        
        order.status = normalized_status
        order.webhook_data = response_data
        
        if response_data.get('tracking_number'):
            order.tracking_number = response_data['tracking_number']
        
        if normalized_status == 'mailed' and not order.mailed_at:
            mailed_str = response_data.get('mailed_at') or response_data.get('mail_date')
            if mailed_str:
                try:
                    order.mailed_at = datetime.fromisoformat(mailed_str.replace('Z', '+00:00'))
                except:
                    order.mailed_at = datetime.utcnow()
            else:
                order.mailed_at = datetime.utcnow()
        
        if normalized_status == 'delivered' and not order.delivered_at:
            delivered_str = response_data.get('delivered_at') or response_data.get('delivery_date')
            if delivered_str:
                try:
                    order.delivered_at = datetime.fromisoformat(delivered_str.replace('Z', '+00:00'))
                except:
                    order.delivered_at = datetime.utcnow()
            else:
                order.delivered_at = datetime.utcnow()
        
        session.commit()
        
        logger.info(f"Updated order {order_id} status to: {normalized_status}")
        
        return {
            'success': True,
            'order_id': order_id,
            'external_order_id': order.external_order_id,
            'tracking_number': order.tracking_number,
            'status': normalized_status,
            'delivered_at': order.delivered_at,
            'api_response': response_data,
            'mock_mode': False,
            'error': None
        }
        
    except requests.RequestException as e:
        error_msg = f"Network error connecting to SendCertifiedMail.com API: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': order_id,
            'external_order_id': None,
            'tracking_number': None,
            'status': None,
            'delivered_at': None,
            'api_response': None,
            'mock_mode': False,
            'error': error_msg
        }
    except Exception as e:
        session.rollback()
        error_msg = f"Error checking delivery status: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': order_id,
            'external_order_id': None,
            'tracking_number': None,
            'status': None,
            'delivered_at': None,
            'api_response': None,
            'mock_mode': False,
            'error': error_msg
        }
    finally:
        session.close()


def _download_delivery_proof(order, proof_url):
    """
    Download and save delivery proof document.
    
    Args:
        order: CertifiedMailOrder object
        proof_url: URL to download proof document from
        
    Returns:
        str: Path to saved proof document, or None if failed
    """
    try:
        response = requests.get(proof_url, timeout=60)
        if response.status_code != 200:
            logger.error(f"Failed to download delivery proof: {response.status_code}")
            return None
        
        client_folder = _get_client_delivery_folder(order.client_id)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"delivery_proof_{order.id}_{timestamp}.pdf"
        file_path = os.path.join(client_folder, filename)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded delivery proof to {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error downloading delivery proof: {str(e)}")
        return None


def handle_webhook(webhook_data):
    """
    Handle incoming webhook notifications from SendCertifiedMail.com.
    Updates CertifiedMailOrder status and downloads proof documents when delivered.
    
    Args:
        webhook_data: dict containing webhook payload
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID (if found)
            - action_taken: description of what was done
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        external_order_id = (
            webhook_data.get('order_id') or 
            webhook_data.get('id') or 
            webhook_data.get('external_order_id')
        )
        event_type = (
            webhook_data.get('event') or 
            webhook_data.get('type') or 
            webhook_data.get('status')
        )
        
        logger.info(f"Received webhook for order {external_order_id}, event: {event_type}")
        
        if not external_order_id:
            return {
                'success': False,
                'order_id': None,
                'action_taken': None,
                'error': 'No order_id in webhook data'
            }
        
        order = session.query(CertifiedMailOrder).filter(
            CertifiedMailOrder.external_order_id == external_order_id
        ).first()
        
        if not order:
            logger.warning(f"No order found for external ID {external_order_id}")
            return {
                'success': False,
                'order_id': None,
                'action_taken': None,
                'error': f'No order found for external ID {external_order_id}'
            }
        
        event_type_lower = str(event_type).lower() if event_type else ''
        
        status_mapping = {
            'order.created': 'pending',
            'order.processing': 'processing',
            'order.printed': 'printed',
            'order.mailed': 'mailed',
            'order.in_transit': 'in_transit',
            'order.out_for_delivery': 'out_for_delivery',
            'order.delivered': 'delivered',
            'order.returned': 'returned',
            'order.failed': 'failed',
            'order.cancelled': 'cancelled',
            'pending': 'pending',
            'processing': 'processing',
            'printed': 'printed',
            'mailed': 'mailed',
            'in_transit': 'in_transit',
            'delivered': 'delivered',
            'returned': 'returned',
            'failed': 'failed',
            'cancelled': 'cancelled'
        }
        
        new_status = status_mapping.get(event_type_lower, event_type_lower)
        old_status = order.status
        order.status = new_status
        order.webhook_data = webhook_data
        
        action_taken = f"Updated status from '{old_status}' to '{new_status}'"
        
        if new_status == 'mailed' and not order.mailed_at:
            mailed_str = webhook_data.get('mailed_at') or webhook_data.get('mail_date')
            if mailed_str:
                try:
                    order.mailed_at = datetime.fromisoformat(mailed_str.replace('Z', '+00:00'))
                except:
                    order.mailed_at = datetime.utcnow()
            else:
                order.mailed_at = datetime.utcnow()
            action_taken += ", set mailed_at timestamp"
        
        if webhook_data.get('tracking_number') and not order.tracking_number:
            order.tracking_number = webhook_data['tracking_number']
            action_taken += f", updated tracking number to {order.tracking_number}"
        
        if new_status == 'delivered':
            if not order.delivered_at:
                delivered_str = webhook_data.get('delivered_at') or webhook_data.get('delivery_date')
                if delivered_str:
                    try:
                        order.delivered_at = datetime.fromisoformat(delivered_str.replace('Z', '+00:00'))
                    except:
                        order.delivered_at = datetime.utcnow()
                else:
                    order.delivered_at = datetime.utcnow()
                action_taken += ", set delivered_at timestamp"
            
            proof_url = (
                webhook_data.get('delivery_proof_url') or 
                webhook_data.get('return_receipt_url') or
                webhook_data.get('proof_url')
            )
            if proof_url:
                proof_path = _download_delivery_proof(order, proof_url)
                if proof_path:
                    order.delivery_proof_path = proof_path
                    action_taken += f", downloaded delivery proof to {proof_path}"
        
        session.commit()
        
        logger.info(f"Processed webhook for order {order.id}: {action_taken}")
        
        return {
            'success': True,
            'order_id': order.id,
            'action_taken': action_taken,
            'error': None
        }
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': None,
            'action_taken': None,
            'error': error_msg
        }
    finally:
        session.close()


def get_order_by_id(order_id):
    """
    Get a certified mail order by its internal ID.
    
    Args:
        order_id: Our internal CertifiedMailOrder ID
        
    Returns:
        dict with order details or None if not found
    """
    session = SessionLocal()
    try:
        order = session.query(CertifiedMailOrder).filter(
            CertifiedMailOrder.id == order_id
        ).first()
        
        if not order:
            return None
        
        return {
            'id': order.id,
            'client_id': order.client_id,
            'external_order_id': order.external_order_id,
            'tracking_number': order.tracking_number,
            'recipient_name': order.recipient_name,
            'recipient_address': order.recipient_address,
            'letter_type': order.letter_type,
            'bureau': order.bureau,
            'dispute_round': order.dispute_round,
            'status': order.status,
            'cost': order.cost,
            'submitted_at': order.submitted_at,
            'mailed_at': order.mailed_at,
            'delivered_at': order.delivered_at,
            'delivery_proof_path': order.delivery_proof_path,
            'created_at': order.created_at
        }
        
    finally:
        session.close()


def get_orders_by_client(client_id):
    """
    Get all certified mail orders for a client.
    
    Args:
        client_id: Client ID
        
    Returns:
        list of order dicts
    """
    session = SessionLocal()
    try:
        orders = session.query(CertifiedMailOrder).filter(
            CertifiedMailOrder.client_id == client_id
        ).order_by(CertifiedMailOrder.created_at.desc()).all()
        
        return [{
            'id': order.id,
            'external_order_id': order.external_order_id,
            'tracking_number': order.tracking_number,
            'recipient_name': order.recipient_name,
            'letter_type': order.letter_type,
            'bureau': order.bureau,
            'dispute_round': order.dispute_round,
            'status': order.status,
            'cost': order.cost,
            'submitted_at': order.submitted_at,
            'mailed_at': order.mailed_at,
            'delivered_at': order.delivered_at,
            'created_at': order.created_at
        } for order in orders]
        
    finally:
        session.close()


def get_pending_orders():
    """
    Get all orders that are not yet delivered.
    Useful for batch status checking.
    
    Returns:
        list of order dicts
    """
    session = SessionLocal()
    try:
        pending_statuses = ['pending', 'submitted', 'processing', 'printed', 'mailed', 'in_transit', 'out_for_delivery']
        
        orders = session.query(CertifiedMailOrder).filter(
            CertifiedMailOrder.status.in_(pending_statuses)
        ).order_by(CertifiedMailOrder.created_at.asc()).all()
        
        return [{
            'id': order.id,
            'client_id': order.client_id,
            'external_order_id': order.external_order_id,
            'tracking_number': order.tracking_number,
            'recipient_name': order.recipient_name,
            'letter_type': order.letter_type,
            'status': order.status,
            'submitted_at': order.submitted_at,
            'created_at': order.created_at
        } for order in orders]
        
    finally:
        session.close()
