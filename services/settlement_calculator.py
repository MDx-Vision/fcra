"""
Settlement Calculator Service for FCRA Cases.
Calculates potential settlement ranges based on violations and damages.
"""
from datetime import datetime
from database import SessionLocal, SettlementEstimate


def format_currency(amount):
    """
    Format a numeric amount as a currency string.
    
    Args:
        amount: Numeric amount (int or float)
        
    Returns:
        Formatted currency string (e.g., "$1,234.56")
    """
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"


def calculate_settlement(case_id, client_id, violations_data):
    """
    Calculate potential settlement ranges for an FCRA case.
    
    Args:
        case_id: The case ID (can be None for estimates without a case)
        client_id: The client ID
        violations_data: Dict containing:
            - total_violations: int
            - willful_violations: int
            - negligent_violations: int
            - actual_damages_items: list of {type, amount, description}
    
    Returns:
        Dict with settlement calculation results and saved SettlementEstimate ID
    """
    total_violations = violations_data.get('total_violations', 0)
    willful_violations = violations_data.get('willful_violations', 0)
    negligent_violations = violations_data.get('negligent_violations', 0)
    actual_damages_items = violations_data.get('actual_damages_items', [])
    
    statutory_low, statutory_high = _calculate_statutory_damages(willful_violations)
    
    actual_damages, actual_damages_breakdown = _calculate_actual_damages(actual_damages_items)
    
    punitive_low, punitive_high = _calculate_punitive_damages(statutory_low, statutory_high)
    
    total_low = statutory_low + actual_damages + punitive_low
    total_high = statutory_high + actual_damages + punitive_high
    
    attorney_fees_low = _calculate_attorney_fees(total_low, 0.30)
    attorney_fees_high = _calculate_attorney_fees(total_high, 0.40)
    attorney_fees_estimate = (attorney_fees_low + attorney_fees_high) / 2
    
    settlement_likelihood = _determine_settlement_likelihood(
        willful_violations, total_high
    )
    
    recommended_demand = _calculate_recommended_demand(total_low, total_high)
    
    calculation_data = {
        'input': {
            'total_violations': total_violations,
            'willful_violations': willful_violations,
            'negligent_violations': negligent_violations,
            'actual_damages_items': actual_damages_items
        },
        'statutory': {
            'low': statutory_low,
            'high': statutory_high,
            'low_formatted': format_currency(statutory_low),
            'high_formatted': format_currency(statutory_high)
        },
        'punitive': {
            'low': punitive_low,
            'high': punitive_high,
            'low_multiplier': 1.0,
            'high_multiplier': 3.0,
            'low_formatted': format_currency(punitive_low),
            'high_formatted': format_currency(punitive_high)
        },
        'actual_damages': {
            'total': actual_damages,
            'breakdown': actual_damages_breakdown,
            'formatted': format_currency(actual_damages)
        },
        'attorney_fees': {
            'low': attorney_fees_low,
            'high': attorney_fees_high,
            'estimate': attorney_fees_estimate,
            'low_percent': 0.30,
            'high_percent': 0.40,
            'formatted': format_currency(attorney_fees_estimate)
        },
        'totals': {
            'low': total_low,
            'high': total_high,
            'low_formatted': format_currency(total_low),
            'high_formatted': format_currency(total_high)
        },
        'settlement_likelihood': settlement_likelihood,
        'recommended_demand': recommended_demand,
        'recommended_demand_formatted': format_currency(recommended_demand),
        'calculated_at': datetime.utcnow().isoformat()
    }
    
    calculation_notes = _generate_calculation_notes(
        willful_violations, negligent_violations, 
        statutory_low, statutory_high,
        actual_damages, punitive_low, punitive_high,
        total_low, total_high, settlement_likelihood, recommended_demand
    )
    
    estimate_id = _save_settlement_estimate(
        client_id=client_id,
        case_id=case_id,
        total_violations=total_violations,
        willful_violations=willful_violations,
        negligent_violations=negligent_violations,
        statutory_damages_low=statutory_low,
        statutory_damages_high=statutory_high,
        actual_damages=actual_damages,
        actual_damages_breakdown=actual_damages_breakdown,
        punitive_damages_low=punitive_low,
        punitive_damages_high=punitive_high,
        attorney_fees_estimate=attorney_fees_estimate,
        total_low=total_low,
        total_high=total_high,
        settlement_likelihood=settlement_likelihood,
        recommended_demand=recommended_demand,
        calculation_notes=calculation_notes,
        calculation_data=calculation_data
    )
    
    return {
        'success': True,
        'estimate_id': estimate_id,
        'statutory_damages_low': statutory_low,
        'statutory_damages_high': statutory_high,
        'actual_damages': actual_damages,
        'actual_damages_breakdown': actual_damages_breakdown,
        'punitive_damages_low': punitive_low,
        'punitive_damages_high': punitive_high,
        'attorney_fees_estimate': attorney_fees_estimate,
        'total_low': total_low,
        'total_high': total_high,
        'settlement_likelihood': settlement_likelihood,
        'recommended_demand': recommended_demand,
        'calculation_notes': calculation_notes,
        'formatted': {
            'statutory_low': format_currency(statutory_low),
            'statutory_high': format_currency(statutory_high),
            'actual_damages': format_currency(actual_damages),
            'punitive_low': format_currency(punitive_low),
            'punitive_high': format_currency(punitive_high),
            'attorney_fees': format_currency(attorney_fees_estimate),
            'total_low': format_currency(total_low),
            'total_high': format_currency(total_high),
            'recommended_demand': format_currency(recommended_demand)
        }
    }


def _calculate_statutory_damages(willful_violations):
    """
    Calculate statutory damages range for willful violations.
    
    FCRA allows $100-$1,000 per willful violation.
    Negligent violations only allow actual damages (no statutory).
    
    Args:
        willful_violations: Number of willful violations
        
    Returns:
        Tuple of (low_estimate, high_estimate)
    """
    if willful_violations <= 0:
        return (0.0, 0.0)
    
    low_per_violation = 100.0
    high_per_violation = 1000.0
    
    statutory_low = willful_violations * low_per_violation
    statutory_high = willful_violations * high_per_violation
    
    return (statutory_low, statutory_high)


def _calculate_punitive_damages(statutory_low, statutory_high):
    """
    Calculate punitive damages range.
    
    Punitive damages are typically 1x-3x the statutory damages for willful violations.
    
    Args:
        statutory_low: Low statutory damages estimate
        statutory_high: High statutory damages estimate
        
    Returns:
        Tuple of (low_estimate, high_estimate)
    """
    low_multiplier = 1.0
    high_multiplier = 3.0
    
    punitive_low = statutory_low * low_multiplier
    punitive_high = statutory_high * high_multiplier
    
    return (punitive_low, punitive_high)


def _calculate_actual_damages(actual_damages_items):
    """
    Calculate actual damages from itemized breakdown.
    
    Valid damage categories:
    - credit_denial: Damages from denied credit applications
    - higher_interest: Extra costs from higher interest rates
    - emotional_distress: Mental anguish and emotional harm
    - lost_employment: Income lost due to credit issues
    - medical_costs: Medical expenses from stress/anxiety
    - time_spent: Value of time spent dealing with credit issues
    
    Args:
        actual_damages_items: List of dicts with {type, amount, description}
        
    Returns:
        Tuple of (total_amount, breakdown_dict)
    """
    valid_categories = [
        'credit_denial', 'higher_interest', 'emotional_distress',
        'lost_employment', 'medical_costs', 'time_spent'
    ]
    
    breakdown = {cat: {'amount': 0.0, 'items': []} for cat in valid_categories}
    breakdown['other'] = {'amount': 0.0, 'items': []}
    
    total = 0.0
    
    for item in actual_damages_items:
        item_type = item.get('type', 'other')
        amount = float(item.get('amount', 0))
        description = item.get('description', '')
        
        if item_type not in valid_categories:
            item_type = 'other'
        
        breakdown[item_type]['amount'] += amount
        breakdown[item_type]['items'].append({
            'amount': amount,
            'description': description,
            'formatted': format_currency(amount)
        })
        total += amount
    
    for cat in breakdown:
        breakdown[cat]['formatted'] = format_currency(breakdown[cat]['amount'])
    
    return (total, breakdown)


def _calculate_attorney_fees(total_recovery, fee_percentage):
    """
    Calculate attorney fees estimate.
    
    FCRA allows fee shifting (defendant pays plaintiff's attorney fees).
    Typical estimates are 30-40% of total recovery.
    
    Args:
        total_recovery: Total expected recovery amount
        fee_percentage: Fee percentage (0.30 for 30%, 0.40 for 40%)
        
    Returns:
        Estimated attorney fees
    """
    return total_recovery * fee_percentage


def _determine_settlement_likelihood(willful_violations, total_high):
    """
    Determine the likelihood of settlement.
    
    Criteria:
    - 'high': willful violations > 3 AND total_high > $10,000
    - 'medium': total_high > $5,000
    - 'low': otherwise
    
    Args:
        willful_violations: Number of willful violations
        total_high: High end of total damages estimate
        
    Returns:
        Settlement likelihood string ('high', 'medium', or 'low')
    """
    if willful_violations > 3 and total_high > 10000:
        return 'high'
    elif total_high > 5000:
        return 'medium'
    else:
        return 'low'


def _calculate_recommended_demand(total_low, total_high):
    """
    Calculate recommended initial demand amount.
    
    Typically 2x-3x of expected value (average of low and high estimates).
    Uses 2.5x as the middle ground.
    
    Args:
        total_low: Low end of total damages
        total_high: High end of total damages
        
    Returns:
        Recommended demand amount
    """
    expected_value = (total_low + total_high) / 2
    demand_multiplier = 2.5
    
    return expected_value * demand_multiplier


def _generate_calculation_notes(
    willful_violations, negligent_violations,
    statutory_low, statutory_high,
    actual_damages, punitive_low, punitive_high,
    total_low, total_high, settlement_likelihood, recommended_demand
):
    """
    Generate human-readable calculation notes.
    
    Returns:
        Formatted string explaining the calculation
    """
    notes = []
    
    notes.append("FCRA Settlement Calculation Summary")
    notes.append("=" * 40)
    notes.append("")
    
    notes.append("VIOLATIONS:")
    notes.append(f"  Willful violations: {willful_violations}")
    notes.append(f"  Negligent violations: {negligent_violations}")
    notes.append("")
    
    notes.append("STATUTORY DAMAGES (Willful only @ $100-$1,000 each):")
    notes.append(f"  Low estimate: {format_currency(statutory_low)}")
    notes.append(f"  High estimate: {format_currency(statutory_high)}")
    notes.append("")
    
    notes.append("ACTUAL DAMAGES:")
    notes.append(f"  Total: {format_currency(actual_damages)}")
    notes.append("")
    
    notes.append("PUNITIVE DAMAGES (1x-3x statutory for willful):")
    notes.append(f"  Low estimate (1x): {format_currency(punitive_low)}")
    notes.append(f"  High estimate (3x): {format_currency(punitive_high)}")
    notes.append("")
    
    notes.append("TOTAL RECOVERY RANGE:")
    notes.append(f"  Low: {format_currency(total_low)}")
    notes.append(f"  High: {format_currency(total_high)}")
    notes.append("")
    
    notes.append(f"SETTLEMENT LIKELIHOOD: {settlement_likelihood.upper()}")
    notes.append(f"RECOMMENDED INITIAL DEMAND: {format_currency(recommended_demand)}")
    notes.append("")
    
    notes.append("Note: Attorney fees are recoverable under FCRA fee-shifting")
    notes.append("provisions and are not included in the demand amount.")
    
    return "\n".join(notes)


def _save_settlement_estimate(
    client_id, case_id, total_violations, willful_violations, negligent_violations,
    statutory_damages_low, statutory_damages_high, actual_damages, actual_damages_breakdown,
    punitive_damages_low, punitive_damages_high, attorney_fees_estimate,
    total_low, total_high, settlement_likelihood, recommended_demand,
    calculation_notes, calculation_data
):
    """
    Save the settlement estimate to the database.
    
    Returns:
        The ID of the created SettlementEstimate record
    """
    db = SessionLocal()
    try:
        estimate = SettlementEstimate(
            client_id=client_id,
            case_id=case_id,
            total_violations=total_violations,
            willful_violations=willful_violations,
            negligent_violations=negligent_violations,
            statutory_damages_low=statutory_damages_low,
            statutory_damages_high=statutory_damages_high,
            actual_damages=actual_damages,
            actual_damages_breakdown=actual_damages_breakdown,
            punitive_multiplier=3.0,
            punitive_damages_low=punitive_damages_low,
            punitive_damages_high=punitive_damages_high,
            attorney_fees_estimate=attorney_fees_estimate,
            total_low=total_low,
            total_high=total_high,
            settlement_likelihood=settlement_likelihood,
            recommended_demand=recommended_demand,
            calculation_notes=calculation_notes,
            calculation_data=calculation_data
        )
        db.add(estimate)
        db.commit()
        db.refresh(estimate)
        return estimate.id
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to save settlement estimate: {str(e)}")
    finally:
        db.close()


def get_settlement_estimate(estimate_id):
    """
    Retrieve a settlement estimate by ID.
    
    Args:
        estimate_id: The ID of the settlement estimate
        
    Returns:
        SettlementEstimate object or None
    """
    db = SessionLocal()
    try:
        estimate = db.query(SettlementEstimate).filter(
            SettlementEstimate.id == estimate_id
        ).first()
        return estimate
    finally:
        db.close()


def get_client_settlement_estimates(client_id):
    """
    Retrieve all settlement estimates for a client.
    
    Args:
        client_id: The client ID
        
    Returns:
        List of SettlementEstimate objects
    """
    db = SessionLocal()
    try:
        estimates = db.query(SettlementEstimate).filter(
            SettlementEstimate.client_id == client_id
        ).order_by(SettlementEstimate.created_at.desc()).all()
        return estimates
    finally:
        db.close()
