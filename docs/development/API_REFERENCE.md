# FCRA Litigation Platform - API Reference

## Overview

The FCRA Litigation Platform provides a comprehensive REST API for managing clients, cases, disputes, and credit report analysis. This document covers all available endpoints.

**Base URL:** `https://your-domain.com`

**API Version:** v1 (for external integrations)

---

## Table of Contents

1. [Authentication](#authentication)
2. [External API (v1)](#external-api-v1)
3. [Client Management](#client-management)
4. [Analysis & Disputes](#analysis--disputes)
5. [Litigation Tools](#litigation-tools)
6. [Communication](#communication)
7. [Webhooks](#webhooks)
8. [Rate Limits](#rate-limits)
9. [Error Handling](#error-handling)

---

## Authentication

### API Key Authentication

All external API endpoints require authentication via API key.

**Header Options:**
```
X-API-Key: ba_your_api_key_here
```
or
```
Authorization: Bearer ba_your_api_key_here
```

### Available Scopes

| Scope | Description |
|-------|-------------|
| `read:clients` | Read client information |
| `write:clients` | Create and update clients |
| `delete:clients` | Delete clients |
| `read:cases` | Read case information |
| `write:cases` | Create and update cases |
| `read:disputes` | Read dispute information |
| `write:disputes` | Create and manage disputes |
| `analyze:reports` | Submit credit reports for AI analysis |
| `read:letters` | Read and download dispute letters |
| `write:letters` | Generate dispute letters |
| `manage:webhooks` | Create and manage webhooks |

### Get Available Scopes

```http
GET /api/keys/scopes
```

**Response:**
```json
{
  "success": true,
  "scopes": {
    "read:clients": "Read client information",
    "write:clients": "Create and update clients",
    ...
  }
}
```

### Verify API Key

```http
GET /api/keys/verify
X-API-Key: ba_your_api_key_here
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "key_id": 1,
  "name": "My Integration",
  "scopes": ["read:clients", "write:clients"],
  "rate_limits": {
    "per_minute": 60,
    "per_day": 10000,
    "remaining_minute": 59,
    "remaining_day": 9999
  },
  "expires_at": null,
  "usage_count": 150
}
```

### Staff Login (Session Auth)

```http
POST /api/staff/login
Content-Type: application/json

{
  "email": "staff@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "staff_id": 1,
  "name": "John Doe",
  "role": "admin"
}
```

---

## External API (v1)

The v1 API is designed for third-party integrations and requires API key authentication.

### Validate API Key

```http
POST /api/v1/auth/validate
X-API-Key: ba_your_api_key_here
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "scopes": ["read:clients", "write:clients"],
  "tenant_id": null
}
```

---

### Clients

#### List Clients

```http
GET /api/v1/clients?page=1&per_page=20&status=active
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:clients`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Results per page (max 100) |
| `status` | string | - | Filter by status |

**Response:**
```json
{
  "success": true,
  "clients": [
    {
      "id": 1,
      "name": "John Doe",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "555-1234",
      "status": "active",
      "current_dispute_round": 1,
      "dispute_status": "in_progress",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### Get Client Details

```http
GET /api/v1/clients/{client_id}
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:clients`

**Response:**
```json
{
  "success": true,
  "client": {
    "id": 1,
    "name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "555-1234",
    "address_street": "123 Main St",
    "address_city": "New York",
    "address_state": "NY",
    "address_zip": "10001",
    "status": "active",
    "current_dispute_round": 1,
    "dispute_status": "in_progress",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-20T15:45:00Z"
  }
}
```

#### Create Client

```http
POST /api/v1/clients
X-API-Key: ba_your_api_key_here
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "address_street": "123 Main St",
  "address_city": "New York",
  "address_state": "NY",
  "address_zip": "10001"
}
```

**Required Scope:** `write:clients`

**Response:**
```json
{
  "success": true,
  "client_id": 123,
  "message": "Client created successfully"
}
```

#### Update Client

```http
PUT /api/v1/clients/{client_id}
X-API-Key: ba_your_api_key_here
Content-Type: application/json

{
  "phone": "555-5678",
  "status": "active"
}
```

**Required Scope:** `write:clients`

**Response:**
```json
{
  "success": true,
  "message": "Client updated successfully"
}
```

---

### Cases

#### List Cases

```http
GET /api/v1/cases?page=1&per_page=20&status=active
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:cases`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Results per page (max 100) |
| `status` | string | - | Filter by case status |

**Response:**
```json
{
  "success": true,
  "cases": [
    {
      "id": 1,
      "client_id": 1,
      "client_name": "John Doe",
      "status": "active",
      "case_type": "fcra_dispute",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3
  }
}
```

#### Get Case Details

```http
GET /api/v1/cases/{case_id}
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:cases`

**Response:**
```json
{
  "success": true,
  "case": {
    "id": 1,
    "client_id": 1,
    "client_name": "John Doe",
    "status": "active",
    "case_type": "fcra_dispute",
    "total_violations": 5,
    "total_damages_estimated": 15000,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### Get Case Violations

```http
GET /api/v1/cases/{case_id}/violations
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:cases`

**Response:**
```json
{
  "success": true,
  "violations": [
    {
      "id": 1,
      "account_name": "Capital One",
      "bureau": "Equifax",
      "fcra_section": "605B",
      "violation_type": "failure_to_investigate",
      "is_willful": true,
      "statutory_damages": 1000,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 5
}
```

#### Get Case Disputes

```http
GET /api/v1/cases/{case_id}/disputes
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:disputes`

---

### Disputes

#### List All Disputes

```http
GET /api/v1/disputes?page=1&per_page=20&status=pending
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:disputes`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Results per page |
| `status` | string | - | Filter by status |
| `bureau` | string | - | Filter by bureau |

#### Create Dispute

```http
POST /api/v1/disputes
X-API-Key: ba_your_api_key_here
Content-Type: application/json

{
  "client_id": 1,
  "bureau": "Equifax",
  "dispute_type": "accuracy",
  "account_name": "Capital One",
  "account_number": "****1234",
  "dispute_reason": "Account reported incorrectly"
}
```

**Required Scope:** `write:disputes`

**Response:**
```json
{
  "success": true,
  "dispute_id": 45,
  "message": "Dispute created successfully"
}
```

#### Get Dispute Status

```http
GET /api/v1/disputes/{dispute_id}/status
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:disputes`

**Response:**
```json
{
  "success": true,
  "dispute": {
    "id": 45,
    "status": "pending",
    "bureau": "Equifax",
    "created_at": "2025-01-15T10:30:00Z",
    "last_updated": "2025-01-20T15:45:00Z"
  }
}
```

---

### Analysis

#### Submit Credit Report for Analysis

```http
POST /api/v1/analyze
X-API-Key: ba_your_api_key_here
Content-Type: application/json

{
  "client_id": 1,
  "credit_report_html": "<html>...credit report content...</html>",
  "dispute_round": 1
}
```

**Required Scope:** `analyze:reports`

**Response:**
```json
{
  "success": true,
  "analysis_id": 123,
  "status": "processing",
  "message": "Analysis queued successfully"
}
```

#### Get Analysis Results

```http
GET /api/v1/analysis/{analysis_id}
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:cases`

**Response:**
```json
{
  "success": true,
  "analysis": {
    "id": 123,
    "client_id": 1,
    "status": "completed",
    "dispute_round": 1,
    "violations_found": 5,
    "total_statutory_damages": 5000,
    "total_actual_damages": 10000,
    "case_score": 8.5,
    "letters_generated": 3,
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:35:00Z"
  }
}
```

---

### Violations

#### List All Violations

```http
GET /api/v1/violations?page=1&per_page=20
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `read:cases`

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Results per page |
| `fcra_section` | string | - | Filter by FCRA section |
| `bureau` | string | - | Filter by bureau |
| `is_willful` | bool | - | Filter by willfulness |

---

### Webhooks

#### List Webhooks

```http
GET /api/v1/webhooks
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `manage:webhooks`

**Response:**
```json
{
  "success": true,
  "webhooks": [
    {
      "id": 1,
      "name": "Case Updates",
      "url": "https://your-server.com/webhook",
      "events": ["case.created", "case.updated"],
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Webhook

```http
POST /api/v1/webhooks
X-API-Key: ba_your_api_key_here
Content-Type: application/json

{
  "name": "Case Updates",
  "url": "https://your-server.com/webhook",
  "events": ["case.created", "case.updated", "dispute.resolved"]
}
```

**Required Scope:** `manage:webhooks`

**Available Events:**
- `case.created` - New case created
- `case.updated` - Case status changed
- `case.closed` - Case closed
- `dispute.created` - New dispute filed
- `dispute.updated` - Dispute status changed
- `dispute.resolved` - Dispute resolved
- `letter.generated` - Dispute letter generated
- `letter.sent` - Letter sent via certified mail
- `analysis.completed` - AI analysis completed

**Response:**
```json
{
  "success": true,
  "webhook_id": 5,
  "secret": "whsec_abc123...",
  "message": "Webhook created. Store the secret securely."
}
```

#### Delete Webhook

```http
DELETE /api/v1/webhooks/{webhook_id}
X-API-Key: ba_your_api_key_here
```

**Required Scope:** `manage:webhooks`

---

## Client Management

### Internal Client Endpoints

These endpoints use session authentication (staff login).

#### Create Client

```http
POST /api/clients/create
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "address_street": "123 Main St",
  "address_city": "New York",
  "address_state": "NY",
  "address_zip": "10001"
}
```

**Response:**
```json
{
  "success": true,
  "client_id": 123
}
```

#### Update Client Status

```http
POST /api/clients/{client_id}/status
Content-Type: application/json

{
  "status": "active",
  "client_type": "premium",
  "follow_up_date": "2025-02-01"
}
```

#### Delete Client

```http
POST /api/clients/{client_id}/delete
```

#### Get Client Tags

```http
GET /api/clients/{client_id}/tags
```

#### Add Tag to Client

```http
POST /api/clients/{client_id}/tags
Content-Type: application/json

{
  "tag_id": 5
}
```

#### Remove Tag from Client

```http
DELETE /api/clients/{client_id}/tags/{tag_id}
```

---

## Analysis & Disputes

### Submit Analysis

```http
POST /api/analyze
Content-Type: application/json

{
  "clientName": "John Doe",
  "clientEmail": "john@example.com",
  "creditProvider": "MyScoreIQ",
  "creditReportHTML": "<html>...</html>",
  "disputeRound": 1,
  "analysisMode": "auto"
}
```

**Response:**
```json
{
  "success": true,
  "analysis_id": 123,
  "letters": [
    {"bureau": "Equifax", "letter_id": 1},
    {"bureau": "Experian", "letter_id": 2},
    {"bureau": "TransUnion", "letter_id": 3}
  ],
  "cost": {
    "input_tokens": 15000,
    "output_tokens": 8000,
    "total_cost": 0.25
  }
}
```

### Download Letter

```http
GET /api/download/{letter_id}
```

Returns PDF file.

### Download All Letters (ZIP)

```http
GET /api/analysis/{analysis_id}/download_all
```

Returns ZIP file with all dispute letters.

### Get Analysis Data

```http
GET /api/analysis/{analysis_id}/data
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "id": 123,
    "client_name": "John Doe",
    "dispute_round": 1,
    "status": "completed",
    "violations": [...],
    "standing": {...},
    "damages": {...},
    "case_score": {...}
  }
}
```

### Add Violation

```http
POST /api/analysis/{analysis_id}/violations
Content-Type: application/json

{
  "account_name": "Capital One",
  "bureau": "Equifax",
  "fcra_section": "605B",
  "violation_type": "failure_to_investigate",
  "description": "Bureau failed to investigate dispute",
  "is_willful": true
}
```

### Get Standing

```http
GET /api/analysis/{analysis_id}/standing
```

### Calculate Damages

```http
POST /api/analysis/{analysis_id}/damages
```

### Get Case Score

```http
GET /api/analysis/{analysis_id}/score
```

**Response:**
```json
{
  "success": true,
  "score": {
    "total_score": 8.5,
    "standing_score": 3,
    "violation_quality_score": 4,
    "willfulness_score": 1.5,
    "settlement_probability": 75,
    "case_strength": "Strong",
    "recommendations": [
      "Pursue settlement negotiations",
      "Document additional harm evidence"
    ]
  }
}
```

---

## Litigation Tools

### Generate Demand Letter

```http
POST /api/generate/demand-letter/{client_id}
Content-Type: application/json

{
  "letter_type": "pre_litigation",
  "recipient": "Equifax",
  "settlement_demand": 15000
}
```

### Generate Client Report

```http
POST /api/generate/client-report/{analysis_id}
```

### Generate Internal Memo

```http
POST /api/generate/internal-memo/{analysis_id}
```

---

## Communication

### Send SMS

```http
POST /api/sms/send
Content-Type: application/json

{
  "client_id": 1,
  "message": "Your dispute letters have been generated."
}
```

### Send Email

```http
POST /api/email/send
Content-Type: application/json

{
  "client_id": 1,
  "template": "dispute_update",
  "subject": "Update on Your Dispute",
  "custom_message": "Additional information..."
}
```

### Get SMS Logs

```http
GET /api/sms/logs?client_id=1
```

---

## Webhooks

### Webhook Payload Format

All webhook payloads follow this format:

```json
{
  "event": "case.updated",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "case_id": 123,
    "client_id": 1,
    "status": "active",
    ...
  }
}
```

### Webhook Signature Verification

Webhooks include a signature header for verification:

```
X-Webhook-Signature: sha256=abc123...
```

Verify using HMAC-SHA256:
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Rate Limits

### Default Limits

| Endpoint Type | Limit |
|---------------|-------|
| Standard API | 100 requests/minute |
| Authentication | 5 requests/minute |
| AI Analysis | 10 requests/minute |
| Bulk Operations | 5 requests/minute |

### Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 59
X-RateLimit-Limit-Day: 10000
X-RateLimit-Remaining-Day: 9999
```

### Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "rate_limits": {
    "minute_remaining": 0,
    "minute_reset": "2025-01-15T10:31:00Z",
    "day_remaining": 500,
    "day_reset": "2025-01-16T00:00:00Z"
  }
}
```

**HTTP Status:** 429 Too Many Requests

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message here",
  "code": "ERROR_CODE",
  "details": {}
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | API key is invalid or revoked |
| `EXPIRED_API_KEY` | API key has expired |
| `INSUFFICIENT_SCOPE` | Missing required scope |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `VALIDATION_ERROR` | Request validation failed |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `DUPLICATE_ENTRY` | Resource already exists |

---

## API Documentation Endpoint

```http
GET /api/v1/docs
```

Returns interactive API documentation.

---

## Configuration Status

Check which services are configured:

```http
GET /api/admin/config-status
```

**Requires:** Admin session authentication

**Response:**
```json
{
  "success": true,
  "environment": "production",
  "is_production": true,
  "services": {
    "anthropic": true,
    "sendgrid": true,
    "twilio": true,
    "stripe": false,
    "sendcertified": false,
    "notarize": false,
    "database": true,
    "encryption": true
  },
  "log_level": "INFO"
}
```

---

## SDK Examples

### Python

```python
import requests

API_KEY = "ba_your_api_key_here"
BASE_URL = "https://your-domain.com"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# List clients
response = requests.get(
    f"{BASE_URL}/api/v1/clients",
    headers=headers,
    params={"page": 1, "per_page": 20}
)
clients = response.json()

# Create client
new_client = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "phone": "555-5678"
}
response = requests.post(
    f"{BASE_URL}/api/v1/clients",
    headers=headers,
    json=new_client
)
result = response.json()
```

### JavaScript

```javascript
const API_KEY = "ba_your_api_key_here";
const BASE_URL = "https://your-domain.com";

// List clients
const response = await fetch(`${BASE_URL}/api/v1/clients?page=1`, {
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
  }
});
const clients = await response.json();

// Create client
const newClient = await fetch(`${BASE_URL}/api/v1/clients`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    first_name: "Jane",
    last_name: "Smith",
    email: "jane@example.com"
  })
});
```

### cURL

```bash
# List clients
curl -X GET "https://your-domain.com/api/v1/clients" \
  -H "X-API-Key: ba_your_api_key_here"

# Create client
curl -X POST "https://your-domain.com/api/v1/clients" \
  -H "X-API-Key: ba_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}'
```

---

**Last Updated:** December 25, 2025
**API Version:** 1.0
