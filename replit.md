# Brightpath Ascend FCRA Platform

## Overview
The Brightpath Ascend FCRA Platform is a comprehensive, production-ready system designed for consumer protection litigation, specifically focusing on FCRA (Fair Credit Reporting Act) violations. It automates the analysis of credit reports and generates all necessary legal documentation for litigation. The platform aims to serve as a full litigation management tool, moving beyond simple credit repair to facilitate robust legal action against credit reporting agencies. It is envisioned to generate significant revenue through a tiered pricing model, targeting a substantial client base.

## User Preferences
- Cost-conscious but values AI quality (accepts $1-3 per analysis)
- Wants automation for clear cases, manual review for complex ones
- Building full litigation platform (not just credit repair)
- Target: 50 clients waiting, $600K-900K year-1 revenue with 3-tier pricing model
- Prefers analytical, data-driven decisions with clear case metrics

## System Architecture
The platform is built on a Flask web framework and employs a novel two-stage, section-based analysis approach to overcome token limits and enhance analytical depth.

### UI/UX Decisions
- **Admin Dashboard**: Professional case management interface at `/dashboard` for pipeline visualization, client lists, and case details.
- **Client Portal**: Branded client-facing portal at `/portal/<token>` for case status.
- **Review Checkpoints**: Dedicated interfaces (`/analysis/<id>/review`) for manual review and editing of AI-extracted data before document generation.
- **PDF Generation**: Documents are generated with specific formatting (e.g., blue text for manual review encouragement) for clarity and legal efficacy.

### Technical Implementations
- **Two-Stage Analysis**:
    - **Stage 1 (Section-Based Analysis)**: Credit reports (of any size, 100MB+) are intelligently split into sections (tradelines, collections, public records, inquiries). Anthropic Claude analyzes each section separately to avoid token limits, extracting violations, assessing standing, and calculating damages. Results are then intelligently merged (e.g., violations tagged by source, standing OR'ed, damages summed).
    - **Stage 2 (Comprehensive Document Generation)**: Upon approval of Stage 1 findings, Claude generates an 80-120 page forensic litigation package, including standing analysis, violation analysis, willfulness assessment, settlement analysis, and dispute letters (Rounds 1-4).
- **Intelligent Data Merging**: Violations are tagged with their source section, standing is determined using OR logic across sections, and damages are summed.
- **Rapid Legal Protection Protocol (RLPP)**: A strategy for tactical bundling of violations and escalation of dispute rounds (R1-R4) to maximize impact.
- **Automated Data Extraction**: Claude outputs structured JSON data (`<LITIGATION_DATA>`) which is automatically parsed to populate the database, eliminating manual data entry.
- **PDF Generation**: Modular PDF generators (ClientReportBuilder, InternalMemoBuilder, RoundLetterBuilder) create detailed reports and letters.
- **Security**: Password encryption using Fernet symmetric encryption with environment-managed keys.

### Feature Specifications
- Full FCRA violation detection with section identification.
- Post-TransUnion standing analysis (concrete harm, dissemination, causation).
- Willfulness assessment based on the Safeco standard.
- Statute of limitations verification.
- Comprehensive damages calculation (statutory, actual, punitive).
- Case scoring (1-10 scale) based on various factors.
- Cost tracking for token usage and cache savings.

### System Design Choices
- **Scalability**: The section-based approach ensures infinite scalability for credit report sizes and efficient processing for a large client base.
- **Cost Efficiency**: Prompt caching significantly reduces API costs for repeat analyses and batch processing.
- **Data Integrity**: Zero data loss due to intelligent sectioning and analysis.
- **Workflow Optimization**: Integration of verification checkpoints for manual review ensures accuracy and control.

## External Dependencies
- **Flask**: Python web framework.
- **Anthropic Claude 3 Sonnet 4**: Primary AI analysis engine for credit report processing and document generation.
- **PostgreSQL**: Database solution, backed by Neon.
- **SQLAlchemy**: Python SQL toolkit and Object-Relational Mapper (ORM) for database interactions.
- **Fernet**: For symmetric encryption of sensitive data.
- **Stripe**: Payment processing via Replit's Stripe connector (5 tiers: $300-$1,500).

## Recent Changes (November 26, 2025)
- **Document Center** (`/dashboard/documents`): Unified document upload system with type-first selection
  - Categories: CRA Response, Collection Letters, Legal/Lawsuit, Credit Reports, Identity Docs
  - Supports collection agency letters, lawsuit complaints, summons, garnishments
  - Admin review workflow with priority flags and action deadlines
  - Client portal upload integration
- **Flexible Signup System**: Configurable fields (Required/Optional/Hidden/Deferred) via admin settings
- **FREE Tier Lead Magnet**: Basic Analysis tier at $0 that skips payment to capture leads
- **Multi-Payment Options**: Support for Stripe, PayPal, Cash App, Venmo, Zelle, and Pay Later
- **Admin Settings Page** (`/dashboard/settings`): Configure signup fields, pricing tiers, and payment methods
- **Payment Confirmation**: Admin can confirm manual payments (Cash App, Venmo, Zelle) in signups view
- **Payment Status Tracking**: Client model tracks payment_method and payment_pending status

## Previous Changes (November 25, 2025)
- **Stripe Payment Integration**: Added 4-step signup flow with Plan & Payment selection, Stripe Checkout redirect, and webhook handling for payment confirmation
- **SignupDraft Model**: Pre-payment intake data storage with 24-hour expiration
- **Client Payment Fields**: Added signup_plan, signup_amount, stripe_customer_id, payment_status, etc. to Client model
- **Dispute Item Tracking**: DisputeItem model for account-by-account tracking with bureau-specific tables
- **Secondary Bureau Freeze Tracking**: SecondaryBureauFreeze model for 9 secondary bureaus (Innovis, ChexSystems, etc.)
- **Client Portal Status Tab**: Enhanced with interactive status tables and freeze tracking
- **Enhanced Contact List** (`/dashboard/contacts`): LMR-style client management grid with:
  - Filter tabs (Mark 1, Mark 2, Affiliates, Active, Leads, Follow Up, Signups, Last 25, Show All)
  - Quick action icons per row (Delete, Add Task, Charge, AI Plan, Workflow, Notes, Documents, Dispute Center, Portal)
  - Contact detail popup with document tracking (Agreement, CR Login, Driver's License, SSN, Utility Bill, POA)
  - Status system (Lead, Active Client, Inactive, Provider, Other, Cancelled)
  - Task Manager (per-client tasks with due dates)
  - Client Notes system
- **New Database Models**: Task, ClientNote, ClientDocument
- **Extended Client Model**: client_type, status_2, company, phone_2, mobile, website, is_affiliate, follow_up_date, groups, mark_1, mark_2

## Admin Routes
- `/dashboard` - Main dashboard with pipeline visualization
- `/dashboard/contacts` - Contact List (LMR-style client grid)
- `/dashboard/clients` - Cases view (analysis-based)
- `/dashboard/signups` - Signups & payment tracking
- `/dashboard/case/<id>` - Individual case details

## Future Integrations (Not Yet Configured)
- **Email Service**: SendGrid for transactional emails (welcome, status updates, notifications)
- **SMS Service**: Twilio for messaging and funnel automation
- **Certified Mail**: SendCertifiedMail.com for legal proof of delivery
- **Physical Mail**: LetterStream for bulk letter automation
- **Credit Report Pull**: API integration for auto-pulling reports (IdentityIQ, SmartCredit, etc.)