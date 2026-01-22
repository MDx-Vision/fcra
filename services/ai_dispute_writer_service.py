"""
AI Dispute Writer Service

Generates customized FCRA dispute letters using AI based on:
- Credit report analysis and violations
- CRA responses from previous rounds
- Selected dispute items
- Current dispute round (R1-R4)
"""

import os
import json
import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from database import (
    Client, Analysis, Violation, DisputeItem, CRAResponse,
    DisputeLetter, CreditScoreSnapshot
)
from prompt_loader import PromptLoader


class AIDisputeWriterService:
    """Service for AI-powered dispute letter generation"""

    # Letter types by round
    ROUND_STRATEGIES = {
        1: {
            'name': 'Round 1 - Initial Dispute',
            'description': 'Section 611 dispute with RLPP bundling',
            'prompt_key': 'r1',
            'focus': 'Initial disputes citing specific violations',
        },
        2: {
            'name': 'Round 2 - Method of Verification',
            'description': 'Cushman-style MOV demands',
            'prompt_key': 'r2',
            'focus': 'Demand proof of investigation procedures',
        },
        3: {
            'name': 'Round 3 - Regulatory Escalation',
            'description': 'CFPB, state AG, and FTC complaints',
            'prompt_key': 'r3',
            'focus': 'Escalate with regulatory agency involvement',
        },
        4: {
            'name': 'Round 4 - Pre-Litigation',
            'description': 'Pre-arbitration demands and lawsuit threats',
            'prompt_key': 'r4',
            'focus': 'Final demand before legal action',
        },
    }

    # Special dispute strategies (non-round based)
    SPECIAL_STRATEGIES = {
        '5dayknockout': {
            'name': '5-Day Knock-Out (Identity Theft)',
            'description': 'FCRA §605B identity theft block - bureaus must block within 4 business days',
            'prompt_key': '5dayknockout',
            'focus': 'Fast removal using identity theft provisions with police report + FTC complaint',
            'requires': ['police_report', 'ftc_complaint', 'notarized_affidavit'],
            'output_files': 15,  # 15 document types generated
        },
        'idtheft': {
            'name': 'Identity Theft Disputes',
            'description': 'Full identity theft dispute package',
            'prompt_key': 'idtheft',
            'focus': 'Comprehensive identity theft dispute with all supporting documents',
            'requires': ['police_report', 'ftc_complaint'],
        },
        'inquiry': {
            'name': 'Inquiry Disputes (Permissible Purpose)',
            'description': 'Challenge unauthorized hard inquiries under §604',
            'prompt_key': 'inquiry',
            'focus': 'Remove unauthorized inquiries - no identity theft required',
            'requires': [],
        },
        'inquirytheft': {
            'name': 'Inquiry Disputes (Identity Theft)',
            'description': 'Challenge fraudulent inquiries from identity theft',
            'prompt_key': 'inquirytheft',
            'focus': 'Remove inquiries caused by identity theft',
            'requires': ['ftc_complaint'],
        },
        'portalfix': {
            'name': 'Portal Quick Fix',
            'description': 'Fast PII & inquiry fixes via online portal',
            'prompt_key': 'portalfix',
            'focus': 'Quick fixes for funding/approval - portal submission + phone follow-up',
            'requires': [],
        },
    }

    # Bureaus
    BUREAUS = ['Equifax', 'Experian', 'TransUnion']

    # Bureau fraud department addresses (for 5-Day Knockout)
    BUREAU_FRAUD_ADDRESSES = {
        'Experian': 'P.O. Box 9554, Allen, TX 75013',
        'Equifax': 'P.O. Box 105069, Atlanta, GA 30348',
        'TransUnion': 'Fraud Victim Assistance Dept, P.O. Box 2000, Chester, PA 19016',
    }

    def __init__(self, db: Session):
        self.db = db
        self.prompt_loader = PromptLoader()
        self._anthropic_client = None

    @property
    def anthropic_client(self):
        """Lazy load Anthropic client"""
        if self._anthropic_client is None:
            try:
                from anthropic import Anthropic
                self._anthropic_client = Anthropic(
                    api_key=os.environ.get('ANTHROPIC_API_KEY')
                )
            except Exception as e:
                print(f"Error initializing Anthropic client: {e}")
                raise
        return self._anthropic_client

    # =========================================================================
    # CONTEXT GATHERING
    # =========================================================================

    def get_client_context(self, client_id: int) -> Dict[str, Any]:
        """Gather all relevant context for a client"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'error': 'Client not found'}

        # Get violations from analysis
        violations = self.db.query(Violation).filter(
            Violation.client_id == client_id
        ).all()

        # Get dispute items
        dispute_items = self.db.query(DisputeItem).filter(
            DisputeItem.client_id == client_id
        ).all()

        # Get CRA responses
        cra_responses = self.db.query(CRAResponse).filter(
            CRAResponse.client_id == client_id
        ).order_by(CRAResponse.dispute_round, CRAResponse.response_date).all()

        # Get latest analysis
        analysis = self.db.query(Analysis).filter(
            Analysis.client_id == client_id
        ).order_by(Analysis.created_at.desc()).first()

        # Get credit score snapshots
        score_snapshots = self.db.query(CreditScoreSnapshot).filter(
            CreditScoreSnapshot.client_id == client_id
        ).order_by(CreditScoreSnapshot.created_at.desc()).limit(2).all()

        return {
            'client': client,
            'violations': violations,
            'dispute_items': dispute_items,
            'cra_responses': cra_responses,
            'analysis': analysis,
            'score_snapshots': score_snapshots,
            'current_round': client.current_dispute_round or 1,
        }

    def format_client_info(self, client: Client) -> str:
        """Format client information for the prompt"""
        dob_str = client.date_of_birth.strftime('%m/%d/%Y') if client.date_of_birth else 'N/A'

        return f"""
CLIENT INFORMATION:
==================
Name: {client.name}
Address: {client.address_street or 'N/A'}
City, State ZIP: {client.address_city or ''}, {client.address_state or ''} {client.address_zip or ''}
SSN Last 4: XXX-XX-{client.ssn_last_four or 'XXXX'}
Date of Birth: {dob_str}
Email: {client.email or 'N/A'}
Phone: {client.phone or 'N/A'}
"""

    def format_violations(self, violations: List[Violation]) -> str:
        """Format violations for the prompt"""
        if not violations:
            return "No violations detected."

        lines = ["DETECTED VIOLATIONS:", "=" * 40]

        for i, v in enumerate(violations, 1):
            lines.append(f"\n{i}. {v.violation_type}")
            lines.append(f"   Bureau: {v.bureau or 'All bureaus'}")
            lines.append(f"   Account: {v.account_name or 'N/A'}")
            lines.append(f"   FCRA Section: {v.fcra_section or 'N/A'}")
            lines.append(f"   Description: {v.description or 'N/A'}")
            if v.statutory_damages_min or v.statutory_damages_max:
                lines.append(f"   Potential Damages: ${v.statutory_damages_min or 0:,.0f} - ${v.statutory_damages_max or 0:,.0f}")

        return '\n'.join(lines)

    def format_dispute_items(
        self,
        items: List[DisputeItem],
        selected_ids: Optional[List[int]] = None
    ) -> str:
        """Format dispute items for the prompt"""
        if not items:
            return "No dispute items."

        # Filter to selected items if specified
        if selected_ids:
            items = [item for item in items if item.id in selected_ids]

        if not items:
            return "No items selected for dispute."

        lines = ["ITEMS TO DISPUTE:", "=" * 40]

        # Group by bureau
        by_bureau = {}
        for item in items:
            bureau = item.bureau or 'Unknown'
            if bureau not in by_bureau:
                by_bureau[bureau] = []
            by_bureau[bureau].append(item)

        for bureau in self.BUREAUS:
            if bureau in by_bureau:
                lines.append(f"\n{bureau.upper()}:")
                lines.append("-" * 30)
                for item in by_bureau[bureau]:
                    status_info = f" [Status: {item.status}]" if item.status else ""
                    lines.append(f"  - {item.creditor_name or 'Unknown Creditor'}")
                    lines.append(f"    Type: {item.item_type or 'N/A'}")
                    lines.append(f"    Account: {item.account_id or 'N/A'}{status_info}")
                    if item.reason:
                        lines.append(f"    Reason: {item.reason}")

        return '\n'.join(lines)

    def format_cra_responses(self, responses: List[CRAResponse], current_round: int) -> str:
        """Format CRA responses for context"""
        if not responses:
            return "No previous CRA responses."

        lines = ["PREVIOUS CRA RESPONSES:", "=" * 40]

        # Group by round
        by_round = {}
        for r in responses:
            rnd = r.dispute_round or 1
            if rnd not in by_round:
                by_round[rnd] = []
            by_round[rnd].append(r)

        for rnd in sorted(by_round.keys()):
            if rnd < current_round:  # Only show previous rounds
                lines.append(f"\nRound {rnd}:")
                lines.append("-" * 20)
                for resp in by_round[rnd]:
                    date_str = resp.response_date.strftime('%m/%d/%Y') if resp.response_date else 'N/A'
                    lines.append(f"  {resp.bureau}: {resp.response_type or 'Unknown'} ({date_str})")
                    if resp.items_deleted:
                        lines.append(f"    Items deleted: {resp.items_deleted}")
                    if resp.items_verified:
                        lines.append(f"    Items verified: {resp.items_verified}")

        return '\n'.join(lines)

    # =========================================================================
    # LETTER GENERATION
    # =========================================================================

    def generate_letters(
        self,
        client_id: int,
        round_number: int = 1,
        selected_item_ids: Optional[List[int]] = None,
        bureaus: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        tone: str = 'professional',  # professional, aggressive, formal
    ) -> Dict[str, Any]:
        """
        Generate dispute letters for a client.

        Args:
            client_id: Client ID
            round_number: Dispute round (1-4)
            selected_item_ids: Specific item IDs to dispute (None = all)
            bureaus: Specific bureaus to generate for (None = all with items)
            custom_instructions: Additional instructions for the AI
            tone: Letter tone (professional, aggressive, formal)

        Returns:
            Dict with generated letters by bureau
        """
        # Gather context
        context = self.get_client_context(client_id)
        if 'error' in context:
            return context

        client = context['client']
        violations = context['violations']
        dispute_items = context['dispute_items']
        cra_responses = context['cra_responses']

        # Validate round
        if round_number not in self.ROUND_STRATEGIES:
            return {'error': f'Invalid round number: {round_number}. Must be 1-4.'}

        round_info = self.ROUND_STRATEGIES[round_number]

        # Filter items by selected IDs
        if selected_item_ids:
            dispute_items = [item for item in dispute_items if item.id in selected_item_ids]

        # Determine which bureaus to generate for
        if bureaus:
            target_bureaus = [b for b in bureaus if b in self.BUREAUS]
        else:
            # Get bureaus that have items
            target_bureaus = list(set(
                item.bureau for item in dispute_items
                if item.bureau in self.BUREAUS
            ))

        if not target_bureaus:
            target_bureaus = self.BUREAUS  # Default to all if no items

        # Build the prompt
        prompt = self._build_generation_prompt(
            client=client,
            violations=violations,
            dispute_items=dispute_items,
            cra_responses=cra_responses,
            round_number=round_number,
            round_info=round_info,
            target_bureaus=target_bureaus,
            custom_instructions=custom_instructions,
            tone=tone,
        )

        # Call AI to generate letters
        try:
            letters = self._call_ai_generate(prompt, round_info['prompt_key'])
        except Exception as e:
            return {'error': f'AI generation failed: {str(e)}'}

        return {
            'success': True,
            'client_id': client_id,
            'client_name': client.name,
            'round': round_number,
            'round_name': round_info['name'],
            'bureaus': target_bureaus,
            'letters': letters,
            'generated_at': datetime.utcnow().isoformat(),
            'items_disputed': len(dispute_items),
            'violations_cited': len(violations),
        }

    def _build_generation_prompt(
        self,
        client: Client,
        violations: List[Violation],
        dispute_items: List[DisputeItem],
        cra_responses: List[CRAResponse],
        round_number: int,
        round_info: Dict,
        target_bureaus: List[str],
        custom_instructions: Optional[str],
        tone: str,
    ) -> str:
        """Build the complete prompt for letter generation"""

        # Format all context
        client_info = self.format_client_info(client)
        violations_text = self.format_violations(violations)
        items_text = self.format_dispute_items(dispute_items)
        responses_text = self.format_cra_responses(cra_responses, round_number)

        # Tone instructions
        tone_instructions = {
            'professional': 'Use a professional but firm tone. Be clear about violations while maintaining a business-like approach.',
            'aggressive': 'Use an aggressive, demanding tone. Emphasize legal consequences and statutory damages. Reference specific case law.',
            'formal': 'Use a formal, legal tone. Structure the letter as a formal legal demand with proper citations.',
        }

        prompt = f"""
DISPUTE LETTER GENERATION REQUEST
{'=' * 60}

ROUND: {round_number} - {round_info['name']}
STRATEGY: {round_info['description']}
FOCUS: {round_info['focus']}

{client_info}

{violations_text}

{items_text}

{responses_text}

TARGET BUREAUS: {', '.join(target_bureaus)}

TONE: {tone_instructions.get(tone, tone_instructions['professional'])}

TODAY'S DATE: {date.today().strftime('%B %d, %Y')}

INSTRUCTIONS:
{'=' * 60}
Generate a separate dispute letter for each target bureau ({', '.join(target_bureaus)}).

Each letter must:
1. Be properly addressed to the specific bureau
2. Include all client identifying information
3. Reference specific FCRA sections violated
4. List each disputed item with specific reasons
5. Demand appropriate action based on the round strategy
6. Include response deadline (30 days for Round 1-2, 15 days for Round 3-4)
7. Reference previous responses if this is Round 2+

{f"ADDITIONAL INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

FORMAT YOUR OUTPUT:
For each bureau, use this format:

===START LETTER: [BUREAU NAME]===
[Full letter content here]
===END LETTER: [BUREAU NAME]===

Generate all letters now:
"""

        return prompt

    def _call_ai_generate(self, prompt: str, round_key: str) -> Dict[str, str]:
        """Call Claude to generate the letters"""

        # Load the round-specific prompt from knowledge base
        try:
            system_prompt = self.prompt_loader.get_round_prompt(
                int(round_key.replace('r', ''))
            )
        except Exception:
            # Fallback to quick prompt
            system_prompt = self.prompt_loader.load_prompt('quick')

        # Truncate system prompt if too long (keep first 50k chars)
        if len(system_prompt) > 50000:
            system_prompt = system_prompt[:50000] + "\n\n[Truncated for length]"

        # Call Claude
        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        response_text = response.content[0].text

        # Parse letters from response
        letters = self._parse_letters(response_text)

        return letters

    def _parse_letters(self, response_text: str) -> Dict[str, str]:
        """Parse individual letters from AI response"""
        letters = {}

        # Pattern to match ===START LETTER: Bureau=== ... ===END LETTER: Bureau===
        pattern = r'===START LETTER:\s*(\w+)===\s*(.*?)\s*===END LETTER:\s*\1==='

        matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)

        for bureau, content in matches:
            bureau_name = bureau.strip().title()
            letters[bureau_name] = content.strip()

        # If no matches with the formal pattern, try simpler parsing
        if not letters:
            # Try to find sections by bureau name
            for bureau in self.BUREAUS:
                # Look for bureau headers
                patterns = [
                    rf'(?:Letter to |For ){bureau}[:\s]*\n(.*?)(?=(?:Letter to |For )(?:Equifax|Experian|TransUnion)|$)',
                    rf'{bureau}\s*-+\s*\n(.*?)(?={"|".join(self.BUREAUS)}|$)',
                ]
                for p in patterns:
                    match = re.search(p, response_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        letters[bureau] = match.group(1).strip()
                        break

        # If still no letters parsed, return the whole response as a single letter
        if not letters:
            letters['Combined'] = response_text.strip()

        return letters

    # =========================================================================
    # QUICK GENERATION
    # =========================================================================

    def generate_quick_letter(
        self,
        client_id: int,
        bureau: str,
        item_description: str,
        violation_type: str,
        custom_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a quick single letter for one item"""

        context = self.get_client_context(client_id)
        if 'error' in context:
            return context

        client = context['client']

        prompt = f"""
Generate a single FCRA dispute letter for:

{self.format_client_info(client)}

BUREAU: {bureau}
ITEM: {item_description}
VIOLATION TYPE: {violation_type}
{f"ADDITIONAL CONTEXT: {custom_text}" if custom_text else ""}

Generate a concise but effective dispute letter citing the appropriate FCRA section.
The letter should demand investigation and correction/deletion of the disputed item.
Include a 30-day response deadline.
"""

        try:
            system_prompt = self.prompt_loader.load_prompt('quick')
            if len(system_prompt) > 30000:
                system_prompt = system_prompt[:30000]

            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            letter_content = response.content[0].text

            return {
                'success': True,
                'client_id': client_id,
                'bureau': bureau,
                'letter': letter_content,
                'generated_at': datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {'error': f'Generation failed: {str(e)}'}

    # =========================================================================
    # LETTER MANAGEMENT
    # =========================================================================

    def save_letter(
        self,
        client_id: int,
        bureau: str,
        content: str,
        round_number: int,
        analysis_id: Optional[int] = None,
    ) -> DisputeLetter:
        """Save a generated letter to the database"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client not found")

        letter = DisputeLetter(
            client_id=client_id,
            client_name=client.name,
            analysis_id=analysis_id,
            bureau=bureau,
            round_number=round_number,
            letter_content=content,
            created_at=datetime.utcnow(),
        )

        self.db.add(letter)
        self.db.commit()
        self.db.refresh(letter)

        return letter

    def get_saved_letters(
        self,
        client_id: int,
        round_number: Optional[int] = None,
    ) -> List[DisputeLetter]:
        """Get saved letters for a client"""
        query = self.db.query(DisputeLetter).filter(
            DisputeLetter.client_id == client_id
        )

        if round_number:
            query = query.filter(DisputeLetter.round_number == round_number)

        return query.order_by(DisputeLetter.created_at.desc()).all()

    # =========================================================================
    # TEMPLATES AND SUGGESTIONS
    # =========================================================================

    def get_round_info(self, round_number: int) -> Dict[str, Any]:
        """Get information about a specific round"""
        if round_number not in self.ROUND_STRATEGIES:
            return {'error': 'Invalid round number'}

        return {
            'round': round_number,
            **self.ROUND_STRATEGIES[round_number],
        }

    def get_all_rounds_info(self) -> List[Dict[str, Any]]:
        """Get information about all rounds"""
        return [
            {'round': rnd, **info}
            for rnd, info in self.ROUND_STRATEGIES.items()
        ]

    def suggest_next_action(self, client_id: int) -> Dict[str, Any]:
        """Suggest the next dispute action based on client's history"""
        context = self.get_client_context(client_id)
        if 'error' in context:
            return context

        client = context['client']
        cra_responses = context['cra_responses']
        dispute_items = context['dispute_items']
        current_round = context['current_round']

        # Count items by status
        items_by_status = {}
        for item in dispute_items:
            status = item.status or 'unknown'
            items_by_status[status] = items_by_status.get(status, 0) + 1

        # Check CRA response status
        responses_by_bureau = {}
        for resp in cra_responses:
            if resp.dispute_round == current_round:
                responses_by_bureau[resp.bureau] = resp.response_type

        # Determine suggestion
        verified_count = items_by_status.get('verified', 0) + items_by_status.get('no_change', 0)
        pending_count = items_by_status.get('sent', 0) + items_by_status.get('in_progress', 0)
        deleted_count = items_by_status.get('deleted', 0)

        suggestion = {
            'client_id': client_id,
            'current_round': current_round,
            'items_summary': items_by_status,
            'responses_received': responses_by_bureau,
        }

        if pending_count > 0:
            suggestion['action'] = 'wait'
            suggestion['message'] = f'Waiting for responses on {pending_count} items'
            suggestion['next_round'] = current_round
        elif verified_count > 0 and current_round < 4:
            suggestion['action'] = 'escalate'
            suggestion['message'] = f'{verified_count} items verified. Recommend escalating to Round {current_round + 1}'
            suggestion['next_round'] = current_round + 1
            suggestion['round_info'] = self.ROUND_STRATEGIES[current_round + 1]
        elif current_round == 4:
            suggestion['action'] = 'litigation'
            suggestion['message'] = 'Round 4 complete. Consider litigation referral.'
            suggestion['next_round'] = None
        else:
            suggestion['action'] = 'generate'
            suggestion['message'] = f'Ready to generate Round {current_round} letters'
            suggestion['next_round'] = current_round
            suggestion['round_info'] = self.ROUND_STRATEGIES[current_round]

        return suggestion

    # =========================================================================
    # REGENERATION WITH EDITS
    # =========================================================================

    def regenerate_with_feedback(
        self,
        client_id: int,
        bureau: str,
        original_letter: str,
        feedback: str,
        round_number: int = 1,
    ) -> Dict[str, Any]:
        """Regenerate a letter incorporating user feedback"""

        context = self.get_client_context(client_id)
        if 'error' in context:
            return context

        client = context['client']

        prompt = f"""
I previously generated this dispute letter:

---ORIGINAL LETTER---
{original_letter}
---END ORIGINAL---

The user has provided this feedback for revision:
{feedback}

Please regenerate the letter incorporating the feedback while maintaining:
1. Proper FCRA citations
2. Professional tone
3. All client information
4. Legal validity

{self.format_client_info(client)}

BUREAU: {bureau}
ROUND: {round_number}

Generate the revised letter:
"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            revised_letter = response.content[0].text

            return {
                'success': True,
                'client_id': client_id,
                'bureau': bureau,
                'letter': revised_letter,
                'feedback_applied': feedback,
                'generated_at': datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {'error': f'Regeneration failed: {str(e)}'}

    # =========================================================================
    # DASHBOARD DATA
    # =========================================================================

    def get_dashboard_data(self, client_id: Optional[int] = None) -> Dict[str, Any]:
        """Get data for the AI Dispute Writer dashboard"""

        if client_id:
            # Single client view
            context = self.get_client_context(client_id)
            if 'error' in context:
                return context

            client = context['client']
            violations = context['violations']
            dispute_items = context['dispute_items']
            cra_responses = context['cra_responses']

            # Get saved letters
            saved_letters = self.get_saved_letters(client_id)

            # Get suggestion
            suggestion = self.suggest_next_action(client_id)

            return {
                'client': {
                    'id': client.id,
                    'name': client.name,
                    'email': client.email,
                    'current_round': client.current_dispute_round or 1,
                    'dispute_status': client.dispute_status,
                },
                'stats': {
                    'violations_count': len(violations),
                    'dispute_items_count': len(dispute_items),
                    'cra_responses_count': len(cra_responses),
                    'saved_letters_count': len(saved_letters),
                },
                'violations': [
                    {
                        'id': v.id,
                        'type': v.violation_type,
                        'bureau': v.bureau,
                        'account': v.account_name,
                        'fcra_section': v.fcra_section,
                    }
                    for v in violations
                ],
                'dispute_items': [
                    {
                        'id': item.id,
                        'bureau': item.bureau,
                        'creditor': item.creditor_name,
                        'type': item.item_type,
                        'status': item.status,
                        'account_id': item.account_id,
                    }
                    for item in dispute_items
                ],
                'suggestion': suggestion,
                'rounds_info': self.get_all_rounds_info(),
            }

        else:
            # Overview dashboard
            # Get clients ready for letter generation
            active_clients = self.db.query(Client).filter(
                Client.status == 'active',
                Client.dispute_status.in_(['active', 'new', 'waiting_response'])
            ).limit(20).all()

            # Get recent letters
            recent_letters = self.db.query(DisputeLetter).order_by(
                DisputeLetter.created_at.desc()
            ).limit(10).all()

            # Count totals
            total_letters = self.db.query(DisputeLetter).count()

            return {
                'active_clients': [
                    {
                        'id': c.id,
                        'name': c.name,
                        'current_round': c.current_dispute_round or 1,
                        'dispute_status': c.dispute_status,
                    }
                    for c in active_clients
                ],
                'recent_letters': [
                    {
                        'id': l.id,
                        'client_id': l.client_id,
                        'client_name': l.client_name,
                        'bureau': l.bureau,
                        'round': l.round_number,
                        'created_at': l.created_at.isoformat() if l.created_at else None,
                    }
                    for l in recent_letters
                ],
                'total_letters': total_letters,
                'rounds_info': self.get_all_rounds_info(),
            }

    # =========================================================================
    # 5-DAY KNOCK-OUT (IDENTITY THEFT) GENERATION
    # =========================================================================

    def generate_5day_knockout(
        self,
        client_id: int,
        police_case_number: Optional[str] = None,
        ftc_reference_number: Optional[str] = None,
        disputed_items: Optional[List[Dict]] = None,
        phase: int = 1,  # 1 = prep docs, 2 = full dispute with police #
    ) -> Dict[str, Any]:
        """
        Generate 5-Day Knock-Out identity theft dispute package.

        Phase 1: Generates preparation documents (before police report)
        - Police Report Prep Sheet
        - FTC Complaint Prep Sheet
        - Notarized Affidavit Template

        Phase 2: Generates full dispute package (after police report filed)
        - 605B Letters to all 3 bureaus (fraud addresses)
        - FTC Identity Theft Affidavit
        - Furnisher dispute letters
        - Third-party agency freeze letters
        - BBB complaint templates (optional escalation)

        Args:
            client_id: Client ID
            police_case_number: Police report case # (required for Phase 2)
            ftc_reference_number: FTC complaint reference # (optional)
            disputed_items: List of accounts to dispute
            phase: 1 for prep, 2 for full dispute

        Returns:
            Dict with generated documents
        """
        context = self.get_client_context(client_id)
        if 'error' in context:
            return context

        client = context['client']
        violations = context['violations']
        dispute_items = context['dispute_items']

        # Use provided items or all dispute items
        if disputed_items:
            items_to_dispute = disputed_items
        else:
            items_to_dispute = [
                {
                    'creditor': item.creditor_name,
                    'account_number': item.account_id,
                    'bureau': item.bureau,
                    'type': item.item_type,
                    'balance': getattr(item, 'balance', 'Unknown'),
                }
                for item in dispute_items
            ]

        strategy = self.SPECIAL_STRATEGIES['5dayknockout']

        # Build the prompt
        prompt = self._build_5day_knockout_prompt(
            client=client,
            items=items_to_dispute,
            violations=violations,
            phase=phase,
            police_case_number=police_case_number,
            ftc_reference_number=ftc_reference_number,
        )

        try:
            documents = self._call_ai_5day_knockout(prompt, phase)
        except Exception as e:
            return {'error': f'AI generation failed: {str(e)}'}

        return {
            'success': True,
            'client_id': client_id,
            'client_name': client.name,
            'strategy': strategy['name'],
            'phase': phase,
            'phase_name': 'Preparation Documents' if phase == 1 else 'Full Dispute Package',
            'police_case_number': police_case_number,
            'ftc_reference_number': ftc_reference_number,
            'documents': documents,
            'items_disputed': len(items_to_dispute),
            'generated_at': datetime.utcnow().isoformat(),
            'next_steps': self._get_5day_knockout_next_steps(phase, police_case_number),
        }

    def _build_5day_knockout_prompt(
        self,
        client: Client,
        items: List[Dict],
        violations: List[Violation],
        phase: int,
        police_case_number: Optional[str],
        ftc_reference_number: Optional[str],
    ) -> str:
        """Build prompt for 5-Day Knock-Out generation"""

        client_info = self.format_client_info(client)

        # Format items for dispute
        items_text = "ACCOUNTS TO DISPUTE:\n" + "=" * 40 + "\n"
        for i, item in enumerate(items, 1):
            items_text += f"\n{i}. {item.get('creditor', 'Unknown Creditor')}\n"
            items_text += f"   Account: {item.get('account_number', 'N/A')}\n"
            items_text += f"   Bureau: {item.get('bureau', 'All')}\n"
            items_text += f"   Type: {item.get('type', 'N/A')}\n"
            if item.get('balance'):
                items_text += f"   Balance: ${item.get('balance')}\n"

        prompt = f"""
5-DAY KNOCK-OUT IDENTITY THEFT DISPUTE GENERATION
{'=' * 60}

PHASE: {phase} - {'PREPARATION DOCUMENTS' if phase == 1 else 'FULL DISPUTE PACKAGE'}

{client_info}

{items_text}

POLICE CASE NUMBER: {police_case_number or 'NOT YET OBTAINED'}
FTC REFERENCE NUMBER: {ftc_reference_number or 'NOT YET OBTAINED'}

TODAY'S DATE: {date.today().strftime('%B %d, %Y')}

BUREAU FRAUD DEPARTMENT ADDRESSES:
- Experian: P.O. Box 9554, Allen, TX 75013
- Equifax: P.O. Box 105069, Atlanta, GA 30348
- TransUnion: Fraud Victim Assistance Dept, P.O. Box 2000, Chester, PA 19016

"""

        if phase == 1:
            prompt += """
PHASE 1 INSTRUCTIONS - Generate these preparation documents:
{'=' * 60}

1. POLICE REPORT PREP SHEET
   - List of accounts to report as fraudulent
   - Talking points for police station visit
   - Key dates and amounts

2. FTC COMPLAINT PREP SHEET
   - Information to enter on IdentityTheft.gov
   - Account details organized for FTC form

3. NOTARIZED AFFIDAVIT TEMPLATE
   - Consumer declaration of identity theft
   - List of fraudulent accounts
   - Signature/notary blocks

Format each document with clear headers:
===START DOCUMENT: [DOCUMENT NAME]===
[Content]
===END DOCUMENT: [DOCUMENT NAME]===
"""
        else:
            prompt += f"""
PHASE 2 INSTRUCTIONS - Generate full dispute package with police case #{police_case_number}:
{'=' * 60}

Generate ALL of the following documents:

BUREAU LETTERS (send to FRAUD addresses, not regular dispute):
1. Experian_605B_Letter - Identity theft block request
2. Equifax_605B_Letter - Identity theft block request
3. TransUnion_605B_Letter - Identity theft block request

FURNISHER LETTERS (one per creditor):
4. Furnisher dispute letters for each account listed

THIRD-PARTY AGENCY FREEZE LETTERS:
5. LexisNexis freeze request
6. Teletrack freeze request
7. Innovis freeze request

SUPPORTING DOCUMENTS:
8. FTC Identity Theft Report (completed version)
9. Certified mail tracking sheet
10. Follow-up call script for bureaus

OPTIONAL ESCALATION:
11. BBB complaint template (for collection agencies)
12. Reinsertion dispute template (if items return)

Each letter must include:
- Police case number: {police_case_number}
- FTC reference: {ftc_reference_number or 'See attached FTC report'}
- Specific FCRA §605B citations
- 4 business day deadline for blocking
- List of specific accounts to block
- Demand for written confirmation

Format each document with clear headers:
===START DOCUMENT: [DOCUMENT NAME]===
[Content]
===END DOCUMENT: [DOCUMENT NAME]===
"""

        return prompt

    def _call_ai_5day_knockout(self, prompt: str, phase: int) -> Dict[str, str]:
        """Call Claude to generate 5-Day Knockout documents"""

        # Load the 5-Day Knockout prompt
        try:
            system_prompt = self.prompt_loader.get_5day_knockout_prompt()
        except Exception:
            # Fallback to quick prompt if 5dayknockout not found
            system_prompt = self.prompt_loader.load_prompt('quick')

        # Truncate if needed
        if len(system_prompt) > 80000:
            system_prompt = system_prompt[:80000] + "\n\n[Truncated for length]"

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,  # Larger for multiple documents
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse documents from response
        documents = {}
        pattern = r'===START DOCUMENT:\s*(.+?)===\s*(.*?)\s*===END DOCUMENT:\s*\1==='
        matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)

        for doc_name, content in matches:
            documents[doc_name.strip()] = content.strip()

        # If no documents parsed, return raw response
        if not documents:
            documents['Combined_Output'] = response_text.strip()

        return documents

    def _get_5day_knockout_next_steps(self, phase: int, police_case_number: Optional[str]) -> List[str]:
        """Get next steps based on current phase"""
        if phase == 1:
            return [
                "1. Print the Police Report Prep Sheet",
                "2. Visit your local police station to file an identity theft report",
                "3. Get the police case number",
                "4. File FTC complaint at IdentityTheft.gov using prep sheet",
                "5. Get affidavit notarized at UPS Store or bank",
                "6. Return here with police case # to generate Phase 2 documents",
            ]
        else:
            return [
                "1. Print all 605B letters and supporting documents",
                "2. Make copies of police report and FTC complaint",
                "3. Mail to bureau FRAUD addresses via certified mail",
                "4. Send furnisher letters via certified mail",
                "5. Submit third-party agency freezes",
                "6. Track with certified mail receipts",
                "7. Follow up by phone after 5 business days",
                "8. Bureaus must block within 4 business days per FCRA §605B",
            ]

    def get_special_strategies_info(self) -> List[Dict[str, Any]]:
        """Get information about all special strategies"""
        return [
            {'key': key, **info}
            for key, info in self.SPECIAL_STRATEGIES.items()
        ]

    def get_strategy_info(self, strategy_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific special strategy"""
        if strategy_key in self.SPECIAL_STRATEGIES:
            return {'key': strategy_key, **self.SPECIAL_STRATEGIES[strategy_key]}
        return None
