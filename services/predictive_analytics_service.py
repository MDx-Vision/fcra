"""
Predictive Analytics Service
Revenue forecasting, client LTV, and business intelligence
"""
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import func, and_, or_, extract
from sqlalchemy.orm import Session
import statistics
import math

from database import (
    get_db, Client, Settlement, Case, Analysis, CaseScore, Violation,
    RevenueForecast, ClientLifetimeValue, CaseOutcome
)


class PredictiveAnalyticsService:
    """Business intelligence and predictive analytics for FCRA platform"""
    
    def __init__(self):
        self.default_acquisition_cost = 150.0
        self.avg_case_fee = 500.0
        self.avg_settlement_fee_percent = 0.33
    
    def forecast_revenue(self, months_ahead: int = 3) -> Dict[str, Any]:
        """
        Predict future revenue using moving averages and trend analysis
        
        Args:
            months_ahead: Number of months to forecast
            
        Returns:
            Dict with forecasts, confidence intervals, and factors
        """
        db = get_db()
        try:
            now = datetime.utcnow()
            
            monthly_revenue = []
            for i in range(12, 0, -1):
                month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
                
                signup_revenue = db.query(func.sum(Client.signup_amount)).filter(
                    Client.payment_status == 'paid',
                    Client.payment_received_at >= month_start,
                    Client.payment_received_at <= month_end
                ).scalar() or 0
                
                settlement_revenue = db.query(func.sum(Settlement.contingency_earned)).filter(
                    Settlement.payment_received == True,
                    Settlement.payment_date >= month_start,
                    Settlement.payment_date <= month_end
                ).scalar() or 0
                
                total = (signup_revenue / 100 if signup_revenue else 0) + (settlement_revenue or 0)
                monthly_revenue.append({
                    'month': month_start.strftime('%Y-%m'),
                    'revenue': total,
                    'signup_revenue': signup_revenue / 100 if signup_revenue else 0,
                    'settlement_revenue': settlement_revenue or 0
                })
            
            if len(monthly_revenue) < 3:
                avg_revenue = 5000.0
            else:
                revenues = [m['revenue'] for m in monthly_revenue[-6:]]
                avg_revenue = statistics.mean(revenues) if revenues else 5000.0
            
            if len(monthly_revenue) >= 6:
                recent_avg = statistics.mean([m['revenue'] for m in monthly_revenue[-3:]])
                older_avg = statistics.mean([m['revenue'] for m in monthly_revenue[-6:-3]])
                trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0.05
            else:
                trend = 0.05
            
            trend = max(-0.20, min(0.30, trend))
            
            forecasts = []
            for i in range(1, months_ahead + 1):
                forecast_date = (now + relativedelta(months=i)).replace(day=1)
                growth_factor = 1 + (trend * i * 0.5)
                predicted = avg_revenue * growth_factor
                
                std_dev = statistics.stdev([m['revenue'] for m in monthly_revenue[-6:]]) if len(monthly_revenue) >= 6 else avg_revenue * 0.2
                confidence_low = max(0, predicted - (1.96 * std_dev))
                confidence_high = predicted + (1.96 * std_dev)
                
                pipeline_clients = db.query(Client).filter(
                    Client.status.in_(['active', 'signup']),
                    Client.payment_status == 'pending'
                ).count()
                
                pending_settlements = db.query(func.sum(Settlement.target_amount)).filter(
                    Settlement.status.in_(['negotiating', 'demand_sent'])
                ).scalar() or 0
                
                forecast = RevenueForecast(
                    forecast_date=forecast_date.date(),
                    forecast_period='monthly',
                    predicted_revenue=predicted,
                    confidence_interval_low=confidence_low,
                    confidence_interval_high=confidence_high,
                    factors={
                        'trend': trend,
                        'avg_base': avg_revenue,
                        'pipeline_clients': pipeline_clients,
                        'pending_settlements': float(pending_settlements or 0)
                    }
                )
                db.add(forecast)
                
                forecasts.append({
                    'period': forecast_date.strftime('%Y-%m'),
                    'predicted_revenue': round(predicted, 2),
                    'confidence_interval_low': round(confidence_low, 2),
                    'confidence_interval_high': round(confidence_high, 2),
                    'trend_factor': round(trend * 100, 1)
                })
            
            db.commit()
            
            return {
                'success': True,
                'forecasts': forecasts,
                'historical': monthly_revenue[-6:],
                'trend_direction': 'up' if trend > 0.02 else ('down' if trend < -0.02 else 'stable'),
                'trend_percent': round(trend * 100, 1),
                'avg_monthly_revenue': round(avg_revenue, 2)
            }
            
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def calculate_client_ltv(self, client_id: int) -> Dict[str, Any]:
        """
        Calculate lifetime value estimation for a client
        
        Args:
            client_id: Client database ID
            
        Returns:
            Dict with LTV estimate and breakdown
        """
        db = get_db()
        try:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            initial_fee = (client.signup_amount or 0) / 100
            
            case = db.query(Case).filter_by(client_id=client_id).order_by(Case.id.desc()).first()
            analysis = db.query(Analysis).filter_by(client_id=client_id).order_by(Analysis.id.desc()).first()
            case_score = db.query(CaseScore).filter_by(client_id=client_id).order_by(CaseScore.id.desc()).first()
            
            if case_score:
                prob_success = min(0.95, max(0.1, case_score.settlement_probability or 0.5))
            else:
                violation_count = db.query(Violation).filter_by(client_id=client_id).count()
                prob_success = min(0.85, 0.3 + (violation_count * 0.05))
            
            settlement = db.query(Settlement).filter_by(case_id=case.id if case else 0).first()
            if settlement and settlement.target_amount:
                expected_settlement = float(settlement.target_amount)
            else:
                damages = db.query(func.sum(Violation.statutory_damages_max)).filter_by(
                    client_id=client_id
                ).scalar() or 5000.0
                expected_settlement = float(damages) * 0.6
            
            expected_fees = expected_settlement * self.avg_settlement_fee_percent
            
            if client.referred_by_affiliate_id:
                acquisition_cost = self.default_acquisition_cost * 1.1
            else:
                acquisition_cost = self.default_acquisition_cost
            
            ltv = initial_fee + (expected_fees * prob_success) - acquisition_cost
            
            churn_risk = self._calculate_churn_risk_internal(db, client)
            
            ltv_record = ClientLifetimeValue(
                client_id=client_id,
                ltv_estimate=ltv,
                probability_of_success=prob_success,
                expected_settlement=expected_settlement,
                expected_fees=expected_fees,
                acquisition_cost=acquisition_cost,
                churn_risk=churn_risk,
                risk_factors={
                    'dispute_round': client.current_dispute_round or 0,
                    'days_since_signup': (datetime.utcnow() - client.created_at).days if client.created_at else 0,
                    'payment_status': client.payment_status
                }
            )
            db.add(ltv_record)
            db.commit()
            
            return {
                'success': True,
                'client_id': client_id,
                'client_name': client.name,
                'ltv_estimate': round(ltv, 2),
                'probability_of_success': round(prob_success, 2),
                'expected_settlement': round(expected_settlement, 2),
                'expected_fees': round(expected_fees, 2),
                'initial_fee': round(initial_fee, 2),
                'acquisition_cost': round(acquisition_cost, 2),
                'churn_risk': round(churn_risk, 2),
                'ltv_tier': 'high' if ltv > 2000 else ('medium' if ltv > 500 else 'low')
            }
            
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def predict_case_timeline(self, client_id: int) -> Dict[str, Any]:
        """
        Predict expected case resolution date
        
        Args:
            client_id: Client database ID
            
        Returns:
            Dict with expected timeline and milestones
        """
        db = get_db()
        try:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            current_round = client.current_dispute_round or 1
            
            avg_days_per_round = 45
            
            outcomes = db.query(CaseOutcome).filter(
                CaseOutcome.time_to_resolution_days > 0
            ).limit(50).all()
            
            if outcomes:
                avg_resolution = statistics.mean([o.time_to_resolution_days for o in outcomes])
            else:
                avg_resolution = 120
            
            rounds_remaining = max(1, 4 - current_round)
            days_remaining = rounds_remaining * avg_days_per_round
            
            case_score = db.query(CaseScore).filter_by(client_id=client_id).first()
            if case_score and case_score.total_score:
                if case_score.total_score >= 8:
                    days_remaining = int(days_remaining * 0.7)
                elif case_score.total_score <= 4:
                    days_remaining = int(days_remaining * 1.3)
            
            expected_resolution = datetime.utcnow() + timedelta(days=days_remaining)
            
            milestones = []
            current_date = datetime.utcnow()
            for round_num in range(current_round, 5):
                round_date = current_date + timedelta(days=avg_days_per_round * (round_num - current_round))
                milestones.append({
                    'round': round_num,
                    'expected_date': round_date.strftime('%Y-%m-%d'),
                    'description': f'Round {round_num} completion'
                })
            
            return {
                'success': True,
                'client_id': client_id,
                'client_name': client.name,
                'current_round': current_round,
                'expected_resolution_date': expected_resolution.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
                'confidence': 'high' if len(outcomes) > 20 else ('medium' if len(outcomes) > 5 else 'low'),
                'milestones': milestones,
                'avg_resolution_days': round(avg_resolution, 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def forecast_caseload(self, months_ahead: int = 3) -> Dict[str, Any]:
        """
        Forecast expected new cases
        
        Args:
            months_ahead: Number of months to forecast
            
        Returns:
            Dict with caseload forecasts
        """
        db = get_db()
        try:
            now = datetime.utcnow()
            
            monthly_signups = []
            for i in range(6, 0, -1):
                month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
                month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
                
                count = db.query(Client).filter(
                    Client.created_at >= month_start,
                    Client.created_at <= month_end
                ).count()
                
                monthly_signups.append({
                    'month': month_start.strftime('%Y-%m'),
                    'new_clients': count
                })
            
            avg_signups = statistics.mean([m['new_clients'] for m in monthly_signups]) if monthly_signups else 10
            
            if len(monthly_signups) >= 3:
                recent = statistics.mean([m['new_clients'] for m in monthly_signups[-2:]])
                older = statistics.mean([m['new_clients'] for m in monthly_signups[:2]])
                trend = (recent - older) / older if older > 0 else 0.1
            else:
                trend = 0.1
            
            forecasts = []
            for i in range(1, months_ahead + 1):
                forecast_date = (now + relativedelta(months=i)).replace(day=1)
                predicted = int(avg_signups * (1 + trend * i * 0.5))
                
                forecasts.append({
                    'period': forecast_date.strftime('%Y-%m'),
                    'predicted_cases': max(1, predicted),
                    'low_estimate': max(1, int(predicted * 0.7)),
                    'high_estimate': int(predicted * 1.3)
                })
            
            current_active = db.query(Client).filter(Client.status == 'active').count()
            current_pending = db.query(Client).filter(Client.status == 'signup').count()
            
            return {
                'success': True,
                'forecasts': forecasts,
                'historical': monthly_signups,
                'current_active_cases': current_active,
                'current_pending_signups': current_pending,
                'trend_percent': round(trend * 100, 1),
                'avg_monthly_signups': round(avg_signups, 1)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def predict_settlement_probability(self, client_id: int) -> Dict[str, Any]:
        """
        Calculate likelihood of settlement for a client
        
        Args:
            client_id: Client database ID
            
        Returns:
            Dict with probability and factors
        """
        db = get_db()
        try:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            base_probability = 0.5
            
            case_score = db.query(CaseScore).filter_by(client_id=client_id).first()
            if case_score and case_score.total_score:
                score_factor = case_score.total_score / 10
                base_probability = 0.3 + (score_factor * 0.5)
            
            violation_count = db.query(Violation).filter_by(client_id=client_id).count()
            willful_count = db.query(Violation).filter_by(client_id=client_id, is_willful=True).count()
            
            if violation_count >= 10:
                base_probability += 0.15
            elif violation_count >= 5:
                base_probability += 0.10
            
            if willful_count >= 3:
                base_probability += 0.10
            
            if client.current_dispute_round and client.current_dispute_round >= 3:
                base_probability += 0.10
            
            probability = min(0.95, max(0.05, base_probability))
            
            factors = {
                'case_score': case_score.total_score if case_score else 0,
                'violation_count': violation_count,
                'willful_violations': willful_count,
                'dispute_round': client.current_dispute_round or 0
            }
            
            if probability >= 0.7:
                recommendation = 'Excellent case for settlement. Consider aggressive demand letter.'
            elif probability >= 0.5:
                recommendation = 'Good settlement prospects. Continue dispute process to strengthen case.'
            elif probability >= 0.3:
                recommendation = 'Moderate probability. Focus on documenting additional violations.'
            else:
                recommendation = 'Low probability currently. Need more evidence or violations.'
            
            return {
                'success': True,
                'client_id': client_id,
                'client_name': client.name,
                'settlement_probability': round(probability, 2),
                'probability_percent': round(probability * 100, 1),
                'factors': factors,
                'recommendation': recommendation,
                'confidence_level': 'high' if case_score else 'medium'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def get_revenue_trends(self) -> Dict[str, Any]:
        """
        Get historical revenue analysis
        
        Returns:
            Dict with revenue trends and analysis
        """
        db = get_db()
        try:
            now = datetime.utcnow()
            
            monthly_data = []
            for i in range(12, 0, -1):
                month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
                month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
                
                signup_revenue = db.query(func.sum(Client.signup_amount)).filter(
                    Client.payment_status == 'paid',
                    Client.payment_received_at >= month_start,
                    Client.payment_received_at <= month_end
                ).scalar() or 0
                
                settlement_revenue = db.query(func.sum(Settlement.contingency_earned)).filter(
                    Settlement.payment_received == True,
                    Settlement.payment_date >= month_start,
                    Settlement.payment_date <= month_end
                ).scalar() or 0
                
                new_clients = db.query(Client).filter(
                    Client.created_at >= month_start,
                    Client.created_at <= month_end
                ).count()
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'month_name': month_start.strftime('%B %Y'),
                    'signup_revenue': (signup_revenue / 100) if signup_revenue else 0,
                    'settlement_revenue': settlement_revenue or 0,
                    'total_revenue': ((signup_revenue / 100) if signup_revenue else 0) + (settlement_revenue or 0),
                    'new_clients': new_clients
                })
            
            total_revenue = sum(m['total_revenue'] for m in monthly_data)
            avg_monthly = total_revenue / 12 if monthly_data else 0
            
            if len(monthly_data) >= 2:
                first_half = sum(m['total_revenue'] for m in monthly_data[:6])
                second_half = sum(m['total_revenue'] for m in monthly_data[6:])
                yoy_growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            else:
                yoy_growth = 0
            
            best_month = max(monthly_data, key=lambda x: x['total_revenue']) if monthly_data else None
            worst_month = min(monthly_data, key=lambda x: x['total_revenue']) if monthly_data else None
            
            return {
                'success': True,
                'monthly_data': monthly_data,
                'total_revenue_12m': round(total_revenue, 2),
                'avg_monthly_revenue': round(avg_monthly, 2),
                'yoy_growth_percent': round(yoy_growth, 1),
                'best_month': best_month,
                'worst_month': worst_month,
                'revenue_by_type': {
                    'signups': sum(m['signup_revenue'] for m in monthly_data),
                    'settlements': sum(m['settlement_revenue'] for m in monthly_data)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def identify_growth_opportunities(self) -> Dict[str, Any]:
        """
        Identify actionable growth opportunities
        
        Returns:
            Dict with opportunities and recommendations
        """
        db = get_db()
        try:
            opportunities = []
            
            dormant_clients = db.query(Client).filter(
                Client.status == 'paused',
                Client.updated_at < datetime.utcnow() - timedelta(days=30)
            ).count()
            
            if dormant_clients > 0:
                opportunities.append({
                    'type': 'reactivation',
                    'title': 'Re-engage Dormant Clients',
                    'description': f'{dormant_clients} clients have been paused for 30+ days',
                    'potential_value': dormant_clients * 300,
                    'action': 'Send re-engagement campaign',
                    'priority': 'high' if dormant_clients > 10 else 'medium',
                    'count': dormant_clients
                })
            
            high_value_pending = db.query(Client).filter(
                Client.status == 'signup',
                Client.payment_status == 'pending'
            ).count()
            
            if high_value_pending > 0:
                opportunities.append({
                    'type': 'conversion',
                    'title': 'Convert Pending Signups',
                    'description': f'{high_value_pending} signups awaiting payment',
                    'potential_value': high_value_pending * 500,
                    'action': 'Send follow-up reminders',
                    'priority': 'high',
                    'count': high_value_pending
                })
            
            settlements_pending = db.query(Settlement).filter(
                Settlement.status == 'negotiating',
                Settlement.target_amount > 5000
            ).count()
            
            total_pending = db.query(func.sum(Settlement.target_amount)).filter(
                Settlement.status.in_(['negotiating', 'demand_sent'])
            ).scalar() or 0
            
            if settlements_pending > 0:
                opportunities.append({
                    'type': 'settlement',
                    'title': 'Accelerate Settlement Negotiations',
                    'description': f'{settlements_pending} high-value settlements in negotiation',
                    'potential_value': float(total_pending) * 0.33,
                    'action': 'Prioritize settlement follow-ups',
                    'priority': 'high',
                    'count': settlements_pending
                })
            
            referral_program = db.query(Client).filter(
                Client.referred_by_client_id.isnot(None)
            ).count()
            
            total_clients = db.query(Client).count()
            referral_rate = referral_program / total_clients if total_clients > 0 else 0
            
            if referral_rate < 0.1:
                opportunities.append({
                    'type': 'referral',
                    'title': 'Boost Referral Program',
                    'description': f'Only {round(referral_rate * 100, 1)}% of clients from referrals',
                    'potential_value': total_clients * 50,
                    'action': 'Launch referral incentive campaign',
                    'priority': 'medium',
                    'count': int(total_clients * 0.1)
                })
            
            round_4_clients = db.query(Client).filter(
                Client.current_dispute_round == 4,
                Client.status == 'active'
            ).count()
            
            if round_4_clients > 0:
                opportunities.append({
                    'type': 'upsell',
                    'title': 'Upsell Litigation Services',
                    'description': f'{round_4_clients} clients at Round 4 (pre-litigation)',
                    'potential_value': round_4_clients * 1500,
                    'action': 'Offer attorney consultation',
                    'priority': 'high',
                    'count': round_4_clients
                })
            
            opportunities.sort(key=lambda x: x['potential_value'], reverse=True)
            
            total_potential = sum(o['potential_value'] for o in opportunities)
            
            return {
                'success': True,
                'opportunities': opportunities,
                'total_potential_value': round(total_potential, 2),
                'high_priority_count': sum(1 for o in opportunities if o['priority'] == 'high'),
                'summary': f'{len(opportunities)} growth opportunities identified worth ${total_potential:,.2f}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def calculate_churn_risk(self, client_id: int) -> Dict[str, Any]:
        """
        Calculate client churn risk
        
        Args:
            client_id: Client database ID
            
        Returns:
            Dict with churn risk assessment
        """
        db = get_db()
        try:
            client = db.query(Client).filter_by(id=client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            risk_score = self._calculate_churn_risk_internal(db, client)
            
            risk_factors = []
            
            if client.status == 'paused':
                risk_factors.append({
                    'factor': 'Account Paused',
                    'impact': 0.3,
                    'description': 'Client has paused their account'
                })
            
            days_since_activity = (datetime.utcnow() - client.updated_at).days if client.updated_at else 90
            if days_since_activity > 30:
                risk_factors.append({
                    'factor': 'Inactivity',
                    'impact': min(0.3, days_since_activity / 100),
                    'description': f'No activity for {days_since_activity} days'
                })
            
            if client.payment_status == 'pending':
                risk_factors.append({
                    'factor': 'Payment Pending',
                    'impact': 0.2,
                    'description': 'Payment has not been completed'
                })
            
            if client.current_dispute_round == 0:
                risk_factors.append({
                    'factor': 'No Dispute Started',
                    'impact': 0.15,
                    'description': 'Dispute process not yet initiated'
                })
            
            if risk_score >= 0.7:
                recommendation = 'High churn risk. Immediate outreach recommended.'
                risk_level = 'high'
            elif risk_score >= 0.4:
                recommendation = 'Moderate risk. Schedule check-in call.'
                risk_level = 'medium'
            else:
                recommendation = 'Low risk. Continue normal engagement.'
                risk_level = 'low'
            
            return {
                'success': True,
                'client_id': client_id,
                'client_name': client.name,
                'churn_risk': round(risk_score, 2),
                'risk_percent': round(risk_score * 100, 1),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendation': recommendation,
                'days_since_activity': days_since_activity
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def _calculate_churn_risk_internal(self, db: Session, client: Client) -> float:
        """Internal helper to calculate churn risk score"""
        risk = 0.1
        
        if client.status == 'paused':
            risk += 0.3
        elif client.status == 'cancelled':
            risk = 0.95
        
        if client.payment_status == 'pending':
            risk += 0.2
        elif client.payment_status == 'failed':
            risk += 0.3
        
        days_since_activity = (datetime.utcnow() - client.updated_at).days if client.updated_at else 90
        risk += min(0.2, days_since_activity / 150)
        
        if client.current_dispute_round == 0:
            risk += 0.1
        elif client.current_dispute_round >= 3:
            risk -= 0.05
        
        return min(0.95, max(0.05, risk))
    
    def get_top_clients_by_ltv(self, limit: int = 10) -> Dict[str, Any]:
        """Get top clients ranked by lifetime value"""
        db = get_db()
        try:
            ltv_records = db.query(ClientLifetimeValue).order_by(
                ClientLifetimeValue.ltv_estimate.desc()
            ).limit(limit).all()
            
            clients = []
            for ltv in ltv_records:
                client = db.query(Client).filter_by(id=ltv.client_id).first()
                if client:
                    clients.append({
                        'client_id': client.id,
                        'client_name': client.name,
                        'ltv_estimate': round(ltv.ltv_estimate, 2),
                        'probability_of_success': round(ltv.probability_of_success, 2),
                        'status': client.status,
                        'dispute_round': client.current_dispute_round or 0
                    })
            
            return {
                'success': True,
                'top_clients': clients,
                'count': len(clients)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()


predictive_analytics_service = PredictiveAnalyticsService()
