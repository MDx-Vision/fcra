# Priority 29+ Feature Roadmap

> Future features and enhancements for Brightpath Ascend FCRA Platform
>
> Created: 2026-01-09

---

## Status Legend

| Status | Meaning |
|--------|---------|
| Proposed | Under consideration |
| Approved | Approved for development |
| In Progress | Currently being built |
| Complete | Finished |

---

## Priority 29: Client Mobile App (Native)

**Status**: Proposed
**Effort**: High
**Dependencies**: PWA already implemented

### Description
Native iOS and Android apps using React Native for enhanced mobile experience beyond PWA capabilities.

### Features
- [ ] Native push notifications (APNs, FCM)
- [ ] Biometric login (Face ID, fingerprint)
- [ ] Offline document viewing
- [ ] Camera integration for document uploads
- [ ] App Store / Play Store distribution

### Technical Approach
- React Native with Expo
- Reuse existing API endpoints
- Native navigation patterns
- Deep linking to portal

---

## Priority 30: Client Chat Support (AI-Powered)

**Status**: Proposed
**Effort**: Medium
**Dependencies**: Anthropic API already integrated

### Description
AI chatbot in client portal to answer common questions and guide clients through the process.

### Features
- [ ] 24/7 automated support in portal
- [ ] FAQ knowledge base integration
- [ ] Escalation to live staff when needed
- [ ] Conversation history saved
- [ ] Multi-language support

### Technical Approach
- Claude AI for responses
- Custom knowledge base of FCRA info
- Intent classification for routing
- Seamless handoff to human agents

---

## Priority 31: Credit Score Simulator

**Status**: Proposed
**Effort**: Medium
**Dependencies**: Credit report parsing already built

### Description
Show clients projected credit score improvements based on potential deletions.

### Features
- [ ] "What-if" scenario modeling
- [ ] Per-item impact estimation
- [ ] Before/after visualization
- [ ] Goal setting (target score)
- [ ] Timeline projections

### Technical Approach
- FICO score factor analysis
- Machine learning on historical data
- Interactive Chart.js visualization
- Save scenarios for tracking

---

## Priority 32: Debt Settlement Module

**Status**: Proposed
**Effort**: High
**Dependencies**: Payment system already built

### Description
Full debt settlement negotiation and tracking system.

### Features
- [ ] Creditor contact database
- [ ] Settlement offer tracking
- [ ] Negotiation templates
- [ ] Payment arrangement management
- [ ] Settlement letter generation
- [ ] Client savings calculator

### Technical Approach
- New database models (Settlement, Offer, Negotiation)
- Creditor directory integration
- PDF settlement agreement generation
- Payment schedule automation

---

## Priority 33: Multi-Language Support (i18n)

**Status**: Proposed
**Effort**: Medium
**Dependencies**: None

### Description
Support Spanish and other languages in client-facing interfaces.

### Features
- [ ] Spanish translation of client portal
- [ ] Spanish email templates
- [ ] Spanish SMS templates
- [ ] Language preference in profile
- [ ] Right-to-left support preparation

### Technical Approach
- Flask-Babel for i18n
- Translation files (.po/.mo)
- Language switcher in UI
- AI-assisted translation review

---

## Priority 34: Advanced Reporting Dashboard

**Status**: Proposed
**Effort**: Medium
**Dependencies**: Analytics already built

### Description
Customizable reporting with saved reports, scheduling, and advanced filters.

### Features
- [ ] Custom report builder
- [ ] Saved report templates
- [ ] Scheduled email reports
- [ ] Advanced filtering (date ranges, segments)
- [ ] Export to PDF, Excel, Google Sheets
- [ ] Report sharing permissions

### Technical Approach
- Report definition models
- Scheduled job for email delivery
- Multiple export formats
- Role-based report access

---

## Priority 35: Creditor Direct Dispute

**Status**: Proposed
**Effort**: Medium
**Dependencies**: Letter generation already built

### Description
Send disputes directly to creditors/furnishers with tracking.

### Features
- [ ] Furnisher address database (already exists)
- [ ] Direct dispute letter templates
- [ ] Response tracking
- [ ] FCRA 623 violation monitoring
- [ ] Auto-escalation workflows

### Technical Approach
- Extend existing furnisher database
- New letter templates for 623 disputes
- Tracking similar to bureau disputes
- Timeline integration

---

## Priority 36: Calendar & Task Management

**Status**: Proposed
**Effort**: Medium
**Dependencies**: Bookings already implemented

### Description
Full staff calendar with task assignments and deadline tracking.

### Features
- [ ] Visual calendar view (day/week/month)
- [ ] Task assignments with due dates
- [ ] Deadline auto-population from FCRA timelines
- [ ] Calendar sync (Google, Outlook)
- [ ] Task notifications and reminders

### Technical Approach
- FullCalendar.js integration
- Task model with assignments
- iCal export/sync
- Integration with existing deadlines

---

## Priority 37: Client Referral Program

**Status**: Proposed
**Effort**: Low-Medium
**Dependencies**: Affiliate system already exists

### Description
Enable clients to refer friends and earn rewards.

### Features
- [ ] Unique referral links for clients
- [ ] Referral tracking dashboard in portal
- [ ] Reward tiers (credits, discounts)
- [ ] Referral status notifications
- [ ] Social sharing integrations

### Technical Approach
- Extend affiliate system for client referrals
- New referral type in database
- Portal UI for tracking
- Automated reward application

---

## Priority 38: Document OCR & Auto-Classification

**Status**: Proposed
**Effort**: Medium
**Dependencies**: Document upload already built

### Description
Automatically classify and extract data from uploaded documents.

### Features
- [ ] Document type detection (ID, SSN card, utility bill, CRA response)
- [ ] OCR text extraction
- [ ] Data field auto-population
- [ ] Quality check (blur detection, completeness)
- [ ] Batch processing

### Technical Approach
- Tesseract OCR or cloud service
- ML classification model
- Auto-population of client fields
- Human review queue for low confidence

---

## Priority 39: White Label API

**Status**: Proposed
**Effort**: High
**Dependencies**: Partner portal already built

### Description
Full API for white label partners to integrate with their own systems.

### Features
- [ ] RESTful API documentation (OpenAPI)
- [ ] Webhook delivery for events
- [ ] Partner-specific API keys
- [ ] Rate limiting per partner
- [ ] SDK libraries (Python, JavaScript)

### Technical Approach
- Extend existing API endpoints
- OpenAPI spec generation
- Webhook infrastructure
- API key management UI

---

## Priority 40: Advanced Analytics & Predictions

**Status**: Proposed
**Effort**: High
**Dependencies**: ML service already exists

### Description
Enhanced predictive analytics for case outcomes and business intelligence.

### Features
- [ ] Case outcome predictions with confidence
- [ ] Bureau behavior analysis
- [ ] Furnisher compliance scoring
- [ ] Revenue forecasting
- [ ] Churn prediction
- [ ] Optimal timing recommendations

### Technical Approach
- Expand ML models
- Historical data analysis
- Interactive visualizations
- Actionable recommendations

---

## Quick Wins (Low Effort, High Value)

### QW-1: Bulk Email/SMS Campaigns
- Marketing campaigns to leads
- Re-engagement sequences
- Educational content delivery

### QW-2: Client Testimonial Collection
- Automated request after success
- Review platform integrations
- Social proof widgets

### QW-3: Progress Badges/Gamification
- Achievement badges for clients
- Progress milestones
- Engagement incentives

### QW-4: Staff Notification Preferences
- Customize which alerts to receive
- Delivery method preferences
- Quiet hours settings

### QW-5: Client Document Templates
- Downloadable templates (ID placeholders, etc.)
- Fillable PDF forms
- Instructions for each document type

---

## Infrastructure Priorities

### INF-1: Send Certified Mail Integration
**Status**: Awaiting SFTP credentials

### INF-2: Twilio A2P 10DLC
**Status**: Awaiting carrier approval

### INF-3: WhatsApp Business
**Status**: Awaiting Meta template approval

### INF-4: Production Deployment
- PostgreSQL hosting
- File storage (S3 or equivalent)
- CDN for static assets
- SSL certificates
- Monitoring and alerting

---

## Feature Request Form

To propose a new feature, provide:

1. **Feature Name**: Short descriptive name
2. **Problem Statement**: What problem does this solve?
3. **User Story**: As a [role], I want [feature] so that [benefit]
4. **Acceptance Criteria**: How do we know it's complete?
5. **Priority Justification**: Why this should be prioritized
6. **Effort Estimate**: Low/Medium/High

---

## Prioritization Criteria

Features are prioritized based on:

| Criterion | Weight |
|-----------|--------|
| Client Impact | 30% |
| Revenue Potential | 25% |
| Competitive Advantage | 20% |
| Technical Feasibility | 15% |
| Maintenance Burden | 10% |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-09 | Initial roadmap with P29-P40 |

---

*Last Updated: 2026-01-09*
