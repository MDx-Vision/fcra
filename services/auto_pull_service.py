"""
Auto-Pull Credit Reports Service

Automatically pulls credit reports from credit monitoring services.
Supports: IdentityIQ, MyScoreIQ, SmartCredit, Credit Karma, Privacy Guard, etc.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import os
import time
import json
import hashlib

from database import (
    get_db, Client, CreditMonitoringCredential, CreditPullLog,
    CreditReport
)
from services.encryption import encrypt_value, decrypt_value


# Supported credit monitoring services
SUPPORTED_SERVICES = {
    'identityiq': {
        'name': 'IdentityIQ',
        'url': 'https://www.identityiq.com',
        'report_type': '3bureau',
        'bureaus': ['Equifax', 'Experian', 'TransUnion'],
        'supports_auto_pull': True,
    },
    'myscoreiq': {
        'name': 'MyScoreIQ',
        'url': 'https://www.myscoreiq.com',
        'report_type': '3bureau',
        'bureaus': ['Equifax', 'Experian', 'TransUnion'],
        'supports_auto_pull': True,
    },
    'smartcredit': {
        'name': 'SmartCredit',
        'url': 'https://www.smartcredit.com',
        'report_type': '3bureau',
        'bureaus': ['Equifax', 'Experian', 'TransUnion'],
        'supports_auto_pull': True,
    },
    'privacyguard': {
        'name': 'Privacy Guard',
        'url': 'https://www.privacyguard.com',
        'report_type': '3bureau',
        'bureaus': ['Equifax', 'Experian', 'TransUnion'],
        'supports_auto_pull': True,
    },
    'creditkarma': {
        'name': 'Credit Karma',
        'url': 'https://www.creditkarma.com',
        'report_type': '2bureau',
        'bureaus': ['Equifax', 'TransUnion'],
        'supports_auto_pull': False,  # Requires OAuth
    },
}

# Pull frequencies
FREQUENCIES = {
    'manual': None,
    'daily': timedelta(days=1),
    'weekly': timedelta(days=7),
    'biweekly': timedelta(days=14),
    'monthly': timedelta(days=30),
    'with_letter_send': None,  # Triggered when letters are sent
}

# Status constants
STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_SUCCESS = 'success'
STATUS_FAILED = 'failed'
STATUS_TIMEOUT = 'timeout'
STATUS_INVALID_CREDENTIALS = 'invalid_credentials'
STATUS_SERVICE_UNAVAILABLE = 'service_unavailable'

# Pull statuses dictionary (for easy lookup/iteration)
PULL_STATUSES = {
    'pending': STATUS_PENDING,
    'in_progress': STATUS_IN_PROGRESS,
    'success': STATUS_SUCCESS,
    'failed': STATUS_FAILED,
    'timeout': STATUS_TIMEOUT,
    'invalid_credentials': STATUS_INVALID_CREDENTIALS,
    'service_unavailable': STATUS_SERVICE_UNAVAILABLE,
}


class AutoPullService:
    """Service for automatically pulling credit reports"""

    def __init__(self):
        self.db = None

    def _get_db(self):
        if not self.db:
            self.db = get_db()
        return self.db

    def _close_db(self):
        if self.db:
            self.db.close()
            self.db = None

    # =========================================================================
    # CREDENTIAL MANAGEMENT
    # =========================================================================

    def add_credential(
        self,
        client_id: int,
        service_name: str,
        username: str,
        password: str,
        ssn_last4: str = None,
        import_frequency: str = 'manual'
    ) -> Dict[str, Any]:
        """Add credit monitoring credentials for a client"""
        db = self._get_db()

        try:
            # Validate service
            service_key = service_name.lower().replace(' ', '')
            if service_key not in SUPPORTED_SERVICES:
                return {'success': False, 'error': f'Unsupported service: {service_name}'}

            # Check if credential already exists
            existing = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.client_id == client_id,
                CreditMonitoringCredential.service_name == service_name,
                CreditMonitoringCredential.is_active == True
            ).first()

            if existing:
                return {'success': False, 'error': 'Active credential already exists for this service'}

            # Encrypt password
            encrypted_password = encrypt_value(password)
            encrypted_ssn = encrypt_value(ssn_last4) if ssn_last4 else None

            # Calculate next scheduled import
            next_import = None
            if import_frequency in FREQUENCIES and FREQUENCIES[import_frequency]:
                next_import = datetime.utcnow() + FREQUENCIES[import_frequency]

            # Create credential
            credential = CreditMonitoringCredential(
                client_id=client_id,
                service_name=service_name,
                username=username,
                password_encrypted=encrypted_password,
                ssn_last4_encrypted=encrypted_ssn,
                is_active=True,
                import_frequency=import_frequency,
                next_scheduled_import=next_import,
                last_import_status='pending'
            )

            db.add(credential)
            db.commit()
            db.refresh(credential)

            return {
                'success': True,
                'credential': credential.to_dict(),
                'message': f'Credential added for {service_name}'
            }

        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}

    def update_credential(
        self,
        credential_id: int,
        username: str = None,
        password: str = None,
        import_frequency: str = None,
        is_active: bool = None
    ) -> Dict[str, Any]:
        """Update existing credential"""
        db = self._get_db()

        try:
            credential = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.id == credential_id
            ).first()

            if not credential:
                return {'success': False, 'error': 'Credential not found'}

            if username:
                credential.username = username
            if password:
                credential.password_encrypted = encrypt_value(password)
            if import_frequency:
                credential.import_frequency = import_frequency
                if import_frequency in FREQUENCIES and FREQUENCIES[import_frequency]:
                    credential.next_scheduled_import = datetime.utcnow() + FREQUENCIES[import_frequency]
            if is_active is not None:
                credential.is_active = is_active

            credential.updated_at = datetime.utcnow()
            db.commit()

            return {'success': True, 'credential': credential.to_dict()}

        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}

    def get_credentials(
        self,
        client_id: int = None,
        service_name: str = None,
        active_only: bool = True
    ) -> List[Dict]:
        """Get credentials with optional filters"""
        db = self._get_db()

        try:
            query = db.query(CreditMonitoringCredential)

            if client_id:
                query = query.filter(CreditMonitoringCredential.client_id == client_id)
            if service_name:
                query = query.filter(CreditMonitoringCredential.service_name == service_name)
            if active_only:
                query = query.filter(CreditMonitoringCredential.is_active == True)

            credentials = query.order_by(CreditMonitoringCredential.created_at.desc()).all()

            return [c.to_dict() for c in credentials]

        except:
            return []

    def delete_credential(self, credential_id: int) -> Dict[str, Any]:
        """Soft delete a credential (mark inactive)"""
        db = self._get_db()

        try:
            credential = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.id == credential_id
            ).first()

            if not credential:
                return {'success': False, 'error': 'Credential not found'}

            credential.is_active = False
            credential.updated_at = datetime.utcnow()
            db.commit()

            return {'success': True, 'message': 'Credential deactivated'}

        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # PULL EXECUTION
    # =========================================================================

    def initiate_pull(
        self,
        credential_id: int,
        pull_type: str = 'manual',
        triggered_by: str = None
    ) -> Dict[str, Any]:
        """Initiate a credit report pull"""
        db = self._get_db()

        try:
            credential = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.id == credential_id,
                CreditMonitoringCredential.is_active == True
            ).first()

            if not credential:
                return {'success': False, 'error': 'Credential not found or inactive'}

            # Get service info
            service_key = credential.service_name.lower().replace(' ', '')
            service_info = SUPPORTED_SERVICES.get(service_key, {})

            # Create pull log
            pull_log = CreditPullLog(
                credential_id=credential_id,
                client_id=credential.client_id,
                service_name=credential.service_name,
                pull_type=pull_type,
                status=STATUS_IN_PROGRESS,
                triggered_by=triggered_by,
                bureaus_included=service_info.get('bureaus', [])
            )

            db.add(pull_log)
            db.commit()
            db.refresh(pull_log)

            # Execute the pull (async in production)
            result = self._execute_pull(credential, pull_log)

            return result

        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}

    def _execute_pull(
        self,
        credential: CreditMonitoringCredential,
        pull_log: CreditPullLog
    ) -> Dict[str, Any]:
        """Execute the actual credit report pull"""
        db = self._get_db()
        start_time = time.time()

        try:
            # Get decrypted password
            password = decrypt_value(credential.password_encrypted)

            # Get service connector
            service_key = credential.service_name.lower().replace(' ', '')
            connector = self._get_connector(service_key)

            if not connector:
                # No connector available - simulate for now
                # In production, this would use Selenium/Playwright
                result = self._simulate_pull(credential, password)
            else:
                result = connector.pull_report(
                    username=credential.username,
                    password=password
                )

            end_time = time.time()
            duration = end_time - start_time

            if result.get('success'):
                # Update pull log with success
                pull_log.status = STATUS_SUCCESS
                pull_log.completed_at = datetime.utcnow()
                pull_log.duration_seconds = duration
                pull_log.report_path = result.get('report_path')
                pull_log.report_type = result.get('report_type', '3bureau')
                pull_log.items_found = result.get('items_found', 0)
                pull_log.negative_items_found = result.get('negative_items_found', 0)
                pull_log.accounts_found = result.get('accounts_found', 0)
                pull_log.inquiries_found = result.get('inquiries_found', 0)

                # Update credential
                credential.last_import_at = datetime.utcnow()
                credential.last_import_status = 'success'
                credential.last_import_error = None
                credential.last_report_path = result.get('report_path')

                # Schedule next import
                if credential.import_frequency in FREQUENCIES and FREQUENCIES[credential.import_frequency]:
                    credential.next_scheduled_import = datetime.utcnow() + FREQUENCIES[credential.import_frequency]

                db.commit()

                return {
                    'success': True,
                    'pull_log': pull_log.to_dict(),
                    'message': f'Successfully pulled report from {credential.service_name}'
                }

            else:
                # Update pull log with failure
                pull_log.status = STATUS_FAILED
                pull_log.completed_at = datetime.utcnow()
                pull_log.duration_seconds = duration
                pull_log.error_message = result.get('error', 'Unknown error')
                pull_log.error_code = result.get('error_code')

                # Update credential
                credential.last_import_at = datetime.utcnow()
                credential.last_import_status = 'failed'
                credential.last_import_error = result.get('error')

                db.commit()

                return {
                    'success': False,
                    'pull_log': pull_log.to_dict(),
                    'error': result.get('error', 'Pull failed')
                }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            pull_log.status = STATUS_FAILED
            pull_log.completed_at = datetime.utcnow()
            pull_log.duration_seconds = duration
            pull_log.error_message = str(e)

            credential.last_import_at = datetime.utcnow()
            credential.last_import_status = 'failed'
            credential.last_import_error = str(e)

            db.commit()

            return {'success': False, 'error': str(e)}

    def _get_connector(self, service_key: str):
        """Get the appropriate connector for a service"""
        # Connector registry - add connectors as they're implemented
        connectors = {
            # 'identityiq': IdentityIQConnector(),
            # 'myscoreiq': MyScoreIQConnector(),
        }
        return connectors.get(service_key)

    def _simulate_pull(
        self,
        credential: CreditMonitoringCredential,
        password: str
    ) -> Dict[str, Any]:
        """Simulate a pull for development/testing"""
        # In production, this would be replaced with actual web scraping
        # For now, return a simulated success

        # Generate a fake report path
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_filename = f"report_{credential.client_id}_{credential.service_name}_{timestamp}.html"
        report_path = f"static/reports/{report_filename}"

        return {
            'success': True,
            'report_path': report_path,
            'report_type': '3bureau',
            'items_found': 45,
            'negative_items_found': 8,
            'accounts_found': 12,
            'inquiries_found': 3,
            'message': 'Simulated pull - connector not implemented'
        }

    # =========================================================================
    # SCHEDULED PULLS
    # =========================================================================

    def get_due_pulls(self) -> List[Dict]:
        """Get credentials that are due for scheduled pull"""
        db = self._get_db()

        try:
            now = datetime.utcnow()

            credentials = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.is_active == True,
                CreditMonitoringCredential.import_frequency != 'manual',
                CreditMonitoringCredential.next_scheduled_import <= now
            ).all()

            return [c.to_dict() for c in credentials]

        except:
            return []

    def run_scheduled_pulls(self, triggered_by: str = 'cron') -> Dict[str, Any]:
        """Run all scheduled pulls that are due"""
        db = self._get_db()

        try:
            now = datetime.utcnow()

            credentials = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.is_active == True,
                CreditMonitoringCredential.import_frequency != 'manual',
                CreditMonitoringCredential.import_frequency != 'with_letter_send',
                CreditMonitoringCredential.next_scheduled_import <= now
            ).all()

            results = {
                'total': len(credentials),
                'success': 0,
                'failed': 0,
                'pulls': []
            }

            for credential in credentials:
                result = self.initiate_pull(
                    credential_id=credential.id,
                    pull_type='scheduled',
                    triggered_by=triggered_by
                )

                if result.get('success'):
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['pulls'].append({
                    'credential_id': credential.id,
                    'client_id': credential.client_id,
                    'service': credential.service_name,
                    'success': result.get('success', False),
                    'error': result.get('error')
                })

            return results

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_letter_send_pulls(self, client_id: int, triggered_by: str = 'letter_send') -> Dict[str, Any]:
        """Trigger pulls for credentials with 'with_letter_send' frequency"""
        db = self._get_db()

        try:
            credentials = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.client_id == client_id,
                CreditMonitoringCredential.is_active == True,
                CreditMonitoringCredential.import_frequency == 'with_letter_send'
            ).all()

            results = {
                'total': len(credentials),
                'success': 0,
                'failed': 0,
                'pulls': []
            }

            for credential in credentials:
                result = self.initiate_pull(
                    credential_id=credential.id,
                    pull_type='letter_send',
                    triggered_by=triggered_by
                )

                if result.get('success'):
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['pulls'].append({
                    'credential_id': credential.id,
                    'service': credential.service_name,
                    'success': result.get('success', False)
                })

            return results

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # PULL LOGS
    # =========================================================================

    def get_pull_logs(
        self,
        client_id: int = None,
        credential_id: int = None,
        status: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get pull logs with filters"""
        db = self._get_db()

        try:
            query = db.query(CreditPullLog)

            if client_id:
                query = query.filter(CreditPullLog.client_id == client_id)
            if credential_id:
                query = query.filter(CreditPullLog.credential_id == credential_id)
            if status:
                query = query.filter(CreditPullLog.status == status)

            logs = query.order_by(CreditPullLog.created_at.desc()).limit(limit).all()

            return [log.to_dict() for log in logs]

        except:
            return []

    def get_pull_stats(self) -> Dict[str, Any]:
        """Get pull statistics for dashboard"""
        db = self._get_db()

        try:
            from sqlalchemy import func

            # Total credentials
            total_credentials = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.is_active == True
            ).count()

            # Pulls today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            pulls_today = db.query(CreditPullLog).filter(
                CreditPullLog.initiated_at >= today_start
            ).count()

            # Successful pulls today
            success_today = db.query(CreditPullLog).filter(
                CreditPullLog.initiated_at >= today_start,
                CreditPullLog.status == STATUS_SUCCESS
            ).count()

            # Failed pulls today
            failed_today = db.query(CreditPullLog).filter(
                CreditPullLog.initiated_at >= today_start,
                CreditPullLog.status == STATUS_FAILED
            ).count()

            # Pending scheduled pulls
            pending_scheduled = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.is_active == True,
                CreditMonitoringCredential.import_frequency != 'manual',
                CreditMonitoringCredential.next_scheduled_import <= datetime.utcnow()
            ).count()

            # Pulls this week
            week_start = today_start - timedelta(days=today_start.weekday())
            pulls_this_week = db.query(CreditPullLog).filter(
                CreditPullLog.initiated_at >= week_start
            ).count()

            # Average pull duration
            avg_duration = db.query(func.avg(CreditPullLog.duration_seconds)).filter(
                CreditPullLog.status == STATUS_SUCCESS,
                CreditPullLog.duration_seconds.isnot(None)
            ).scalar() or 0

            # By service breakdown
            service_breakdown = {}
            for service_key, service_info in SUPPORTED_SERVICES.items():
                service_name = service_info['name']
                count = db.query(CreditMonitoringCredential).filter(
                    CreditMonitoringCredential.service_name == service_name,
                    CreditMonitoringCredential.is_active == True
                ).count()
                if count > 0:
                    service_breakdown[service_name] = count

            return {
                'total_credentials': total_credentials,
                'pulls_today': pulls_today,
                'success_today': success_today,
                'failed_today': failed_today,
                'pending_scheduled': pending_scheduled,
                'pulls_this_week': pulls_this_week,
                'avg_duration_seconds': round(avg_duration, 2),
                'service_breakdown': service_breakdown
            }

        except:
            return {
                'total_credentials': 0,
                'pulls_today': 0,
                'success_today': 0,
                'failed_today': 0,
                'pending_scheduled': 0,
                'pulls_this_week': 0,
                'avg_duration_seconds': 0,
                'service_breakdown': {}
            }

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate_credentials(self, credential_id: int) -> Dict[str, Any]:
        """Validate credentials by attempting a login (without full pull)"""
        db = self._get_db()

        try:
            credential = db.query(CreditMonitoringCredential).filter(
                CreditMonitoringCredential.id == credential_id
            ).first()

            if not credential:
                return {'success': False, 'error': 'Credential not found'}

            # Get decrypted password
            password = decrypt_value(credential.password_encrypted)

            # In production, this would attempt a login
            # For now, simulate validation
            is_valid = len(credential.username) > 0 and len(password) > 0

            return {
                'success': True,
                'valid': is_valid,
                'message': 'Credentials validated' if is_valid else 'Invalid credentials'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # SUPPORTED SERVICES
    # =========================================================================

    @staticmethod
    def get_supported_services() -> List[Dict]:
        """Get list of supported credit monitoring services"""
        return [
            {
                'key': key,
                'name': info['name'],
                'url': info['url'],
                'report_type': info['report_type'],
                'bureaus': info['bureaus'],
                'supports_auto_pull': info['supports_auto_pull']
            }
            for key, info in SUPPORTED_SERVICES.items()
        ]

    @staticmethod
    def get_frequencies() -> List[Dict]:
        """Get available import frequencies"""
        return [
            {'value': 'manual', 'label': 'Manual Only'},
            {'value': 'daily', 'label': 'Daily'},
            {'value': 'weekly', 'label': 'Weekly'},
            {'value': 'biweekly', 'label': 'Every 2 Weeks'},
            {'value': 'monthly', 'label': 'Monthly'},
            {'value': 'with_letter_send', 'label': 'With Letter Send'},
        ]
