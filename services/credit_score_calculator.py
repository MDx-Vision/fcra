"""
Credit Score Improvement Calculator Service
Estimates credit score improvements based on negative item removal
and tracks progress from beginning to end.
"""
from datetime import datetime
from database import get_db, CreditScoreSnapshot, CreditScoreProjection, Client, Violation, Analysis


SCORE_IMPACT_BY_TYPE = {
    'late_payment_30': {'min': 15, 'max': 40, 'avg': 25},
    'late_payment_60': {'min': 25, 'max': 65, 'avg': 45},
    'late_payment_90': {'min': 35, 'max': 85, 'avg': 60},
    'collection': {'min': 50, 'max': 110, 'avg': 80},
    'charge_off': {'min': 55, 'max': 120, 'avg': 85},
    'repossession': {'min': 60, 'max': 130, 'avg': 95},
    'foreclosure': {'min': 85, 'max': 160, 'avg': 120},
    'bankruptcy': {'min': 130, 'max': 240, 'avg': 180},
    'judgment': {'min': 50, 'max': 100, 'avg': 75},
    'tax_lien': {'min': 40, 'max': 90, 'avg': 65},
    'inquiry': {'min': 5, 'max': 15, 'avg': 10},
    'high_utilization': {'min': 10, 'max': 45, 'avg': 25},
    'mixed_file': {'min': 30, 'max': 80, 'avg': 50},
    'inaccurate_info': {'min': 15, 'max': 60, 'avg': 35},
    'duplicate_account': {'min': 20, 'max': 50, 'avg': 35},
    'wrong_balance': {'min': 10, 'max': 40, 'avg': 25},
    'wrong_status': {'min': 15, 'max': 50, 'avg': 30},
    'identity_error': {'min': 25, 'max': 70, 'avg': 45},
    'unknown': {'min': 10, 'max': 30, 'avg': 20},
}

SCORE_RANGES = {
    'poor': {'min': 300, 'max': 579, 'label': 'Poor'},
    'fair': {'min': 580, 'max': 669, 'label': 'Fair'},
    'good': {'min': 670, 'max': 739, 'label': 'Good'},
    'very_good': {'min': 740, 'max': 799, 'label': 'Very Good'},
    'excellent': {'min': 800, 'max': 850, 'label': 'Excellent'},
}


def get_score_range_label(score):
    """Get the credit score range label"""
    if not score:
        return 'Unknown'
    for range_key, range_data in SCORE_RANGES.items():
        if range_data['min'] <= score <= range_data['max']:
            return range_data['label']
    return 'Unknown'


def categorize_violation_type(violation_text):
    """Map violation description to impact category"""
    text = violation_text.lower() if violation_text else ''
    
    if 'bankruptcy' in text:
        return 'bankruptcy'
    elif 'foreclosure' in text:
        return 'foreclosure'
    elif 'repossession' in text or 'repo' in text:
        return 'repossession'
    elif 'charge' in text and 'off' in text:
        return 'charge_off'
    elif 'collection' in text or 'collect' in text:
        return 'collection'
    elif '90' in text and ('day' in text or 'late' in text):
        return 'late_payment_90'
    elif '60' in text and ('day' in text or 'late' in text):
        return 'late_payment_60'
    elif '30' in text and ('day' in text or 'late' in text):
        return 'late_payment_30'
    elif 'late' in text or 'delinquen' in text:
        return 'late_payment_30'
    elif 'judgment' in text or 'court' in text:
        return 'judgment'
    elif 'tax' in text and 'lien' in text:
        return 'tax_lien'
    elif 'inquiry' in text or 'inquir' in text:
        return 'inquiry'
    elif 'utilization' in text or 'balance' in text:
        return 'high_utilization'
    elif 'mixed' in text or 'file' in text:
        return 'mixed_file'
    elif 'duplicate' in text:
        return 'duplicate_account'
    elif 'identity' in text or 'fraud' in text:
        return 'identity_error'
    elif 'inaccurate' in text or 'error' in text or 'wrong' in text:
        return 'inaccurate_info'
    else:
        return 'unknown'


def estimate_score_improvement(current_score, negatives_to_remove, negative_types=None):
    """
    Estimate potential score improvement based on negative items to be removed.
    
    Args:
        current_score: Current credit score
        negatives_to_remove: Number of negative items to remove
        negative_types: Optional list of negative item types for more accurate estimate
    
    Returns:
        dict with min, max, avg projected scores and improvement
    """
    if not current_score:
        current_score = 550
    
    if not negative_types:
        points_per_negative = 20
        total_min = negatives_to_remove * 10
        total_max = negatives_to_remove * 35
        total_avg = negatives_to_remove * points_per_negative
    else:
        total_min = 0
        total_max = 0
        total_avg = 0
        for neg_type in negative_types:
            impact = SCORE_IMPACT_BY_TYPE.get(neg_type, SCORE_IMPACT_BY_TYPE['unknown'])
            total_min += impact['min']
            total_max += impact['max']
            total_avg += impact['avg']
    
    diminishing_factor = max(0.5, 1 - (negatives_to_remove * 0.03))
    total_min = int(total_min * diminishing_factor)
    total_max = int(total_max * diminishing_factor)
    total_avg = int(total_avg * diminishing_factor)
    
    projected_min = min(850, current_score + total_min)
    projected_max = min(850, current_score + total_max)
    projected_avg = min(850, current_score + total_avg)
    
    return {
        'current_score': current_score,
        'current_range': get_score_range_label(current_score),
        'negatives_to_remove': negatives_to_remove,
        'improvement': {
            'min': total_min,
            'max': total_max,
            'avg': total_avg,
        },
        'projected': {
            'min': projected_min,
            'max': projected_max,
            'avg': projected_avg,
        },
        'projected_range': get_score_range_label(projected_avg),
        'confidence': 'high' if negative_types else 'medium',
    }


def calculate_client_projection(client_id):
    """
    Calculate comprehensive score projection for a client based on their violations.
    """
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return None
        
        analyses = db.query(Analysis).filter_by(client_id=client_id).all()
        analysis_ids = [a.id for a in analyses]
        violations = db.query(Violation).filter(Violation.analysis_id.in_(analysis_ids)).all() if analysis_ids else []
        
        snapshots = db.query(CreditScoreSnapshot).filter_by(
            client_id=client_id
        ).order_by(CreditScoreSnapshot.created_at.desc()).all()
        
        if snapshots:
            latest = snapshots[0]
            current_eq = latest.equifax_score
            current_ex = latest.experian_score
            current_tu = latest.transunion_score
            current_avg = latest.average_score
            current_negatives = latest.total_negatives
        else:
            current_eq = None
            current_ex = None
            current_tu = None
            current_avg = 550
            current_negatives = len(violations)
        
        negative_types = []
        for v in violations:
            neg_type = categorize_violation_type(v.violation_type or v.description or '')
            negative_types.append(neg_type)
        
        projection = estimate_score_improvement(
            current_avg or 550,
            len(violations),
            negative_types
        )
        
        starting_score = None
        starting_negatives = 0
        if len(snapshots) > 1:
            oldest = snapshots[-1]
            starting_score = oldest.average_score
            starting_negatives = oldest.total_negatives
        elif len(snapshots) == 1:
            starting_score = snapshots[0].average_score
            starting_negatives = snapshots[0].total_negatives
        
        total_removed = 0
        if snapshots:
            total_removed = snapshots[0].total_removed or 0
        
        score_gained = 0
        if starting_score and current_avg:
            score_gained = current_avg - starting_score
        
        return {
            'client_id': client_id,
            'client_name': client.name,
            'scores': {
                'starting': {
                    'average': starting_score,
                    'range': get_score_range_label(starting_score),
                },
                'current': {
                    'equifax': current_eq,
                    'experian': current_ex,
                    'transunion': current_tu,
                    'average': current_avg,
                    'range': get_score_range_label(current_avg),
                },
                'projected': {
                    'min': projection['projected']['min'],
                    'max': projection['projected']['max'],
                    'avg': projection['projected']['avg'],
                    'range': projection['projected_range'],
                },
            },
            'negatives': {
                'starting': starting_negatives,
                'current': current_negatives,
                'removed': total_removed,
                'remaining': max(0, current_negatives - total_removed),
            },
            'improvement': {
                'points_gained': score_gained,
                'potential_min': projection['improvement']['min'],
                'potential_max': projection['improvement']['max'],
                'potential_avg': projection['improvement']['avg'],
            },
            'progress_percentage': round((total_removed / starting_negatives * 100) if starting_negatives > 0 else 0, 1),
            'violation_breakdown': get_violation_breakdown(violations),
            'timeline': get_score_timeline(client_id),
            'confidence': projection['confidence'],
        }
    finally:
        db.close()


def get_violation_breakdown(violations):
    """Break down violations by type for the calculator"""
    breakdown = {}
    for v in violations:
        neg_type = categorize_violation_type(v.violation_type or getattr(v, 'description', '') or '')
        if neg_type not in breakdown:
            breakdown[neg_type] = {
                'count': 0,
                'impact': SCORE_IMPACT_BY_TYPE.get(neg_type, SCORE_IMPACT_BY_TYPE['unknown']),
                'label': neg_type.replace('_', ' ').title(),
            }
        breakdown[neg_type]['count'] += 1
    return breakdown


def get_score_timeline(client_id):
    """Get score history timeline for charts"""
    db = get_db()
    try:
        snapshots = db.query(CreditScoreSnapshot).filter_by(
            client_id=client_id
        ).order_by(CreditScoreSnapshot.created_at.asc()).all()
        
        timeline = []
        for s in snapshots:
            timeline.append({
                'date': s.created_at.isoformat() if s.created_at else None,
                'equifax': s.equifax_score,
                'experian': s.experian_score,
                'transunion': s.transunion_score,
                'average': s.average_score,
                'negatives': s.total_negatives,
                'removed': s.total_removed,
                'milestone': s.milestone,
                'round': s.dispute_round,
            })
        
        return timeline
    finally:
        db.close()


def add_score_snapshot(client_id, equifax=None, experian=None, transunion=None,
                       negatives=0, removed=0, milestone=None, dispute_round=0,
                       snapshot_type='manual', source=None, notes=None):
    """Add a new credit score snapshot for a client"""
    db = get_db()
    try:
        scores = [s for s in [equifax, experian, transunion] if s is not None]
        average = round(sum(scores) / len(scores)) if scores else None
        
        snapshot = CreditScoreSnapshot(
            client_id=client_id,
            equifax_score=equifax,
            experian_score=experian,
            transunion_score=transunion,
            average_score=average,
            total_negatives=negatives,
            total_removed=removed,
            milestone=milestone,
            dispute_round=dispute_round,
            snapshot_type=snapshot_type,
            source=source,
            notes=notes
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        return {
            'success': True,
            'snapshot_id': snapshot.id,
            'average_score': average,
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def get_improvement_summary(client_id):
    """Get a quick summary of client's credit improvement journey"""
    db = get_db()
    try:
        snapshots = db.query(CreditScoreSnapshot).filter_by(
            client_id=client_id
        ).order_by(CreditScoreSnapshot.created_at.asc()).all()
        
        if not snapshots:
            return {
                'has_data': False,
                'message': 'No credit score data recorded yet',
            }
        
        first = snapshots[0]
        latest = snapshots[-1]
        
        starting_avg = first.average_score or 0
        current_avg = latest.average_score or 0
        points_gained = current_avg - starting_avg
        
        starting_negatives = first.total_negatives or 0
        current_negatives = latest.total_negatives or 0
        items_removed = latest.total_removed or 0
        
        return {
            'has_data': True,
            'starting_score': starting_avg,
            'starting_range': get_score_range_label(starting_avg),
            'current_score': current_avg,
            'current_range': get_score_range_label(current_avg),
            'points_gained': points_gained,
            'points_gained_text': f"+{points_gained}" if points_gained > 0 else str(points_gained),
            'starting_negatives': starting_negatives,
            'current_negatives': current_negatives,
            'items_removed': items_removed,
            'removal_percentage': round((items_removed / starting_negatives * 100) if starting_negatives > 0 else 0, 1),
            'snapshots_count': len(snapshots),
            'first_snapshot_date': first.created_at.isoformat() if first.created_at else None,
            'latest_snapshot_date': latest.created_at.isoformat() if latest.created_at else None,
            'current_round': latest.dispute_round or 0,
        }
    finally:
        db.close()


def quick_estimate(current_score, num_negatives):
    """Quick estimate without detailed violation types"""
    return estimate_score_improvement(current_score, num_negatives)
