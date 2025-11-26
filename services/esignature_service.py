"""
Electronic Signature Service for Brightpath Ascend FCRA Platform
Handles in-app signature capture for client agreements without external API dependency
"""
import os
import base64
import secrets
import logging
from datetime import datetime, timedelta
from database import SessionLocal, ESignatureRequest, Client

logger = logging.getLogger(__name__)

PROVIDER_NAME = "in_app"
TOKEN_EXPIRY_DAYS = 7
SIGNATURE_FOLDER = "static/signatures"

DOCUMENT_TYPES = {
    'client_agreement': 'Main Service Agreement',
    'limited_poa': 'Limited Power of Attorney',
    'dispute_authorization': 'Authorization for Dispute Filing',
    'fee_agreement': 'Fee Agreement'
}


def _ensure_signature_folder():
    """Ensure the signature storage folder exists."""
    os.makedirs(SIGNATURE_FOLDER, exist_ok=True)
    return SIGNATURE_FOLDER


def _get_base_url():
    """Get the base URL for generating signing links."""
    domain = os.environ.get('REPLIT_DEV_DOMAIN') or os.environ.get('REPL_SLUG_URL', '')
    if domain:
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        return domain
    return ""


def _generate_token():
    """Generate a unique, URL-safe token for signing."""
    return secrets.token_urlsafe(32)


def create_signature_request(client_id, document_type, document_name, document_path, signer_email, signer_name):
    """
    Create a new e-signature request for a client document.
    
    Args:
        client_id: ID of the client in our database
        document_type: Type of document (client_agreement, limited_poa, dispute_authorization, fee_agreement)
        document_name: Display name for the document
        document_path: Path to the document to be signed
        signer_email: Email address of the signer
        signer_name: Full name of the signer
        
    Returns:
        dict with:
            - success: bool
            - request_id: our internal request ID
            - signing_link: URL for signer to access signing page
            - expires_at: datetime when the signing link expires
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        if document_type not in DOCUMENT_TYPES:
            return {
                'success': False,
                'request_id': None,
                'signing_link': None,
                'expires_at': None,
                'error': f'Invalid document type: {document_type}. Valid types: {list(DOCUMENT_TYPES.keys())}'
            }
        
        if document_path and not os.path.exists(document_path):
            logger.warning(f"Document not found at path: {document_path}")
        
        token = _generate_token()
        base_url = _get_base_url()
        signing_link = f"{base_url}/sign/{token}" if base_url else f"/sign/{token}"
        expires_at = datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
        
        request = ESignatureRequest(
            client_id=client_id,
            provider=PROVIDER_NAME,
            external_request_id=token,
            document_type=document_type,
            document_name=document_name,
            document_path=document_path,
            signer_email=signer_email,
            signer_name=signer_name,
            signing_link=signing_link,
            status='pending',
            expires_at=expires_at
        )
        
        session.add(request)
        session.commit()
        session.refresh(request)
        
        logger.info(f"Created e-signature request {request.id} for client {client_id}, document: {document_name}")
        
        return {
            'success': True,
            'request_id': request.id,
            'signing_link': signing_link,
            'expires_at': expires_at,
            'error': None
        }
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error creating signature request: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'request_id': None,
            'signing_link': None,
            'expires_at': None,
            'error': error_msg
        }
    finally:
        session.close()


def generate_signing_link(request_id):
    """
    Generate a new unique signing token/link for an existing request.
    Useful for regenerating expired links.
    
    Args:
        request_id: Our internal ESignatureRequest ID
        
    Returns:
        dict with:
            - success: bool
            - request_id: the request ID
            - signing_link: new URL for signer to access signing page
            - token: the raw token
            - expires_at: datetime when the new link expires
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        request = session.query(ESignatureRequest).filter(
            ESignatureRequest.id == request_id
        ).first()
        
        if not request:
            return {
                'success': False,
                'request_id': request_id,
                'signing_link': None,
                'token': None,
                'expires_at': None,
                'error': f'Signature request {request_id} not found'
            }
        
        if request.status == 'signed':
            return {
                'success': False,
                'request_id': request_id,
                'signing_link': request.signing_link,
                'token': request.external_request_id,
                'expires_at': request.expires_at,
                'error': 'Document has already been signed'
            }
        
        token = _generate_token()
        base_url = _get_base_url()
        signing_link = f"{base_url}/sign/{token}" if base_url else f"/sign/{token}"
        expires_at = datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
        
        request.external_request_id = token
        request.signing_link = signing_link
        request.expires_at = expires_at
        request.updated_at = datetime.utcnow()
        
        session.commit()
        
        logger.info(f"Regenerated signing link for request {request_id}")
        
        return {
            'success': True,
            'request_id': request_id,
            'signing_link': signing_link,
            'token': token,
            'expires_at': expires_at,
            'error': None
        }
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error generating signing link: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'request_id': request_id,
            'signing_link': None,
            'token': None,
            'expires_at': None,
            'error': error_msg
        }
    finally:
        session.close()


def verify_signing_token(token):
    """
    Verify if a signing token is valid and not expired.
    
    Args:
        token: The signing token from the URL
        
    Returns:
        dict with:
            - valid: bool indicating if token is valid
            - request_id: the request ID if valid
            - request_details: dict with signature request details if valid
            - error: error message if invalid
    """
    session = SessionLocal()
    try:
        request = session.query(ESignatureRequest).filter(
            ESignatureRequest.external_request_id == token
        ).first()
        
        if not request:
            return {
                'valid': False,
                'request_id': None,
                'request_details': None,
                'error': 'Invalid signing token'
            }
        
        if request.status == 'signed':
            return {
                'valid': False,
                'request_id': request.id,
                'request_details': None,
                'error': 'Document has already been signed'
            }
        
        if request.expires_at and request.expires_at < datetime.utcnow():
            return {
                'valid': False,
                'request_id': request.id,
                'request_details': None,
                'error': 'Signing link has expired'
            }
        
        client = session.query(Client).filter(Client.id == request.client_id).first()
        client_name = client.name if client else 'Unknown'
        
        request_details = {
            'request_id': request.id,
            'client_id': request.client_id,
            'client_name': client_name,
            'document_type': request.document_type,
            'document_type_display': DOCUMENT_TYPES.get(request.document_type, request.document_type),
            'document_name': request.document_name,
            'document_path': request.document_path,
            'signer_email': request.signer_email,
            'signer_name': request.signer_name,
            'status': request.status,
            'expires_at': request.expires_at.isoformat() if request.expires_at else None,
            'created_at': request.created_at.isoformat() if request.created_at else None
        }
        
        logger.info(f"Token verified successfully for request {request.id}")
        
        return {
            'valid': True,
            'request_id': request.id,
            'request_details': request_details,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"Error verifying token: {str(e)}"
        logger.error(error_msg)
        return {
            'valid': False,
            'request_id': None,
            'request_details': None,
            'error': error_msg
        }
    finally:
        session.close()


def capture_signature(request_id, signature_data):
    """
    Capture and save a signature for a document.
    
    Args:
        request_id: Our internal ESignatureRequest ID
        signature_data: Base64 encoded signature image (PNG format expected)
        
    Returns:
        dict with:
            - success: bool
            - request_id: the request ID
            - signature_path: path to saved signature image
            - signed_document_path: path to the signed document (or original + signature reference)
            - signed_at: datetime when signature was captured
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        request = session.query(ESignatureRequest).filter(
            ESignatureRequest.id == request_id
        ).first()
        
        if not request:
            return {
                'success': False,
                'request_id': request_id,
                'signature_path': None,
                'signed_document_path': None,
                'signed_at': None,
                'error': f'Signature request {request_id} not found'
            }
        
        if request.status == 'signed':
            return {
                'success': False,
                'request_id': request_id,
                'signature_path': None,
                'signed_document_path': request.signed_document_path,
                'signed_at': request.signed_at,
                'error': 'Document has already been signed'
            }
        
        _ensure_signature_folder()
        
        if signature_data.startswith('data:image'):
            header, signature_data = signature_data.split(',', 1)
        
        try:
            signature_bytes = base64.b64decode(signature_data)
        except Exception as e:
            return {
                'success': False,
                'request_id': request_id,
                'signature_path': None,
                'signed_document_path': None,
                'signed_at': None,
                'error': f'Invalid base64 signature data: {str(e)}'
            }
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        signature_filename = f"signature_{request.client_id}_{request_id}_{timestamp}.png"
        signature_path = os.path.join(SIGNATURE_FOLDER, signature_filename)
        
        with open(signature_path, 'wb') as f:
            f.write(signature_bytes)
        
        logger.info(f"Saved signature image to {signature_path}")
        
        signed_document_path = request.document_path
        
        signed_at = datetime.utcnow()
        request.status = 'signed'
        request.signed_at = signed_at
        request.signed_document_path = signature_path
        request.updated_at = signed_at
        
        request.webhook_data = {
            'signature_file': signature_path,
            'original_document': request.document_path,
            'signed_at': signed_at.isoformat(),
            'capture_method': 'in_app'
        }
        
        session.commit()
        
        logger.info(f"Signature captured for request {request_id}, saved to {signature_path}")
        
        try:
            _update_client_agreement_status(session, request.client_id, request.document_type)
        except Exception as e:
            logger.warning(f"Could not update client agreement status: {str(e)}")
        
        return {
            'success': True,
            'request_id': request_id,
            'signature_path': signature_path,
            'signed_document_path': signed_document_path,
            'signed_at': signed_at,
            'error': None
        }
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error capturing signature: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'request_id': request_id,
            'signature_path': None,
            'signed_document_path': None,
            'signed_at': None,
            'error': error_msg
        }
    finally:
        session.close()


def _update_client_agreement_status(session, client_id, document_type):
    """Update client record when agreement is signed."""
    if document_type == 'client_agreement':
        client = session.query(Client).filter(Client.id == client_id).first()
        if client:
            client.agreement_signed = True
            client.agreement_signed_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated client {client_id} agreement_signed status")


def get_signature_status(request_id):
    """
    Get the current status and details of a signature request.
    
    Args:
        request_id: Our internal ESignatureRequest ID
        
    Returns:
        dict with:
            - success: bool
            - request_id: the request ID
            - status: current status (pending, signed, expired, cancelled)
            - details: dict with full request details
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        request = session.query(ESignatureRequest).filter(
            ESignatureRequest.id == request_id
        ).first()
        
        if not request:
            return {
                'success': False,
                'request_id': request_id,
                'status': None,
                'details': None,
                'error': f'Signature request {request_id} not found'
            }
        
        status = request.status
        if status == 'pending' and request.expires_at and request.expires_at < datetime.utcnow():
            status = 'expired'
        
        client = session.query(Client).filter(Client.id == request.client_id).first()
        client_name = client.name if client else 'Unknown'
        
        details = {
            'request_id': request.id,
            'client_id': request.client_id,
            'client_name': client_name,
            'provider': request.provider,
            'document_type': request.document_type,
            'document_type_display': DOCUMENT_TYPES.get(request.document_type, request.document_type),
            'document_name': request.document_name,
            'document_path': request.document_path,
            'signer_email': request.signer_email,
            'signer_name': request.signer_name,
            'signing_link': request.signing_link,
            'status': status,
            'signed_at': request.signed_at.isoformat() if request.signed_at else None,
            'signed_document_path': request.signed_document_path,
            'expires_at': request.expires_at.isoformat() if request.expires_at else None,
            'created_at': request.created_at.isoformat() if request.created_at else None,
            'updated_at': request.updated_at.isoformat() if request.updated_at else None
        }
        
        return {
            'success': True,
            'request_id': request_id,
            'status': status,
            'details': details,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"Error getting signature status: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'request_id': request_id,
            'status': None,
            'details': None,
            'error': error_msg
        }
    finally:
        session.close()


def get_pending_signatures(client_id):
    """
    Get all unsigned documents for a client.
    
    Args:
        client_id: ID of the client
        
    Returns:
        dict with:
            - success: bool
            - client_id: the client ID
            - pending_count: number of pending signatures
            - pending_requests: list of pending signature request details
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        requests = session.query(ESignatureRequest).filter(
            ESignatureRequest.client_id == client_id,
            ESignatureRequest.status == 'pending'
        ).order_by(ESignatureRequest.created_at.desc()).all()
        
        pending_requests = []
        now = datetime.utcnow()
        
        for req in requests:
            is_expired = req.expires_at and req.expires_at < now
            status = 'expired' if is_expired else 'pending'
            
            pending_requests.append({
                'request_id': req.id,
                'document_type': req.document_type,
                'document_type_display': DOCUMENT_TYPES.get(req.document_type, req.document_type),
                'document_name': req.document_name,
                'signer_name': req.signer_name,
                'signer_email': req.signer_email,
                'signing_link': req.signing_link,
                'status': status,
                'is_expired': is_expired,
                'expires_at': req.expires_at.isoformat() if req.expires_at else None,
                'created_at': req.created_at.isoformat() if req.created_at else None
            })
        
        return {
            'success': True,
            'client_id': client_id,
            'pending_count': len(pending_requests),
            'pending_requests': pending_requests,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"Error getting pending signatures: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'client_id': client_id,
            'pending_count': 0,
            'pending_requests': [],
            'error': error_msg
        }
    finally:
        session.close()


def send_signature_reminder(request_id):
    """
    Send an email reminder to sign a pending document.
    
    Args:
        request_id: Our internal ESignatureRequest ID
        
    Returns:
        dict with:
            - success: bool
            - request_id: the request ID
            - email_sent: bool indicating if email was sent
            - recipient: email address reminder was sent to
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        request = session.query(ESignatureRequest).filter(
            ESignatureRequest.id == request_id
        ).first()
        
        if not request:
            return {
                'success': False,
                'request_id': request_id,
                'email_sent': False,
                'recipient': None,
                'error': f'Signature request {request_id} not found'
            }
        
        if request.status == 'signed':
            return {
                'success': False,
                'request_id': request_id,
                'email_sent': False,
                'recipient': request.signer_email,
                'error': 'Document has already been signed'
            }
        
        if request.expires_at and request.expires_at < datetime.utcnow():
            result = generate_signing_link(request_id)
            if result['success']:
                session.refresh(request)
        
        try:
            from services.email_service import send_email, is_sendgrid_configured
            from services.email_templates import get_base_template, PRIMARY_COLOR, SECONDARY_COLOR, DARK_COLOR
            
            if not is_sendgrid_configured():
                return {
                    'success': False,
                    'request_id': request_id,
                    'email_sent': False,
                    'recipient': request.signer_email,
                    'error': 'Email service not configured'
                }
            
            first_name = request.signer_name.split()[0] if request.signer_name else "there"
            document_type_display = DOCUMENT_TYPES.get(request.document_type, request.document_type)
            
            content = f'''
                <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Signature Reminder</h2>
                
                <p style="color: #334155; line-height: 1.6; font-size: 16px;">
                    Hi {first_name},
                </p>
                
                <p style="color: #334155; line-height: 1.6; font-size: 16px;">
                    This is a friendly reminder that you have a document waiting for your signature.
                </p>
                
                <div style="background-color: #f8fafc; border-left: 4px solid {PRIMARY_COLOR}; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                    <p style="color: #334155; margin: 0; font-size: 14px;">
                        <strong>Document:</strong> {request.document_name}<br>
                        <strong>Type:</strong> {document_type_display}
                    </p>
                </div>
                
                <p style="margin: 25px 0; text-align: center;">
                    <a href="{request.signing_link}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        Sign Document Now
                    </a>
                </p>
                
                <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
                    This link will expire on {request.expires_at.strftime('%B %d, %Y') if request.expires_at else 'in 7 days'}. If you have any questions, please reply to this email.
                </p>
            '''
            
            html_content = get_base_template(content, "Signature Reminder")
            
            email_result = send_email(
                to_email=request.signer_email,
                subject=f"Signature Required: {request.document_name}",
                html_content=html_content
            )
            
            if email_result['success']:
                logger.info(f"Sent signature reminder for request {request_id} to {request.signer_email}")
                return {
                    'success': True,
                    'request_id': request_id,
                    'email_sent': True,
                    'recipient': request.signer_email,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'request_id': request_id,
                    'email_sent': False,
                    'recipient': request.signer_email,
                    'error': f"Failed to send email: {email_result.get('error')}"
                }
                
        except ImportError as e:
            logger.warning(f"Email service not available: {str(e)}")
            return {
                'success': False,
                'request_id': request_id,
                'email_sent': False,
                'recipient': request.signer_email,
                'error': 'Email service not available'
            }
        
    except Exception as e:
        error_msg = f"Error sending signature reminder: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'request_id': request_id,
            'email_sent': False,
            'recipient': None,
            'error': error_msg
        }
    finally:
        session.close()


def cancel_signature_request(request_id):
    """
    Cancel a pending signature request.
    
    Args:
        request_id: Our internal ESignatureRequest ID
        
    Returns:
        dict with:
            - success: bool
            - request_id: the request ID
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        request = session.query(ESignatureRequest).filter(
            ESignatureRequest.id == request_id
        ).first()
        
        if not request:
            return {
                'success': False,
                'request_id': request_id,
                'error': f'Signature request {request_id} not found'
            }
        
        if request.status == 'signed':
            return {
                'success': False,
                'request_id': request_id,
                'error': 'Cannot cancel a signed document'
            }
        
        request.status = 'cancelled'
        request.updated_at = datetime.utcnow()
        session.commit()
        
        logger.info(f"Cancelled signature request {request_id}")
        
        return {
            'success': True,
            'request_id': request_id,
            'error': None
        }
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error cancelling signature request: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'request_id': request_id,
            'error': error_msg
        }
    finally:
        session.close()


def get_client_signature_history(client_id):
    """
    Get all signature requests (pending and signed) for a client.
    
    Args:
        client_id: ID of the client
        
    Returns:
        dict with:
            - success: bool
            - client_id: the client ID
            - total_count: total number of signature requests
            - signed_count: number of signed documents
            - pending_count: number of pending signatures
            - requests: list of all signature request details
            - error: error message if failed
    """
    session = SessionLocal()
    try:
        requests = session.query(ESignatureRequest).filter(
            ESignatureRequest.client_id == client_id
        ).order_by(ESignatureRequest.created_at.desc()).all()
        
        now = datetime.utcnow()
        request_list = []
        signed_count = 0
        pending_count = 0
        
        for req in requests:
            status = req.status
            if status == 'pending' and req.expires_at and req.expires_at < now:
                status = 'expired'
            
            if status == 'signed':
                signed_count += 1
            elif status == 'pending':
                pending_count += 1
            
            request_list.append({
                'request_id': req.id,
                'document_type': req.document_type,
                'document_type_display': DOCUMENT_TYPES.get(req.document_type, req.document_type),
                'document_name': req.document_name,
                'document_path': req.document_path,
                'signer_name': req.signer_name,
                'signer_email': req.signer_email,
                'signing_link': req.signing_link,
                'status': status,
                'signed_at': req.signed_at.isoformat() if req.signed_at else None,
                'signed_document_path': req.signed_document_path,
                'expires_at': req.expires_at.isoformat() if req.expires_at else None,
                'created_at': req.created_at.isoformat() if req.created_at else None
            })
        
        return {
            'success': True,
            'client_id': client_id,
            'total_count': len(request_list),
            'signed_count': signed_count,
            'pending_count': pending_count,
            'requests': request_list,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"Error getting signature history: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'client_id': client_id,
            'total_count': 0,
            'signed_count': 0,
            'pending_count': 0,
            'requests': [],
            'error': error_msg
        }
    finally:
        session.close()


def list_document_types():
    """
    Get list of supported document types.
    
    Returns:
        dict with document type codes as keys and display names as values
    """
    return DOCUMENT_TYPES.copy()
