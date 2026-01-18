"""
FCRA Knowledge Base for AI Chat Support

Contains curated information about:
- Fair Credit Reporting Act (FCRA) basics
- Credit restoration process
- Dispute timelines and expectations
- Common FAQs
- Company information

Used by ChatService to provide context-aware responses.
"""

# Company Information
COMPANY_INFO = """
COMPANY INFORMATION:
- Company Name: Brightpath Ascend Group
- Services: Credit restoration, FCRA dispute services
- Website: brightpathascend.com
- Founded: 2024
- Mission: Help clients restore their credit through lawful FCRA dispute processes

SERVICE HIGHLIGHTS:
- Free initial credit analysis
- AI-powered credit report analysis
- FCRA-compliant dispute letters
- Direct communication with credit bureaus
- Ongoing case management and support
- Client portal for tracking progress
"""

# FCRA Overview
FCRA_BASICS = """
FAIR CREDIT REPORTING ACT (FCRA) OVERVIEW:

The FCRA is a federal law that:
1. Gives consumers the right to know what's in their credit file
2. Requires credit bureaus to investigate disputed information
3. Mandates accurate and fair credit reporting
4. Provides remedies when rights are violated

KEY CONSUMER RIGHTS:
- Right to dispute inaccurate information
- Right to a free credit report annually from each bureau
- Right to know who has accessed your credit report
- Right to have errors corrected within 30 days (sometimes 45)
- Right to sue for damages if your rights are violated

THREE MAJOR CREDIT BUREAUS:
- Equifax
- Experian
- TransUnion
"""

# Dispute Process
DISPUTE_PROCESS = """
THE DISPUTE PROCESS:

ROUND 1 - Initial Dispute:
- Send dispute letters to all three credit bureaus
- Cite specific FCRA violations for each item
- Bureaus have 30 days to investigate (sometimes 45)
- We use certified mail for proof of delivery

ROUND 2 - Method of Verification (MOV):
- If items are not removed in Round 1, we escalate
- Request proof of how the bureau investigated
- Demand verification documentation from furnisher
- 30-day response window

ROUND 3 - Regulatory Escalation:
- File complaints with CFPB (Consumer Financial Protection Bureau)
- Involve state Attorney General if needed
- Reference FTC guidelines and precedents
- Increased pressure on bureaus

ROUND 4 - Pre-Litigation:
- Final demand letters
- Pre-arbitration notice if applicable
- Document all violations for potential lawsuit
- Settlement negotiations may begin

TYPICAL TIMELINE:
- Each round takes 30-45 days for bureau response
- Full process usually 3-6 months
- Results vary based on case complexity
"""

# Timeline Expectations
TIMELINE_INFO = """
TIMELINE EXPECTATIONS:

WHAT TO EXPECT:
- Credit bureau response: 30-45 days per round
- Typical case duration: 3-6 months
- Some deletions happen quickly, others take multiple rounds
- Complex cases may take longer

FACTORS AFFECTING TIMELINE:
- Number of items being disputed
- Type of accounts (collections, charge-offs, inquiries, etc.)
- Furnisher responsiveness
- Bureau compliance with deadlines

IMPORTANT NOTES:
- Results are never guaranteed
- Each case is unique
- Patience is important - the process works but takes time
- We'll keep you updated on every development
"""

# Common FAQs
FAQ_CONTENT = """
FREQUENTLY ASKED QUESTIONS:

Q: How long does the dispute process take?
A: Typically 3-6 months, with each round taking 30-45 days for bureau response.

Q: What items can be disputed?
A: Any inaccurate, incomplete, unverifiable, or outdated information including:
- Collections
- Charge-offs
- Late payments
- Inquiries
- Bankruptcies (if inaccurate)
- Public records

Q: Do I need to do anything during the process?
A: You may need to:
- Provide additional documents if requested
- Check your mail for bureau responses
- Upload CRA response letters to your portal
- Freeze your secondary bureaus

Q: What are secondary bureau freezes?
A: Besides the 3 major bureaus, there are specialty bureaus like:
- Innovis
- ChexSystems
- LexisNexis
- PRBC/MicroBilt
Freezing these prevents new negative info and protects your identity.

Q: What happens if an item is "verified"?
A: We escalate to the next round with stronger demands. "Verified" doesn't mean accurate - bureaus often rubber-stamp verifications without proper investigation.

Q: Can I see my progress?
A: Yes! Log into your client portal to view:
- Current case status
- Dispute history
- Uploaded documents
- Timeline of events

Q: What if I have questions about my case?
A: You can:
- Check your portal for updates
- Message support through the portal
- Book a consultation call
- Or chat with me here!

Q: How much does this cost?
A: Our pricing includes:
- Free initial credit analysis
- $199 for full analysis (credited toward first round)
- Round 1: $497 ($298 after credit)
- Round 2+: $297 per round
- Prepay packages available for savings
"""

# Portal Navigation Help
PORTAL_HELP = """
PORTAL NAVIGATION GUIDE:

DASHBOARD:
- Overview of your case status
- Quick stats on disputes and deletions
- Recent activity timeline

DOCUMENTS:
- Upload CRA response letters here
- Download dispute letters we've prepared
- View all case documents

STATUS:
- Track bureau freeze progress
- See which bureaus have responded
- Monitor secondary bureau freezes

MESSAGES:
- Communicate with our support team
- View message history
- Get notifications on updates

PROFILE:
- Update your contact information
- Change password
- Manage notification preferences
"""

# Response Guidelines
RESPONSE_GUIDELINES = """
RESPONSE STYLE GUIDELINES:

1. Be friendly, professional, and empathetic
2. Keep answers concise but informative
3. Use simple language - avoid legal jargon when possible
4. Always be honest about what we can and cannot do
5. Never make promises about specific outcomes
6. Refer to the portal for case-specific details
7. Offer to escalate to human support when appropriate

THINGS TO AVOID:
- Guaranteeing deletions or score improvements
- Giving legal advice (we're not attorneys)
- Making promises about timelines
- Discussing other clients or their results
- Speculating on lawsuit outcomes
"""

# Escalation Triggers
ESCALATION_TRIGGERS = """
ESCALATION KEYWORDS AND PHRASES:

PAYMENT/BILLING ISSUES:
- refund, cancel, money back, overcharged
- payment problem, billing issue, charge disputed

DISSATISFACTION:
- angry, frustrated, upset, disappointed
- not working, waste of time, scam
- want to speak to someone, talk to manager

LEGAL CONCERNS:
- lawyer, attorney, legal action, sue
- court, lawsuit, arbitration

EXPLICIT REQUEST:
- "speak to a human"
- "talk to a person"
- "real person"
- "live agent"

COMPLEX QUESTIONS:
- Questions about specific legal strategy
- Questions requiring case-specific analysis
- Technical questions about credit scoring
"""

# Full Knowledge Base Combined
def get_full_knowledge_base() -> str:
    """Returns the complete knowledge base as a single string"""
    return f"""
{COMPANY_INFO}

{FCRA_BASICS}

{DISPUTE_PROCESS}

{TIMELINE_INFO}

{FAQ_CONTENT}

{PORTAL_HELP}

{RESPONSE_GUIDELINES}
"""


def get_system_prompt(client_context: dict = None) -> str:
    """
    Generate the system prompt for the chat AI

    Args:
        client_context: Optional dict with client-specific info like:
            - client_name
            - case_status
            - client_stage
            - dispute_round
            - days_active
            - violations_count
    """
    base_prompt = f"""You are a helpful support assistant for Brightpath Ascend Group, a credit restoration company. You help clients understand the FCRA dispute process and answer questions about their case.

{get_full_knowledge_base()}

GUIDELINES:
1. Be friendly, professional, and concise
2. Answer questions about FCRA, credit disputes, and the process
3. If asked about specific case details, refer them to their portal or escalate
4. For payment/billing issues, offer to escalate to staff
5. For legal advice, clarify you're not a lawyer and offer escalation
6. If you can't help, offer to connect them with a team member
7. Never make promises about specific results or timelines
8. Keep responses focused and under 3 paragraphs when possible

ESCALATE TO HUMAN IF:
- Client requests to speak to a person
- Payment disputes or refund requests
- Legal questions requiring attorney
- Client expresses frustration/anger
- Question is outside your knowledge
- Complex case-specific strategy questions"""

    if client_context:
        client_info = "\n\nCLIENT CONTEXT:"
        if client_context.get('client_name'):
            client_info += f"\n- Name: {client_context['client_name']}"
        if client_context.get('case_status'):
            client_info += f"\n- Case Status: {client_context['case_status']}"
        if client_context.get('client_stage'):
            client_info += f"\n- Account Stage: {client_context['client_stage']}"
        if client_context.get('dispute_round'):
            client_info += f"\n- Current Round: Round {client_context['dispute_round']}"
        if client_context.get('days_active'):
            client_info += f"\n- Days Active: {client_context['days_active']}"
        if client_context.get('violations_count'):
            client_info += f"\n- Violations Found: {client_context['violations_count']}"
        if client_context.get('items_removed'):
            client_info += f"\n- Items Removed: {client_context['items_removed']}"

        base_prompt += client_info
        base_prompt += "\n\nUse this context to personalize your responses, but don't reveal sensitive details unless the client asks."

    return base_prompt


def check_escalation_needed(message: str) -> dict:
    """
    Check if a message should trigger escalation to human support

    Returns:
        dict with:
            - should_escalate: bool
            - reason: str (if escalation needed)
    """
    message_lower = message.lower()

    # Payment/billing triggers
    payment_keywords = ['refund', 'cancel', 'money back', 'overcharged',
                       'payment problem', 'billing issue', 'charge disputed']
    for keyword in payment_keywords:
        if keyword in message_lower:
            return {
                'should_escalate': True,
                'reason': 'payment_billing',
                'message': "I understand you have a question about payments or billing. Let me connect you with our support team who can better assist you with this."
            }

    # Dissatisfaction triggers
    dissatisfaction_keywords = ['angry', 'frustrated', 'upset', 'disappointed',
                                'not working', 'waste of time', 'scam', 'rip off',
                                'terrible', 'horrible', 'worst']
    for keyword in dissatisfaction_keywords:
        if keyword in message_lower:
            return {
                'should_escalate': True,
                'reason': 'dissatisfaction',
                'message': "I'm sorry to hear you're frustrated. Let me connect you with a team member who can address your concerns directly."
            }

    # Legal triggers
    legal_keywords = ['lawyer', 'attorney', 'legal action', 'sue', 'lawsuit',
                     'court', 'arbitration', 'legal advice']
    for keyword in legal_keywords:
        if keyword in message_lower:
            return {
                'should_escalate': True,
                'reason': 'legal',
                'message': "For questions involving legal matters, I'd recommend speaking with our team. I can connect you with a staff member who can provide more guidance."
            }

    # Explicit human request
    human_keywords = ['speak to a human', 'talk to a person', 'real person',
                     'live agent', 'speak to someone', 'talk to someone',
                     'human please', 'actual person', 'speak with someone']
    for keyword in human_keywords:
        if keyword in message_lower:
            return {
                'should_escalate': True,
                'reason': 'explicit_request',
                'message': "Of course! I'll connect you with a team member right away."
            }

    return {'should_escalate': False, 'reason': None}
