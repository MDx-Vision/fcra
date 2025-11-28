"""
Audit Service for SOC 2 and HIPAA Compliance
Comprehensive action logging with compliance reporting capabilities
"""
import os
import json
import uuid
import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from functools import wraps

from flask import request, session, g
from sqlalchemy import func, and_, or_, desc, cast, String
from sqlalchemy.orm import Session

from database import get_db, AuditLog, AUDIT_EVENT_TYPES, AUDIT_RESOURCE_TYPES, AUDIT_SEVERITY_LEVELS


PHI_FIELDS = [
    'ssn', 'ssn_last_four', 'date_of_birth', 'social_security',
    'credit_monitoring_username', 'credit_monitoring_password_encrypted',
    'address_street', 'address_city', 'address_state', 'address_zip',
    'phone', 'email', 'mobile', 'name', 'first_name', 'last_name'
]


class AuditService:
    """Service for comprehensive audit logging with compliance features"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self._current_request_id = None
    
    def _get_db(self) -> Tuple[Session, bool]:
        """Get database session"""
        if self.db:
            return self.db, False
        return get_db(), True
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Extract context from current Flask request"""
        context = {
            'user_ip': None,
            'user_agent': None,
            'endpoint': None,
            'http_method': None,
            'session_id': None,
            'request_id': None,
            'user_id': None,
            'user_type': 'system',
            'user_email': None,
            'user_name': None,
            'organization_id': None,
            'tenant_id': None
        }
        
        try:
            if request:
                context['user_ip'] = request.headers.get('X-Forwarded-For', request.remote_addr)
                context['user_agent'] = request.headers.get('User-Agent', '')[:500]
                context['endpoint'] = request.path
                context['http_method'] = request.method
                context['request_id'] = getattr(g, 'request_id', None) or str(uuid.uuid4())[:8]
        except RuntimeError:
            pass
        
        try:
            if session:
                context['session_id'] = session.get('_id', str(uuid.uuid4())[:16])
                
                if 'staff_id' in session:
                    context['user_id'] = session.get('staff_id')
                    context['user_type'] = 'staff'
                    context['user_email'] = session.get('staff_email')
                    context['user_name'] = session.get('staff_name')
                elif 'client_id' in session:
                    context['user_id'] = session.get('client_id')
                    context['user_type'] = 'client'
                    context['user_email'] = session.get('client_email')
                    context['user_name'] = session.get('client_name')
        except RuntimeError:
            pass
        
        try:
            if hasattr(g, 'api_key'):
                context['user_type'] = 'api'
                context['user_id'] = g.api_key.id
                context['user_name'] = f"API Key: {g.api_key.name}"
            
            if hasattr(g, 'tenant') and g.tenant:
                context['tenant_id'] = g.tenant.id
        except RuntimeError:
            pass
        
        return context
    
    def _detect_phi_access(self, details: Dict = None, old_values: Dict = None, new_values: Dict = None) -> Tuple[bool, List[str]]:
        """Detect if PHI fields were accessed"""
        phi_accessed = []
        
        for data in [details, old_values, new_values]:
            if data:
                for key in data.keys():
                    key_lower = key.lower()
                    for phi_field in PHI_FIELDS:
                        if phi_field in key_lower:
                            if key not in phi_accessed:
                                phi_accessed.append(key)
        
        return bool(phi_accessed), phi_accessed
    
    def log_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = None,
        details: Dict = None,
        old_values: Dict = None,
        new_values: Dict = None,
        severity: str = None,
        user_id: int = None,
        user_type: str = None,
        user_email: str = None,
        user_name: str = None,
        duration_ms: int = None,
        http_status: int = None,
        compliance_flags: Dict = None
    ) -> Optional[AuditLog]:
        """
        Core audit logging method
        
        Args:
            event_type: Type of event (login, create, update, delete, etc.)
            resource_type: Type of resource affected (client, case, document, etc.)
            resource_id: ID of the specific resource
            action: Human-readable description of the action
            details: Additional JSON details about the event
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            severity: Override auto-detected severity level
            user_id: Override auto-detected user ID
            user_type: Override auto-detected user type
            duration_ms: Request duration in milliseconds
            http_status: HTTP response status code
            compliance_flags: Special compliance markers
        
        Returns:
            Created AuditLog entry or None if failed
        """
        db, should_close = self._get_db()
        
        try:
            context = self._get_request_context()
            
            is_phi, phi_fields = self._detect_phi_access(details, old_values, new_values)
            
            auto_severity = AuditLog.get_severity_for_event(event_type)
            if is_phi:
                auto_severity = 'warning' if auto_severity == 'info' else auto_severity
            
            audit_entry = AuditLog(
                timestamp=datetime.utcnow(),
                event_type=event_type,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                user_id=user_id or context['user_id'],
                user_type=user_type or context['user_type'],
                user_email=user_email or context['user_email'],
                user_name=user_name or context['user_name'],
                user_ip=context['user_ip'],
                user_agent=context['user_agent'],
                action=action or f"{event_type} {resource_type}",
                details=details,
                old_values=old_values,
                new_values=new_values,
                severity=severity or auto_severity,
                session_id=context['session_id'],
                request_id=context['request_id'],
                duration_ms=duration_ms,
                endpoint=context['endpoint'],
                http_method=context['http_method'],
                http_status=http_status,
                organization_id=context.get('organization_id'),
                tenant_id=context['tenant_id'],
                is_phi_access=is_phi,
                phi_fields_accessed=phi_fields if phi_fields else None,
                compliance_flags=compliance_flags
            )
            
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            
            return audit_entry
            
        except Exception as e:
            print(f"Audit logging error: {e}")
            db.rollback()
            return None
        finally:
            if should_close:
                db.close()
    
    def log_login(
        self,
        user_id: int,
        user_type: str,
        success: bool,
        ip: str = None,
        email: str = None,
        name: str = None,
        failure_reason: str = None
    ) -> Optional[AuditLog]:
        """Log login attempt"""
        event_type = 'login' if success else 'login_failed'
        severity = 'info' if success else 'critical'
        
        details = {
            'success': success,
            'login_method': 'password'
        }
        
        if failure_reason:
            details['failure_reason'] = failure_reason
        
        return self.log_event(
            event_type=event_type,
            resource_type='staff' if user_type == 'staff' else 'client',
            resource_id=str(user_id) if user_id else None,
            action=f"{'Successful' if success else 'Failed'} login attempt",
            details=details,
            severity=severity,
            user_id=user_id,
            user_type=user_type,
            user_email=email,
            user_name=name,
            compliance_flags={'security_event': True} if not success else None
        )
    
    def log_logout(self, user_id: int, user_type: str, email: str = None, name: str = None) -> Optional[AuditLog]:
        """Log logout event"""
        return self.log_event(
            event_type='logout',
            resource_type='staff' if user_type == 'staff' else 'client',
            resource_id=str(user_id),
            action="User logged out",
            user_id=user_id,
            user_type=user_type,
            user_email=email,
            user_name=name
        )
    
    def log_data_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: str,
        fields_accessed: List[str] = None,
        reason: str = None
    ) -> Optional[AuditLog]:
        """Log PHI/sensitive data access for HIPAA compliance"""
        is_phi = any(field.lower() in [f.lower() for f in PHI_FIELDS] for field in (fields_accessed or []))
        
        details = {
            'fields_accessed': fields_accessed,
            'access_reason': reason
        }
        
        return self.log_event(
            event_type='phi_access' if is_phi else 'read',
            resource_type=resource_type,
            resource_id=str(resource_id),
            action=f"Accessed {'PHI data in ' if is_phi else ''}{resource_type} record",
            details=details,
            severity='warning' if is_phi else 'info',
            compliance_flags={'hipaa_phi_access': True} if is_phi else None
        )
    
    def log_credit_report_access(
        self,
        user_id: int,
        client_id: int,
        report_id: int = None,
        action_type: str = 'view'
    ) -> Optional[AuditLog]:
        """Log credit report access - always treated as PHI"""
        return self.log_event(
            event_type='credit_report_access',
            resource_type='credit_report',
            resource_id=str(report_id) if report_id else str(client_id),
            action=f"Credit report {action_type} for client {client_id}",
            details={
                'client_id': client_id,
                'report_id': report_id,
                'action_type': action_type
            },
            severity='warning',
            compliance_flags={'hipaa_phi_access': True, 'fcra_regulated': True}
        )
    
    def log_export(
        self,
        user_id: int,
        resource_type: str,
        export_format: str,
        record_count: int = None,
        filter_criteria: Dict = None
    ) -> Optional[AuditLog]:
        """Log data export for compliance tracking"""
        return self.log_event(
            event_type='export',
            resource_type=resource_type,
            action=f"Exported {resource_type} data to {export_format}",
            details={
                'format': export_format,
                'record_count': record_count,
                'filters': filter_criteria
            },
            severity='warning',
            compliance_flags={'data_export': True}
        )
    
    def log_document_action(
        self,
        action_type: str,
        document_type: str,
        document_id: int = None,
        client_id: int = None,
        filename: str = None
    ) -> Optional[AuditLog]:
        """Log document upload/download/view actions"""
        event_map = {
            'upload': 'document_upload',
            'download': 'document_download',
            'view': 'document_view',
            'delete': 'delete'
        }
        
        return self.log_event(
            event_type=event_map.get(action_type, 'read'),
            resource_type='document',
            resource_id=str(document_id) if document_id else None,
            action=f"Document {action_type}: {filename or document_type}",
            details={
                'action_type': action_type,
                'document_type': document_type,
                'client_id': client_id,
                'filename': filename
            },
            severity='warning' if action_type == 'download' else 'info'
        )
    
    def log_settings_change(
        self,
        setting_type: str,
        old_values: Dict = None,
        new_values: Dict = None,
        description: str = None
    ) -> Optional[AuditLog]:
        """Log system configuration changes"""
        return self.log_event(
            event_type='settings_change',
            resource_type='settings',
            resource_id=setting_type,
            action=description or f"Modified {setting_type} settings",
            old_values=old_values,
            new_values=new_values,
            severity='critical',
            compliance_flags={'configuration_change': True}
        )
    
    def log_permission_change(
        self,
        target_user_id: int,
        target_user_type: str,
        old_permissions: Dict = None,
        new_permissions: Dict = None
    ) -> Optional[AuditLog]:
        """Log permission/role changes"""
        return self.log_event(
            event_type='permission_change',
            resource_type=target_user_type,
            resource_id=str(target_user_id),
            action=f"Modified permissions for {target_user_type} {target_user_id}",
            old_values=old_permissions,
            new_values=new_permissions,
            severity='critical',
            compliance_flags={'access_control_change': True}
        )
    
    def get_audit_trail(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get complete audit trail for a specific resource"""
        db, should_close = self._get_db()
        
        try:
            logs = db.query(AuditLog).filter(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == str(resource_id)
            ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
            
            return [log.to_dict() for log in logs]
        finally:
            if should_close:
                db.close()
    
    def get_user_activity(
        self,
        user_id: int,
        user_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 500
    ) -> List[Dict]:
        """Get activity report for a specific user"""
        db, should_close = self._get_db()
        
        try:
            query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
            
            if user_type:
                query = query.filter(AuditLog.user_type == user_type)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
            
            return [log.to_dict() for log in logs]
        finally:
            if should_close:
                db.close()
    
    def get_security_events(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        severity: str = None,
        limit: int = 500
    ) -> List[Dict]:
        """Get security-related events"""
        db, should_close = self._get_db()
        
        try:
            security_event_types = ['login_failed', 'permission_change', 'password_reset', 'password_change', 'settings_change']
            
            query = db.query(AuditLog).filter(
                or_(
                    AuditLog.event_type.in_(security_event_types),
                    AuditLog.severity.in_(['warning', 'critical'])
                )
            )
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            if severity:
                query = query.filter(AuditLog.severity == severity)
            
            logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
            
            return [log.to_dict() for log in logs]
        finally:
            if should_close:
                db.close()
    
    def get_phi_access_logs(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
        limit: int = 500
    ) -> List[Dict]:
        """Get PHI access logs for HIPAA compliance"""
        db, should_close = self._get_db()
        
        try:
            query = db.query(AuditLog).filter(AuditLog.is_phi_access == True)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
            
            return [log.to_dict() for log in logs]
        finally:
            if should_close:
                db.close()
    
    def get_logs(
        self,
        event_type: str = None,
        resource_type: str = None,
        user_type: str = None,
        severity: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        search_query: str = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[Dict], int]:
        """Get filtered audit logs with pagination"""
        db, should_close = self._get_db()
        
        try:
            query = db.query(AuditLog)
            
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if user_type:
                query = query.filter(AuditLog.user_type == user_type)
            
            if severity:
                query = query.filter(AuditLog.severity == severity)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    or_(
                        AuditLog.action.ilike(search_pattern),
                        AuditLog.user_email.ilike(search_pattern),
                        AuditLog.user_name.ilike(search_pattern),
                        AuditLog.resource_id.ilike(search_pattern),
                        AuditLog.user_ip.ilike(search_pattern)
                    )
                )
            
            total = query.count()
            
            offset = (page - 1) * per_page
            logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(per_page).all()
            
            return [log.to_dict() for log in logs], total
        finally:
            if should_close:
                db.close()
    
    def generate_compliance_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate compliance report (SOC 2 or HIPAA)
        
        Args:
            report_type: 'soc2' or 'hipaa'
            start_date: Report period start
            end_date: Report period end
        
        Returns:
            Comprehensive compliance report data
        """
        db, should_close = self._get_db()
        
        try:
            base_query = db.query(AuditLog).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            )
            
            report = {
                'report_type': report_type,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {},
                'details': {}
            }
            
            total_events = base_query.count()
            report['summary']['total_events'] = total_events
            
            event_counts = db.query(
                AuditLog.event_type,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).group_by(AuditLog.event_type).all()
            
            report['summary']['events_by_type'] = {event: count for event, count in event_counts}
            
            severity_counts = db.query(
                AuditLog.severity,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).group_by(AuditLog.severity).all()
            
            report['summary']['events_by_severity'] = {sev: count for sev, count in severity_counts}
            
            user_type_counts = db.query(
                AuditLog.user_type,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).group_by(AuditLog.user_type).all()
            
            report['summary']['events_by_user_type'] = {ut: count for ut, count in user_type_counts}
            
            if report_type == 'soc2':
                login_failures = base_query.filter(AuditLog.event_type == 'login_failed').count()
                report['details']['failed_logins'] = login_failures
                
                permission_changes = base_query.filter(AuditLog.event_type == 'permission_change').count()
                report['details']['permission_changes'] = permission_changes
                
                config_changes = base_query.filter(AuditLog.event_type == 'settings_change').count()
                report['details']['configuration_changes'] = config_changes
                
                data_exports = base_query.filter(AuditLog.event_type == 'export').count()
                report['details']['data_exports'] = data_exports
                
                unique_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                    AuditLog.user_id.isnot(None)
                ).scalar()
                report['details']['unique_users'] = unique_users or 0
                
                unique_ips = db.query(func.count(func.distinct(AuditLog.user_ip))).filter(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                    AuditLog.user_ip.isnot(None)
                ).scalar()
                report['details']['unique_ip_addresses'] = unique_ips or 0
                
                critical_events = base_query.filter(AuditLog.severity == 'critical').order_by(
                    desc(AuditLog.timestamp)
                ).limit(100).all()
                report['details']['critical_events'] = [e.to_dict() for e in critical_events]
                
            elif report_type == 'hipaa':
                phi_accesses = base_query.filter(AuditLog.is_phi_access == True).count()
                report['details']['phi_access_count'] = phi_accesses
                
                phi_by_user = db.query(
                    AuditLog.user_id,
                    AuditLog.user_email,
                    AuditLog.user_name,
                    func.count(AuditLog.id)
                ).filter(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                    AuditLog.is_phi_access == True
                ).group_by(
                    AuditLog.user_id,
                    AuditLog.user_email,
                    AuditLog.user_name
                ).all()
                
                report['details']['phi_access_by_user'] = [
                    {'user_id': uid, 'email': email, 'name': name, 'count': count}
                    for uid, email, name, count in phi_by_user
                ]
                
                credit_report_accesses = base_query.filter(
                    AuditLog.event_type == 'credit_report_access'
                ).count()
                report['details']['credit_report_accesses'] = credit_report_accesses
                
                client_data_exports = base_query.filter(
                    AuditLog.event_type == 'export',
                    AuditLog.resource_type == 'client'
                ).count()
                report['details']['client_data_exports'] = client_data_exports
                
                recent_phi_logs = base_query.filter(
                    AuditLog.is_phi_access == True
                ).order_by(desc(AuditLog.timestamp)).limit(100).all()
                report['details']['recent_phi_access'] = [e.to_dict() for e in recent_phi_logs]
            
            return report
            
        finally:
            if should_close:
                db.close()
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get audit log statistics for dashboard"""
        db, should_close = self._get_db()
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stats = {
                'period_days': days,
                'total_events': 0,
                'events_by_day': [],
                'events_by_type': {},
                'events_by_severity': {},
                'top_users': [],
                'recent_security_events': []
            }
            
            stats['total_events'] = db.query(AuditLog).filter(
                AuditLog.timestamp >= start_date
            ).count()
            
            daily_counts = db.query(
                func.date(AuditLog.timestamp).label('date'),
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date
            ).group_by(func.date(AuditLog.timestamp)).order_by('date').all()
            
            stats['events_by_day'] = [
                {'date': str(date), 'count': count}
                for date, count in daily_counts
            ]
            
            type_counts = db.query(
                AuditLog.event_type,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date
            ).group_by(AuditLog.event_type).all()
            
            stats['events_by_type'] = {t: c for t, c in type_counts}
            
            severity_counts = db.query(
                AuditLog.severity,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date
            ).group_by(AuditLog.severity).all()
            
            stats['events_by_severity'] = {s: c for s, c in severity_counts}
            
            top_users = db.query(
                AuditLog.user_id,
                AuditLog.user_email,
                AuditLog.user_name,
                AuditLog.user_type,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= start_date,
                AuditLog.user_id.isnot(None)
            ).group_by(
                AuditLog.user_id,
                AuditLog.user_email,
                AuditLog.user_name,
                AuditLog.user_type
            ).order_by(desc(func.count(AuditLog.id))).limit(10).all()
            
            stats['top_users'] = [
                {'user_id': uid, 'email': email, 'name': name, 'type': utype, 'count': count}
                for uid, email, name, utype, count in top_users
            ]
            
            security_events = db.query(AuditLog).filter(
                AuditLog.timestamp >= start_date,
                or_(
                    AuditLog.severity == 'critical',
                    AuditLog.event_type.in_(['login_failed', 'permission_change'])
                )
            ).order_by(desc(AuditLog.timestamp)).limit(10).all()
            
            stats['recent_security_events'] = [e.to_dict() for e in security_events]
            
            return stats
            
        finally:
            if should_close:
                db.close()
    
    def export_logs(
        self,
        format: str,
        start_date: datetime = None,
        end_date: datetime = None,
        event_type: str = None,
        resource_type: str = None
    ) -> Tuple[str, str]:
        """
        Export audit logs to CSV or JSON
        
        Returns:
            Tuple of (content, filename)
        """
        db, should_close = self._get_db()
        
        try:
            query = db.query(AuditLog)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            logs = query.order_by(desc(AuditLog.timestamp)).limit(10000).all()
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            if format == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)
                
                writer.writerow([
                    'ID', 'Timestamp', 'Event Type', 'Resource Type', 'Resource ID',
                    'User ID', 'User Type', 'User Email', 'User Name', 'User IP',
                    'Action', 'Severity', 'Session ID', 'Endpoint', 'HTTP Method',
                    'HTTP Status', 'Duration (ms)', 'Is PHI Access'
                ])
                
                for log in logs:
                    writer.writerow([
                        log.id, log.timestamp, log.event_type, log.resource_type,
                        log.resource_id, log.user_id, log.user_type, log.user_email,
                        log.user_name, log.user_ip, log.action, log.severity,
                        log.session_id, log.endpoint, log.http_method,
                        log.http_status, log.duration_ms, log.is_phi_access
                    ])
                
                content = output.getvalue()
                filename = f"audit_logs_{timestamp}.csv"
                
            else:
                data = [log.to_dict() for log in logs]
                content = json.dumps(data, indent=2)
                filename = f"audit_logs_{timestamp}.json"
            
            self.log_export(
                user_id=None,
                resource_type='audit_logs',
                export_format=format,
                record_count=len(logs),
                filter_criteria={
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'event_type': event_type,
                    'resource_type': resource_type
                }
            )
            
            return content, filename
            
        finally:
            if should_close:
                db.close()
    
    def cleanup_old_logs(self, retention_days: int = 365) -> int:
        """
        Remove audit logs older than retention period (GDPR compliance)
        
        Args:
            retention_days: Number of days to retain logs (default 1 year for SOC 2)
        
        Returns:
            Number of deleted records
        """
        db, should_close = self._get_db()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            count = db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).count()
            
            if count > 0:
                db.query(AuditLog).filter(
                    AuditLog.timestamp < cutoff_date
                ).delete(synchronize_session=False)
                db.commit()
                
                self.log_event(
                    event_type='delete',
                    resource_type='audit_logs',
                    action=f"Cleanup: Deleted {count} audit logs older than {retention_days} days",
                    details={
                        'deleted_count': count,
                        'retention_days': retention_days,
                        'cutoff_date': cutoff_date.isoformat()
                    },
                    severity='info',
                    compliance_flags={'gdpr_retention': True}
                )
            
            return count
            
        finally:
            if should_close:
                db.close()


_audit_service_instance = None


def get_audit_service(db: Session = None) -> AuditService:
    """Get or create audit service instance"""
    global _audit_service_instance
    if db:
        return AuditService(db)
    if _audit_service_instance is None:
        _audit_service_instance = AuditService()
    return _audit_service_instance


def audit_action(event_type: str, resource_type: str, get_resource_id=None):
    """
    Decorator for automatically logging actions
    
    Usage:
        @audit_action('update', 'client', lambda args, kwargs, result: kwargs.get('client_id'))
        def update_client(client_id, data):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            result = None
            error = None
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                resource_id = None
                if get_resource_id:
                    try:
                        resource_id = get_resource_id(args, kwargs, result)
                    except:
                        pass
                
                service = get_audit_service()
                service.log_event(
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    action=f.__name__,
                    details={'error': str(error)} if error else None,
                    duration_ms=duration_ms,
                    severity='critical' if error else None
                )
        
        return wrapper
    return decorator
