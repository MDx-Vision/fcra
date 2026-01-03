"""
Revenue Metrics Service

Provides comprehensive revenue analytics including:
- MRR/ARR (Monthly/Annual Recurring Revenue)
- Total revenue and growth
- Churn rate and retention
- LTV (Lifetime Value)
- Revenue by source (plans, payment methods)
- Commission payouts
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import func, and_, or_, extract
from sqlalchemy.orm import Session

from database import (
    Client, ClientSubscription, BillingPlan,
    Commission, Affiliate
)


class RevenueMetricsService:
    """Service for calculating and tracking revenue metrics."""

    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session

    # =========================================================================
    # Core Revenue Metrics
    # =========================================================================

    def get_total_revenue(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Get total revenue for a period.

        Args:
            start_date: Start of period (default: all time)
            end_date: End of period (default: now)

        Returns:
            Dict with total revenue, count, average
        """
        query = self.db.query(
            func.sum(Client.total_paid).label('total'),
            func.count(Client.id).label('count'),
            func.avg(Client.total_paid).label('average')
        ).filter(
            Client.total_paid > 0
        )

        if start_date:
            query = query.filter(Client.payment_received_at >= start_date)
        if end_date:
            query = query.filter(Client.payment_received_at <= end_date)

        result = query.first()

        return {
            'total_cents': result.total or 0,
            'total_dollars': (result.total or 0) / 100,
            'paying_clients': result.count or 0,
            'average_cents': int(result.average or 0),
            'average_dollars': (result.average or 0) / 100
        }

    def get_revenue_by_period(self, period: str = 'month', limit: int = 12) -> List[Dict[str, Any]]:
        """
        Get revenue broken down by time period.

        Args:
            period: 'day', 'week', 'month', 'year'
            limit: Number of periods to return

        Returns:
            List of period revenue data
        """
        if period == 'day':
            date_trunc = func.date_trunc('day', Client.payment_received_at)
        elif period == 'week':
            date_trunc = func.date_trunc('week', Client.payment_received_at)
        elif period == 'year':
            date_trunc = func.date_trunc('year', Client.payment_received_at)
        else:  # month
            date_trunc = func.date_trunc('month', Client.payment_received_at)

        results = self.db.query(
            date_trunc.label('period'),
            func.sum(Client.total_paid).label('total'),
            func.count(Client.id).label('count')
        ).filter(
            Client.total_paid > 0,
            Client.payment_received_at.isnot(None)
        ).group_by(
            date_trunc
        ).order_by(
            date_trunc.desc()
        ).limit(limit).all()

        return [{
            'period': r.period.isoformat() if r.period else None,
            'total_cents': r.total or 0,
            'total_dollars': (r.total or 0) / 100,
            'client_count': r.count or 0
        } for r in reversed(results)]

    def get_revenue_by_payment_method(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get revenue breakdown by payment method."""
        query = self.db.query(
            Client.payment_method,
            func.sum(Client.total_paid).label('total'),
            func.count(Client.id).label('count')
        ).filter(
            Client.total_paid > 0
        )

        if start_date:
            query = query.filter(Client.payment_received_at >= start_date)
        if end_date:
            query = query.filter(Client.payment_received_at <= end_date)

        results = query.group_by(Client.payment_method).all()

        breakdown = {}
        for r in results:
            method = r.payment_method or 'unknown'
            breakdown[method] = {
                'total_cents': r.total or 0,
                'total_dollars': (r.total or 0) / 100,
                'count': r.count or 0
            }

        return breakdown

    def get_revenue_by_plan(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get revenue breakdown by signup plan/tier."""
        query = self.db.query(
            Client.signup_plan,
            func.sum(Client.total_paid).label('total'),
            func.count(Client.id).label('count')
        ).filter(
            Client.total_paid > 0
        )

        if start_date:
            query = query.filter(Client.payment_received_at >= start_date)
        if end_date:
            query = query.filter(Client.payment_received_at <= end_date)

        results = query.group_by(Client.signup_plan).all()

        breakdown = {}
        for r in results:
            plan = r.signup_plan or 'unknown'
            breakdown[plan] = {
                'total_cents': r.total or 0,
                'total_dollars': (r.total or 0) / 100,
                'count': r.count or 0
            }

        return breakdown

    # =========================================================================
    # MRR / ARR (Recurring Revenue)
    # =========================================================================

    def get_mrr(self) -> Dict[str, Any]:
        """
        Calculate Monthly Recurring Revenue from active subscriptions.

        Returns:
            Dict with MRR, subscriber count, ARPU
        """
        # Get active subscriptions
        results = self.db.query(
            func.sum(BillingPlan.price_cents).label('mrr'),
            func.count(ClientSubscription.id).label('count')
        ).join(
            BillingPlan, ClientSubscription.plan_id == BillingPlan.id
        ).filter(
            ClientSubscription.status == 'active',
            BillingPlan.billing_interval == 'month'
        ).first()

        mrr_cents = results.mrr or 0
        subscriber_count = results.count or 0
        arpu = mrr_cents / subscriber_count if subscriber_count > 0 else 0

        return {
            'mrr_cents': mrr_cents,
            'mrr_dollars': mrr_cents / 100,
            'arr_cents': mrr_cents * 12,
            'arr_dollars': (mrr_cents * 12) / 100,
            'subscriber_count': subscriber_count,
            'arpu_cents': int(arpu),
            'arpu_dollars': arpu / 100
        }

    def get_mrr_growth(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Get MRR growth over time.

        Args:
            months: Number of months to analyze

        Returns:
            List of monthly MRR data
        """
        data = []
        now = datetime.utcnow()

        for i in range(months - 1, -1, -1):
            # Calculate date for this month
            target_date = now - timedelta(days=i * 30)
            month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Count active subscriptions as of that date
            # This is simplified - in production you'd track subscription history
            count = self.db.query(func.count(ClientSubscription.id)).filter(
                ClientSubscription.status == 'active',
                ClientSubscription.created_at <= month_start
            ).scalar() or 0

            # Estimate MRR based on average plan price
            avg_plan_price = self.db.query(func.avg(BillingPlan.price_cents)).filter(
                BillingPlan.billing_interval == 'month'
            ).scalar() or 0

            estimated_mrr = count * avg_plan_price

            data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_label': month_start.strftime('%b %Y'),
                'mrr_cents': int(estimated_mrr),
                'mrr_dollars': estimated_mrr / 100,
                'subscriber_count': count
            })

        return data

    # =========================================================================
    # Churn & Retention
    # =========================================================================

    def get_churn_rate(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate churn rate for a period.

        Args:
            period_days: Number of days to analyze

        Returns:
            Dict with churn rate, churned count, retained count
        """
        period_start = datetime.utcnow() - timedelta(days=period_days)

        # Clients who were active at start of period
        active_at_start = self.db.query(func.count(Client.id)).filter(
            Client.status == 'active',
            Client.created_at < period_start,
            Client.payment_status == 'paid'
        ).scalar() or 0

        # Clients who cancelled during period
        churned = self.db.query(func.count(Client.id)).filter(
            Client.status == 'cancelled',
            Client.updated_at >= period_start,
            Client.payment_status == 'paid'
        ).scalar() or 0

        churn_rate = (churned / active_at_start * 100) if active_at_start > 0 else 0

        return {
            'period_days': period_days,
            'active_at_start': active_at_start,
            'churned': churned,
            'retained': active_at_start - churned,
            'churn_rate': round(churn_rate, 2),
            'retention_rate': round(100 - churn_rate, 2)
        }

    def get_client_retention_cohorts(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Get retention by monthly cohorts.

        Returns:
            List of cohort retention data
        """
        cohorts = []
        now = datetime.utcnow()

        for i in range(months - 1, -1, -1):
            month_start = (now - timedelta(days=i * 30)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            # Clients acquired in this month
            acquired = self.db.query(func.count(Client.id)).filter(
                Client.created_at >= month_start,
                Client.created_at < month_end,
                Client.payment_status == 'paid'
            ).scalar() or 0

            # Of those, how many are still active
            retained = self.db.query(func.count(Client.id)).filter(
                Client.created_at >= month_start,
                Client.created_at < month_end,
                Client.payment_status == 'paid',
                Client.status == 'active'
            ).scalar() or 0

            retention_rate = (retained / acquired * 100) if acquired > 0 else 0

            cohorts.append({
                'cohort': month_start.strftime('%Y-%m'),
                'cohort_label': month_start.strftime('%b %Y'),
                'acquired': acquired,
                'retained': retained,
                'churned': acquired - retained,
                'retention_rate': round(retention_rate, 2)
            })

        return cohorts

    # =========================================================================
    # LTV (Lifetime Value)
    # =========================================================================

    def get_ltv(self) -> Dict[str, Any]:
        """
        Calculate Customer Lifetime Value.

        Returns:
            Dict with LTV, average revenue, average lifespan
        """
        # Average revenue per paying customer
        avg_result = self.db.query(
            func.avg(Client.total_paid).label('avg_revenue'),
            func.count(Client.id).label('count')
        ).filter(
            Client.total_paid > 0
        ).first()

        avg_revenue = avg_result.avg_revenue or 0
        paying_count = avg_result.count or 0

        # Average customer lifespan (in months)
        # Calculate as average time between signup and either cancellation or now
        active_clients = self.db.query(
            func.avg(
                extract('epoch', func.coalesce(
                    Client.updated_at,
                    datetime.utcnow()
                ) - Client.created_at) / (30 * 24 * 60 * 60)
            ).label('avg_months')
        ).filter(
            Client.payment_status == 'paid'
        ).first()

        avg_lifespan_months = active_clients.avg_months or 1

        # Simple LTV = Average Revenue * Average Lifespan (simplified)
        # More accurate would use: ARPU / Churn Rate
        ltv = avg_revenue

        return {
            'ltv_cents': int(ltv),
            'ltv_dollars': ltv / 100,
            'avg_revenue_cents': int(avg_revenue),
            'avg_revenue_dollars': avg_revenue / 100,
            'avg_lifespan_months': round(avg_lifespan_months, 1),
            'paying_customers': paying_count
        }

    # =========================================================================
    # Affiliate / Commission Metrics
    # =========================================================================

    def get_commission_metrics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get commission and affiliate metrics."""
        query = self.db.query(
            func.sum(Commission.commission_amount).label('total_commissions'),
            func.sum(Commission.trigger_amount).label('total_triggered'),
            func.count(Commission.id).label('commission_count')
        )

        if start_date:
            query = query.filter(Commission.created_at >= start_date)
        if end_date:
            query = query.filter(Commission.created_at <= end_date)

        result = query.first()

        # Paid vs pending
        paid = self.db.query(func.sum(Commission.commission_amount)).filter(
            Commission.status == 'paid'
        )
        if start_date:
            paid = paid.filter(Commission.created_at >= start_date)
        if end_date:
            paid = paid.filter(Commission.created_at <= end_date)
        paid_amount = paid.scalar() or 0

        pending = self.db.query(func.sum(Commission.commission_amount)).filter(
            Commission.status == 'pending'
        )
        if start_date:
            pending = pending.filter(Commission.created_at >= start_date)
        if end_date:
            pending = pending.filter(Commission.created_at <= end_date)
        pending_amount = pending.scalar() or 0

        # Active affiliates
        active_affiliates = self.db.query(func.count(Affiliate.id)).filter(
            Affiliate.status == 'active'
        ).scalar() or 0

        return {
            'total_commissions': result.total_commissions or 0,
            'total_triggered_revenue': result.total_triggered or 0,
            'commission_count': result.commission_count or 0,
            'paid_commissions': paid_amount,
            'pending_commissions': pending_amount,
            'active_affiliates': active_affiliates
        }

    def get_top_affiliates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing affiliates."""
        results = self.db.query(
            Affiliate.id,
            Affiliate.name,
            Affiliate.email,
            Affiliate.total_referrals,
            Affiliate.total_earnings,
            Affiliate.pending_earnings
        ).filter(
            Affiliate.status == 'active'
        ).order_by(
            Affiliate.total_earnings.desc()
        ).limit(limit).all()

        return [{
            'id': r.id,
            'name': r.name or r.email,
            'email': r.email,
            'total_referrals': r.total_referrals or 0,
            'total_earnings': r.total_earnings or 0,
            'pending_earnings': r.pending_earnings or 0
        } for r in results]

    # =========================================================================
    # Dashboard Summary
    # =========================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive revenue dashboard summary.

        Returns:
            Dict with all key metrics for the dashboard
        """
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        prev_month_start = now - timedelta(days=60)
        prev_month_end = month_ago

        # Current period revenue
        current_revenue = self.get_total_revenue(month_ago, now)
        prev_revenue = self.get_total_revenue(prev_month_start, prev_month_end)

        # Calculate growth
        revenue_growth = 0
        if prev_revenue['total_cents'] > 0:
            revenue_growth = ((current_revenue['total_cents'] - prev_revenue['total_cents']) / prev_revenue['total_cents']) * 100

        # MRR
        mrr = self.get_mrr()

        # LTV
        ltv = self.get_ltv()

        # Churn
        churn = self.get_churn_rate(30)

        # Commission metrics
        commissions = self.get_commission_metrics(month_ago, now)

        # New clients this month
        new_clients = self.db.query(func.count(Client.id)).filter(
            Client.created_at >= month_ago
        ).scalar() or 0

        # Paid clients this month
        new_paid = self.db.query(func.count(Client.id)).filter(
            Client.payment_received_at >= month_ago,
            Client.payment_status == 'paid'
        ).scalar() or 0

        return {
            'period': {
                'start': month_ago.isoformat(),
                'end': now.isoformat(),
                'days': 30
            },
            'revenue': {
                'current_period': current_revenue,
                'previous_period': prev_revenue,
                'growth_percent': round(revenue_growth, 2)
            },
            'mrr': mrr,
            'ltv': ltv,
            'churn': churn,
            'clients': {
                'new_signups': new_clients,
                'new_paid': new_paid,
                'conversion_rate': round((new_paid / new_clients * 100) if new_clients > 0 else 0, 2)
            },
            'affiliates': {
                'total_commissions': commissions['total_commissions'],
                'pending_commissions': commissions['pending_commissions'],
                'active_affiliates': commissions['active_affiliates']
            }
        }

    def get_revenue_chart_data(self, period: str = 'month', limit: int = 12) -> Dict[str, Any]:
        """
        Get data formatted for Chart.js.

        Returns:
            Dict with labels and datasets for charts
        """
        revenue_data = self.get_revenue_by_period(period, limit)

        labels = [r['period'][:7] if r['period'] else 'Unknown' for r in revenue_data]
        revenue_values = [r['total_dollars'] for r in revenue_data]
        client_counts = [r['client_count'] for r in revenue_data]

        return {
            'labels': labels,
            'datasets': {
                'revenue': revenue_values,
                'clients': client_counts
            }
        }

    # =========================================================================
    # Export
    # =========================================================================

    def export_revenue_data(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Export detailed revenue data for CSV/Excel.

        Returns:
            List of payment records
        """
        query = self.db.query(
            Client.id,
            Client.first_name,
            Client.last_name,
            Client.email,
            Client.signup_plan,
            Client.total_paid,
            Client.payment_status,
            Client.payment_method,
            Client.payment_received_at,
            Client.created_at
        ).filter(
            Client.total_paid > 0
        )

        if start_date:
            query = query.filter(Client.payment_received_at >= start_date)
        if end_date:
            query = query.filter(Client.payment_received_at <= end_date)

        results = query.order_by(Client.payment_received_at.desc()).all()

        return [{
            'client_id': r.id,
            'name': f"{r.first_name or ''} {r.last_name or ''}".strip(),
            'email': r.email,
            'plan': r.signup_plan,
            'amount_cents': r.total_paid,
            'amount_dollars': r.total_paid / 100,
            'status': r.payment_status,
            'method': r.payment_method,
            'payment_date': r.payment_received_at.isoformat() if r.payment_received_at else None,
            'signup_date': r.created_at.isoformat() if r.created_at else None
        } for r in results]


# Factory function
def get_revenue_metrics_service(db_session: Session) -> RevenueMetricsService:
    """Create a RevenueMetricsService instance."""
    return RevenueMetricsService(db_session)
