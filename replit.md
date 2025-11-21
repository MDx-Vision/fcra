# FCRA Automation Server - Consumer Protection Litigation Platform

## Overview
A Python Flask-based FCRA automation server that receives credit report data via webhook, analyzes it using Claude AI (Anthropic) for comprehensive FCRA violations, and generates escalating dispute letters across multiple rounds (1-4) using the RLPP (Rapid Legal Protection Protocol) strategy.

The system supports both:
- **New client workflows**: Full analysis + Round 1 letters
- **Existing client workflows**: Context-aware escalated letters using previous dispute history and bureau responses

## Architecture

### Positioning
**Consumer Protection Litigation** (not credit repair)
- Federal law enforcement through FCRA compliance
- High-value legal strategy with sophisticated analysis
- Premium pricing justified by AI-powered comprehensive analysis

### Cost Optimization (November 21, 2025)
**Implemented three major cost reductions:**

1. **Anthropic Prompt Caching** (70-90% savings)
   - Caches the massive super_prompt (~80,000 tokens) across all requests
   - First request: Creates cache (normal cost)
   - Subsequent requests within 5 minutes: 90% discount on cached tokens
   - Typical savings: $0.90-2.70 per analysis
   - Cost: ~$1-3 → ~$0.10-0.40 per analysis

2. **Batch Processing** (maximizes cache efficiency)
   - New endpoint: `/webhook/batch` for processing multiple clients
   - All clients share the cached prompt
   - Process 10 clients within 5 minutes = 9 benefit from cache
   - Perfect for bulk client onboarding

3. **Real-time Cost Tracking**
   - Console logs show token usage breakdown
   - Displays cache creation/read tokens
   - Calculates actual cost vs. cost without caching
   - Shows savings percentage per request

### Expected Costs
- **Without optimization**: $1-3 per comprehensive analysis
- **With optimization**: $0.10-0.40 per analysis (first request creates cache)
- **Batch of 10 clients**: ~$1.50 total ($0.15 per client average)

## API Endpoints

### 1. `/` (GET)
Home page with web form for credit report submission
- Client information fields
- Dispute round selector (Round 1-4)
- Previous dispute context fields (shown for Round 2+)
- Analysis mode selector (Manual/Automatic)
- Credit report HTML input

### 2. `/webhook` (POST)
Single client analysis endpoint

**Request Body:**
```json
{
  "clientName": "John Doe",
  "cmmContactId": "CMM12345",
  "creditProvider": "IdentityIQ.com",
  "disputeRound": 1,
  "analysisMode": "manual",
  "creditReportHTML": "<html>...</html>",
  "previousLetters": "...",  // Round 2+ only
  "bureauResponses": "...",  // Round 2+ only
  "disputeTimeline": "..."   // Round 2+ only
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credit report received successfully! ✅",
  "client": "John Doe",
  "timestamp": "2025-11-21 12:30:45"
}
```

### 3. `/webhook/batch` (POST) - NEW
Batch client processing endpoint (maximizes cache efficiency)

**Request Body:**
```json
{
  "clients": [
    {
      "clientName": "Client 1",
      "cmmContactId": "CMM001",
      "creditProvider": "IdentityIQ.com",
      "disputeRound": 1,
      "analysisMode": "auto",
      "creditReportHTML": "<html>...</html>"
    },
    {
      "clientName": "Client 2",
      ...
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "total_clients": 10,
  "successful": 10,
  "failed": 0,
  "results": [
    {"client_name": "Client 1", "success": true},
    {"client_name": "Client 2", "success": true}
  ]
}
```

### 4. `/history` (GET)
View all processed reports summary

### 5. `/view/<report_id>` (GET)
View individual analysis results

### 6. `/clear` (POST)
Clear all stored reports (testing only)

## Features

### Dispute Round System
- **Round 1**: Initial Dispute (New Client) - Full FCRA analysis + strong RLPP letters
- **Round 2**: MOV Request / Follow-up - Escalated letters with bureau response analysis
- **Round 3**: Pre-Litigation Warning - Pre-suit demand letters
- **Round 4**: Final Demand / Intent to Sue - Final notice before federal filing

### Analysis Modes
- **Manual Review**: Stops at verification checkpoint (Part 4.5) for human review before generating client deliverables
- **Automatic**: Generates complete report immediately (full Parts 0-8)

### RLPP Strategy
Rapid Legal Protection Protocol - Strong legal language from Round 1 (not soft-then-aggressive)
- Bundled violations for maximum pressure
- Case law citations (Cushman v. TransUnion, Safeco Insurance v. Burr)
- Quantified damages exposure
- Makes deletion cheaper than investigation

## Project Structure
- `app.py` - Main Flask application (6,100+ lines)
  - Webhook endpoints
  - Claude AI integration with prompt caching
  - Batch processing support
  - Cost tracking and optimization
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore patterns

## How It Works

### Single Client Workflow
1. User submits credit report via web form
2. HTML is cleaned (removes styles, scripts, extracts text)
3. Reduced size by ~70-80% before sending to Claude
4. Claude analyzes using cached super_prompt framework
5. Generates 40-50 page analysis + dispute letters
6. Console logs show cost breakdown and savings
7. Results available at `/view/<id>`

### Batch Processing Workflow
1. Submit multiple clients to `/webhook/batch`
2. First client creates prompt cache
3. Next 9 clients (within 5 min) read from cache (90% discount)
4. All analyses run sequentially with shared context
5. Total cost: ~$0.15 per client average (vs. $1-3 without caching)

## Technical Details

### Prompt Caching Implementation
```python
system=[
    {
        "type": "text",
        "text": super_prompt,
        "cache_control": {"type": "ephemeral"}
    }
]
```

### Cost Calculation
- Input tokens: $3.00 per million
- Cached input tokens: $0.30 per million (90% discount)
- Output tokens: $15.00 per million

### Cache Behavior
- Cache TTL: 5 minutes (refreshed on each use)
- Cache is per-prompt (identical system prompts share cache)
- Perfect for batch processing within time window

## Recent Changes
- November 21, 2025: Implemented Anthropic prompt caching + batch processing + real-time cost tracking
- November 20, 2025: Added dispute round selector with escalation context for Round 2+ clients
- November 19, 2025: Initial Flask webhook server setup
- November 15, 2025: Claude AI integration with FCRA super_prompt v2.6

## User Preferences
- Cost-conscious but values AI quality over templates
- Accepts $1-3 per analysis as worthwhile investment
- Wants cost optimization without sacrificing analysis quality
- Prefers automation for clear cases, manual review for complex ones
