# FCRA Automation Server - Consumer Protection Litigation Platform

## Overview
This Python Flask-based FCRA automation server replaces Credit Money Machine (CMM). It uses Anthropic's Claude AI to analyze credit reports for FCRA violations and generates escalating dispute letters (Rounds 1-4) following the Rapid Legal Protection Protocol (RLPP) strategy. The platform supports both new client onboarding with full analysis and existing clients requiring context-aware escalated letters. It focuses on consumer protection litigation, leveraging AI for comprehensive legal analysis and aiming for high-value legal outcomes.

## User Preferences
- Cost-conscious but values AI quality over templates
- Accepts $1-3 per analysis as worthwhile investment
- Wants cost optimization without sacrificing analysis quality
- Prefers automation for clear cases, manual review for complex ones
- Building full litigation platform (not just credit repair)
- Target: 50 clients waiting, $600K-900K year-1 revenue with 3-tier pricing model

## System Architecture

### Positioning
The platform is positioned for **Consumer Protection Litigation**, emphasizing federal law enforcement through FCRA compliance. It employs a high-value legal strategy with sophisticated AI analysis.

### UI/UX Decisions
- **Admin Dashboard**: A web interface facilitates processing credit reports, selecting client information, choosing dispute rounds, and generating AI analyses and PDF letters.
- **PDF Generation**: Custom-styled PDFs with blue text (#1a1a8e) are generated to encourage manual review by credit bureaus.
- **Litigation Review Interface**: A dedicated `/analysis/<id>/review` page provides a verification checkpoint with a case strength dashboard, violations list, standing verification checklist, damages table, and strategic recommendations, featuring color-coded scoring.

### Technical Implementations
- **AI Analysis**: Claude AI (Anthropic) performs comprehensive FCRA violation analysis.
- **Dispute Round System**: Supports escalating dispute rounds (1-4) with increasing legal intensity:
    - **Round 1**: Initial Dispute (full FCRA analysis).
    - **Round 2**: MOV Request / Follow-up (escalated with bureau response analysis).
    - **Round 3**: Pre-Litigation Warning.
    - **Round 4**: Final Demand / Intent to Sue.
- **Analysis Modes**: Offers "Manual Review" (human checkpoint before deliverables) and "Automatic" (full report generation).
- **RLPP Strategy**: Implements the Rapid Legal Protection Protocol with strong legal language, bundled violations, case law citations, and quantified damages from Round 1.
- **Cost Optimization**:
    - **Anthropic Prompt Caching**: Caches the system prompt (90% discount for subsequent requests within 5 minutes) to save 20-30% on AI costs.
    - **Batch Processing**: A `/webhook/batch` endpoint processes multiple clients, maximizing cache efficiency.
    - **Real-time Cost Tracking**: Console logs provide token usage breakdown and cost savings.
- **Automated Litigation Database Population**: Claude AI outputs structured JSON (`<LITIGATION_DATA>`) containing violations, standing, and damages, which is automatically parsed to populate the database tables, eliminating manual data entry.
- **Litigation Calculation Tools**: `litigation_tools.py` includes production-ready algorithms for calculating damages (statutory, punitive, attorney fees, settlement targets) and case scoring (standing, violation quality, willfulness, documentation completeness, settlement probability).

### System Design Choices
- **Flask Application**: The core application (`app.py`) manages webhook endpoints, AI integration, batch processing, and cost tracking.
- **Database**: PostgreSQL is used to track clients, analyses, and generated letters.
- **API Endpoints**: A comprehensive set of API endpoints for admin functions, analysis, PDF download, client management, and litigation data management.
- **Project Structure**: `app.py` for main logic, `requirements.txt` for dependencies, and `.gitignore`.

## External Dependencies
- **Anthropic Claude AI**: Used for comprehensive FCRA violation analysis and structured JSON output.
- **PostgreSQL**: The relational database management system for storing all client, analysis, and letter data.