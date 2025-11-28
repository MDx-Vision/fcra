"""
Franchise Service for Multi-Office Law Firm Management
Handles organization hierarchy, member management, client assignments, and revenue sharing.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from database import (
    FranchiseOrganization, OrganizationMembership, OrganizationClient, InterOrgTransfer,
    Staff, Client, Case, Settlement, FRANCHISE_ORG_TYPES, FRANCHISE_MEMBER_ROLES
)


class FranchiseService:
    """Service class for franchise organization management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        base_slug = slug
        counter = 1
        while self.db.query(FranchiseOrganization).filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def create_organization(
        self,
        name: str,
        org_type: str = 'branch',
        parent_org_id: Optional[int] = None,
        **kwargs
    ) -> FranchiseOrganization:
        """
        Create a new franchise organization.
        
        Args:
            name: Organization display name
            org_type: Type of organization (headquarters/regional/branch)
            parent_org_id: Parent organization ID for hierarchy
            **kwargs: Additional organization fields
        
        Returns:
            Created FranchiseOrganization instance
        """
        if org_type not in FRANCHISE_ORG_TYPES:
            raise ValueError(f"Invalid org_type. Must be one of: {list(FRANCHISE_ORG_TYPES.keys())}")
        
        if parent_org_id:
            parent = self.db.query(FranchiseOrganization).filter_by(id=parent_org_id).first()
            if not parent:
                raise ValueError(f"Parent organization with ID {parent_org_id} not found")
            
            parent_level = FRANCHISE_ORG_TYPES.get(parent.org_type, {}).get('level', 0)
            child_level = FRANCHISE_ORG_TYPES.get(org_type, {}).get('level', 0)
            if child_level <= parent_level:
                raise ValueError(f"Child organization type must be lower in hierarchy than parent")
        
        slug = kwargs.get('slug') or self._generate_slug(name)
        
        existing = self.db.query(FranchiseOrganization).filter_by(slug=slug).first()
        if existing:
            raise ValueError(f"Organization with slug '{slug}' already exists")
        
        org = FranchiseOrganization(
            name=name,
            slug=slug,
            org_type=org_type,
            parent_org_id=parent_org_id,
            address=kwargs.get('address'),
            city=kwargs.get('city'),
            state=kwargs.get('state'),
            zip_code=kwargs.get('zip_code'),
            phone=kwargs.get('phone'),
            email=kwargs.get('email'),
            manager_staff_id=kwargs.get('manager_staff_id'),
            is_active=kwargs.get('is_active', True),
            settings=kwargs.get('settings', {}),
            revenue_share_percent=kwargs.get('revenue_share_percent', 0.0)
        )
        
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        
        return org
    
    def update_organization(self, org_id: int, **kwargs) -> Optional[FranchiseOrganization]:
        """
        Update an existing organization.
        
        Args:
            org_id: ID of the organization to update
            **kwargs: Fields to update
        
        Returns:
            Updated FranchiseOrganization instance or None if not found
        """
        org = self.db.query(FranchiseOrganization).filter_by(id=org_id).first()
        if not org:
            return None
        
        if 'slug' in kwargs and kwargs['slug'] != org.slug:
            existing = self.db.query(FranchiseOrganization).filter(
                FranchiseOrganization.slug == kwargs['slug'],
                FranchiseOrganization.id != org_id
            ).first()
            if existing:
                raise ValueError(f"Organization with slug '{kwargs['slug']}' already exists")
        
        if 'org_type' in kwargs and kwargs['org_type'] not in FRANCHISE_ORG_TYPES:
            raise ValueError(f"Invalid org_type. Must be one of: {list(FRANCHISE_ORG_TYPES.keys())}")
        
        allowed_fields = [
            'name', 'slug', 'org_type', 'parent_org_id', 'address', 'city',
            'state', 'zip_code', 'phone', 'email', 'manager_staff_id',
            'is_active', 'settings', 'revenue_share_percent'
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(org, key, value)
        
        org.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(org)
        
        return org
    
    def delete_organization(self, org_id: int) -> bool:
        """
        Delete an organization (soft delete by setting is_active=False).
        
        Args:
            org_id: ID of the organization to delete
        
        Returns:
            True if deleted, False if not found
        """
        org = self.db.query(FranchiseOrganization).filter_by(id=org_id).first()
        if not org:
            return False
        
        children = self.db.query(FranchiseOrganization).filter_by(parent_org_id=org_id).all()
        if children:
            raise ValueError("Cannot delete organization with child organizations. Delete children first.")
        
        org.is_active = False
        org.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def get_organization_by_id(self, org_id: int) -> Optional[FranchiseOrganization]:
        """Get an organization by ID"""
        return self.db.query(FranchiseOrganization).filter_by(id=org_id).first()
    
    def get_organization_by_slug(self, slug: str) -> Optional[FranchiseOrganization]:
        """Get an organization by slug"""
        return self.db.query(FranchiseOrganization).filter_by(slug=slug, is_active=True).first()
    
    def get_all_organizations(self, include_inactive: bool = False) -> List[FranchiseOrganization]:
        """Get all organizations"""
        query = self.db.query(FranchiseOrganization)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(FranchiseOrganization.name).all()
    
    def get_organization_hierarchy(self, org_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get organization hierarchy as a tree structure.
        
        Args:
            org_id: Starting organization ID (None for all root organizations)
        
        Returns:
            List of organization dictionaries with nested children
        """
        def build_tree(org: FranchiseOrganization) -> Dict[str, Any]:
            org_dict = org.to_dict()
            children = self.db.query(FranchiseOrganization).filter_by(
                parent_org_id=org.id,
                is_active=True
            ).order_by(FranchiseOrganization.name).all()
            org_dict['children'] = [build_tree(child) for child in children]
            org_dict['member_count'] = len(org.members)
            org_dict['client_count'] = len(org.clients)
            return org_dict
        
        if org_id:
            org = self.get_organization_by_id(org_id)
            if not org:
                return []
            return [build_tree(org)]
        
        root_orgs = self.db.query(FranchiseOrganization).filter(
            FranchiseOrganization.parent_org_id.is_(None),
            FranchiseOrganization.is_active == True
        ).order_by(FranchiseOrganization.name).all()
        
        return [build_tree(org) for org in root_orgs]
    
    def get_child_organizations(self, org_id: int, recursive: bool = False) -> List[FranchiseOrganization]:
        """
        Get child organizations.
        
        Args:
            org_id: Parent organization ID
            recursive: If True, get all descendants; if False, only direct children
        
        Returns:
            List of child organizations
        """
        direct_children = self.db.query(FranchiseOrganization).filter_by(
            parent_org_id=org_id,
            is_active=True
        ).order_by(FranchiseOrganization.name).all()
        
        if not recursive:
            return direct_children
        
        all_children = list(direct_children)
        for child in direct_children:
            all_children.extend(self.get_child_organizations(child.id, recursive=True))
        
        return all_children
    
    def add_member(
        self,
        org_id: int,
        staff_id: int,
        role: str = 'staff',
        permissions: Optional[List[str]] = None,
        is_primary: bool = False
    ) -> OrganizationMembership:
        """
        Add a staff member to an organization.
        
        Args:
            org_id: Organization ID
            staff_id: Staff user ID
            role: Member role (owner/manager/staff)
            permissions: Custom permissions list
            is_primary: Whether this is the user's primary organization
        
        Returns:
            Created OrganizationMembership instance
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            raise ValueError(f"Organization with ID {org_id} not found")
        
        staff = self.db.query(Staff).filter_by(id=staff_id).first()
        if not staff:
            raise ValueError(f"Staff user with ID {staff_id} not found")
        
        if role not in FRANCHISE_MEMBER_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {list(FRANCHISE_MEMBER_ROLES.keys())}")
        
        existing = self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id,
            staff_id=staff_id
        ).first()
        if existing:
            raise ValueError(f"Staff user is already a member of this organization")
        
        if is_primary:
            self.db.query(OrganizationMembership).filter_by(
                staff_id=staff_id,
                is_primary=True
            ).update({'is_primary': False})
        
        membership = OrganizationMembership(
            organization_id=org_id,
            staff_id=staff_id,
            role=role,
            permissions=permissions or [],
            is_primary=is_primary
        )
        
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        
        return membership
    
    def update_member(
        self,
        org_id: int,
        staff_id: int,
        **kwargs
    ) -> Optional[OrganizationMembership]:
        """
        Update a member's role or permissions.
        
        Args:
            org_id: Organization ID
            staff_id: Staff user ID
            **kwargs: Fields to update (role, permissions, is_primary)
        
        Returns:
            Updated OrganizationMembership instance or None
        """
        membership = self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id,
            staff_id=staff_id
        ).first()
        
        if not membership:
            return None
        
        if 'role' in kwargs:
            if kwargs['role'] not in FRANCHISE_MEMBER_ROLES:
                raise ValueError(f"Invalid role. Must be one of: {list(FRANCHISE_MEMBER_ROLES.keys())}")
            membership.role = kwargs['role']
        
        if 'permissions' in kwargs:
            membership.permissions = kwargs['permissions']
        
        if 'is_primary' in kwargs and kwargs['is_primary']:
            self.db.query(OrganizationMembership).filter_by(
                staff_id=staff_id,
                is_primary=True
            ).update({'is_primary': False})
            membership.is_primary = True
        
        self.db.commit()
        self.db.refresh(membership)
        
        return membership
    
    def remove_member(self, org_id: int, staff_id: int) -> bool:
        """
        Remove a staff member from an organization.
        
        Args:
            org_id: Organization ID
            staff_id: Staff user ID
        
        Returns:
            True if removed, False if not found
        """
        membership = self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id,
            staff_id=staff_id
        ).first()
        
        if not membership:
            return False
        
        self.db.delete(membership)
        self.db.commit()
        
        return True
    
    def get_organization_members(self, org_id: int) -> List[OrganizationMembership]:
        """Get all members of an organization"""
        return self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id
        ).all()
    
    def assign_client_to_org(
        self,
        client_id: int,
        org_id: int,
        assigned_by_staff_id: Optional[int] = None
    ) -> OrganizationClient:
        """
        Assign a client to an organization.
        
        Args:
            client_id: Client ID
            org_id: Organization ID
            assigned_by_staff_id: ID of staff who assigned the client
        
        Returns:
            Created OrganizationClient instance
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            raise ValueError(f"Organization with ID {org_id} not found")
        
        client = self.db.query(Client).filter_by(id=client_id).first()
        if not client:
            raise ValueError(f"Client with ID {client_id} not found")
        
        existing = self.db.query(OrganizationClient).filter_by(
            organization_id=org_id,
            client_id=client_id
        ).first()
        if existing:
            raise ValueError(f"Client is already assigned to this organization")
        
        assignment = OrganizationClient(
            organization_id=org_id,
            client_id=client_id,
            assigned_by_staff_id=assigned_by_staff_id
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment
    
    def unassign_client_from_org(self, client_id: int, org_id: int) -> bool:
        """
        Remove client assignment from an organization.
        
        Args:
            client_id: Client ID
            org_id: Organization ID
        
        Returns:
            True if removed, False if not found
        """
        assignment = self.db.query(OrganizationClient).filter_by(
            organization_id=org_id,
            client_id=client_id
        ).first()
        
        if not assignment:
            return False
        
        self.db.delete(assignment)
        self.db.commit()
        
        return True
    
    def get_organization_clients(
        self,
        org_id: int,
        include_child_orgs: bool = False
    ) -> List[OrganizationClient]:
        """
        Get clients assigned to an organization.
        
        Args:
            org_id: Organization ID
            include_child_orgs: Include clients from child organizations
        
        Returns:
            List of OrganizationClient instances
        """
        if not include_child_orgs:
            return self.db.query(OrganizationClient).filter_by(
                organization_id=org_id
            ).all()
        
        org_ids = [org_id]
        child_orgs = self.get_child_organizations(org_id, recursive=True)
        org_ids.extend([child.id for child in child_orgs])
        
        return self.db.query(OrganizationClient).filter(
            OrganizationClient.organization_id.in_(org_ids)
        ).all()
    
    def transfer_client(
        self,
        client_id: int,
        from_org_id: int,
        to_org_id: int,
        reason: str,
        transferred_by_staff_id: int,
        transfer_type: str = 'referral'
    ) -> InterOrgTransfer:
        """
        Initiate a client transfer between organizations.
        
        Args:
            client_id: Client ID to transfer
            from_org_id: Source organization ID
            to_org_id: Destination organization ID
            reason: Reason for transfer
            transferred_by_staff_id: ID of staff initiating transfer
            transfer_type: Type of transfer (referral/escalation/reassignment)
        
        Returns:
            Created InterOrgTransfer instance
        """
        client = self.db.query(Client).filter_by(id=client_id).first()
        if not client:
            raise ValueError(f"Client with ID {client_id} not found")
        
        from_org = self.get_organization_by_id(from_org_id)
        if not from_org:
            raise ValueError(f"Source organization with ID {from_org_id} not found")
        
        to_org = self.get_organization_by_id(to_org_id)
        if not to_org:
            raise ValueError(f"Destination organization with ID {to_org_id} not found")
        
        client_assignment = self.db.query(OrganizationClient).filter_by(
            organization_id=from_org_id,
            client_id=client_id
        ).first()
        if not client_assignment:
            raise ValueError(f"Client is not assigned to the source organization")
        
        valid_transfer_types = ['referral', 'escalation', 'reassignment']
        if transfer_type not in valid_transfer_types:
            raise ValueError(f"Invalid transfer_type. Must be one of: {valid_transfer_types}")
        
        pending_transfer = self.db.query(InterOrgTransfer).filter_by(
            client_id=client_id,
            status='pending'
        ).first()
        if pending_transfer:
            raise ValueError(f"Client already has a pending transfer request")
        
        transfer = InterOrgTransfer(
            client_id=client_id,
            from_org_id=from_org_id,
            to_org_id=to_org_id,
            transfer_type=transfer_type,
            reason=reason,
            transferred_by_staff_id=transferred_by_staff_id,
            status='pending'
        )
        
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def approve_transfer(
        self,
        transfer_id: int,
        approved_by_staff_id: int,
        approve: bool = True
    ) -> InterOrgTransfer:
        """
        Approve or reject a client transfer.
        
        Args:
            transfer_id: Transfer request ID
            approved_by_staff_id: ID of staff approving/rejecting
            approve: True to approve, False to reject
        
        Returns:
            Updated InterOrgTransfer instance
        """
        transfer = self.db.query(InterOrgTransfer).filter_by(id=transfer_id).first()
        if not transfer:
            raise ValueError(f"Transfer with ID {transfer_id} not found")
        
        if transfer.status != 'pending':
            raise ValueError(f"Transfer is already {transfer.status}")
        
        transfer.approved_by_staff_id = approved_by_staff_id
        transfer.completed_at = datetime.utcnow()
        
        if approve:
            transfer.status = 'approved'
            
            self.db.query(OrganizationClient).filter_by(
                organization_id=transfer.from_org_id,
                client_id=transfer.client_id
            ).delete()
            
            new_assignment = OrganizationClient(
                organization_id=transfer.to_org_id,
                client_id=transfer.client_id,
                assigned_by_staff_id=approved_by_staff_id
            )
            self.db.add(new_assignment)
        else:
            transfer.status = 'rejected'
        
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def get_pending_transfers(
        self,
        org_id: Optional[int] = None,
        direction: str = 'both'
    ) -> List[InterOrgTransfer]:
        """
        Get pending transfer requests.
        
        Args:
            org_id: Filter by organization ID
            direction: 'incoming', 'outgoing', or 'both'
        
        Returns:
            List of pending InterOrgTransfer instances
        """
        query = self.db.query(InterOrgTransfer).filter_by(status='pending')
        
        if org_id:
            if direction == 'incoming':
                query = query.filter_by(to_org_id=org_id)
            elif direction == 'outgoing':
                query = query.filter_by(from_org_id=org_id)
            else:
                query = query.filter(or_(
                    InterOrgTransfer.from_org_id == org_id,
                    InterOrgTransfer.to_org_id == org_id
                ))
        
        return query.order_by(InterOrgTransfer.created_at.desc()).all()
    
    def get_transfer_history(
        self,
        org_id: Optional[int] = None,
        client_id: Optional[int] = None,
        limit: int = 50
    ) -> List[InterOrgTransfer]:
        """
        Get transfer history.
        
        Args:
            org_id: Filter by organization ID
            client_id: Filter by client ID
            limit: Maximum number of records
        
        Returns:
            List of InterOrgTransfer instances
        """
        query = self.db.query(InterOrgTransfer)
        
        if org_id:
            query = query.filter(or_(
                InterOrgTransfer.from_org_id == org_id,
                InterOrgTransfer.to_org_id == org_id
            ))
        
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        return query.order_by(InterOrgTransfer.created_at.desc()).limit(limit).all()
    
    def get_org_stats(self, org_id: int, include_children: bool = False) -> Dict[str, Any]:
        """
        Get organization statistics.
        
        Args:
            org_id: Organization ID
            include_children: Include stats from child organizations
        
        Returns:
            Dictionary with organization statistics
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            return {}
        
        org_ids = [org_id]
        if include_children:
            child_orgs = self.get_child_organizations(org_id, recursive=True)
            org_ids.extend([child.id for child in child_orgs])
        
        client_assignments = self.db.query(OrganizationClient).filter(
            OrganizationClient.organization_id.in_(org_ids)
        ).all()
        client_ids = [a.client_id for a in client_assignments]
        
        total_clients = len(client_ids)
        
        active_clients = 0
        total_cases = 0
        active_cases = 0
        total_revenue = 0.0
        
        if client_ids:
            active_clients = self.db.query(Client).filter(
                Client.id.in_(client_ids),
                Client.status.in_(['active', 'in_progress', 'intake'])
            ).count()
            
            cases = self.db.query(Case).filter(Case.client_id.in_(client_ids)).all()
            total_cases = len(cases)
            active_cases = len([c for c in cases if c.status in ['active', 'in_progress', 'pending']])
            
            settlements = self.db.query(func.sum(Settlement.final_amount)).filter(
                Settlement.client_id.in_(client_ids),
                Settlement.status == 'completed'
            ).scalar()
            total_revenue = float(settlements or 0)
        
        member_count = self.db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id.in_(org_ids)
        ).count()
        
        pending_incoming = self.db.query(InterOrgTransfer).filter_by(
            to_org_id=org_id,
            status='pending'
        ).count()
        
        pending_outgoing = self.db.query(InterOrgTransfer).filter_by(
            from_org_id=org_id,
            status='pending'
        ).count()
        
        return {
            'organization_id': org_id,
            'organization_name': org.name,
            'total_clients': total_clients,
            'active_clients': active_clients,
            'total_cases': total_cases,
            'active_cases': active_cases,
            'total_revenue': total_revenue,
            'member_count': member_count,
            'child_org_count': len(org_ids) - 1 if include_children else 0,
            'pending_transfers_in': pending_incoming,
            'pending_transfers_out': pending_outgoing
        }
    
    def get_org_revenue_report(
        self,
        org_id: int,
        period: str = 'month',
        include_children: bool = True
    ) -> Dict[str, Any]:
        """
        Get revenue report for an organization.
        
        Args:
            org_id: Organization ID
            period: Report period ('week', 'month', 'quarter', 'year')
            include_children: Include revenue from child organizations
        
        Returns:
            Dictionary with revenue report data
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            return {}
        
        period_days = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365}
        days = period_days.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        org_ids = [org_id]
        if include_children:
            child_orgs = self.get_child_organizations(org_id, recursive=True)
            org_ids.extend([child.id for child in child_orgs])
        
        client_assignments = self.db.query(OrganizationClient).filter(
            OrganizationClient.organization_id.in_(org_ids)
        ).all()
        client_ids = [a.client_id for a in client_assignments]
        
        total_revenue = 0.0
        revenue_by_type = {}
        revenue_by_month = {}
        
        if client_ids:
            settlements = self.db.query(Settlement).filter(
                Settlement.client_id.in_(client_ids),
                Settlement.status == 'completed',
                Settlement.created_at >= start_date
            ).all()
            
            for settlement in settlements:
                total_revenue += float(settlement.final_amount or 0)
                
                settlement_type = 'settlement'
                revenue_by_type[settlement_type] = revenue_by_type.get(settlement_type, 0) + float(settlement.final_amount or 0)
                
                if settlement.created_at:
                    month_key = settlement.created_at.strftime('%Y-%m')
                    revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + float(settlement.final_amount or 0)
        
        return {
            'organization_id': org_id,
            'organization_name': org.name,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': datetime.utcnow().isoformat(),
            'total_revenue': total_revenue,
            'revenue_by_type': revenue_by_type,
            'revenue_by_month': dict(sorted(revenue_by_month.items())),
            'included_organizations': org_ids
        }
    
    def calculate_revenue_share(
        self,
        org_id: int,
        period: str = 'month'
    ) -> Dict[str, Any]:
        """
        Calculate revenue share for an organization based on hierarchy.
        
        Args:
            org_id: Organization ID
            period: Calculation period ('week', 'month', 'quarter', 'year')
        
        Returns:
            Dictionary with revenue share calculations
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            return {}
        
        revenue_report = self.get_org_revenue_report(org_id, period, include_children=False)
        org_revenue = revenue_report.get('total_revenue', 0)
        
        shares = []
        current = org
        remaining_revenue = org_revenue
        
        while current.parent:
            parent = current.parent
            share_percent = current.revenue_share_percent or 0
            share_amount = remaining_revenue * (share_percent / 100)
            
            shares.append({
                'organization_id': parent.id,
                'organization_name': parent.name,
                'share_percent': share_percent,
                'share_amount': share_amount
            })
            
            remaining_revenue -= share_amount
            current = parent
        
        return {
            'organization_id': org_id,
            'organization_name': org.name,
            'period': period,
            'total_revenue': org_revenue,
            'net_revenue': remaining_revenue,
            'revenue_shares': shares,
            'total_shared': org_revenue - remaining_revenue
        }
    
    def get_user_organizations(self, staff_id: int) -> List[Dict[str, Any]]:
        """
        Get all organizations a user belongs to.
        
        Args:
            staff_id: Staff user ID
        
        Returns:
            List of organization dictionaries with membership info
        """
        memberships = self.db.query(OrganizationMembership).filter_by(
            staff_id=staff_id
        ).all()
        
        result = []
        for membership in memberships:
            org = membership.organization
            if org and org.is_active:
                org_data = org.to_dict()
                org_data['membership'] = membership.to_dict()
                result.append(org_data)
        
        return result
    
    def get_accessible_organizations(self, staff_id: int) -> List[FranchiseOrganization]:
        """
        Get all organizations a user can access (their orgs plus children).
        
        Args:
            staff_id: Staff user ID
        
        Returns:
            List of accessible FranchiseOrganization instances
        """
        direct_memberships = self.db.query(OrganizationMembership).filter_by(
            staff_id=staff_id
        ).all()
        
        accessible_orgs = set()
        
        for membership in direct_memberships:
            if membership.organization and membership.organization.is_active:
                accessible_orgs.add(membership.organization)
                
                if membership.role in ['owner', 'manager']:
                    children = self.get_child_organizations(membership.organization_id, recursive=True)
                    accessible_orgs.update(children)
        
        return list(accessible_orgs)
    
    def check_org_permission(
        self,
        staff_id: int,
        org_id: int,
        permission: str
    ) -> bool:
        """
        Check if a user has a specific permission for an organization.
        
        Args:
            staff_id: Staff user ID
            org_id: Organization ID
            permission: Permission to check
        
        Returns:
            True if user has permission, False otherwise
        """
        membership = self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id,
            staff_id=staff_id
        ).first()
        
        if membership:
            return membership.has_permission(permission)
        
        staff = self.db.query(Staff).filter_by(id=staff_id).first()
        if staff and staff.role == 'admin':
            return True
        
        parent_memberships = self.db.query(OrganizationMembership).filter_by(
            staff_id=staff_id
        ).all()
        
        for parent_membership in parent_memberships:
            if parent_membership.role in ['owner', 'manager']:
                children = self.get_child_organizations(parent_membership.organization_id, recursive=True)
                if any(child.id == org_id for child in children):
                    return parent_membership.has_permission(permission)
        
        return False
    
    def get_org_permission_context(self, staff_id: int, org_id: int) -> Dict[str, Any]:
        """
        Get full permission context for a user in an organization.
        
        Args:
            staff_id: Staff user ID
            org_id: Organization ID
        
        Returns:
            Dictionary with permission details
        """
        membership = self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id,
            staff_id=staff_id
        ).first()
        
        if membership:
            role_config = FRANCHISE_MEMBER_ROLES.get(membership.role, {})
            return {
                'has_access': True,
                'is_direct_member': True,
                'role': membership.role,
                'role_name': role_config.get('name', membership.role),
                'permissions': role_config.get('permissions', []) + (membership.permissions or []),
                'is_primary': membership.is_primary
            }
        
        staff = self.db.query(Staff).filter_by(id=staff_id).first()
        if staff and staff.role == 'admin':
            return {
                'has_access': True,
                'is_direct_member': False,
                'role': 'admin',
                'role_name': 'System Administrator',
                'permissions': ['*'],
                'is_primary': False
            }
        
        parent_memberships = self.db.query(OrganizationMembership).filter_by(
            staff_id=staff_id
        ).all()
        
        for parent_membership in parent_memberships:
            if parent_membership.role in ['owner', 'manager']:
                children = self.get_child_organizations(parent_membership.organization_id, recursive=True)
                if any(child.id == org_id for child in children):
                    role_config = FRANCHISE_MEMBER_ROLES.get(parent_membership.role, {})
                    return {
                        'has_access': True,
                        'is_direct_member': False,
                        'inherited_from_org_id': parent_membership.organization_id,
                        'role': parent_membership.role,
                        'role_name': role_config.get('name', parent_membership.role),
                        'permissions': role_config.get('permissions', []),
                        'is_primary': False
                    }
        
        return {
            'has_access': False,
            'is_direct_member': False,
            'role': None,
            'permissions': []
        }
    
    def get_consolidated_report(self, org_id: int) -> Dict[str, Any]:
        """
        Get consolidated report aggregating data from org and all child organizations.
        
        Args:
            org_id: Organization ID
        
        Returns:
            Dictionary with consolidated statistics across all child orgs
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            return {}
        
        org_ids = [org_id]
        child_orgs = self.get_child_organizations(org_id, recursive=True)
        org_ids.extend([child.id for child in child_orgs])
        
        client_assignments = self.db.query(OrganizationClient).filter(
            OrganizationClient.organization_id.in_(org_ids)
        ).all()
        client_ids = [a.client_id for a in client_assignments]
        
        total_clients = len(client_ids)
        active_clients = 0
        total_cases = 0
        active_cases = 0
        completed_cases = 0
        total_revenue = 0.0
        total_settlements = 0
        avg_settlement_amount = 0.0
        
        if client_ids:
            active_clients = self.db.query(Client).filter(
                Client.id.in_(client_ids),
                Client.status.in_(['active', 'in_progress', 'intake'])
            ).count()
            
            cases = self.db.query(Case).filter(Case.client_id.in_(client_ids)).all()
            total_cases = len(cases)
            active_cases = len([c for c in cases if c.status in ['active', 'in_progress', 'pending']])
            completed_cases = len([c for c in cases if c.status in ['completed', 'settled', 'closed']])
            
            settlements = self.db.query(Settlement).filter(
                Settlement.client_id.in_(client_ids),
                Settlement.status == 'completed'
            ).all()
            total_settlements = len(settlements)
            total_revenue = sum(float(s.final_amount or 0) for s in settlements)
            if total_settlements > 0:
                avg_settlement_amount = total_revenue / total_settlements
        
        member_count = self.db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id.in_(org_ids)
        ).count()
        
        org_breakdown = []
        for oid in org_ids:
            org_detail = self.get_organization_by_id(oid)
            org_stats = self.get_org_stats(oid, include_children=False)
            if org_detail and org_stats:
                org_breakdown.append({
                    'organization_id': oid,
                    'organization_name': org_detail.name,
                    'org_type': org_detail.org_type,
                    **org_stats
                })
        
        return {
            'organization_id': org_id,
            'organization_name': org.name,
            'report_type': 'consolidated',
            'included_organization_count': len(org_ids),
            'summary': {
                'total_clients': total_clients,
                'active_clients': active_clients,
                'total_cases': total_cases,
                'active_cases': active_cases,
                'completed_cases': completed_cases,
                'total_revenue': total_revenue,
                'total_settlements': total_settlements,
                'avg_settlement_amount': avg_settlement_amount,
                'total_staff': member_count
            },
            'organization_breakdown': org_breakdown,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def check_org_limits(self, org_id: int) -> Dict[str, Any]:
        """
        Check if organization has reached user/client limits.
        
        Args:
            org_id: Organization ID
        
        Returns:
            Dictionary with limit check results
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            return {'error': 'Organization not found'}
        
        current_users = self.db.query(OrganizationMembership).filter_by(
            organization_id=org_id
        ).count()
        
        current_clients = self.db.query(OrganizationClient).filter_by(
            organization_id=org_id
        ).count()
        
        max_users = org.max_users or 999999
        max_clients = org.max_clients or 999999
        
        users_remaining = max_users - current_users
        clients_remaining = max_clients - current_clients
        
        users_at_limit = current_users >= max_users
        clients_at_limit = current_clients >= max_clients
        
        users_warning = current_users >= (max_users * 0.8)
        clients_warning = current_clients >= (max_clients * 0.8)
        
        return {
            'organization_id': org_id,
            'organization_name': org.name,
            'subscription_tier': org.subscription_tier or 'basic',
            'users': {
                'current': current_users,
                'max': max_users,
                'remaining': max(0, users_remaining),
                'at_limit': users_at_limit,
                'warning': users_warning,
                'usage_percent': round((current_users / max_users) * 100, 1) if max_users > 0 else 0
            },
            'clients': {
                'current': current_clients,
                'max': max_clients,
                'remaining': max(0, clients_remaining),
                'at_limit': clients_at_limit,
                'warning': clients_warning,
                'usage_percent': round((current_clients / max_clients) * 100, 1) if max_clients > 0 else 0
            },
            'can_add_users': not users_at_limit,
            'can_add_clients': not clients_at_limit,
            'has_warnings': users_warning or clients_warning,
            'license_number': org.license_number,
            'billing_contact_email': org.billing_contact_email
        }


def get_org_filter(db, staff_user) -> List[int]:
    """
    Get list of organization IDs that a staff user has access to for query filtering.
    
    Args:
        db: Database session
        staff_user: Staff model instance
    
    Returns:
        List of accessible organization IDs, or None if user has access to all
    """
    from database import Staff, OrganizationMembership, FranchiseOrganization
    
    if staff_user.role == 'admin':
        return None
    
    service = FranchiseService(db)
    accessible_orgs = service.get_accessible_organizations(staff_user.id)
    
    if not accessible_orgs:
        primary_membership = db.query(OrganizationMembership).filter_by(
            staff_id=staff_user.id,
            is_primary=True
        ).first()
        
        if primary_membership:
            return [primary_membership.organization_id]
        
        any_membership = db.query(OrganizationMembership).filter_by(
            staff_id=staff_user.id
        ).first()
        
        if any_membership:
            return [any_membership.organization_id]
        
        return []
    
    return [org.id for org in accessible_orgs]


def get_clients_for_org(db, org_ids: Optional[List[int]]) -> List[int]:
    """
    Get list of client IDs belonging to specified organizations.
    
    Args:
        db: Database session
        org_ids: List of organization IDs, or None for all clients
    
    Returns:
        List of client IDs
    """
    from database import Client, OrganizationClient
    
    if org_ids is None:
        return None
    
    if not org_ids:
        return []
    
    client_assignments = db.query(OrganizationClient.client_id).filter(
        OrganizationClient.organization_id.in_(org_ids)
    ).all()
    
    assigned_ids = [ca.client_id for ca in client_assignments]
    
    unassigned = db.query(Client.id).filter(
        Client.organization_id.is_(None)
    ).all()
    unassigned_ids = [c.id for c in unassigned]
    
    all_ids = list(set(assigned_ids) | set(unassigned_ids))
    
    return all_ids if all_ids else None
