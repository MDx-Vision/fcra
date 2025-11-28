"""
Attorney Analytics Service
Staff performance tracking, leaderboards, and case assignment recommendations
"""
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
import statistics

from database import (
    get_db, Staff, Client, Case, Settlement, Analysis, CaseScore,
    Violation, AttorneyPerformance, CaseOutcome
)


class AttorneyAnalyticsService:
    """Attorney/staff performance analytics and case assignment optimization"""
    
    PERIOD_MAPPINGS = {
        'week': 7,
        'month': 30,
        'quarter': 90,
        'year': 365
    }
    
    METRICS = ['cases_handled', 'cases_won', 'cases_settled', 'total_settlements', 'avg_resolution_days', 'efficiency_score']
    
    def __init__(self):
        self.min_cases_for_ranking = 3
    
    def calculate_performance(self, staff_user_id: int, period: str = 'month') -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for a staff member
        
        Args:
            staff_user_id: Staff database ID
            period: Time period ('week', 'month', 'quarter', 'year')
            
        Returns:
            Dict with performance metrics
        """
        db = get_db()
        try:
            staff = db.query(Staff).filter_by(id=staff_user_id).first()
            if not staff:
                return {'success': False, 'error': 'Staff member not found'}
            
            days = self.PERIOD_MAPPINGS.get(period, 30)
            period_start = datetime.utcnow() - timedelta(days=days)
            period_end = datetime.utcnow()
            
            outcomes = db.query(CaseOutcome).filter(
                CaseOutcome.attorney_id == staff_user_id,
                CaseOutcome.created_at >= period_start
            ).all()
            
            cases_handled = len(outcomes)
            cases_won = sum(1 for o in outcomes if o.final_outcome == 'won')
            cases_lost = sum(1 for o in outcomes if o.final_outcome == 'lost')
            cases_settled = sum(1 for o in outcomes if o.final_outcome == 'settled')
            
            total_settlements = sum(o.settlement_amount or 0 for o in outcomes if o.final_outcome == 'settled')
            
            resolution_times = [o.time_to_resolution_days for o in outcomes if o.time_to_resolution_days and o.time_to_resolution_days > 0]
            avg_resolution_days = statistics.mean(resolution_times) if resolution_times else 0
            
            avg_settlement = total_settlements / cases_settled if cases_settled > 0 else 0
            
            win_rate = (cases_won + cases_settled) / cases_handled if cases_handled > 0 else 0
            efficiency_score = self._calculate_efficiency_score(
                cases_handled, win_rate, avg_resolution_days, total_settlements
            )
            
            strengths = self._identify_strengths(outcomes)
            
            perf = AttorneyPerformance(
                staff_user_id=staff_user_id,
                period_start=period_start.date(),
                period_end=period_end.date(),
                cases_handled=cases_handled,
                cases_won=cases_won,
                cases_lost=cases_lost,
                cases_settled=cases_settled,
                cases_pending=0,
                total_settlements=total_settlements,
                avg_settlement_amount=avg_settlement,
                avg_resolution_days=avg_resolution_days,
                client_satisfaction=0.8,
                efficiency_score=efficiency_score,
                strengths=strengths
            )
            db.add(perf)
            db.commit()
            
            return {
                'success': True,
                'staff_id': staff_user_id,
                'staff_name': staff.full_name,
                'period': period,
                'period_start': period_start.strftime('%Y-%m-%d'),
                'period_end': period_end.strftime('%Y-%m-%d'),
                'metrics': {
                    'cases_handled': cases_handled,
                    'cases_won': cases_won,
                    'cases_lost': cases_lost,
                    'cases_settled': cases_settled,
                    'win_rate': round(win_rate * 100, 1),
                    'total_settlements': round(total_settlements, 2),
                    'avg_settlement_amount': round(avg_settlement, 2),
                    'avg_resolution_days': round(avg_resolution_days, 1),
                    'efficiency_score': round(efficiency_score, 1)
                },
                'strengths': strengths,
                'performance_tier': self._get_performance_tier(efficiency_score)
            }
            
        except Exception as e:
            db.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def get_leaderboard(self, metric: str = 'efficiency_score', period: str = 'month') -> Dict[str, Any]:
        """
        Get ranked staff list by specified metric
        
        Args:
            metric: Metric to rank by ('cases_handled', 'cases_won', 'total_settlements', etc.)
            period: Time period ('week', 'month', 'quarter', 'year')
            
        Returns:
            Dict with leaderboard rankings
        """
        db = get_db()
        try:
            if metric not in self.METRICS:
                metric = 'efficiency_score'
            
            days = self.PERIOD_MAPPINGS.get(period, 30)
            period_start = datetime.utcnow() - timedelta(days=days)
            
            attorneys = db.query(Staff).filter(
                Staff.role.in_(['attorney', 'admin', 'paralegal']),
                Staff.is_active == True
            ).all()
            
            leaderboard = []
            for attorney in attorneys:
                perf = db.query(AttorneyPerformance).filter(
                    AttorneyPerformance.staff_user_id == attorney.id,
                    AttorneyPerformance.period_start >= period_start.date()
                ).order_by(AttorneyPerformance.calculated_at.desc()).first()
                
                if perf:
                    metric_value = getattr(perf, metric, 0) or 0
                else:
                    outcomes = db.query(CaseOutcome).filter(
                        CaseOutcome.attorney_id == attorney.id,
                        CaseOutcome.created_at >= period_start
                    ).all()
                    
                    if metric == 'cases_handled':
                        metric_value = len(outcomes)
                    elif metric == 'cases_won':
                        metric_value = sum(1 for o in outcomes if o.final_outcome == 'won')
                    elif metric == 'cases_settled':
                        metric_value = sum(1 for o in outcomes if o.final_outcome == 'settled')
                    elif metric == 'total_settlements':
                        metric_value = sum(o.settlement_amount or 0 for o in outcomes if o.final_outcome == 'settled')
                    elif metric == 'avg_resolution_days':
                        times = [o.time_to_resolution_days for o in outcomes if o.time_to_resolution_days]
                        metric_value = statistics.mean(times) if times else 0
                    else:
                        cases = len(outcomes)
                        wins = sum(1 for o in outcomes if o.final_outcome in ['won', 'settled'])
                        win_rate = wins / cases if cases > 0 else 0
                        metric_value = win_rate * 100
                
                leaderboard.append({
                    'staff_id': attorney.id,
                    'staff_name': attorney.full_name,
                    'role': attorney.role,
                    'metric_value': round(metric_value, 2) if isinstance(metric_value, float) else metric_value,
                    'initials': attorney.initials
                })
            
            reverse_sort = metric not in ['avg_resolution_days']
            leaderboard.sort(key=lambda x: x['metric_value'], reverse=reverse_sort)
            
            for i, entry in enumerate(leaderboard):
                entry['rank'] = i + 1
                if i == 0:
                    entry['badge'] = '🥇'
                elif i == 1:
                    entry['badge'] = '🥈'
                elif i == 2:
                    entry['badge'] = '🥉'
                else:
                    entry['badge'] = ''
            
            return {
                'success': True,
                'metric': metric,
                'metric_display': metric.replace('_', ' ').title(),
                'period': period,
                'leaderboard': leaderboard,
                'total_staff': len(leaderboard)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def identify_strengths(self, staff_user_id: int) -> Dict[str, Any]:
        """
        Identify what a staff member excels at
        
        Args:
            staff_user_id: Staff database ID
            
        Returns:
            Dict with strengths analysis
        """
        db = get_db()
        try:
            staff = db.query(Staff).filter_by(id=staff_user_id).first()
            if not staff:
                return {'success': False, 'error': 'Staff member not found'}
            
            outcomes = db.query(CaseOutcome).filter(
                CaseOutcome.attorney_id == staff_user_id
            ).all()
            
            if not outcomes:
                return {
                    'success': True,
                    'staff_id': staff_user_id,
                    'staff_name': staff.full_name,
                    'strengths': [],
                    'areas_for_improvement': [],
                    'message': 'Not enough case data for analysis'
                }
            
            strengths = []
            improvements = []
            
            settled = sum(1 for o in outcomes if o.final_outcome == 'settled')
            total = len(outcomes)
            settlement_rate = settled / total if total > 0 else 0
            
            if settlement_rate >= 0.6:
                strengths.append({
                    'area': 'Settlement Negotiation',
                    'score': round(settlement_rate * 100, 1),
                    'description': f'Excellent settlement rate of {round(settlement_rate * 100)}%'
                })
            elif settlement_rate < 0.3:
                improvements.append({
                    'area': 'Settlement Negotiation',
                    'current': round(settlement_rate * 100, 1),
                    'target': 50,
                    'suggestion': 'Consider additional negotiation training'
                })
            
            resolution_times = [o.time_to_resolution_days for o in outcomes if o.time_to_resolution_days and o.time_to_resolution_days > 0]
            if resolution_times:
                avg_time = statistics.mean(resolution_times)
                if avg_time <= 60:
                    strengths.append({
                        'area': 'Case Velocity',
                        'score': round(100 - (avg_time / 1.2), 1),
                        'description': f'Fast case resolution averaging {round(avg_time)} days'
                    })
                elif avg_time > 120:
                    improvements.append({
                        'area': 'Case Velocity',
                        'current': round(avg_time, 1),
                        'target': 90,
                        'suggestion': 'Focus on reducing case backlog'
                    })
            
            violation_types = {}
            for o in outcomes:
                if o.violation_types:
                    for vtype in (o.violation_types if isinstance(o.violation_types, list) else []):
                        if vtype not in violation_types:
                            violation_types[vtype] = {'won': 0, 'total': 0}
                        violation_types[vtype]['total'] += 1
                        if o.final_outcome in ['won', 'settled']:
                            violation_types[vtype]['won'] += 1
            
            for vtype, stats in violation_types.items():
                if stats['total'] >= 3:
                    win_rate = stats['won'] / stats['total']
                    if win_rate >= 0.7:
                        strengths.append({
                            'area': f'{vtype} Cases',
                            'score': round(win_rate * 100, 1),
                            'description': f'Strong track record with {vtype} violations'
                        })
            
            total_value = sum(o.settlement_amount or 0 for o in outcomes if o.final_outcome == 'settled')
            if total_value > 50000:
                strengths.append({
                    'area': 'High-Value Cases',
                    'score': 85,
                    'description': f'Generated ${total_value:,.0f} in settlements'
                })
            
            return {
                'success': True,
                'staff_id': staff_user_id,
                'staff_name': staff.full_name,
                'strengths': strengths[:5],
                'areas_for_improvement': improvements[:3],
                'total_cases_analyzed': len(outcomes),
                'overall_win_rate': round((settled + sum(1 for o in outcomes if o.final_outcome == 'won')) / total * 100 if total > 0 else 0, 1)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def recommend_case_assignment(self, case_id: int) -> Dict[str, Any]:
        """
        Recommend best attorney for a specific case
        
        Args:
            case_id: Case database ID
            
        Returns:
            Dict with recommended attorneys and reasoning
        """
        db = get_db()
        try:
            case = db.query(Case).filter_by(id=case_id).first()
            if not case:
                return {'success': False, 'error': 'Case not found'}
            
            client = db.query(Client).filter_by(id=case.client_id).first()
            
            case_score = db.query(CaseScore).filter_by(
                analysis_id=case.analysis_id
            ).first() if case.analysis_id else None
            
            violations = db.query(Violation).filter_by(client_id=case.client_id).all()
            violation_types = list(set(v.violation_type for v in violations if v.violation_type))
            
            is_high_value = case_score and case_score.total_score >= 8
            is_complex = len(violations) >= 10
            
            attorneys = db.query(Staff).filter(
                Staff.role.in_(['attorney', 'admin']),
                Staff.is_active == True
            ).all()
            
            recommendations = []
            for attorney in attorneys:
                score = 50
                reasons = []
                
                outcomes = db.query(CaseOutcome).filter(
                    CaseOutcome.attorney_id == attorney.id
                ).all()
                
                if outcomes:
                    win_rate = sum(1 for o in outcomes if o.final_outcome in ['won', 'settled']) / len(outcomes)
                    score += win_rate * 30
                    if win_rate >= 0.7:
                        reasons.append(f'{round(win_rate * 100)}% win rate')
                
                for vtype in violation_types:
                    matching = [o for o in outcomes if o.violation_types and vtype in str(o.violation_types)]
                    if len(matching) >= 2:
                        score += 10
                        reasons.append(f'Experience with {vtype}')
                        break
                
                current_cases = db.query(CaseOutcome).filter(
                    CaseOutcome.attorney_id == attorney.id,
                    CaseOutcome.created_at >= datetime.utcnow() - timedelta(days=30)
                ).count()
                
                if current_cases < 5:
                    score += 15
                    reasons.append('Available capacity')
                elif current_cases > 15:
                    score -= 10
                    reasons.append('Heavy caseload')
                
                if is_high_value:
                    high_value_wins = sum(1 for o in outcomes if (o.settlement_amount or 0) > 10000 and o.final_outcome == 'settled')
                    if high_value_wins >= 2:
                        score += 15
                        reasons.append('High-value case experience')
                
                recommendations.append({
                    'staff_id': attorney.id,
                    'staff_name': attorney.full_name,
                    'role': attorney.role,
                    'match_score': round(min(100, score), 1),
                    'reasons': reasons[:3],
                    'current_caseload': current_cases,
                    'availability': 'high' if current_cases < 5 else ('medium' if current_cases < 10 else 'low')
                })
            
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            
            return {
                'success': True,
                'case_id': case_id,
                'client_name': client.name if client else 'Unknown',
                'case_characteristics': {
                    'violation_types': violation_types[:5],
                    'is_high_value': is_high_value,
                    'is_complex': is_complex,
                    'case_score': case_score.total_score if case_score else None
                },
                'recommendations': recommendations[:5],
                'top_recommendation': recommendations[0] if recommendations else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def get_workload_distribution(self) -> Dict[str, Any]:
        """
        Get current case assignments across staff
        
        Returns:
            Dict with workload distribution data
        """
        db = get_db()
        try:
            attorneys = db.query(Staff).filter(
                Staff.role.in_(['attorney', 'admin', 'paralegal']),
                Staff.is_active == True
            ).all()
            
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            
            distribution = []
            total_cases = 0
            
            for attorney in attorneys:
                recent_cases = db.query(CaseOutcome).filter(
                    CaseOutcome.attorney_id == attorney.id,
                    CaseOutcome.created_at >= thirty_days_ago
                ).count()
                
                pending_settlements = db.query(Settlement).join(
                    Case, Settlement.case_id == Case.id
                ).filter(
                    Settlement.status.in_(['negotiating', 'demand_sent'])
                ).count()
                
                total_cases += recent_cases
                
                distribution.append({
                    'staff_id': attorney.id,
                    'staff_name': attorney.full_name,
                    'role': attorney.role,
                    'active_cases': recent_cases,
                    'pending_settlements': pending_settlements,
                    'total_workload': recent_cases + pending_settlements,
                    'capacity_status': 'overloaded' if recent_cases > 15 else ('optimal' if recent_cases >= 5 else 'available')
                })
            
            distribution.sort(key=lambda x: x['total_workload'], reverse=True)
            
            avg_workload = total_cases / len(attorneys) if attorneys else 0
            
            overloaded = sum(1 for d in distribution if d['capacity_status'] == 'overloaded')
            available = sum(1 for d in distribution if d['capacity_status'] == 'available')
            
            return {
                'success': True,
                'distribution': distribution,
                'summary': {
                    'total_staff': len(attorneys),
                    'total_active_cases': total_cases,
                    'avg_workload': round(avg_workload, 1),
                    'overloaded_count': overloaded,
                    'available_count': available
                },
                'balance_recommendation': 'Redistribute cases' if overloaded > 0 and available > 0 else 'Workload balanced'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def forecast_capacity(self, staff_user_id: int) -> Dict[str, Any]:
        """
        Forecast available bandwidth for a staff member
        
        Args:
            staff_user_id: Staff database ID
            
        Returns:
            Dict with capacity forecast
        """
        db = get_db()
        try:
            staff = db.query(Staff).filter_by(id=staff_user_id).first()
            if not staff:
                return {'success': False, 'error': 'Staff member not found'}
            
            max_capacity = 15
            
            current_cases = db.query(CaseOutcome).filter(
                CaseOutcome.attorney_id == staff_user_id,
                CaseOutcome.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            pending_settlements = db.query(Settlement).filter(
                Settlement.status.in_(['negotiating', 'demand_sent'])
            ).count()
            
            resolution_times = db.query(CaseOutcome.time_to_resolution_days).filter(
                CaseOutcome.attorney_id == staff_user_id,
                CaseOutcome.time_to_resolution_days > 0
            ).all()
            
            avg_resolution = statistics.mean([r[0] for r in resolution_times]) if resolution_times else 45
            
            cases_closing_soon = int(current_cases * (30 / avg_resolution)) if avg_resolution > 0 else 0
            
            available_slots = max(0, max_capacity - current_cases + cases_closing_soon)
            
            utilization = (current_cases / max_capacity) * 100
            
            weekly_forecast = []
            current_load = current_cases
            for week in range(1, 5):
                expected_completions = int(cases_closing_soon / 4)
                expected_new = 2
                projected_load = max(0, current_load - expected_completions + expected_new)
                
                weekly_forecast.append({
                    'week': week,
                    'projected_cases': projected_load,
                    'available_capacity': max(0, max_capacity - projected_load)
                })
                current_load = projected_load
            
            return {
                'success': True,
                'staff_id': staff_user_id,
                'staff_name': staff.full_name,
                'current_capacity': {
                    'active_cases': current_cases,
                    'pending_settlements': pending_settlements,
                    'max_capacity': max_capacity,
                    'available_slots': available_slots,
                    'utilization_percent': round(utilization, 1)
                },
                'forecast': {
                    'cases_closing_within_30_days': cases_closing_soon,
                    'avg_case_duration_days': round(avg_resolution, 1),
                    'weekly_projection': weekly_forecast
                },
                'recommendation': self._get_capacity_recommendation(utilization, available_slots)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            db.close()
    
    def _calculate_efficiency_score(self, cases: int, win_rate: float, 
                                    avg_days: float, total_value: float) -> float:
        """Calculate efficiency score (0-100)"""
        if cases == 0:
            return 0
        
        case_score = min(30, cases * 3)
        win_score = win_rate * 30
        speed_score = max(0, 20 - (avg_days / 5)) if avg_days > 0 else 10
        value_score = min(20, total_value / 5000)
        
        return min(100, case_score + win_score + speed_score + value_score)
    
    def _identify_strengths(self, outcomes: List) -> List[str]:
        """Identify strength areas from case outcomes"""
        strengths = []
        
        if not outcomes:
            return strengths
        
        settled = sum(1 for o in outcomes if o.final_outcome == 'settled')
        if settled / len(outcomes) >= 0.5:
            strengths.append('Strong negotiator')
        
        times = [o.time_to_resolution_days for o in outcomes if o.time_to_resolution_days]
        if times and statistics.mean(times) < 60:
            strengths.append('Fast case resolution')
        
        high_value = sum(1 for o in outcomes if (o.settlement_amount or 0) > 10000)
        if high_value >= 2:
            strengths.append('High-value case specialist')
        
        willful_cases = sum(1 for o in outcomes if o.willfulness_score and o.willfulness_score > 0.7)
        if willful_cases >= 2:
            strengths.append('Willfulness documentation')
        
        return strengths[:4]
    
    def _get_performance_tier(self, score: float) -> str:
        """Get performance tier based on efficiency score"""
        if score >= 80:
            return 'Elite'
        elif score >= 60:
            return 'Strong'
        elif score >= 40:
            return 'Developing'
        else:
            return 'New'
    
    def _get_capacity_recommendation(self, utilization: float, available: int) -> str:
        """Get capacity recommendation"""
        if utilization >= 100:
            return 'At maximum capacity. Consider redistributing cases.'
        elif utilization >= 80:
            return 'Near capacity. Accept only high-priority cases.'
        elif utilization >= 50:
            return 'Optimal utilization. Can accept new cases.'
        else:
            return f'Under-utilized. {available} slots available for new cases.'


attorney_analytics_service = AttorneyAnalyticsService()
