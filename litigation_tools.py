"""
Litigation Tools - Damages Calculator and Case Scoring
FCRA Litigation Platform
"""

def calculate_damages(violations, actual_damages_input):
    """
    Calculate total damages exposure including actual, statutory, punitive, and attorney fees
    
    Args:
        violations: List of Violation objects with FCRA sections
        actual_damages_input: Dict with actual damage amounts
    
    Returns:
        Dict with complete damages breakdown
    """
    damages = {
        'actual': {
            'credit_denials': actual_damages_input.get('credit_denials', 0),
            'higher_interest': actual_damages_input.get('higher_interest', 0),
            'credit_monitoring': actual_damages_input.get('credit_monitoring', 0),
            'time_stress': actual_damages_input.get('time_stress', 0),
            'other': actual_damages_input.get('other', 0),
            'total': 0
        },
        'statutory': {
            '605b': {'count': 0, 'amount': 0},
            '607b': {'count': 0, 'amount': 0},
            '611': {'count': 0, 'amount': 0},
            '623': {'count': 0, 'amount': 0},
            'total': 0
        },
        'punitive': {
            'multiplier': 0,
            'amount': 0
        },
        'attorney_fees': {
            'estimated_hours': 0,
            'hourly_rate': 250,
            'total': 0
        },
        'settlement': {
            'total_exposure': 0,
            'target': 0,
            'minimum': 0
        }
    }
    
    # Calculate actual damages total
    damages['actual']['total'] = sum([
        damages['actual']['credit_denials'],
        damages['actual']['higher_interest'],
        damages['actual']['credit_monitoring'],
        damages['actual']['time_stress'],
        damages['actual']['other']
    ])
    
    # Calculate statutory damages by FCRA section
    willful_violations = 0
    
    for violation in violations:
        section = violation.get('fcra_section', '')
        is_willful = violation.get('is_willful', False)
        
        if is_willful:
            willful_violations += 1
        
        # FCRA statutory damages: $100-$1,000 per violation
        # Using conservative estimates within legal limits
        if '605B' in section.upper() or '605(B)' in section.upper():
            damages['statutory']['605b']['count'] += 1
            damages['statutory']['605b']['amount'] += 1000  # Max allowed under FCRA
        elif '607' in section and 'B' in section.upper():
            damages['statutory']['607b']['count'] += 1
            damages['statutory']['607b']['amount'] += 750  # Mid-high range
        elif '611' in section:
            damages['statutory']['611']['count'] += 1
            damages['statutory']['611']['amount'] += 750  # Mid-high range
        elif '623' in section:
            damages['statutory']['623']['count'] += 1
            damages['statutory']['623']['amount'] += 750  # Mid-high range
    
    damages['statutory']['total'] = sum([
        damages['statutory']['605b']['amount'],
        damages['statutory']['607b']['amount'],
        damages['statutory']['611']['amount'],
        damages['statutory']['623']['amount']
    ])
    
    # Calculate punitive damages (if willful violations present)
    total_violations = len(violations)
    if total_violations > 0:
        willfulness_ratio = willful_violations / total_violations
        
        if willfulness_ratio >= 0.7:
            damages['punitive']['multiplier'] = 5
        elif willfulness_ratio >= 0.5:
            damages['punitive']['multiplier'] = 4
        elif willfulness_ratio >= 0.3:
            damages['punitive']['multiplier'] = 3
        elif willfulness_ratio >= 0.1:
            damages['punitive']['multiplier'] = 2
        else:
            damages['punitive']['multiplier'] = 0
        
        if damages['punitive']['multiplier'] > 0:
            damages['punitive']['amount'] = damages['statutory']['total'] * damages['punitive']['multiplier']
    
    # Estimate attorney fees based on case complexity
    violation_count = len(violations)
    if violation_count < 5:
        damages['attorney_fees']['estimated_hours'] = 15
    elif violation_count < 10:
        damages['attorney_fees']['estimated_hours'] = 25
    elif violation_count < 20:
        damages['attorney_fees']['estimated_hours'] = 40
    else:
        damages['attorney_fees']['estimated_hours'] = 60
    
    damages['attorney_fees']['total'] = (
        damages['attorney_fees']['estimated_hours'] * 
        damages['attorney_fees']['hourly_rate']
    )
    
    # Calculate settlement targets
    damages['settlement']['total_exposure'] = (
        damages['actual']['total'] +
        damages['statutory']['total'] +
        damages['punitive']['amount'] +
        damages['attorney_fees']['total']
    )
    
    damages['settlement']['target'] = damages['settlement']['total_exposure'] * 0.65
    damages['settlement']['minimum'] = damages['settlement']['total_exposure'] * 0.45
    
    return damages


def calculate_case_score(standing, violations, damages_data, documentation_complete):
    """
    Calculate case strength score (1-10) and settlement probability
    
    Scoring breakdown:
    - Standing (0-3 points): Concrete harm, dissemination, causation
    - Violation Quality (0-4 points): Type and strength of violations
    - Willfulness (0-2 points): Reckless disregard indicators
    - Documentation (0-1 point): Complete records and evidence
    
    Args:
        standing: Dict with standing elements
        violations: List of violation dicts
        damages_data: Dict with damages calculations
        documentation_complete: Boolean
    
    Returns:
        Dict with score breakdown and recommendation
    """
    score = {
        'standing': 0,
        'violation_quality': 0,
        'willfulness': 0,
        'documentation': 0,
        'total': 0,
        'settlement_probability': 0,
        'case_strength': '',
        'recommendation': '',
        'notes': []
    }
    
    # STANDING SCORE (0-3 points)
    if standing.get('has_concrete_harm', False):
        score['standing'] = 3
        score['notes'].append('✓ Standing: Concrete harm documented')
    elif standing.get('has_dissemination', False):
        score['standing'] = 1
        score['notes'].append('⚠ Standing: Dissemination but no concrete harm')
    else:
        score['standing'] = 0
        score['notes'].append('✗ Standing: NO STANDING - Case should be rejected')
    
    # VIOLATION QUALITY SCORE (0-4 points)
    has_impossible_contradiction = False
    has_reinsertion = False
    has_identity_theft_block_failure = False
    has_generic_accuracy = False
    
    for violation in violations:
        vtype = violation.get('violation_type', '').lower()
        if 'impossible' in vtype or 'contradiction' in vtype:
            has_impossible_contradiction = True
        if 'reinsertion' in vtype or 'reinsert' in vtype:
            has_reinsertion = True
        if 'identity' in vtype and 'block' in vtype:
            has_identity_theft_block_failure = True
        if 'accuracy' in vtype or 'incorrect' in vtype:
            has_generic_accuracy = True
    
    if has_impossible_contradiction:
        score['violation_quality'] = 4
        score['notes'].append('✓ Violations: Impossible contradictions (STRONGEST)')
    elif has_reinsertion:
        score['violation_quality'] = 3
        score['notes'].append('✓ Violations: Reinsertion violations (STRONG)')
    elif has_identity_theft_block_failure:
        score['violation_quality'] = 3
        score['notes'].append('✓ Violations: Identity theft block failures (STRONG)')
    elif has_generic_accuracy and len(violations) >= 3:
        score['violation_quality'] = 2
        score['notes'].append('⚠ Violations: Generic accuracy issues (DECENT)')
    elif len(violations) > 0:
        score['violation_quality'] = 1
        score['notes'].append('⚠ Violations: Weak violations present')
    else:
        score['violation_quality'] = 0
        score['notes'].append('✗ Violations: No violations identified')
    
    # WILLFULNESS SCORE (0-2 points)
    willful_count = sum(1 for v in violations if v.get('is_willful', False))
    total_violations = len(violations)
    
    if total_violations > 0:
        willfulness_ratio = willful_count / total_violations
        if willfulness_ratio >= 0.5:
            score['willfulness'] = 2
            score['notes'].append('✓ Willfulness: Strong indicators (50%+ willful)')
        elif willfulness_ratio >= 0.2:
            score['willfulness'] = 1
            score['notes'].append('⚠ Willfulness: Some indicators present')
        else:
            score['willfulness'] = 0
            score['notes'].append('⚠ Willfulness: Negligence only')
    
    # DOCUMENTATION SCORE (0-1 point)
    if documentation_complete:
        score['documentation'] = 1
        score['notes'].append('✓ Documentation: Complete records + denial letters')
    else:
        score['documentation'] = 0
        score['notes'].append('⚠ Documentation: Incomplete records')
    
    # TOTAL SCORE
    score['total'] = (
        score['standing'] +
        score['violation_quality'] +
        score['willfulness'] +
        score['documentation']
    )
    
    # SETTLEMENT PROBABILITY
    if score['total'] >= 8:
        score['settlement_probability'] = 0.85
        score['case_strength'] = 'Excellent'
        score['recommendation'] = 'ACCEPT - Strong case, high settlement probability'
    elif score['total'] >= 6:
        score['settlement_probability'] = 0.75
        score['case_strength'] = 'Strong'
        score['recommendation'] = 'ACCEPT - Good case, likely to settle'
    elif score['total'] >= 4:
        score['settlement_probability'] = 0.60
        score['case_strength'] = 'Decent'
        score['recommendation'] = 'ACCEPT - Acceptable case with fair settlement chance'
    elif score['total'] >= 2:
        score['settlement_probability'] = 0.40
        score['case_strength'] = 'Weak'
        score['recommendation'] = 'REVIEW - Weak case, may not justify investment'
    else:
        score['settlement_probability'] = 0.20
        score['case_strength'] = 'Very Weak'
        score['recommendation'] = 'REJECT - Case unlikely to succeed'
    
    return score


def assess_willfulness(violation_description, violation_type, bureau_responses=None):
    """
    Assess willfulness based on Safeco Insurance standards
    
    Returns:
        Dict with is_willful boolean and reasoning
    """
    willfulness = {
        'is_willful': False,
        'indicators': [],
        'level': 'Negligence'
    }
    
    description_lower = violation_description.lower() if violation_description else ''
    type_lower = violation_type.lower() if violation_type else ''
    
    # Strong willfulness indicators
    if 'reinsertion' in type_lower or 'reinsert' in description_lower:
        willfulness['is_willful'] = True
        willfulness['indicators'].append('Reinsertion violation (strong willfulness)')
        willfulness['level'] = 'Reckless Disregard'
    
    if 'metro 2' in description_lower and 'contradiction' in description_lower:
        willfulness['is_willful'] = True
        willfulness['indicators'].append('Metro 2 contradictions (systemic failure)')
        willfulness['level'] = 'Reckless Disregard'
    
    if 'multiple disputes' in description_lower or 'ignored' in description_lower:
        willfulness['is_willful'] = True
        willfulness['indicators'].append('Ignored multiple disputes')
        willfulness['level'] = 'Reckless Disregard'
    
    if 'documented proof' in description_lower and 'failed to correct' in description_lower:
        willfulness['is_willful'] = True
        willfulness['indicators'].append('Failed to correct despite proof')
        willfulness['level'] = 'Reckless Disregard'
    
    # Moderate willfulness indicators
    if 'pattern' in description_lower or 'systemic' in description_lower:
        willfulness['is_willful'] = True
        willfulness['indicators'].append('Pattern across multiple accounts')
        willfulness['level'] = 'Reckless Disregard'
    
    return willfulness
