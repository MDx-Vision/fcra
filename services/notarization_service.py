"""
Proof.com (Notarize) Remote Online Notarization Service
Integrates with Proof.com API for remote online notarization of documents
"""
import os
import logging
import requests
from datetime import datetime
from database import SessionLocal, NotarizationOrder

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.notarize.com/v1"
PROVIDER_NAME = "proof.com"


def is_proof_configured():
    """
    Check if Proof.com API key is configured.
    Returns True if API key exists, False otherwise.
    """
    api_key = os.environ.get('PROOF_API_KEY')
    return bool(api_key)


def get_api_key():
    """
    Get Proof.com API key from environment variable.
    Raises ValueError if not configured.
    """
    api_key = os.environ.get('PROOF_API_KEY')
    if not api_key:
        raise ValueError('PROOF_API_KEY environment variable is not set')
    return api_key


def _get_headers():
    """Get headers for API requests."""
    api_key = get_api_key()
    return {
        'ApiKey': api_key,
        'Content-Type': 'application/json'
    }


def _get_client_upload_folder(client_id):
    """Get or create client's upload folder."""
    folder_path = f"static/client_uploads/{client_id}/notarized"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def create_notarization_order(client_id, document_path, document_name, signer_email, signer_name):
    """
    Create a new notarization transaction via Proof.com API.
    
    Args:
        client_id: ID of the client in our database
        document_path: Path to the document to be notarized (relative or absolute)
        document_name: Display name for the document
        signer_email: Email address of the signer
        signer_name: Full name of the signer
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID
            - transaction_id: Proof.com transaction ID
            - session_link: URL for signer to access notarization session
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        if not os.path.exists(document_path):
            return {
                'success': False,
                'order_id': None,
                'transaction_id': None,
                'session_link': None,
                'error': f'Document not found: {document_path}'
            }
        
        domain = os.environ.get('REPL_SLUG_URL') or os.environ.get('REPLIT_DEV_DOMAIN', '')
        if domain:
            document_url = f"https://{domain}/{document_path}"
        else:
            document_url = f"file://{os.path.abspath(document_path)}"
        
        payload = {
            'signers': [
                {
                    'email': signer_email,
                    'name': signer_name
                }
            ],
            'documents': [
                {
                    'resource': document_url,
                    'requirement': 'notarization',
                    'name': document_name
                }
            ]
        }
        
        logger.info(f"Creating notarization order for client {client_id}, document: {document_name}")
        
        response = requests.post(
            f"{API_BASE_URL}/transactions",
            headers=_get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            error_msg = f"API request failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': None,
                'transaction_id': None,
                'session_link': None,
                'error': error_msg
            }
        
        response_data = response.json()
        
        transaction_id = response_data.get('id') or response_data.get('transaction_id')
        session_link = response_data.get('session_link') or response_data.get('signerUrl') or response_data.get('url')
        
        order = NotarizationOrder(
            client_id=client_id,
            provider=PROVIDER_NAME,
            external_transaction_id=transaction_id,
            document_name=document_name,
            document_path=document_path,
            signer_email=signer_email,
            signer_name=signer_name,
            session_link=session_link,
            status='pending',
            webhook_data=response_data
        )
        
        session.add(order)
        session.commit()
        session.refresh(order)
        
        logger.info(f"Created notarization order {order.id} with transaction ID {transaction_id}")
        
        return {
            'success': True,
            'order_id': order.id,
            'transaction_id': transaction_id,
            'session_link': session_link,
            'error': None
        }
        
    except requests.RequestException as e:
        error_msg = f"Network error connecting to Proof.com API: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': None,
            'transaction_id': None,
            'session_link': None,
            'error': error_msg
        }
    except Exception as e:
        session.rollback()
        error_msg = f"Error creating notarization order: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': None,
            'transaction_id': None,
            'session_link': None,
            'error': error_msg
        }
    finally:
        session.close()


def get_notarization_status(order_id):
    """
    Get the current status of a notarization transaction.
    
    Args:
        order_id: Our internal NotarizationOrder ID
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID
            - transaction_id: Proof.com transaction ID
            - status: current status from API
            - api_response: full API response data
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        order = session.query(NotarizationOrder).filter(
            NotarizationOrder.id == order_id
        ).first()
        
        if not order:
            return {
                'success': False,
                'order_id': order_id,
                'transaction_id': None,
                'status': None,
                'api_response': None,
                'error': f'Notarization order {order_id} not found'
            }
        
        if not order.external_transaction_id:
            return {
                'success': False,
                'order_id': order_id,
                'transaction_id': None,
                'status': order.status,
                'api_response': None,
                'error': 'No external transaction ID found for this order'
            }
        
        logger.info(f"Getting status for notarization order {order_id}, transaction: {order.external_transaction_id}")
        
        response = requests.get(
            f"{API_BASE_URL}/transactions/{order.external_transaction_id}",
            headers=_get_headers(),
            timeout=30
        )
        
        if response.status_code == 404:
            return {
                'success': False,
                'order_id': order_id,
                'transaction_id': order.external_transaction_id,
                'status': 'not_found',
                'api_response': None,
                'error': 'Transaction not found in Proof.com'
            }
        
        if response.status_code != 200:
            error_msg = f"API request failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': order_id,
                'transaction_id': order.external_transaction_id,
                'status': None,
                'api_response': None,
                'error': error_msg
            }
        
        response_data = response.json()
        api_status = response_data.get('status', '').lower()
        
        status_mapping = {
            'created': 'pending',
            'pending': 'pending',
            'in_progress': 'in_progress',
            'in progress': 'in_progress',
            'scheduled': 'scheduled',
            'completed': 'completed',
            'complete': 'completed',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
            'expired': 'expired',
            'failed': 'failed'
        }
        normalized_status = status_mapping.get(api_status, api_status)
        
        order.status = normalized_status
        order.webhook_data = response_data
        
        if normalized_status == 'completed':
            order.notarized_at = datetime.utcnow()
        
        session.commit()
        
        logger.info(f"Updated notarization order {order_id} status to: {normalized_status}")
        
        return {
            'success': True,
            'order_id': order_id,
            'transaction_id': order.external_transaction_id,
            'status': normalized_status,
            'api_response': response_data,
            'error': None
        }
        
    except requests.RequestException as e:
        error_msg = f"Network error connecting to Proof.com API: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': order_id,
            'transaction_id': None,
            'status': None,
            'api_response': None,
            'error': error_msg
        }
    except Exception as e:
        session.rollback()
        error_msg = f"Error getting notarization status: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': order_id,
            'transaction_id': None,
            'status': None,
            'api_response': None,
            'error': error_msg
        }
    finally:
        session.close()


def download_notarized_document(order_id):
    """
    Download the completed notarized document and save to client's folder.
    
    Args:
        order_id: Our internal NotarizationOrder ID
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID
            - file_path: path to downloaded notarized document
            - audit_trail_path: path to audit trail document (if available)
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        order = session.query(NotarizationOrder).filter(
            NotarizationOrder.id == order_id
        ).first()
        
        if not order:
            return {
                'success': False,
                'order_id': order_id,
                'file_path': None,
                'audit_trail_path': None,
                'error': f'Notarization order {order_id} not found'
            }
        
        if not order.external_transaction_id:
            return {
                'success': False,
                'order_id': order_id,
                'file_path': None,
                'audit_trail_path': None,
                'error': 'No external transaction ID found for this order'
            }
        
        status_result = get_notarization_status(order_id)
        if status_result.get('status') != 'completed':
            return {
                'success': False,
                'order_id': order_id,
                'file_path': None,
                'audit_trail_path': None,
                'error': f"Notarization not completed. Current status: {status_result.get('status')}"
            }
        
        logger.info(f"Downloading notarized document for order {order_id}")
        
        response = requests.get(
            f"{API_BASE_URL}/transactions/{order.external_transaction_id}/documents",
            headers=_get_headers(),
            timeout=60
        )
        
        if response.status_code != 200:
            error_msg = f"Failed to get documents: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': order_id,
                'file_path': None,
                'audit_trail_path': None,
                'error': error_msg
            }
        
        documents = response.json()
        if isinstance(documents, dict):
            documents = documents.get('documents', [])
        
        client_folder = _get_client_upload_folder(order.client_id)
        notarized_path = None
        audit_trail_path = None
        
        for doc in documents:
            doc_url = doc.get('url') or doc.get('download_url') or doc.get('resource')
            doc_type = doc.get('type', '').lower()
            doc_name = doc.get('name', 'document')
            
            if not doc_url:
                continue
            
            try:
                doc_response = requests.get(doc_url, timeout=120)
                if doc_response.status_code != 200:
                    logger.warning(f"Failed to download document from {doc_url}")
                    continue
                
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                
                if 'audit' in doc_type or 'audit' in doc_name.lower():
                    filename = f"audit_trail_{order_id}_{timestamp}.pdf"
                    file_path = os.path.join(client_folder, filename)
                    with open(file_path, 'wb') as f:
                        f.write(doc_response.content)
                    audit_trail_path = file_path
                    logger.info(f"Downloaded audit trail to {file_path}")
                else:
                    safe_name = "".join(c for c in order.document_name if c.isalnum() or c in (' ', '_', '-')).strip()
                    safe_name = safe_name.replace(' ', '_')[:50]
                    filename = f"{safe_name}_notarized_{order_id}_{timestamp}.pdf"
                    file_path = os.path.join(client_folder, filename)
                    with open(file_path, 'wb') as f:
                        f.write(doc_response.content)
                    notarized_path = file_path
                    logger.info(f"Downloaded notarized document to {file_path}")
                    
            except Exception as e:
                logger.error(f"Error downloading document: {str(e)}")
                continue
        
        if notarized_path:
            order.notarized_document_path = notarized_path
        if audit_trail_path:
            order.audit_trail_path = audit_trail_path
        
        session.commit()
        
        if not notarized_path:
            return {
                'success': False,
                'order_id': order_id,
                'file_path': None,
                'audit_trail_path': audit_trail_path,
                'error': 'Could not download notarized document'
            }
        
        logger.info(f"Successfully downloaded documents for order {order_id}")
        
        return {
            'success': True,
            'order_id': order_id,
            'file_path': notarized_path,
            'audit_trail_path': audit_trail_path,
            'error': None
        }
        
    except requests.RequestException as e:
        error_msg = f"Network error downloading documents: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': order_id,
            'file_path': None,
            'audit_trail_path': None,
            'error': error_msg
        }
    except Exception as e:
        session.rollback()
        error_msg = f"Error downloading notarized document: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'order_id': order_id,
            'file_path': None,
            'audit_trail_path': None,
            'error': error_msg
        }
    finally:
        session.close()


def handle_webhook(webhook_data):
    """
    Handle incoming webhook notifications from Proof.com.
    Updates NotarizationOrder status and downloads completed documents.
    
    Args:
        webhook_data: dict containing webhook payload from Proof.com
        
    Returns:
        dict with:
            - success: bool
            - order_id: our internal order ID (if found)
            - action_taken: description of what was done
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        transaction_id = webhook_data.get('transaction_id') or webhook_data.get('id')
        event_type = webhook_data.get('event') or webhook_data.get('type') or webhook_data.get('status')
        
        logger.info(f"Received webhook for transaction {transaction_id}, event: {event_type}")
        
        if not transaction_id:
            return {
                'success': False,
                'order_id': None,
                'action_taken': None,
                'error': 'No transaction_id in webhook data'
            }
        
        order = session.query(NotarizationOrder).filter(
            NotarizationOrder.external_transaction_id == transaction_id
        ).first()
        
        if not order:
            logger.warning(f"No order found for transaction {transaction_id}")
            return {
                'success': False,
                'order_id': None,
                'action_taken': None,
                'error': f'No order found for transaction {transaction_id}'
            }
        
        status_mapping = {
            'transaction.created': 'pending',
            'transaction.started': 'in_progress',
            'transaction.scheduled': 'scheduled',
            'transaction.completed': 'completed',
            'transaction.cancelled': 'cancelled',
            'transaction.expired': 'expired',
            'transaction.failed': 'failed',
            'created': 'pending',
            'started': 'in_progress',
            'in_progress': 'in_progress',
            'scheduled': 'scheduled',
            'completed': 'completed',
            'complete': 'completed',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
            'expired': 'expired',
            'failed': 'failed'
        }
        
        event_lower = str(event_type).lower() if event_type else ''
        new_status = status_mapping.get(event_lower, order.status)
        
        order.status = new_status
        order.webhook_data = webhook_data
        order.updated_at = datetime.utcnow()
        
        action_taken = f"Updated status to {new_status}"
        
        if new_status == 'completed':
            order.notarized_at = datetime.utcnow()
            session.commit()
            
            download_result = download_notarized_document(order.id)
            if download_result['success']:
                action_taken = f"Updated status to completed and downloaded documents"
            else:
                action_taken = f"Updated status to completed, but document download failed: {download_result.get('error')}"
        else:
            session.commit()
        
        logger.info(f"Webhook processed for order {order.id}: {action_taken}")
        
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
    Get a NotarizationOrder by its ID.
    
    Args:
        order_id: Our internal NotarizationOrder ID
        
    Returns:
        NotarizationOrder object or None
    """
    session = SessionLocal()
    try:
        order = session.query(NotarizationOrder).filter(
            NotarizationOrder.id == order_id
        ).first()
        return order
    finally:
        session.close()


def get_orders_by_client(client_id, status=None):
    """
    Get all NotarizationOrders for a client.
    
    Args:
        client_id: Client ID
        status: Optional status filter
        
    Returns:
        List of NotarizationOrder objects
    """
    session = SessionLocal()
    try:
        query = session.query(NotarizationOrder).filter(
            NotarizationOrder.client_id == client_id
        )
        if status:
            query = query.filter(NotarizationOrder.status == status)
        return query.order_by(NotarizationOrder.created_at.desc()).all()
    finally:
        session.close()
