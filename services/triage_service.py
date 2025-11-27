"""
Triage Service for FCRA Litigation Platform.
AI-powered case triage system for priority scoring and queue assignment.
"""
from datetime import datetime
from database import SessionLocal, CaseTriage, Analysis, Violation, Standing, Damages, CaseScore, Client


def calculate_priority_score(violations, standing, damages, case_score):
    """
    Calculate priority score (1-5 stars) based on case factors.
    
    Scoring factors:
    - Violation types (reinsertion = +2, identity theft = +2, multiple bureaus = +1)
    - Standing strength (documented harm = +1, credit denial = +1)
    - Damages potential (>$10K = +1, >$25K = +2)
    - Willfulness indicators (+1.5 each)
    - Evidence quality (+1 for strong documentation)
    
    Returns:
        Tuple of (priority_score 1-5, raw_score, confidence)
    """
    score = 0.0
    confidence_factors = 0
    
    bureaus_affected = set()
    
    for violation in violations:
        violation_type = (violation.violation_type or '').lower()
        description = (violation.description or '').lower()
        
        if 'reinsertion' in violation_type or 'reinsertion' in description:
            score += 2
        if 'identity' in violation_type or 'identity theft' in description:
            score += 2
        if violation.fcra_section in ['611(a)(5)', '605B', '§611(a)(5)', '§605B']:
            score += 1.5
        
        score += 0.5
        
        if violation.is_willful:
            score += 1.5
        
        if violation.bureau:
            bureaus_affected.add(violation.bureau.lower())
        
        confidence_factors += 1
    
    if len(bureaus_affected) > 1:
        score += 1
    if len(bureaus_affected) >= 3:
        score += 0.5
    
    if standing:
        if standing.has_concrete_harm:
            score += 1
            confidence_factors += 1
        if standing.denial_letters_count and standing.denial_letters_count > 0:
            score += 1
            confidence_factors += 1
        if standing.has_dissemination:
            score += 0.5
            confidence_factors += 1
        if standing.adverse_action_notices_count and standing.adverse_action_notices_count > 0:
            score += 0.5
    
    if damages:
        total_damages = (damages.actual_damages_total or 0) + (damages.statutory_damages_total or 0)
        if total_damages > 25000:
            score += 2
            confidence_factors += 1
        elif total_damages > 10000:
            score += 1
            confidence_factors += 1
    
    if case_score:
        if case_score.documentation_score and case_score.documentation_score >= 7:
            score += 1
            confidence_factors += 1
    
    raw_score = score
    priority_score = max(1, min(5, int(score / 2) + 1))
    
    confidence = min(1.0, max(0.3, confidence_factors / 10.0 + 0.3))
    
    return priority_score, raw_score, confidence


def estimate_settlement_value(violations, standing, damages):
    """
    Predict settlement value based on case factors.
    
    Base: $1,000 per violation
    Multipliers:
    - Willful violations: 2x
    - Reinsertion: 2.5x
    - Identity theft: 3x
    - Strong standing: 1.5x
    - Multiple bureaus: 1.3x
    
    Returns:
        Estimated settlement value as float
    """
    base_per_violation = 1000.0
    total_value = 0.0
    bureaus = set()
    
    for violation in violations:
        violation_value = base_per_violation
        violation_type = (violation.violation_type or '').lower()
        description = (violation.description or '').lower()
        
        if violation.is_willful:
            violation_value *= 2
        
        if 'reinsertion' in violation_type or 'reinsertion' in description:
            violation_value *= 2.5
        elif 'identity' in violation_type or 'identity theft' in description:
            violation_value *= 3
        
        if violation.bureau:
            bureaus.add(violation.bureau.lower())
        
        total_value += violation_value
    
    if standing:
        if standing.has_concrete_harm and (standing.denial_letters_count or 0) > 0:
            total_value *= 1.5
        elif standing.has_concrete_harm or standing.has_dissemination:
            total_value *= 1.3
    
    if len(bureaus) >= 3:
        total_value *= 1.3
    elif len(bureaus) >= 2:
        total_value *= 1.15
    
    if damages:
        actual = damages.actual_damages_total or 0
        if actual > 0:
            total_value += actual * 0.5
    
    return round(total_value, 2)


def determine_complexity(violations, standing, damages):
    """
    Determine case complexity level.
    
    Returns:
        String: 'simple', 'moderate', 'complex', or 'expert_review'
    """
    complexity_score = 0
    
    violation_count = len(violations) if violations else 0
    if violation_count >= 10:
        complexity_score += 3
    elif violation_count >= 5:
        complexity_score += 2
    elif violation_count >= 2:
        complexity_score += 1
    
    bureaus = set()
    for v in violations:
        if v.bureau:
            bureaus.add(v.bureau.lower())
    
    if len(bureaus) >= 3:
        complexity_score += 2
    elif len(bureaus) >= 2:
        complexity_score += 1
    
    for v in violations:
        vtype = (v.violation_type or '').lower()
        if 'identity' in vtype or 'fraud' in vtype:
            complexity_score += 2
            break
    
    if damages:
        total = (damages.actual_damages_total or 0) + (damages.punitive_damages_amount or 0)
        if total > 50000:
            complexity_score += 2
        elif total > 25000:
            complexity_score += 1
    
    if complexity_score >= 7:
        return 'expert_review'
    elif complexity_score >= 5:
        return 'complex'
    elif complexity_score >= 2:
        return 'moderate'
    else:
        return 'simple'


def recommend_queue(priority_score, complexity_level, has_critical_info=True):
    """
    Assign case to appropriate queue.
    
    fast_track: Priority 5, simple/moderate
    standard: Priority 3-4, any complexity
    review_needed: Priority 1-2 OR complex cases
    hold: Missing critical information
    
    Returns:
        String: 'fast_track', 'standard', 'review_needed', or 'hold'
    """
    if not has_critical_info:
        return 'hold'
    
    if complexity_level == 'expert_review':
        return 'review_needed'
    
    if priority_score >= 5:
        if complexity_level in ['simple', 'moderate']:
            return 'fast_track'
        return 'standard'
    elif priority_score >= 3:
        return 'standard'
    else:
        return 'review_needed'


def identify_key_violations(violations):
    """
    Identify high-value violations for case summary.
    
    Returns:
        List of key violation dictionaries
    """
    key_violations = []
    
    for v in violations:
        vtype = (v.violation_type or '').lower()
        desc = (v.description or '').lower()
        
        is_key = False
        reason = []
        
        if 'reinsertion' in vtype or 'reinsertion' in desc:
            is_key = True
            reason.append('Reinsertion violation')
        if 'identity' in vtype or 'identity theft' in desc:
            is_key = True
            reason.append('Identity theft related')
        if v.fcra_section in ['611(a)(5)', '605B', '§611(a)(5)', '§605B']:
            is_key = True
            reason.append(f'Strong FCRA section: {v.fcra_section}')
        if v.is_willful:
            is_key = True
            reason.append('Willful violation')
        
        if is_key:
            key_violations.append({
                'id': v.id,
                'type': v.violation_type,
                'section': v.fcra_section,
                'bureau': v.bureau,
                'willful': v.is_willful,
                'reasons': reason,
                'damages_min': v.statutory_damages_min or 0,
                'damages_max': v.statutory_damages_max or 0
            })
    
    return key_violations[:10]


def identify_risk_factors(violations, standing, damages):
    """
    Identify potential issues with the case.
    
    Returns:
        List of risk factor dictionaries
    """
    risks = []
    
    if not standing:
        risks.append({
            'type': 'missing_standing',
            'severity': 'high',
            'description': 'Standing analysis not available'
        })
    elif not standing.has_concrete_harm:
        risks.append({
            'type': 'weak_standing',
            'severity': 'medium',
            'description': 'No documented concrete harm'
        })
    
    if not damages:
        risks.append({
            'type': 'missing_damages',
            'severity': 'medium',
            'description': 'Damages calculation not available'
        })
    elif (damages.actual_damages_total or 0) + (damages.statutory_damages_total or 0) < 1000:
        risks.append({
            'type': 'low_damages',
            'severity': 'medium',
            'description': 'Estimated damages below $1,000'
        })
    
    if not violations or len(violations) == 0:
        risks.append({
            'type': 'no_violations',
            'severity': 'high',
            'description': 'No violations identified'
        })
    elif len(violations) == 1:
        risks.append({
            'type': 'single_violation',
            'severity': 'low',
            'description': 'Only one violation identified'
        })
    
    willful_count = sum(1 for v in violations if v.is_willful)
    if willful_count == 0 and len(violations) > 0:
        risks.append({
            'type': 'no_willfulness',
            'severity': 'medium',
            'description': 'No willfulness indicators found'
        })
    
    return risks


def identify_strengths(violations, standing, damages, case_score):
    """
    Identify strong points for the case.
    
    Returns:
        List of strength dictionaries
    """
    strengths = []
    
    bureaus = set(v.bureau for v in violations if v.bureau)
    if len(bureaus) >= 3:
        strengths.append({
            'type': 'multi_bureau',
            'description': f'Violations across all 3 bureaus'
        })
    
    willful_count = sum(1 for v in violations if v.is_willful)
    if willful_count >= 3:
        strengths.append({
            'type': 'willful_violations',
            'description': f'{willful_count} willful violations identified'
        })
    
    for v in violations:
        vtype = (v.violation_type or '').lower()
        if 'reinsertion' in vtype:
            strengths.append({
                'type': 'reinsertion',
                'description': 'Reinsertion violation (high value)'
            })
            break
    
    if standing and standing.has_concrete_harm and (standing.denial_letters_count or 0) > 0:
        strengths.append({
            'type': 'strong_standing',
            'description': f'Strong standing with {standing.denial_letters_count} denial letters'
        })
    
    if damages:
        total = (damages.actual_damages_total or 0) + (damages.statutory_damages_total or 0)
        if total > 10000:
            strengths.append({
                'type': 'high_damages',
                'description': f'Damages potential: ${total:,.0f}'
            })
    
    if case_score and case_score.total_score and case_score.total_score >= 8:
        strengths.append({
            'type': 'strong_case_score',
            'description': f'High case strength score: {case_score.total_score}/10'
        })
    
    return strengths


def generate_triage_summary(priority_score, estimated_value, complexity_level, queue, 
                           key_violations, risks, strengths, violations_count):
    """
    Generate an AI-style summary of the triage results.
    
    Returns:
        String summary
    """
    priority_labels = {
        5: 'HIGH PRIORITY',
        4: 'ELEVATED PRIORITY',
        3: 'STANDARD PRIORITY',
        2: 'LOW PRIORITY',
        1: 'MINIMAL PRIORITY'
    }
    
    queue_labels = {
        'fast_track': 'Fast Track processing recommended',
        'standard': 'Standard queue assignment',
        'review_needed': 'Manual review required',
        'hold': 'Case on hold pending information'
    }
    
    summary_parts = [
        f"CASE TRIAGE: {priority_labels.get(priority_score, 'UNKNOWN')} ({priority_score}/5 stars)",
        f"Estimated Value: ${estimated_value:,.2f}",
        f"Complexity: {complexity_level.upper()}",
        f"Queue: {queue_labels.get(queue, queue)}",
        "",
        f"Violations: {violations_count} identified, {len(key_violations)} high-value"
    ]
    
    if strengths:
        summary_parts.append(f"Strengths: {', '.join(s['description'] for s in strengths[:3])}")
    
    if risks:
        high_risks = [r for r in risks if r['severity'] == 'high']
        if high_risks:
            summary_parts.append(f"⚠️ Risks: {', '.join(r['description'] for r in high_risks)}")
    
    return "\n".join(summary_parts)


def triage_case(analysis_id):
    """
    Main triage function - analyze case and create CaseTriage record.
    
    Args:
        analysis_id: The ID of the analysis to triage
        
    Returns:
        Dict with triage results and CaseTriage record ID
    """
    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return {'success': False, 'error': 'Analysis not found'}
        
        existing_triage = db.query(CaseTriage).filter(
            CaseTriage.analysis_id == analysis_id
        ).first()
        
        if existing_triage:
            return {
                'success': True,
                'triage_id': existing_triage.id,
                'message': 'Triage already exists',
                'priority_score': existing_triage.priority_score,
                'estimated_value': existing_triage.estimated_value,
                'recommended_queue': existing_triage.recommended_queue
            }
        
        violations = db.query(Violation).filter(Violation.analysis_id == analysis_id).all()
        standing = db.query(Standing).filter(Standing.analysis_id == analysis_id).first()
        damages = db.query(Damages).filter(Damages.analysis_id == analysis_id).first()
        case_score = db.query(CaseScore).filter(CaseScore.analysis_id == analysis_id).first()
        
        priority_score, raw_score, confidence = calculate_priority_score(
            violations, standing, damages, case_score
        )
        
        estimated_value = estimate_settlement_value(violations, standing, damages)
        
        complexity_level = determine_complexity(violations, standing, damages)
        
        has_critical = len(violations) > 0
        recommended_queue = recommend_queue(priority_score, complexity_level, has_critical)
        
        key_violations = identify_key_violations(violations)
        risk_factors = identify_risk_factors(violations, standing, damages)
        strengths = identify_strengths(violations, standing, damages, case_score)
        
        triage_summary = generate_triage_summary(
            priority_score, estimated_value, complexity_level, recommended_queue,
            key_violations, risk_factors, strengths, len(violations)
        )
        
        triage = CaseTriage(
            client_id=analysis.client_id,
            analysis_id=analysis_id,
            priority_score=priority_score,
            estimated_value=estimated_value,
            complexity_level=complexity_level,
            recommended_queue=recommended_queue,
            key_violations=key_violations,
            risk_factors=risk_factors,
            strengths=strengths,
            triage_summary=triage_summary,
            ai_confidence=confidence,
            reviewed=False
        )
        
        db.add(triage)
        db.commit()
        db.refresh(triage)
        
        return {
            'success': True,
            'triage_id': triage.id,
            'priority_score': priority_score,
            'raw_score': raw_score,
            'estimated_value': estimated_value,
            'complexity_level': complexity_level,
            'recommended_queue': recommended_queue,
            'ai_confidence': confidence,
            'key_violations_count': len(key_violations),
            'risk_factors_count': len(risk_factors),
            'strengths_count': len(strengths),
            'triage_summary': triage_summary
        }
        
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


def get_triage_by_id(triage_id):
    """Get a triage record by ID."""
    db = SessionLocal()
    try:
        triage = db.query(CaseTriage).filter(CaseTriage.id == triage_id).first()
        if not triage:
            return None
        
        return {
            'id': triage.id,
            'client_id': triage.client_id,
            'analysis_id': triage.analysis_id,
            'priority_score': triage.priority_score,
            'estimated_value': triage.estimated_value,
            'complexity_level': triage.complexity_level,
            'recommended_queue': triage.recommended_queue,
            'key_violations': triage.key_violations,
            'risk_factors': triage.risk_factors,
            'strengths': triage.strengths,
            'triage_summary': triage.triage_summary,
            'ai_confidence': triage.ai_confidence,
            'reviewed': triage.reviewed,
            'reviewed_by': triage.reviewed_by,
            'reviewed_at': triage.reviewed_at.isoformat() if triage.reviewed_at else None,
            'final_priority': triage.final_priority,
            'notes': triage.notes,
            'created_at': triage.created_at.isoformat() if triage.created_at else None
        }
    finally:
        db.close()


def get_triage_by_analysis(analysis_id):
    """Get triage record for an analysis."""
    db = SessionLocal()
    try:
        triage = db.query(CaseTriage).filter(CaseTriage.analysis_id == analysis_id).first()
        if triage:
            return get_triage_by_id(triage.id)
        return None
    finally:
        db.close()


def get_queue_cases(queue_name=None, limit=50):
    """Get cases by queue."""
    db = SessionLocal()
    try:
        query = db.query(CaseTriage).order_by(
            CaseTriage.priority_score.desc(),
            CaseTriage.created_at.desc()
        )
        
        if queue_name:
            query = query.filter(CaseTriage.recommended_queue == queue_name)
        
        cases = query.limit(limit).all()
        
        result = []
        for triage in cases:
            client = db.query(Client).filter(Client.id == triage.client_id).first()
            analysis = db.query(Analysis).filter(Analysis.id == triage.analysis_id).first()
            
            result.append({
                'id': triage.id,
                'client_id': triage.client_id,
                'client_name': client.name if client else 'Unknown',
                'client_email': client.email if client else '',
                'analysis_id': triage.analysis_id,
                'priority_score': triage.priority_score,
                'estimated_value': triage.estimated_value,
                'complexity_level': triage.complexity_level,
                'recommended_queue': triage.recommended_queue,
                'ai_confidence': triage.ai_confidence,
                'reviewed': triage.reviewed,
                'final_priority': triage.final_priority,
                'created_at': triage.created_at.isoformat() if triage.created_at else None,
                'dispute_round': analysis.dispute_round if analysis else 1
            })
        
        return result
    finally:
        db.close()


def get_triage_stats():
    """Get triage queue statistics."""
    db = SessionLocal()
    try:
        total = db.query(CaseTriage).count()
        
        fast_track = db.query(CaseTriage).filter(
            CaseTriage.recommended_queue == 'fast_track'
        ).count()
        
        standard = db.query(CaseTriage).filter(
            CaseTriage.recommended_queue == 'standard'
        ).count()
        
        review_needed = db.query(CaseTriage).filter(
            CaseTriage.recommended_queue == 'review_needed'
        ).count()
        
        hold = db.query(CaseTriage).filter(
            CaseTriage.recommended_queue == 'hold'
        ).count()
        
        unreviewed = db.query(CaseTriage).filter(
            CaseTriage.reviewed == False
        ).count()
        
        high_priority = db.query(CaseTriage).filter(
            CaseTriage.priority_score >= 4
        ).count()
        
        from sqlalchemy import func
        avg_value = db.query(func.avg(CaseTriage.estimated_value)).scalar() or 0
        total_value = db.query(func.sum(CaseTriage.estimated_value)).scalar() or 0
        
        return {
            'total': total,
            'fast_track': fast_track,
            'standard': standard,
            'review_needed': review_needed,
            'hold': hold,
            'unreviewed': unreviewed,
            'high_priority': high_priority,
            'avg_estimated_value': round(avg_value, 2),
            'total_estimated_value': round(total_value, 2)
        }
    finally:
        db.close()


def update_triage_review(triage_id, reviewed_by, final_priority=None, notes=None):
    """Submit human review for a triage record."""
    db = SessionLocal()
    try:
        triage = db.query(CaseTriage).filter(CaseTriage.id == triage_id).first()
        if not triage:
            return {'success': False, 'error': 'Triage record not found'}
        
        triage.reviewed = True
        triage.reviewed_by = reviewed_by
        triage.reviewed_at = datetime.utcnow()
        
        if final_priority is not None:
            triage.final_priority = max(1, min(5, int(final_priority)))
            triage.recommended_queue = recommend_queue(
                triage.final_priority, 
                triage.complexity_level
            )
        else:
            triage.final_priority = triage.priority_score
        
        if notes:
            triage.notes = notes
        
        triage.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            'success': True,
            'triage_id': triage.id,
            'final_priority': triage.final_priority,
            'recommended_queue': triage.recommended_queue
        }
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()
