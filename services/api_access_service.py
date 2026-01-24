"""
API Access Service
Manages API keys, rate limiting, request logging, and webhooks for third-party integrations
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests  # type: ignore[import-untyped]
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    API_SCOPES,
    WEBHOOK_EVENTS,
    APIKey,
    APIRequest,
    APIWebhook,
    Staff,
    get_db,
)


class RateLimiter:
    """In-memory rate limiter for API requests"""

    def __init__(self):
        self._minute_counts = defaultdict(lambda: {"count": 0, "reset_at": None})
        self._day_counts = defaultdict(lambda: {"count": 0, "reset_at": None})

    def check_and_increment(
        self, key_id: int, per_minute: int, per_day: int
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limits and increment counters
        Returns (is_allowed, rate_limit_info)
        """
        now = datetime.utcnow()

        minute_key = f"minute:{key_id}"
        day_key = f"day:{key_id}"

        minute_data = self._minute_counts[minute_key]
        if minute_data["reset_at"] is None or minute_data["reset_at"] <= now:
            minute_data["count"] = 0
            minute_data["reset_at"] = now + timedelta(minutes=1)

        day_data = self._day_counts[day_key]
        if day_data["reset_at"] is None or day_data["reset_at"] <= now:
            day_data["count"] = 0
            day_data["reset_at"] = now + timedelta(days=1)

        rate_info = {
            "minute_remaining": max(0, per_minute - minute_data["count"]),
            "minute_limit": per_minute,
            "minute_reset": minute_data["reset_at"].isoformat(),
            "day_remaining": max(0, per_day - day_data["count"]),
            "day_limit": per_day,
            "day_reset": day_data["reset_at"].isoformat(),
        }

        if minute_data["count"] >= per_minute:
            return False, {**rate_info, "error": "Rate limit exceeded (per minute)"}

        if day_data["count"] >= per_day:
            return False, {**rate_info, "error": "Rate limit exceeded (per day)"}

        minute_data["count"] += 1
        day_data["count"] += 1
        rate_info["minute_remaining"] -= 1
        rate_info["day_remaining"] -= 1

        return True, rate_info

    def get_usage(self, key_id: int) -> dict:
        """Get current usage stats for a key"""
        minute_data = self._minute_counts.get(f"minute:{key_id}", {"count": 0})
        day_data = self._day_counts.get(f"day:{key_id}", {"count": 0})
        return {
            "minute_count": minute_data.get("count", 0),
            "day_count": day_data.get("count", 0),
        }


rate_limiter = RateLimiter()


class APIAccessService:
    """Service for managing API access, keys, and webhooks"""

    def __init__(self, db: Any = None):
        self.db = db

    def _get_db(self) -> Tuple[Any, bool]:
        """Get database session"""
        if self.db:
            return self.db, False
        return get_db(), True

    def generate_api_key(
        self,
        name: str,
        staff_id: int,
        scopes: List[str],
        rate_limit_per_minute: int = 60,
        rate_limit_per_day: int = 10000,
        tenant_id: Optional[int] = None,
        expires_in_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a new API key
        Returns the full key only once - it's not stored in plaintext
        """
        db, should_close = self._get_db()
        try:
            raw_key = f"ba_{secrets.token_urlsafe(32)}"
            key_prefix = raw_key[:8]
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            api_key = APIKey(
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                staff_id=staff_id,
                tenant_id=tenant_id,
                scopes=scopes,
                rate_limit_per_minute=rate_limit_per_minute,
                rate_limit_per_day=rate_limit_per_day,
                expires_at=expires_at,
                is_active=True,
            )

            db.add(api_key)
            db.commit()
            db.refresh(api_key)

            return {
                "success": True,
                "api_key": raw_key,
                "key_prefix": key_prefix,
                "key_id": api_key.id,
                "name": name,
                "scopes": scopes,
                "rate_limit_per_minute": rate_limit_per_minute,
                "rate_limit_per_day": rate_limit_per_day,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "message": "Store this API key securely - it will not be shown again!",
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def validate_api_key(self, raw_key: str) -> Tuple[Optional[APIKey], Optional[str]]:
        """
        Validate an API key and return the key object if valid
        Returns (api_key, error_message)
        """
        if not raw_key:
            return None, "API key is required"

        raw_key = raw_key.strip()
        if raw_key.startswith("Bearer "):
            raw_key = raw_key[7:]

        if len(raw_key) < 8:
            return None, "Invalid API key format"

        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        db, should_close = self._get_db()
        try:
            api_key = (
                db.query(APIKey)
                .filter(APIKey.key_hash == key_hash, APIKey.key_prefix == key_prefix)
                .first()
            )

            if not api_key:
                return None, "Invalid API key"

            if not api_key.is_active:
                return None, "API key has been revoked"

            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return None, "API key has expired"

            api_key.last_used_at = datetime.utcnow()
            api_key.usage_count = (api_key.usage_count or 0) + 1
            db.commit()

            return api_key, None
        except Exception as e:
            return None, f"Validation error: {str(e)}"
        finally:
            if should_close:
                db.close()

    def revoke_api_key(
        self, key_id: int, staff_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Revoke an API key"""
        db, should_close = self._get_db()
        try:
            api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

            if not api_key:
                return {"success": False, "error": "API key not found"}

            if staff_id and api_key.staff_id != staff_id:
                staff = db.query(Staff).filter_by(id=staff_id).first()
                if not staff or staff.role != "admin":
                    return {"success": False, "error": "Permission denied"}

            api_key.is_active = False
            api_key.updated_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "message": f'API key "{api_key.name}" has been revoked',
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def rotate_api_key(
        self, key_id: int, staff_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rotate an API key - generates a new key and invalidates the old one
        Returns the new key (only shown once)
        """
        db, should_close = self._get_db()
        try:
            old_key = db.query(APIKey).filter(APIKey.id == key_id).first()

            if not old_key:
                return {"success": False, "error": "API key not found"}

            if not old_key.is_active:
                return {"success": False, "error": "Cannot rotate an inactive key"}

            if staff_id and old_key.staff_id != staff_id:
                from database import Staff

                staff = db.query(Staff).filter_by(id=staff_id).first()
                if not staff or staff.role != "admin":
                    return {"success": False, "error": "Permission denied"}

            raw_key = f"ba_{secrets.token_urlsafe(32)}"
            key_prefix = raw_key[:8]
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            old_key.key_hash = key_hash
            old_key.key_prefix = key_prefix
            old_key.updated_at = datetime.utcnow()

            db.commit()

            return {
                "success": True,
                "api_key": raw_key,
                "key_prefix": key_prefix,
                "key_id": old_key.id,
                "name": old_key.name,
                "message": "API key rotated successfully. Store this new key securely - it will not be shown again!",
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def check_rate_limit(
        self, key_id: int, per_minute: int = 60, per_day: int = 10000
    ) -> Tuple[bool, dict]:
        """
        Check if a key is within rate limits
        Returns (is_allowed, rate_info)
        """
        return rate_limiter.check_and_increment(key_id, per_minute, per_day)

    def log_request(
        self,
        key_id: int,
        endpoint: str,
        method: str,
        request_ip: str,
        response_status: int,
        response_time_ms: int,
        request_headers: Optional[dict] = None,
        request_body: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Log an API request for analytics"""
        db, should_close = self._get_db()
        try:
            safe_headers = {}
            if request_headers:
                for k, v in request_headers.items():
                    if k.lower() not in ["authorization", "cookie", "x-api-key"]:
                        safe_headers[k] = v

            safe_body = None
            if request_body:
                safe_body = {
                    k: v
                    for k, v in request_body.items()
                    if k.lower()
                    not in ["password", "secret", "token", "key", "ssn", "credit_card"]
                }

            log = APIRequest(
                api_key_id=key_id,
                endpoint=endpoint,
                method=method,
                request_ip=request_ip,
                request_headers=safe_headers,
                request_body=safe_body,
                response_status=response_status,
                response_time_ms=response_time_ms,
                error_message=error_message,
            )

            db.add(log)

            api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
            if api_key:
                api_key.last_used_ip = request_ip

            db.commit()
            return True
        except Exception as e:
            print(f"Failed to log API request: {e}")
            return False
        finally:
            if should_close:
                db.close()

    def get_key_usage_stats(self, key_id: int, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for an API key"""
        db, should_close = self._get_db()
        try:
            api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
            if not api_key:
                return {"success": False, "error": "API key not found"}

            start_date = datetime.utcnow() - timedelta(days=days)

            requests = (
                db.query(APIRequest)
                .filter(
                    APIRequest.api_key_id == key_id, APIRequest.created_at >= start_date
                )
                .all()
            )

            total_requests = len(requests)
            successful_requests = sum(
                1 for r in requests if 200 <= r.response_status < 300
            )
            error_requests = sum(1 for r in requests if r.response_status >= 400)
            avg_response_time = (
                sum(r.response_time_ms or 0 for r in requests) / total_requests
                if total_requests > 0
                else 0
            )

            endpoint_counts: Dict[str, int] = defaultdict(int)
            daily_counts: Dict[str, int] = defaultdict(int)
            status_counts: Dict[str, int] = defaultdict(int)

            for r in requests:
                endpoint_counts[r.endpoint] += 1
                day_key = (
                    r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown"
                )
                daily_counts[day_key] += 1
                status_counts[str(r.response_status)] += 1

            current_usage = rate_limiter.get_usage(key_id)

            return {
                "success": True,
                "key_id": key_id,
                "key_name": api_key.name,
                "period_days": days,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "error_requests": error_requests,
                "success_rate": (
                    (successful_requests / total_requests * 100)
                    if total_requests > 0
                    else 0
                ),
                "avg_response_time_ms": round(avg_response_time, 2),
                "top_endpoints": dict(
                    sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[
                        :10
                    ]
                ),
                "daily_usage": dict(sorted(daily_counts.items())),
                "status_codes": dict(status_counts),
                "current_minute_usage": current_usage["minute_count"],
                "current_day_usage": current_usage["day_count"],
                "rate_limit_per_minute": api_key.rate_limit_per_minute,
                "rate_limit_per_day": api_key.rate_limit_per_day,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def list_api_keys(
        self, staff_id: Optional[int] = None, tenant_id: Optional[int] = None
    ) -> List[Dict]:
        """List API keys, optionally filtered by staff or tenant"""
        db, should_close = self._get_db()
        try:
            query = db.query(APIKey)

            if staff_id:
                query = query.filter(APIKey.staff_id == staff_id)
            if tenant_id:
                query = query.filter(APIKey.tenant_id == tenant_id)

            keys = query.order_by(APIKey.created_at.desc()).all()
            return [k.to_dict() for k in keys]
        finally:
            if should_close:
                db.close()

    def create_webhook(
        self, name: str, url: str, events: List[str], tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new webhook"""
        db, should_close = self._get_db()
        try:
            invalid_events = [e for e in events if e not in WEBHOOK_EVENTS]
            if invalid_events:
                return {
                    "success": False,
                    "error": f"Invalid events: {invalid_events}. Valid events are: {WEBHOOK_EVENTS}",
                }

            secret = secrets.token_urlsafe(32)

            webhook = APIWebhook(
                name=name,
                url=url,
                secret=secret,
                events=events,
                tenant_id=tenant_id,
                is_active=True,
            )

            db.add(webhook)
            db.commit()
            db.refresh(webhook)

            return {
                "success": True,
                "webhook": webhook.to_dict(),
                "secret": secret,
                "message": "Store this webhook secret securely!",
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def delete_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """Delete a webhook"""
        db, should_close = self._get_db()
        try:
            webhook = db.query(APIWebhook).filter(APIWebhook.id == webhook_id).first()
            if not webhook:
                return {"success": False, "error": "Webhook not found"}

            db.delete(webhook)
            db.commit()

            return {"success": True, "message": f'Webhook "{webhook.name}" deleted'}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def list_webhooks(self, tenant_id: Optional[int] = None) -> List[Dict]:
        """List webhooks, optionally filtered by tenant"""
        db, should_close = self._get_db()
        try:
            query = db.query(APIWebhook)
            if tenant_id:
                query = query.filter(APIWebhook.tenant_id == tenant_id)

            webhooks = query.order_by(APIWebhook.created_at.desc()).all()
            return [w.to_dict() for w in webhooks]
        finally:
            if should_close:
                db.close()

    def trigger_webhook(
        self, event_type: str, payload: dict, tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trigger webhooks for a specific event
        Sends to all matching active webhooks
        """
        db, should_close = self._get_db()
        results = []

        try:
            query = db.query(APIWebhook).filter(APIWebhook.is_active == True)

            if tenant_id:
                query = query.filter(APIWebhook.tenant_id == tenant_id)

            webhooks = query.all()

            for webhook in webhooks:
                if event_type not in (webhook.events or []):
                    continue

                timestamp = int(time.time())
                payload_json = json.dumps(payload)
                signature = self.generate_webhook_signature(
                    payload_json, webhook.secret, timestamp
                )

                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Timestamp": str(timestamp),
                    "X-Webhook-Event": event_type,
                }

                try:
                    response = requests.post(
                        webhook.url, data=payload_json, headers=headers, timeout=10
                    )

                    webhook.last_triggered = datetime.utcnow()

                    if response.status_code >= 400:
                        webhook.failure_count += 1
                        results.append(
                            {
                                "webhook_id": webhook.id,
                                "success": False,
                                "status_code": response.status_code,
                                "error": response.text[:200],
                            }
                        )
                    else:
                        webhook.failure_count = 0
                        results.append(
                            {
                                "webhook_id": webhook.id,
                                "success": True,
                                "status_code": response.status_code,
                            }
                        )

                    if webhook.failure_count >= 5:
                        webhook.is_active = False

                except requests.RequestException as e:
                    webhook.failure_count += 1
                    webhook.last_triggered = datetime.utcnow()
                    results.append(
                        {"webhook_id": webhook.id, "success": False, "error": str(e)}
                    )

            db.commit()

            return {
                "success": True,
                "event_type": event_type,
                "webhooks_triggered": len(results),
                "results": results,
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if should_close:
                db.close()

    def generate_webhook_signature(
        self, payload: str, secret: str, timestamp: int
    ) -> str:
        """Generate HMAC signature for webhook payload"""
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return f"v1={signature}"

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
        timestamp: int,
        max_age_seconds: int = 300,
    ) -> bool:
        """Verify a webhook signature"""
        current_time = int(time.time())
        if abs(current_time - timestamp) > max_age_seconds:
            return False

        expected_signature = self.generate_webhook_signature(payload, secret, timestamp)
        return hmac.compare_digest(signature, expected_signature)

    def get_api_documentation(self) -> Dict[str, Any]:
        """Return OpenAPI specification for the API"""
        base_url = os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Brightpath Ascend FCRA Platform API",
                "description": "RESTful API for third-party integrations with the Brightpath Ascend FCRA litigation platform.",
                "version": "1.0.0",
                "contact": {
                    "name": "Brightpath Ascend Support",
                    "email": "support@brightpathascend.com",
                },
            },
            "servers": [{"url": f"{base_url}/api/v1", "description": "Production API"}],
            "security": [{"bearerAuth": []}],
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "description": "API key authentication. Use your API key as the bearer token.",
                    }
                },
                "schemas": {
                    "Client": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "phone": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": [
                                    "signup",
                                    "active",
                                    "paused",
                                    "complete",
                                    "cancelled",
                                ],
                            },
                            "current_dispute_round": {"type": "integer"},
                            "created_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "Case": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "client_id": {"type": "integer"},
                            "case_number": {"type": "string"},
                            "status": {"type": "string"},
                            "created_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "Violation": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "bureau": {"type": "string"},
                            "account_name": {"type": "string"},
                            "fcra_section": {"type": "string"},
                            "violation_type": {"type": "string"},
                            "description": {"type": "string"},
                            "is_willful": {"type": "boolean"},
                        },
                    },
                    "Dispute": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "client_id": {"type": "integer"},
                            "account_name": {"type": "string"},
                            "bureau": {"type": "string"},
                            "status": {"type": "string"},
                            "round": {"type": "integer"},
                        },
                    },
                    "Error": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": False},
                            "error": {"type": "string"},
                        },
                    },
                },
            },
            "paths": {
                "/auth/validate": {
                    "post": {
                        "summary": "Validate API Key",
                        "description": "Validate your API key and get key information",
                        "tags": ["Authentication"],
                        "responses": {
                            "200": {"description": "Key is valid"},
                            "401": {"description": "Invalid or expired key"},
                        },
                    }
                },
                "/clients": {
                    "get": {
                        "summary": "List Clients",
                        "description": "Get paginated list of clients",
                        "tags": ["Clients"],
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "schema": {"type": "integer", "default": 1},
                            },
                            {
                                "name": "per_page",
                                "in": "query",
                                "schema": {"type": "integer", "default": 20},
                            },
                            {
                                "name": "status",
                                "in": "query",
                                "schema": {"type": "string"},
                            },
                        ],
                        "responses": {
                            "200": {"description": "List of clients"},
                            "403": {"description": "Insufficient scope"},
                        },
                    },
                    "post": {
                        "summary": "Create Client",
                        "description": "Create a new client",
                        "tags": ["Clients"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Client"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Client created"},
                            "400": {"description": "Invalid request"},
                        },
                    },
                },
                "/clients/{id}": {
                    "get": {
                        "summary": "Get Client",
                        "description": "Get client details by ID",
                        "tags": ["Clients"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {"description": "Client details"},
                            "404": {"description": "Client not found"},
                        },
                    },
                    "put": {
                        "summary": "Update Client",
                        "description": "Update client information",
                        "tags": ["Clients"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {"description": "Client updated"},
                            "404": {"description": "Client not found"},
                        },
                    },
                },
                "/cases": {
                    "get": {
                        "summary": "List Cases",
                        "description": "Get paginated list of cases",
                        "tags": ["Cases"],
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "schema": {"type": "integer", "default": 1},
                            },
                            {
                                "name": "per_page",
                                "in": "query",
                                "schema": {"type": "integer", "default": 20},
                            },
                            {
                                "name": "status",
                                "in": "query",
                                "schema": {"type": "string"},
                            },
                            {
                                "name": "client_id",
                                "in": "query",
                                "schema": {"type": "integer"},
                            },
                        ],
                        "responses": {"200": {"description": "List of cases"}},
                    }
                },
                "/cases/{id}": {
                    "get": {
                        "summary": "Get Case",
                        "description": "Get case details by ID",
                        "tags": ["Cases"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {"description": "Case details"},
                            "404": {"description": "Case not found"},
                        },
                    }
                },
                "/cases/{id}/violations": {
                    "get": {
                        "summary": "Get Case Violations",
                        "description": "Get all violations for a case",
                        "tags": ["Cases"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {"200": {"description": "List of violations"}},
                    }
                },
                "/disputes": {
                    "post": {
                        "summary": "Create Dispute",
                        "description": "Create a new dispute",
                        "tags": ["Disputes"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Dispute"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Dispute created"},
                            "400": {"description": "Invalid request"},
                        },
                    }
                },
                "/disputes/{id}/status": {
                    "get": {
                        "summary": "Get Dispute Status",
                        "description": "Get current status of a dispute",
                        "tags": ["Disputes"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {"description": "Dispute status"},
                            "404": {"description": "Dispute not found"},
                        },
                    }
                },
                "/analyze": {
                    "post": {
                        "summary": "Submit Analysis",
                        "description": "Submit credit report for FCRA analysis",
                        "tags": ["Analysis"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["client_id", "credit_report_html"],
                                        "properties": {
                                            "client_id": {"type": "integer"},
                                            "credit_report_html": {"type": "string"},
                                            "dispute_round": {
                                                "type": "integer",
                                                "default": 1,
                                            },
                                        },
                                    }
                                }
                            }
                        },
                        "responses": {"202": {"description": "Analysis queued"}},
                    }
                },
                "/analysis/{id}": {
                    "get": {
                        "summary": "Get Analysis Results",
                        "description": "Get results of a completed analysis",
                        "tags": ["Analysis"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {"description": "Analysis results"},
                            "404": {"description": "Analysis not found"},
                        },
                    }
                },
                "/webhooks": {
                    "get": {
                        "summary": "List Webhooks",
                        "description": "Get list of registered webhooks",
                        "tags": ["Webhooks"],
                        "responses": {"200": {"description": "List of webhooks"}},
                    },
                    "post": {
                        "summary": "Create Webhook",
                        "description": "Register a new webhook endpoint",
                        "tags": ["Webhooks"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name", "url", "events"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "url": {"type": "string", "format": "uri"},
                                            "events": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string",
                                                    "enum": [
                                                        "client.created",
                                                        "client.updated",
                                                        "case.created",
                                                        "case.status_changed",
                                                        "dispute.created",
                                                        "dispute.status_changed",
                                                        "analysis.completed",
                                                        "document.generated",
                                                        "settlement.updated",
                                                    ],
                                                },
                                            },
                                        },
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Webhook created"},
                            "400": {"description": "Invalid request"},
                        },
                    },
                },
                "/webhooks/{id}": {
                    "delete": {
                        "summary": "Delete Webhook",
                        "description": "Delete a webhook",
                        "tags": ["Webhooks"],
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {
                            "200": {"description": "Webhook deleted"},
                            "404": {"description": "Webhook not found"},
                        },
                    }
                },
            },
            "tags": [
                {"name": "Authentication", "description": "API key validation"},
                {"name": "Clients", "description": "Client management"},
                {"name": "Cases", "description": "Case management"},
                {"name": "Disputes", "description": "Dispute management"},
                {"name": "Analysis", "description": "FCRA analysis"},
                {"name": "Webhooks", "description": "Webhook management"},
            ],
        }


def get_api_access_service(db: Any = None) -> APIAccessService:
    """Factory function to get API access service instance"""
    return APIAccessService(db)
