# AI Chat Support Implementation Checklist

> Priority 30: AI-Powered Chat Support for Client Portal
>
> **Created**: 2026-01-18
> **Status**: 🔄 IN PROGRESS - Phase 5 Complete

---

## Overview

Add a Claude-powered AI chatbot to the client portal for 24/7 automated support. The chatbot answers common questions, guides clients through the process, and escalates to live staff when needed.

**Key Features:**
- 24/7 automated support in client portal
- FCRA knowledge base integration
- Conversation history saved
- Escalation to live staff
- Context-aware responses (knows client's case status)

---

## Breakproof Regression Plan

### Before Starting
```bash
# Run full test suite and record baseline
source venv/bin/activate
export DATABASE_URL="postgresql://localhost/fcra_test?sslmode=disable"
python3 -m pytest --tb=short -q 2>&1 | tee /tmp/pre-chat-tests.log
# Expected: 5725 passed, 9 skipped
```

### After Each Phase
```bash
# Run tests after each phase completes
python3 -m pytest --tb=short -q
# Must match baseline or improve
```

### After All Phases Complete
```bash
# Full regression + new chat tests
python3 -m pytest --tb=short -q
python3 -m pytest tests/test_chat_service.py -v
# Run Cypress E2E if chat has UI
CI=true npx cypress run --spec "cypress/e2e/portal_chat.cy.js"
```

---

## Phase 1: Database & Models ✅ COMPLETE

### 1.1 Database Schema
- [x] Create `ChatConversation` model
  ```python
  id: Integer (PK)
  client_id: Integer (FK -> Client)
  started_at: DateTime
  ended_at: DateTime (nullable)
  status: String (active, closed, escalated)
  escalated_to_staff_id: Integer (FK -> Staff, nullable)
  escalated_at: DateTime (nullable)
  extra_data: JSON (nullable)  # renamed from metadata (reserved word)
  ```

- [x] Create `ChatMessage` model
  ```python
  id: Integer (PK)
  conversation_id: Integer (FK -> ChatConversation)
  role: String (user, assistant, system)
  content: Text
  created_at: DateTime
  tokens_used: Integer (nullable)
  extra_data: JSON (nullable)  # renamed from metadata (reserved word)
  ```

- [x] Add migration entries to `database.py`
- [x] **RUN TESTS** after database changes

### 1.2 Verification
- [x] Models can be imported without errors
- [x] Migration runs successfully
- [x] All existing tests still pass (5758 passed, 9 skipped)

---

## Phase 2: Chat Service (Backend) ✅ COMPLETE

### 2.1 Create ChatService
- [x] Create `services/chat_service.py`
- [x] Implement core functions:
  ```python
  - start_conversation(client_id) -> conversation
  - send_message(conversation_id, message) -> response
  - get_conversation(conversation_id) -> conversation + messages
  - get_client_conversations(client_id) -> list
  - escalate_to_staff(conversation_id, staff_id) -> bool
  - close_conversation(conversation_id) -> bool
  - get_client_context(client_id) -> dict (case status, stage, etc.)
  ```

### 2.2 Claude AI Integration
- [x] Use existing Anthropic client pattern (lazy-loaded)
- [x] Create system prompt with:
  - [x] FCRA knowledge base
  - [x] Company info (Brightpath Ascend Group)
  - [x] Client context injection (name, case status, stage)
  - [x] Escalation triggers (payment issues, complaints, legal questions)
  - [x] Response guidelines (friendly, professional, concise)

### 2.3 Knowledge Base
- [x] Create `services/chat_knowledge_base.py` with:
  - [x] FCRA basics (what it is, client rights)
  - [x] Dispute process overview
  - [x] Timeline expectations (30-45 days)
  - [x] Payment/billing FAQs
  - [x] Portal navigation help
  - [x] Common questions & answers

### 2.4 Escalation Logic
- [x] Define escalation triggers:
  - [x] Keywords: "cancel", "refund", "lawyer", "sue", "complaint"
  - [x] Sentiment: Frustrated/angry detection
  - [x] Explicit request: "talk to human", "speak to someone"
- [ ] Auto-notify staff on escalation (email/SMS) - deferred to Phase 5

### 2.5 Rate Limiting
- [x] Max messages per minute per client (default: 10)
- [x] Max conversations per day per client (default: 5)
- [x] Token budget per conversation (default: 50,000)

### 2.6 Unit Tests
- [x] Create `tests/test_chat_service.py` (49 tests)
- [x] Test conversation lifecycle
- [x] Test message sending/receiving
- [x] Test escalation triggers
- [x] Test client context injection
- [x] Test rate limiting
- [x] **RUN FULL TEST SUITE** (5807 passed, 9 skipped)

---

## Phase 3: API Endpoints ✅ COMPLETE

### 3.1 Portal API Endpoints (routes/portal.py)
- [x] `POST /portal/api/chat/start` - Start new conversation
- [x] `POST /portal/api/chat/message` - Send message, get AI response
- [x] `GET /portal/api/chat/conversations` - List client's conversations
- [x] `GET /portal/api/chat/conversation/<id>` - Get conversation + messages
- [x] `POST /portal/api/chat/escalate` - Request human support
- [x] `POST /portal/api/chat/close` - Close conversation
- [x] `GET /portal/chat` - Full chat page route

### 3.2 Staff API Endpoints (app.py)
- [x] `GET /api/chat/escalated` - List escalated conversations
- [x] `GET /api/chat/conversation/<id>` - View any conversation
- [x] `POST /api/chat/conversation/<id>/respond` - Staff response
- [x] `POST /api/chat/conversation/<id>/close` - Staff closes chat
- [x] `GET /dashboard/chat` - Staff chat dashboard page

### 3.3 Verification
- [x] All endpoints return proper JSON
- [x] Authentication works (portal_login_required, require_staff)
- [x] Error handling for invalid requests
- [x] **RUN TESTS** (5807 passed, 9 skipped)

---

## Phase 4: Frontend UI (Portal) ✅ COMPLETE

### 4.1 Chat Widget Component
- [x] Create floating chat button (bottom-right corner)
- [x] Chat window with:
  - [x] Header (title, minimize, close buttons)
  - [x] Message area (scrollable)
  - [x] Input field + send button
  - [x] Typing indicator
  - [x] Escalation button

### 4.2 Message Styling
- [x] User messages (right-aligned, teal background)
- [x] AI messages (left-aligned, gray background)
- [x] System messages (centered, italic)
- [x] Timestamps
- [x] Typing dots animation

### 4.3 Chat Page (Full View)
- [x] Create `/portal/chat` route
- [x] Show conversation history
- [x] Full-screen chat experience
- [x] Previous conversations list

### 4.4 Integration Points
- [x] Add chat widget to `base_portal.html`
- [x] Only show for active clients (not onboarding)
- [x] Chat widget hidden on chat page (to avoid duplication)
- [ ] Unread message indicator/badge (deferred)

### 4.5 JavaScript Functions
- [x] `init()` - Initialize chat widget
- [x] `toggleChat()` - Open/close chat window
- [x] `sendMessage()` - Send message to API
- [x] `addMessage()` - Display AI response
- [x] `loadConversation()` - Load previous messages
- [x] `escalateChat()` - Request human support

### 4.6 Verification
- [x] Chat widget appears on portal pages
- [x] Messages send and receive correctly
- [x] Conversation persists across page loads
- [x] Mobile responsive (dark mode supported)
- [x] **TESTS PASSING** (5807 passed)

---

## Phase 5: Staff Dashboard Integration ✅ COMPLETE

### 5.1 Escalated Chats UI
- [x] Add to staff dashboard sidebar (`/dashboard/chat`)
- [x] Escalated chats list with:
  - [x] Client name
  - [x] Time waiting
  - [x] Preview of last message
  - [x] Priority indicator (color-coded)
- [x] Chat detail view for staff responses

### 5.2 Notifications
- [ ] Email notification on escalation (deferred)
- [ ] SMS notification (optional, deferred)
- [ ] Dashboard badge for unread escalations (deferred)

### 5.3 Staff Response Flow
- [x] Staff can view full conversation
- [x] Staff can respond (message goes to client)
- [x] Staff can close/resolve conversation
- [ ] Staff can add internal notes (deferred)

### 5.4 Verification
- [x] Escalated chats appear in dashboard
- [x] Staff can respond to clients
- [x] Sidebar link added ("AI Chat Support")
- [x] **TESTS PASSING** (5807 passed)

---

## Phase 6: Testing & Polish

### 6.1 Unit Tests (Complete)
- [ ] `tests/test_chat_service.py` - All service functions
- [ ] Minimum 30 tests covering:
  - [ ] Conversation CRUD
  - [ ] Message handling
  - [ ] AI response generation
  - [ ] Escalation logic
  - [ ] Rate limiting
  - [ ] Error handling

### 6.2 Cypress E2E Tests
- [ ] Create `cypress/e2e/portal_chat.cy.js`
- [ ] Test chat widget visibility
- [ ] Test sending messages
- [ ] Test receiving responses
- [ ] Test escalation flow
- [ ] Test conversation history

### 6.3 Final Regression
```bash
# Full test suite
python3 -m pytest --tb=short -q
# Expected: 5755+ passed (30+ new tests)

# Cypress
CI=true npx cypress run
# Expected: 90+ tests passing
```

### 6.4 Manual Testing
- [ ] Test as onboarding client (chat hidden or limited)
- [ ] Test as active client (full chat access)
- [ ] Test escalation flow end-to-end
- [ ] Test on mobile device
- [ ] Test conversation persistence

---

## Implementation Progress

| Phase | Status | Tests Before | Tests After |
|-------|--------|--------------|-------------|
| Phase 1: Database | ✅ Complete | 5596 | 5758 |
| Phase 2: Service | ✅ Complete | 5758 | 5807 |
| Phase 3: API | ✅ Complete | 5807 | 5807 |
| Phase 4: Frontend | ✅ Complete | 5807 | 5807 |
| Phase 5: Staff UI | ✅ Complete | 5807 | 5807 |
| Phase 6: Testing | ⏳ Pending | 5807 | - |

---

## Files to Create/Modify

| File | Action | Description | Status |
|------|--------|-------------|--------|
| `database.py` | MODIFY | Add ChatConversation, ChatMessage models | ✅ Done |
| `services/chat_service.py` | CREATE | AI chat service (~600 lines) | ✅ Done |
| `services/chat_knowledge_base.py` | CREATE | FCRA knowledge for AI | ✅ Done |
| `tests/test_chat_service.py` | CREATE | Unit tests (49 tests) | ✅ Done |
| `routes/portal.py` | MODIFY | Add chat API endpoints | ✅ Done |
| `app.py` | MODIFY | Add staff chat endpoints | ✅ Done |
| `templates/portal/base_portal.html` | MODIFY | Add chat widget | ✅ Done |
| `templates/portal/chat.html` | CREATE | Full chat page | ✅ Done |
| `templates/chat_dashboard.html` | CREATE | Staff escalated chats | ✅ Done |
| `static/js/chat-widget.js` | CREATE | Chat JavaScript (~490 lines) | ✅ Done |
| `static/css/chat-widget.css` | CREATE | Chat styles (~490 lines) | ✅ Done |
| `templates/includes/dashboard_sidebar.html` | MODIFY | Add AI Chat Support link | ✅ Done |
| `cypress/e2e/portal_chat.cy.js` | CREATE | E2E tests | ⏳ Pending |

---

## Environment Variables

```bash
# Already configured (uses existing Anthropic key)
ANTHROPIC_API_KEY=sk-ant-...

# Optional new variables
CHAT_MAX_MESSAGES_PER_MINUTE=10
CHAT_MAX_CONVERSATIONS_PER_DAY=5
CHAT_ESCALATION_EMAIL=support@brightpathascend.com
```

---

## AI System Prompt Template

```
You are a helpful support assistant for Brightpath Ascend Group, a credit restoration company. You help clients understand the FCRA dispute process and answer questions about their case.

CLIENT CONTEXT:
- Name: {client_name}
- Case Status: {case_status}
- Current Stage: {client_stage}
- Days Active: {days_active}

GUIDELINES:
1. Be friendly, professional, and concise
2. Answer questions about FCRA, credit disputes, and the process
3. If asked about specific case details, refer to their portal
4. For payment/billing issues, offer to escalate to staff
5. For legal advice, clarify you're not a lawyer and offer escalation
6. If you can't help, offer to connect them with a team member

ESCALATE TO HUMAN IF:
- Client requests to speak to a person
- Payment disputes or refund requests
- Legal questions requiring attorney
- Client expresses frustration/anger
- Question is outside your knowledge

KNOWLEDGE BASE:
{knowledge_base_content}
```

---

## Cost Estimation

| Item | Estimate |
|------|----------|
| Claude API (per message) | ~$0.01-0.03 |
| Avg messages per conversation | 5-10 |
| Cost per conversation | ~$0.05-0.30 |
| Monthly (100 conversations) | ~$5-30 |

---

## Resources

- Anthropic API Docs: https://docs.anthropic.com/
- Claude Messages API: https://docs.anthropic.com/claude/reference/messages
- Existing integration: `services/ai_dispute_writer_service.py`

---

## Notes

- Uses existing Anthropic API key (already configured)
- Chat only for active clients (not onboarding stage)
- Conversations stored for compliance/audit
- Staff can review all conversations
- AI never makes promises about results or timelines

---

*Last Updated: 2026-01-18*
