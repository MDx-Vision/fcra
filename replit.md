# Brightpath Ascend FCRA Platform

## Overview
The Brightpath Ascend FCRA Platform is a production-ready system designed for consumer protection litigation, specifically focusing on FCRA (Fair Credit Reporting Act) violations. It automates the analysis of credit reports and generates all necessary legal documentation for litigation, serving as a full litigation management tool. The platform aims to facilitate robust legal action against credit reporting agencies and generate significant revenue through a tiered pricing model.

## User Preferences
- Cost-conscious but values AI quality (accepts $1-3 per analysis)
- Wants automation for clear cases, manual review for complex ones
- Building full litigation platform (not just credit repair)
- Target: 50 clients waiting, $600K-900K year-1 revenue with 3-tier pricing model
- Prefers analytical, data-driven decisions with clear case metrics

## System Architecture
The platform is built on a Flask web framework and employs a two-stage, section-based analysis approach to overcome token limits and enhance analytical depth.

### UI/UX Decisions
- **Admin Dashboard**: Professional case management interface at `/dashboard` for pipeline visualization, client lists, and case details.
- **Client Portal**: Branded client-facing portal at `/portal/<token>` for case status.
- **Review Checkpoints**: Dedicated interfaces (`/analysis/<id>/review`) for manual review and editing of AI-extracted data.
- **PDF Generation**: Client-facing documents (action plans, case summaries) use Brightpath Ascend branding with teal-to-lime gradient headers. External correspondence (freeze letters, validation letters to bureaus/creditors) remain unbranded for professional consumer letters.

### Technical Implementations
- **Two-Stage Analysis**:
    - **Stage 1 (Section-Based Analysis)**: Credit reports are split into sections. Anthropic Claude analyzes each section, extracting violations, assessing standing, and calculating damages. Results are intelligently merged.
    - **Stage 2 (Comprehensive Document Generation)**: Claude generates a forensic litigation package, including standing analysis, violation analysis, willfulness assessment, settlement analysis, and dispute letters.
- **Automated Data Extraction**: Claude outputs structured JSON data, which is automatically parsed to populate the database.
- **PDF Generation**: Modular PDF generators create detailed reports and letters.
- **Security**: Password encryption using Fernet symmetric encryption.
- **Rapid Legal Protection Protocol (RLPP)**: A strategy for tactical bundling of violations and escalation of dispute rounds.
- **Automation Tools Dashboard**: A 6-tab admin interface for services like Freeze Letters, Validation Letters, Deadlines, Settlement Calculator, Certified Mail, and Notarization.
- **Action Plan Generator**: Creates branded action plan PDFs with case overviews, deadlines, task checklists, and cost estimates.
- **Mobile Document Scanner** (`/scanner`): Multi-page document scanning with:
  - Camera capture or file upload
  - Multi-page queue with visual "Add More Pages" prompt
  - Automatic PDF generation from images
  - Claude Vision OCR text extraction (~$0.01-0.03/page)
  - CRA Response round selection (R1, R2, R3, R4) for dispute tracking
  - Document types: CRA Responses, Collection Letters, Creditor Responses, Court Documents, ID, Proof of Address
  - Note: Credit reports pulled via API integrations, not scanned
  - **Client Portal Integration**: Scanner accessible at `/portal/<token>/scanner` - documents automatically linked to client
  - **Admin Review Dashboard**: `/dashboard/scanned-documents` shows all scanned docs with OCR text preview
- **E-Signature System**: Client-facing signature capture for various legal documents.
- **Metro2 Violation Detection API**: Detects 10 types of Metro2 format violations with auto-generated dispute language and damage calculation.
- **PWA Support**: Progressive Web App manifest and service worker for offline caching and push notifications.
- **Email/SMS Automation**: SendGrid and Twilio-powered systems for automated client communications with configurable templates and merge tags.
- **Document Center**: Unified document upload system with type-first selection and admin review workflow.
- **Flexible Signup System**: Configurable fields and multi-payment options (Stripe, PayPal, etc.).
- **Credit Score Improvement Tracker** (`/dashboard/credit-tracker`): Comprehensive score tracking and projection system with:
  - **Quick Estimator**: Simple current score + negative count for rough projections
  - **Detailed Calculator**: 35+ specific negative item types with accurate impact ranges based on industry research
  - **Item Categories**: Payment History, Derogatory Marks, Public Records, Credit Utilization, Credit Inquiries, Reporting Errors, Fraud/Identity Theft, Account Status
  - **Severity Levels**: Low, Moderate, High, Severe, Critical - each with color coding and accurate impact ranges
  - **Per-Item Impact Data**: Different items have different score impacts (e.g., hard inquiry +5-15 pts vs collection +50-110 pts vs bankruptcy +130-240 pts)
  - **Client Progress Tracking**: Before/after scores, items removed, timeline visualization
  - **Score Snapshots**: Track Equifax, Experian, TransUnion scores over time with dispute round correlation
  - **Client Portal Integration**: Score Progress tab shows clients their improvement journey with Chart.js visualizations
  - **API Endpoints**: `/api/credit-score/item-types`, `/api/credit-score/estimate-detailed`, `/api/credit-score/projection/<id>`, `/api/credit-score/history/<id>`
- **Client Avatar/Photo Feature**: Personalized client experience with profile photos:
  - **Client Portal Profile Tab**: New "My Profile" tab with avatar upload/remove functionality
  - **Header Display**: Avatar shown in portal header with initials fallback
  - **Admin Dashboard Integration**: Client avatars displayed in case lists and client tables
  - **Security**: File extension validation, MIME type checking, 5MB size limit, secure_filename sanitization
  - **API Endpoints**: `POST/DELETE /api/portal/<token>/avatar`, `POST /api/client/<id>/avatar`
  - **Storage**: Avatars stored in `static/avatars/` with timestamped unique filenames

### Feature Specifications
- Full FCRA violation detection with section identification.
- Post-TransUnion standing analysis, willfulness assessment, and statute of limitations verification.
- Comprehensive damages calculation (statutory, actual, punitive).
- Case scoring (1-10 scale).
- Cost tracking for token usage and cache savings.

### System Design Choices
- **Scalability**: Section-based analysis ensures scalability for credit report sizes and large client bases.
- **Cost Efficiency**: Prompt caching reduces API costs.
- **Data Integrity**: Intelligent sectioning and analysis prevent data loss.
- **Workflow Optimization**: Verification checkpoints ensure accuracy and control.

## External Dependencies
- **Flask**: Python web framework.
- **Anthropic Claude 3 Sonnet 4**: Primary AI analysis engine.
- **PostgreSQL**: Database solution, backed by Neon.
- **SQLAlchemy**: ORM for database interactions.
- **Fernet**: For symmetric encryption.
- **Stripe**: Payment processing.
- **Twilio**: SMS automation.
- **SendGrid**: Email automation.