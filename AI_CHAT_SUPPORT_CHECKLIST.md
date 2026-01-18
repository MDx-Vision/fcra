# AI Chat Support Implementation Checklist

> Priority 30: AI-Powered Chat Support for Client Portal
>
> **Created**: 2026-01-18
> **Status**: 🔄 PLANNING

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

## Phase 1: Database & Models

### 1.1 Database Schema
- [ ] Create `ChatConversation` model
  ```python
  id: Integer (PK)
  client_id: Integer (FK -> Client)
  started_at: DateTime
  ended_at: DateTime (nullable)
  status: String (active, closed, escalated)
  escalated_to_staff_id: Integer (FK -> Staff, nullable)
  escalated_at: DateTime (nullable)
  metadata: JSON (nullable)
  ```

- [ ] Create `ChatMessage` model
  ```python
  id: Integer (PK)
  conversation_id: Integer (FK -> ChatConversation)
  role: String (user, assistant, system)
  content: Text
  created_at: DateTime
  tokens_used: Integer (nullable)
  metadata: JSON (nullable)
  ```

- [ ] Add migration entries to `database.py`
- [ ] **RUN TESTS** after database changes

### 1.2 Verification
- [ ] Models can be imported without errors
- [ ] Migration runs successfully
- [ ] All existing tests still pass

---

## Phase 2: Chat Service (Backend)

### 2.1 Create ChatService
- [ ] Create `services/chat_service.py`
- [ ] Implement core functions:
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
- [ ] Use existing Anthropic client from `services/config.py`
- [ ] Create system prompt with:
  - [ ] FCRA knowledge base
  - [ ] Company info (Brightpath Ascend Group)
  - [ ] Client context injection (name, case status, stage)
  - [ ] Escalation triggers (payment issues, complaints, legal questions)
  - [ ] Response guidelines (friendly, professional, concise)

### 2.3 Knowledge Base
- [ ] Create `CHAT_KNOWLEDGE_BASE` constant or file with:
  - [ ] FCRA basics (what it is, client rights)
  - [ ] Dispute process overview
  - [ ] Timeline expectations (30-45 days)
  - [ ] Document requirements
  - [ ] Payment/billing FAQs
  - [ ] Portal navigation help
  - [ ] Common questions & answers

### 2.4 Escalation Logic
- [ ] Define escalation triggers:
  - [ ] Keywords: "cancel", "refund", "lawyer", "sue", "complaint"
  - [ ] Sentiment: Frustrated/angry detection
  - [ ] Explicit request: "talk to human", "speak to someone"
  - [ ] Complex questions AI can't answer
- [ ] Auto-notify staff on escalation (email/SMS)

### 2.5 Rate Limiting
- [ ] Max messages per minute per client
- [ ] Max conversations per day per client
- [ ] Token budget per conversation

### 2.6 Unit Tests
- [ ] Create `tests/test_chat_service.py`
- [ ] Test conversation lifecycle
- [ ] Test message sending/receiving
- [ ] Test escalation triggers
- [ ] Test client context injection
- [ ] Test rate limiting
- [ ] **RUN FULL TEST SUITE**

---

## Phase 3: API Endpoints

### 3.1 Portal API Endpoints
- [ ] `POST /portal/api/chat/start` - Start new conversation
- [ ] `POST /portal/api/chat/message` - Send message, get AI response
- [ ] `GET /portal/api/chat/conversations` - List client's conversations
- [ ] `GET /portal/api/chat/conversation/<id>` - Get conversation + messages
- [ ] `POST /portal/api/chat/escalate` - Request human support
- [ ] `POST /portal/api/chat/close` - Close conversation

### 3.2 Staff API Endpoints (for escalated chats)
- [ ] `GET /api/chat/escalated` - List escalated conversations
- [ ] `GET /api/chat/conversation/<id>` - View any conversation
- [ ] `POST /api/chat/conversation/<id>/respond` - Staff response
- [ ] `POST /api/chat/conversation/<id>/close` - Staff closes chat

### 3.3 Verification
- [ ] All endpoints return proper JSON
- [ ] Authentication works (portal_login_required)
- [ ] Error handling for invalid requests
- [ ] **RUN TESTS**

---

## Phase 4: Frontend UI (Portal)

### 4.1 Chat Widget Component
- [ ] Create floating chat button (bottom-right corner)
- [ ] Chat window with:
  - [ ] Header (title, minimize, close buttons)
  - [ ] Message area (scrollable)
  - [ ] Input field + send button
  - [ ] Typing indicator
  - [ ] Escalation button

### 4.2 Message Styling
- [ ] User messages (right-aligned, teal background)
- [ ] AI messages (left-aligned, gray background)
- [ ] System messages (centered, italic)
- [ ] Timestamps
- [ ] Typing dots animation

### 4.3 Chat Page (Full View)
- [ ] Create `/portal/chat` route
- [ ] Show conversation history
- [ ] Full-screen chat experience
- [ ] Previous conversations list

### 4.4 Integration Points
- [ ] Add chat widget to `base_portal.html`
- [ ] Only show for active clients (not onboarding)
- [ ] Add "Chat Support" to portal navigation
- [ ] Unread message indicator/badge

### 4.5 JavaScript Functions
- [ ] `initChat()` - Initialize chat widget
- [ ] `toggleChat()` - Open/close chat window
- [ ] `sendMessage()` - Send message to API
- [ ] `receiveMessage()` - Display AI response
- [ ] `loadHistory()` - Load previous messages
- [ ] `escalateChat()` - Request human support

### 4.6 Verification
- [ ] Chat widget appears on portal pages
- [ ] Messages send and receive correctly
- [ ] Conversation persists across page loads
- [ ] Mobile responsive
- [ ] **RUN TESTS**

---

## Phase 5: Staff Dashboard Integration

### 5.1 Escalated Chats UI
- [ ] Add to staff dashboard sidebar
- [ ] Escalated chats list with:
  - [ ] Client name
  - [ ] Time waiting
  - [ ] Preview of last message
  - [ ] Priority indicator
- [ ] Chat detail view for staff responses

### 5.2 Notifications
- [ ] Email notification on escalation
- [ ] SMS notification (optional)
- [ ] Dashboard badge for unread escalations

### 5.3 Staff Response Flow
- [ ] Staff can view full conversation
- [ ] Staff can respond (message goes to client)
- [ ] Staff can close/resolve conversation
- [ ] Staff can add internal notes

### 5.4 Verification
- [ ] Escalated chats appear in dashboard
- [ ] Staff can respond to clients
- [ ] Notifications work
- [ ] **RUN TESTS**

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
| Phase 1: Database | ⏳ Pending | 5725 | - |
| Phase 2: Service | ⏳ Pending | - | - |
| Phase 3: API | ⏳ Pending | - | - |
| Phase 4: Frontend | ⏳ Pending | - | - |
| Phase 5: Staff UI | ⏳ Pending | - | - |
| Phase 6: Testing | ⏳ Pending | - | 5755+ |

---

## Files to Create/Modify

| File | Action | Description | Status |
|------|--------|-------------|--------|
| `database.py` | MODIFY | Add ChatConversation, ChatMessage models | ⏳ |
| `services/chat_service.py` | CREATE | AI chat service (~400 lines) | ⏳ |
| `services/chat_knowledge_base.py` | CREATE | FCRA knowledge for AI | ⏳ |
| `tests/test_chat_service.py` | CREATE | Unit tests (30+ tests) | ⏳ |
| `routes/portal.py` | MODIFY | Add chat API endpoints | ⏳ |
| `app.py` | MODIFY | Add staff chat endpoints | ⏳ |
| `templates/portal/base_portal.html` | MODIFY | Add chat widget | ⏳ |
| `templates/portal/chat.html` | CREATE | Full chat page | ⏳ |
| `templates/chat_dashboard.html` | CREATE | Staff escalated chats | ⏳ |
| `static/js/chat-widget.js` | CREATE | Chat JavaScript | ⏳ |
| `static/css/chat-widget.css` | CREATE | Chat styles | ⏳ |
| `cypress/e2e/portal_chat.cy.js` | CREATE | E2E tests | ⏳ |

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
