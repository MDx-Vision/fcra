"""
AI Usage Tracking Service

Tracks Claude API usage, calculates costs, and provides reporting.

Pricing (Claude Sonnet 4 - as of Jan 2025):
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens

Usage:
    from services.ai_usage_service import log_ai_usage, get_usage_stats

    # After an API call:
    log_ai_usage(
        service="dispute_writer",
        operation="generate_letters",
        model="claude-sonnet-4-20250514",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        duration_ms=elapsed_ms,
        client_id=client.id
    )
"""

import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

from sqlalchemy import extract, func

from database import AIUsageLog, get_db

# Claude pricing per 1M tokens (in dollars)
PRICING = {
    "claude-sonnet-4-20250514": {
        "input": 3.00,  # $3 per 1M input tokens
        "output": 15.00,  # $15 per 1M output tokens
    },
    "claude-opus-4-5-20251101": {
        "input": 15.00,  # $15 per 1M input tokens
        "output": 75.00,  # $75 per 1M output tokens
    },
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    # Default fallback
    "default": {"input": 3.00, "output": 15.00},
}


def calculate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> tuple:
    """
    Calculate cost in cents for given token usage.

    Returns:
        tuple: (input_cost_cents, output_cost_cents, total_cost_cents)
    """
    pricing = PRICING.get(model, PRICING["default"])

    # Cost = (tokens / 1,000,000) * price_per_million * 100 (for cents)
    input_cost = (input_tokens / 1_000_000) * pricing["input"] * 100
    output_cost = (output_tokens / 1_000_000) * pricing["output"] * 100
    total_cost = input_cost + output_cost

    return int(input_cost), int(output_cost), int(total_cost)


def log_ai_usage(
    service: str,
    operation: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int = 0,
    client_id: int = None,
    staff_id: int = None,
    dispute_round: int = None,
    letter_type: str = None,
    success: bool = True,
    error_message: str = None,
) -> Optional[AIUsageLog]:
    """
    Log an AI API call with token usage and cost.

    Args:
        service: Service name (dispute_writer, chat_support, etc.)
        operation: Operation type (generate_letters, chat_message, etc.)
        model: Model name (claude-sonnet-4-20250514, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        duration_ms: API call duration in milliseconds
        client_id: Associated client ID (optional)
        staff_id: Staff who initiated (optional)
        dispute_round: Dispute round number (optional)
        letter_type: Type of letter generated (optional)
        success: Whether the call succeeded
        error_message: Error message if failed

    Returns:
        AIUsageLog record or None if failed
    """
    db = get_db()
    try:
        input_cost, output_cost, total_cost = calculate_cost_cents(
            model, input_tokens, output_tokens
        )

        log = AIUsageLog(
            client_id=client_id,
            staff_id=staff_id,
            service=service,
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost_cents=input_cost,
            output_cost_cents=output_cost,
            total_cost_cents=total_cost,
            duration_ms=duration_ms,
            dispute_round=dispute_round,
            letter_type=letter_type,
            success=success,
            error_message=error_message,
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    except Exception as e:
        print(f"Error logging AI usage: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def get_usage_summary(days: int = 30, client_id: int = None) -> Dict[str, Any]:
    """
    Get usage summary for the specified period.

    Args:
        days: Number of days to look back
        client_id: Filter by client (optional)

    Returns:
        Dictionary with usage statistics
    """
    db = get_db()
    try:
        since = datetime.utcnow() - timedelta(days=days)

        query = db.query(AIUsageLog).filter(AIUsageLog.created_at >= since)
        if client_id:
            query = query.filter(AIUsageLog.client_id == client_id)

        logs = query.all()

        total_input = sum(log.input_tokens or 0 for log in logs)
        total_output = sum(log.output_tokens or 0 for log in logs)
        total_cost = sum(log.total_cost_cents or 0 for log in logs)
        total_calls = len(logs)
        successful_calls = len([log for log in logs if log.success])

        # Group by service
        by_service = {}
        for log in logs:
            if log.service not in by_service:
                by_service[log.service] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_cents": 0,
                }
            by_service[log.service]["calls"] += 1
            by_service[log.service]["input_tokens"] += log.input_tokens or 0
            by_service[log.service]["output_tokens"] += log.output_tokens or 0
            by_service[log.service]["cost_cents"] += log.total_cost_cents or 0

        # Group by day for chart
        by_day = {}
        for log in logs:
            day = log.created_at.strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = {"calls": 0, "cost_cents": 0, "tokens": 0}
            by_day[day]["calls"] += 1
            by_day[day]["cost_cents"] += log.total_cost_cents or 0
            by_day[day]["tokens"] += log.total_tokens or 0

        return {
            "period_days": days,
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_cents": total_cost,
            "total_cost_dollars": total_cost / 100,
            "avg_cost_per_call_cents": (
                total_cost / total_calls if total_calls > 0 else 0
            ),
            "by_service": by_service,
            "by_day": dict(sorted(by_day.items())),
        }

    except Exception as e:
        print(f"Error getting usage summary: {e}")
        return {"error": str(e)}
    finally:
        db.close()


def get_usage_by_client(days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get usage breakdown by client.

    Returns:
        List of clients with their usage stats, sorted by cost descending
    """
    db = get_db()
    try:
        since = datetime.utcnow() - timedelta(days=days)

        results = (
            db.query(
                AIUsageLog.client_id,
                func.count(AIUsageLog.id).label("total_calls"),
                func.sum(AIUsageLog.input_tokens).label("total_input"),
                func.sum(AIUsageLog.output_tokens).label("total_output"),
                func.sum(AIUsageLog.total_cost_cents).label("total_cost"),
            )
            .filter(AIUsageLog.created_at >= since, AIUsageLog.client_id.isnot(None))
            .group_by(AIUsageLog.client_id)
            .order_by(func.sum(AIUsageLog.total_cost_cents).desc())
            .limit(limit)
            .all()
        )

        # Get client names
        from database import Client

        clients = []
        for r in results:
            client = db.query(Client).filter_by(id=r.client_id).first()
            clients.append(
                {
                    "client_id": r.client_id,
                    "client_name": client.name if client else "Unknown",
                    "total_calls": r.total_calls,
                    "total_input_tokens": r.total_input or 0,
                    "total_output_tokens": r.total_output or 0,
                    "total_cost_cents": r.total_cost or 0,
                    "total_cost_dollars": (r.total_cost or 0) / 100,
                }
            )

        return clients

    except Exception as e:
        print(f"Error getting usage by client: {e}")
        return []
    finally:
        db.close()


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent AI usage logs."""
    db = get_db()
    try:
        logs = (
            db.query(AIUsageLog)
            .order_by(AIUsageLog.created_at.desc())
            .limit(limit)
            .all()
        )

        return [log.to_dict() for log in logs]

    except Exception as e:
        print(f"Error getting recent logs: {e}")
        return []
    finally:
        db.close()


def get_monthly_report(year: int = None, month: int = None) -> Dict[str, Any]:
    """
    Get monthly usage report.

    Args:
        year: Year (defaults to current)
        month: Month (defaults to current)

    Returns:
        Monthly usage statistics
    """
    db = get_db()
    try:
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month

        # Get first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1)
        else:
            last_day = datetime(year, month + 1, 1)

        logs = (
            db.query(AIUsageLog)
            .filter(
                AIUsageLog.created_at >= first_day, AIUsageLog.created_at < last_day
            )
            .all()
        )

        total_input = sum(log.input_tokens or 0 for log in logs)
        total_output = sum(log.output_tokens or 0 for log in logs)
        total_cost = sum(log.total_cost_cents or 0 for log in logs)

        # By operation type
        by_operation = {}
        for log in logs:
            key = f"{log.service}:{log.operation}"
            if key not in by_operation:
                by_operation[key] = {"calls": 0, "cost_cents": 0}
            by_operation[key]["calls"] += 1
            by_operation[key]["cost_cents"] += log.total_cost_cents or 0

        return {
            "year": year,
            "month": month,
            "month_name": first_day.strftime("%B %Y"),
            "total_calls": len(logs),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_cents": total_cost,
            "total_cost_dollars": total_cost / 100,
            "by_operation": by_operation,
        }

    except Exception as e:
        print(f"Error getting monthly report: {e}")
        return {"error": str(e)}
    finally:
        db.close()


# Decorator for timing and logging AI calls
def track_ai_usage(service: str, operation: str):
    """
    Decorator to automatically track AI API calls.

    Usage:
        @track_ai_usage("dispute_writer", "generate_letters")
        def generate_letters(self, client_id, ...):
            response = self.anthropic_client.messages.create(...)
            return response

    Note: The decorated function should return the Anthropic response object
    or a dict with 'response' key containing the response object.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)

                # Extract response object
                response = result
                if isinstance(result, dict) and "response" in result:
                    response = result["response"]

                # Log usage if response has usage info
                if hasattr(response, "usage"):
                    log_ai_usage(
                        service=service,
                        operation=operation,
                        model=getattr(response, "model", "unknown"),
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                        duration_ms=duration_ms,
                        client_id=kwargs.get("client_id"),
                        staff_id=kwargs.get("staff_id"),
                        success=True,
                    )

                return result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                log_ai_usage(
                    service=service,
                    operation=operation,
                    model="unknown",
                    input_tokens=0,
                    output_tokens=0,
                    duration_ms=duration_ms,
                    client_id=kwargs.get("client_id"),
                    staff_id=kwargs.get("staff_id"),
                    success=False,
                    error_message=str(e),
                )
                raise

        return wrapper

    return decorator
