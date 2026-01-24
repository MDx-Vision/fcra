# Credit Score Simulator Implementation Checklist

> Priority 31: Credit Score Simulator for Client Portal
>
> **Created**: 2026-01-18
> **Status**: IN PROGRESS

---

## Overview

Add an interactive credit score simulator to the client portal that lets clients see projected score improvements based on which negative items get removed.

**Key Features:**
- "What-if" scenario modeling
- Per-item impact estimation
- Before/after visualization
- Goal setting (target score)
- Save scenarios for tracking

---

## Phase 1: Database Model (If Needed)

### 1.1 Check Existing Models
- [x] `CreditScoreSnapshot` - Already exists (tracks score over time)
- [x] `CreditScoreProjection` - Already exists (stores projections)
- [ ] `ScoreScenario` - NEW model needed for saved "what-if" scenarios

### 1.2 Add ScoreScenario Model
```python
class ScoreScenario(Base):
    __tablename__ = 'score_scenarios'

    id: Integer (PK)
    client_id: Integer (FK -> Client)
    name: String (e.g., "Best Case", "Conservative")
    current_score: Integer
    projected_score: Integer
    selected_items: JSON  # List of item IDs selected for removal
    item_breakdown: JSON  # Detailed breakdown by item type
    goal_score: Integer (nullable)
    notes: Text
    is_favorite: Boolean (default False)
    created_at: DateTime
    updated_at: DateTime
```

---

## Phase 2: Backend Service Enhancement

### 2.1 Extend Credit Score Calculator
- [x] `get_all_item_types()` - Already exists
- [x] `estimate_by_item_types()` - Already exists
- [x] `calculate_client_projection()` - Already exists
- [ ] `simulate_with_items(client_id, item_ids)` - NEW: Simulate specific items
- [ ] `save_scenario(client_id, scenario_data)` - NEW: Save scenario
- [ ] `get_client_scenarios(client_id)` - NEW: List saved scenarios
- [ ] `delete_scenario(scenario_id)` - NEW: Delete scenario
- [ ] `get_goal_recommendations(current_score, target_score)` - NEW

### 2.2 Portal-Specific Functions
- [ ] `get_client_dispute_items_with_impact(client_id)` - Get items with estimated impact
- [ ] `calculate_scenario_for_portal(client_id, selected_item_ids)` - Portal-safe projection

---

## Phase 3: Portal API Endpoints

### 3.1 New Portal Endpoints (routes/portal.py)
- [ ] `GET /portal/score-simulator` - Simulator page route
- [ ] `GET /portal/api/score/current` - Get current scores
- [ ] `GET /portal/api/score/items` - Get dispute items with impacts
- [ ] `POST /portal/api/score/simulate` - Run "what-if" simulation
- [ ] `GET /portal/api/score/scenarios` - List saved scenarios
- [ ] `POST /portal/api/score/scenarios` - Save scenario
- [ ] `DELETE /portal/api/score/scenarios/<id>` - Delete scenario
- [ ] `GET /portal/api/score/goal-tips` - Get tips to reach goal

---

## Phase 4: Portal UI

### 4.1 Score Simulator Page (`templates/portal/score_simulator.html`)
- [ ] Current score display (all 3 bureaus)
- [ ] Score range indicator (Poor → Excellent)
- [ ] Interactive item selection (checkboxes)
- [ ] Per-item impact preview on hover
- [ ] "Simulate" button
- [ ] Results panel with:
  - [ ] Current vs Projected comparison
  - [ ] Score gauge visualization
  - [ ] Item breakdown table
  - [ ] Confidence level indicator
- [ ] Goal setting:
  - [ ] Target score input
  - [ ] "What do I need to remove?" calculator
- [ ] Save scenario button
- [ ] Saved scenarios list

### 4.2 Visualizations
- [ ] Score gauge (semi-circular, color-coded)
- [ ] Before/after bar chart
- [ ] Item impact breakdown (horizontal bars)
- [ ] Score range color bands (Poor/Fair/Good/Very Good/Excellent)

### 4.3 Mobile Responsive
- [ ] Stacked layout for mobile
- [ ] Touch-friendly item selection
- [ ] Collapsible sections

---

## Phase 5: Unit Tests

### 5.1 Create Tests (`tests/test_score_simulator_service.py`)
- [ ] Test scenario CRUD
- [ ] Test simulation calculations
- [ ] Test goal recommendations
- [ ] Test portal-safe projections
- [ ] Test with various score ranges
- [ ] Test with no items
- [ ] Test with all items selected

---

## Implementation Progress

| Phase | Status | Tests Before | Tests After |
|-------|--------|--------------|-------------|
| Phase 1: Database | ⏳ Pending | 5807 | - |
| Phase 2: Service | ⏳ Pending | - | - |
| Phase 3: API | ⏳ Pending | - | - |
| Phase 4: UI | ⏳ Pending | - | - |
| Phase 5: Tests | ⏳ Pending | - | - |

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `database.py` | MODIFY | Add ScoreScenario model |
| `services/credit_score_calculator.py` | MODIFY | Add scenario functions |
| `routes/portal.py` | MODIFY | Add simulator endpoints |
| `templates/portal/score_simulator.html` | CREATE | Simulator page |
| `templates/portal/base_portal.html` | MODIFY | Add nav link |
| `tests/test_score_simulator_service.py` | CREATE | Unit tests |

---

## Design Notes

### Score Impact Factors (from existing service)
- Collections: 50-110 points
- Charge-offs: 55-120 points
- Late payments: 15-95 points (varies by severity)
- Bankruptcies: 100-240 points
- Inquiries: 5-35 points
- Public records: 40-160 points

### Confidence Levels
- High: Item type well-documented, removal likely
- Medium: Standard estimation
- Low: Complex situation, many variables

### UI Color Scheme
- Poor (300-579): Red
- Fair (580-669): Orange
- Good (670-739): Yellow
- Very Good (740-799): Light Green
- Excellent (800-850): Green

---

*Last Updated: 2026-01-18*
