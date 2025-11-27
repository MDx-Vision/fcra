"""
Case Law Citation Service for FCRA Litigation Platform

Provides functions for managing and querying FCRA case law citations.
"""

from datetime import datetime
from database import get_db, CaseLawCitation


DEFAULT_FCRA_CASES = [
    {
        "case_name": "Cousin v. Trans Union Corp.",
        "citation": "246 F.3d 359 (5th Cir. 2001)",
        "court": "5th Circuit",
        "year": 2001,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reinsertion", "failure_to_investigate"],
        "key_holding": "A CRA must maintain reasonable procedures to prevent reinsertion of previously deleted information without notice to consumer.",
        "full_summary": "The court held that Trans Union violated the FCRA by reinserting previously deleted information without proper verification and without notifying the consumer. The case established that CRAs have an ongoing duty to ensure the accuracy of information and cannot simply reinsert disputed items without a legitimate basis.",
        "quote_snippets": [
            {"quote": "The FCRA imposes a duty on CRAs to follow reasonable procedures to assure maximum possible accuracy.", "page": "365"},
            {"quote": "Reinsertion of previously deleted information without notification violates the consumer's rights under § 1681i.", "page": "367"}
        ],
        "damages_awarded": 75000.00,
        "plaintiff_won": True,
        "relevance_score": 5,
        "tags": ["reinsertion", "trans_union", "notification", "reasonable_procedures"]
    },
    {
        "case_name": "Dennis v. BEH-1, LLC",
        "citation": "520 F.3d 1066 (9th Cir. 2008)",
        "court": "9th Circuit",
        "year": 2008,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reinsertion", "failure_to_investigate"],
        "key_holding": "Reinsertion of disputed information after deletion requires the CRA to certify that the information is complete and accurate.",
        "full_summary": "This Ninth Circuit case reinforced the standards for reinsertion of credit information. The court found that debt collectors acting as furnishers must ensure complete accuracy before information can be reinserted, and CRAs must have proper certification procedures.",
        "quote_snippets": [
            {"quote": "A CRA that reinserts previously deleted information must certify that the information meets accuracy requirements.", "page": "1071"}
        ],
        "damages_awarded": 50000.00,
        "plaintiff_won": True,
        "relevance_score": 4,
        "tags": ["reinsertion", "debt_collector", "certification", "accuracy"]
    },
    {
        "case_name": "Stevenson v. TRW Inc.",
        "citation": "987 F.2d 288 (5th Cir. 1993)",
        "court": "5th Circuit",
        "year": 1993,
        "fcra_sections": ["611", "1681i", "1681e"],
        "violation_types": ["reinsertion", "reasonable_procedures"],
        "key_holding": "CRAs must conduct a reasonable reinvestigation when a consumer disputes information, and repeated failures constitute willful violations.",
        "full_summary": "Landmark case establishing that TRW's repeated reinsertion of inaccurate accounts after disputes constituted a pattern of willful non-compliance. The court emphasized that consumers are entitled to meaningful dispute resolution, not a rubber-stamp process.",
        "quote_snippets": [
            {"quote": "A CRA's reinvestigation duty requires more than a cursory review; it must be meaningful and thorough.", "page": "293"},
            {"quote": "Repeated failures to correct inaccurate information can evidence willful non-compliance.", "page": "294"}
        ],
        "damages_awarded": 290000.00,
        "plaintiff_won": True,
        "relevance_score": 5,
        "tags": ["reinsertion", "willful", "punitive_damages", "repeated_violations"]
    },
    {
        "case_name": "Safeco Insurance Co. of America v. Burr",
        "citation": "551 U.S. 47 (2007)",
        "court": "Supreme Court",
        "year": 2007,
        "fcra_sections": ["615", "1681m", "1681n"],
        "violation_types": ["willfulness", "adverse_action"],
        "key_holding": "Willfulness under FCRA includes reckless disregard of statutory duty, not just knowing violations.",
        "full_summary": "The Supreme Court defined 'willfulness' under FCRA § 1681n to include reckless disregard of statutory duties. A company acts willfully if it knew or showed reckless disregard for whether its conduct violated the FCRA. This is the controlling standard for statutory and punitive damages.",
        "quote_snippets": [
            {"quote": "A company subject to FCRA does not act in reckless disregard of it unless the action is not only a violation under a reasonable reading of the statute's terms, but shows that the company ran a risk of violating the law substantially greater than the risk associated with a reading that was merely careless.", "page": "69"},
            {"quote": "Willful violations include both knowing violations and reckless ones.", "page": "57"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 5,
        "tags": ["willfulness", "supreme_court", "reckless_disregard", "statutory_damages"]
    },
    {
        "case_name": "Saunders v. Branch Banking & Trust Co. of Virginia",
        "citation": "526 F.3d 142 (4th Cir. 2008)",
        "court": "4th Circuit",
        "year": 2008,
        "fcra_sections": ["623", "1681s-2"],
        "violation_types": ["willfulness", "furnisher_duties"],
        "key_holding": "Furnishers must conduct reasonable investigations upon receiving notice of dispute from a CRA.",
        "full_summary": "This case applied the Safeco willfulness standard to furnisher liability. The court held that a furnisher who fails to investigate a dispute properly after receiving notice from a CRA may be liable for willful or negligent violations depending on the circumstances.",
        "quote_snippets": [
            {"quote": "A furnisher's investigation must be reasonable under the circumstances, not merely a verification of its own records.", "page": "150"}
        ],
        "damages_awarded": 15000.00,
        "plaintiff_won": True,
        "relevance_score": 4,
        "tags": ["willfulness", "furnisher", "investigation", "safeco_standard"]
    },
    {
        "case_name": "Cushman v. Trans Union Corp.",
        "citation": "115 F.3d 220 (3rd Cir. 1997)",
        "court": "3rd Circuit",
        "year": 1997,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reasonable_investigation", "failure_to_investigate"],
        "key_holding": "A CRA's reinvestigation must be reasonably designed to determine the accuracy of disputed information.",
        "full_summary": "The Third Circuit established that merely forwarding a dispute to the furnisher and relying on verification is insufficient. CRAs must conduct their own reasonable investigation, especially when the consumer provides documentation supporting the dispute.",
        "quote_snippets": [
            {"quote": "The FCRA requires CRAs to actually investigate disputes, not merely parrot information from furnishers.", "page": "225"},
            {"quote": "A reasonable investigation includes reviewing documentation provided by the consumer.", "page": "227"}
        ],
        "damages_awarded": 30000.00,
        "plaintiff_won": True,
        "relevance_score": 5,
        "tags": ["reasonable_investigation", "trans_union", "documentation", "cushman_standard"]
    },
    {
        "case_name": "Henson v. CSC Credit Services",
        "citation": "29 F.3d 280 (7th Cir. 1994)",
        "court": "7th Circuit",
        "year": 1994,
        "fcra_sections": ["607", "611", "1681e", "1681i"],
        "violation_types": ["reasonable_investigation", "reasonable_procedures"],
        "key_holding": "What constitutes reasonable procedures varies with the circumstances, including the cost of verification versus the harm to consumers.",
        "full_summary": "Judge Posner's opinion established that 'reasonableness' under FCRA is a balancing test. CRAs must weigh the cost of additional verification against the magnitude and frequency of harm to consumers. High-impact disputes require more thorough investigation.",
        "quote_snippets": [
            {"quote": "The greater the harm from inaccuracy, the more effort must be made to prevent it.", "page": "284"},
            {"quote": "Reasonableness requires balancing the cost of verification against the risk and magnitude of consumer harm.", "page": "285"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 4,
        "tags": ["reasonable_procedures", "balancing_test", "posner", "cost_benefit"]
    },
    {
        "case_name": "Johnson v. MBNA America Bank, NA",
        "citation": "357 F.3d 426 (4th Cir. 2004)",
        "court": "4th Circuit",
        "year": 2004,
        "fcra_sections": ["623", "1681s-2(b)"],
        "violation_types": ["furnisher_duties", "reasonable_investigation"],
        "key_holding": "Furnishers must conduct a reasonable investigation upon receiving notice of dispute, which requires more than verifying internal records.",
        "full_summary": "The Fourth Circuit clarified furnisher duties under § 1681s-2(b). Upon receiving dispute notice from a CRA, furnishers must investigate beyond their own records when circumstances warrant. Simply verifying that internal records match reported data is insufficient.",
        "quote_snippets": [
            {"quote": "A furnisher's investigation is unreasonable as a matter of law if it merely verifies that its internal records match the information previously reported.", "page": "431"}
        ],
        "damages_awarded": 20000.00,
        "plaintiff_won": True,
        "relevance_score": 5,
        "tags": ["furnisher", "investigation", "mbna", "beyond_internal_records"]
    },
    {
        "case_name": "Spokeo, Inc. v. Robins",
        "citation": "578 U.S. 330 (2016)",
        "court": "Supreme Court",
        "year": 2016,
        "fcra_sections": ["607", "1681e"],
        "violation_types": ["standing", "article_iii"],
        "key_holding": "A plaintiff must show concrete injury, not just a bare procedural violation, to have Article III standing for FCRA claims.",
        "full_summary": "The Supreme Court held that a plaintiff cannot satisfy Article III standing based solely on a statutory violation. The plaintiff must show that the violation caused a concrete injury. However, intangible harms can be concrete if they have a close relationship to harms traditionally recognized by law.",
        "quote_snippets": [
            {"quote": "Article III standing requires a concrete injury even in the context of a statutory violation.", "page": "341"},
            {"quote": "A bare procedural violation, divorced from any concrete harm, will not satisfy the injury-in-fact requirement.", "page": "342"},
            {"quote": "Intangible injuries can be concrete if they bear a close relationship to harms traditionally recognized as providing a basis for lawsuits.", "page": "340"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 5,
        "tags": ["standing", "supreme_court", "concrete_harm", "procedural_violation"]
    },
    {
        "case_name": "TransUnion LLC v. Ramirez",
        "citation": "594 U.S. 413 (2021)",
        "court": "Supreme Court",
        "year": 2021,
        "fcra_sections": ["607", "611", "1681e", "1681g"],
        "violation_types": ["standing", "article_iii", "dissemination"],
        "key_holding": "Only plaintiffs whose inaccurate credit information was actually disseminated to third parties have standing; internal errors alone are insufficient.",
        "full_summary": "Building on Spokeo, the Supreme Court held that consumers whose inaccurate OFAC terrorist alerts were never disseminated to third parties lacked standing. Only the 1,853 class members whose information was actually shared with potential creditors had concrete injury. This significantly limits class actions for internal-only FCRA violations.",
        "quote_snippets": [
            {"quote": "No concrete harm, no standing.", "page": "426"},
            {"quote": "The mere existence of inaccurate information in a database, without dissemination, does not constitute concrete harm.", "page": "432"},
            {"quote": "Publication of misleading credit information to third parties is the hallmark of concrete reputational harm.", "page": "433"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 5,
        "tags": ["standing", "supreme_court", "dissemination", "concrete_harm", "class_action"]
    },
    {
        "case_name": "Gorman v. Wolpoff & Abramson, LLP",
        "citation": "584 F.3d 1147 (9th Cir. 2009)",
        "court": "9th Circuit",
        "year": 2009,
        "fcra_sections": ["623", "1681s-2"],
        "violation_types": ["furnisher_duties", "reasonable_investigation"],
        "key_holding": "Furnishers must investigate disputes using all relevant information, not just their own files.",
        "full_summary": "The Ninth Circuit held that debt collectors acting as furnishers must conduct meaningful investigations. They cannot ignore consumer-provided documentation that contradicts their records. The investigation must consider information beyond the furnisher's internal files.",
        "quote_snippets": [
            {"quote": "An investigation that ignores contradictory information from the consumer is unreasonable as a matter of law.", "page": "1157"},
            {"quote": "The furnisher's duty extends to reviewing relevant information beyond its own records.", "page": "1158"}
        ],
        "damages_awarded": 60000.00,
        "plaintiff_won": True,
        "relevance_score": 5,
        "tags": ["furnisher", "debt_collector", "investigation", "consumer_documentation"]
    },
    {
        "case_name": "Nelson v. Chase Manhattan Mortgage Corp.",
        "citation": "282 F.3d 1057 (9th Cir. 2002)",
        "court": "9th Circuit",
        "year": 2002,
        "fcra_sections": ["623", "1681s-2"],
        "violation_types": ["furnisher_duties", "private_right_of_action"],
        "key_holding": "There is no private right of action under § 1681s-2(a); consumers can only sue under § 1681s-2(b) after a CRA-forwarded dispute.",
        "full_summary": "This case clarified the scope of private enforcement against furnishers. Consumers cannot directly sue furnishers for violations of § 1681s-2(a) (duty to report accurate information). Private suits are only available under § 1681s-2(b) after the consumer disputes through a CRA and the furnisher fails to investigate properly.",
        "quote_snippets": [
            {"quote": "Section 1681s-2(a) is enforceable only through regulatory action, not private lawsuits.", "page": "1060"},
            {"quote": "The private right of action arises only after a CRA notifies the furnisher of a consumer dispute.", "page": "1061"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 4,
        "tags": ["furnisher", "private_right_of_action", "section_2a", "section_2b"]
    },
    {
        "case_name": "Guimond v. Trans Union Credit Information Co.",
        "citation": "45 F.3d 1329 (9th Cir. 1995)",
        "court": "9th Circuit",
        "year": 1995,
        "fcra_sections": ["607", "611", "1681e", "1681i"],
        "violation_types": ["reasonable_procedures", "systemic_failures"],
        "key_holding": "Systemic failures in procedures can constitute willful FCRA violations warranting punitive damages.",
        "full_summary": "The Ninth Circuit upheld a substantial punitive damages award where Trans Union's systemic procedural failures demonstrated reckless disregard for consumer rights. When a CRA's basic operating procedures are fundamentally flawed, this can constitute willfulness.",
        "quote_snippets": [
            {"quote": "Systemic procedural deficiencies that repeatedly harm consumers can evidence willful non-compliance.", "page": "1333"}
        ],
        "damages_awarded": 500000.00,
        "plaintiff_won": True,
        "relevance_score": 4,
        "tags": ["willful", "punitive_damages", "systemic_failures", "trans_union"]
    },
    {
        "case_name": "Dalton v. Capital Associated Industries, Inc.",
        "citation": "257 F.3d 409 (4th Cir. 2001)",
        "court": "4th Circuit",
        "year": 2001,
        "fcra_sections": ["604", "607", "1681b", "1681e"],
        "violation_types": ["permissible_purpose", "employment"],
        "key_holding": "Employers must obtain consent before obtaining consumer reports and provide proper disclosure.",
        "full_summary": "This employment screening case established that FCRA's consent and disclosure requirements for employment background checks must be strictly followed. Employers cannot bury FCRA authorizations in general application forms.",
        "quote_snippets": [
            {"quote": "The FCRA disclosure must be clear, conspicuous, and in a document consisting solely of the disclosure.", "page": "415"}
        ],
        "damages_awarded": 25000.00,
        "plaintiff_won": True,
        "relevance_score": 3,
        "tags": ["employment", "consent", "disclosure", "background_check"]
    },
    {
        "case_name": "Philbin v. Trans Union Corp.",
        "citation": "101 F.3d 957 (3rd Cir. 1996)",
        "court": "3rd Circuit",
        "year": 1996,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reinvestigation", "mixed_files"],
        "key_holding": "A CRA must correct its files when a reinvestigation reveals the original information was inaccurate.",
        "full_summary": "The court addressed mixed file cases where one consumer's information is placed on another's report. Trans Union was found liable for failing to properly investigate and correct a mixed file situation even after multiple disputes.",
        "quote_snippets": [
            {"quote": "When a reinvestigation reveals inaccuracy, the CRA has an absolute duty to correct the file.", "page": "963"}
        ],
        "damages_awarded": 45000.00,
        "plaintiff_won": True,
        "relevance_score": 4,
        "tags": ["mixed_files", "reinvestigation", "correction", "trans_union"]
    },
    {
        "case_name": "Seamans v. Temple University",
        "citation": "744 F.3d 853 (3rd Cir. 2014)",
        "court": "3rd Circuit",
        "year": 2014,
        "fcra_sections": ["615", "1681m"],
        "violation_types": ["adverse_action", "notice"],
        "key_holding": "An employer must provide proper adverse action notice when taking action based in whole or in part on a consumer report.",
        "full_summary": "This case reinforced that employers using consumer reports for hiring decisions must provide the required pre-adverse action notice and adverse action notice. The timing and content of these notices are strictly construed.",
        "quote_snippets": [
            {"quote": "The adverse action notice provisions protect the consumer's ability to challenge inaccurate information before harm occurs.", "page": "861"}
        ],
        "damages_awarded": 35000.00,
        "plaintiff_won": True,
        "relevance_score": 3,
        "tags": ["adverse_action", "employment", "notice", "pre_adverse"]
    },
    {
        "case_name": "Cortez v. Trans Union, LLC",
        "citation": "617 F.3d 688 (3rd Cir. 2010)",
        "court": "3rd Circuit",
        "year": 2010,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reasonable_investigation", "stale_information"],
        "key_holding": "CRAs must investigate whether reported information is current and not stale or obsolete.",
        "full_summary": "The Third Circuit ruled that Trans Union's investigation was unreasonable when it failed to verify whether disputed information was timely and should still be reported. Merely confirming the account existed was insufficient.",
        "quote_snippets": [
            {"quote": "A reasonable investigation must address the consumer's specific dispute, including whether information should still be reported.", "page": "696"}
        ],
        "damages_awarded": 18000.00,
        "plaintiff_won": True,
        "relevance_score": 4,
        "tags": ["stale_information", "reasonable_investigation", "obsolete", "trans_union"]
    },
    {
        "case_name": "Chuluunbat v. Experian Information Solutions",
        "citation": "4 F.4th 562 (7th Cir. 2021)",
        "court": "7th Circuit",
        "year": 2021,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reasonable_investigation", "legal_disputes"],
        "key_holding": "CRAs are not required to resolve underlying legal disputes between consumers and creditors.",
        "full_summary": "The Seventh Circuit held that when a consumer's dispute involves a legal question about whether they owe a debt, CRAs are not required to make that legal determination. However, they must still report the account status accurately.",
        "quote_snippets": [
            {"quote": "CRAs are not courts; they need not resolve legal disputes between consumers and creditors.", "page": "568"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 3,
        "tags": ["legal_disputes", "cra_limitations", "experian", "debt_validation"]
    },
    {
        "case_name": "Carvalho v. Equifax Information Services, LLC",
        "citation": "629 F.3d 876 (9th Cir. 2010)",
        "court": "9th Circuit",
        "year": 2010,
        "fcra_sections": ["611", "1681i"],
        "violation_types": ["reasonable_investigation", "methodology"],
        "key_holding": "The reasonableness of a CRA's investigation is judged by its procedures, not just outcomes.",
        "full_summary": "The Ninth Circuit emphasized that courts evaluate the process of investigation, not whether the outcome was ultimately correct. A CRA that uses reasonable procedures to investigate may not be liable even if errors persist.",
        "quote_snippets": [
            {"quote": "We evaluate reasonableness based on what the CRA did, not merely what it found.", "page": "883"}
        ],
        "damages_awarded": None,
        "plaintiff_won": False,
        "relevance_score": 4,
        "tags": ["reasonable_investigation", "procedures", "equifax", "methodology"]
    },
    {
        "case_name": "Syed v. M-I, LLC",
        "citation": "853 F.3d 492 (9th Cir. 2017)",
        "court": "9th Circuit",
        "year": 2017,
        "fcra_sections": ["604", "1681b"],
        "violation_types": ["standalone_disclosure", "employment"],
        "key_holding": "The FCRA disclosure document must not include any extraneous information; it must consist solely of the disclosure.",
        "full_summary": "This case strictly interpreted the 'standalone document' requirement for employment disclosures. Including a liability waiver or other language with the disclosure violates FCRA, even if the extraneous text seems beneficial to the consumer.",
        "quote_snippets": [
            {"quote": "Congress meant what it said: the disclosure must consist 'solely' of the disclosure itself.", "page": "499"}
        ],
        "damages_awarded": None,
        "plaintiff_won": True,
        "relevance_score": 4,
        "tags": ["employment", "standalone_disclosure", "liability_waiver", "class_action"]
    }
]


def populate_default_cases(db=None):
    """Seeds database with default FCRA case law citations."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        existing_count = db.query(CaseLawCitation).count()
        if existing_count > 0:
            return {"status": "skipped", "message": f"Database already has {existing_count} cases", "count": existing_count}
        
        added_count = 0
        for case_data in DEFAULT_FCRA_CASES:
            citation = CaseLawCitation(
                case_name=case_data["case_name"],
                citation=case_data["citation"],
                court=case_data["court"],
                year=case_data["year"],
                fcra_sections=case_data["fcra_sections"],
                violation_types=case_data["violation_types"],
                key_holding=case_data["key_holding"],
                full_summary=case_data["full_summary"],
                quote_snippets=case_data["quote_snippets"],
                damages_awarded=case_data.get("damages_awarded"),
                plaintiff_won=case_data.get("plaintiff_won"),
                relevance_score=case_data.get("relevance_score", 3),
                tags=case_data.get("tags", [])
            )
            db.add(citation)
            added_count += 1
        
        db.commit()
        return {"status": "success", "message": f"Added {added_count} case law citations", "count": added_count}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if close_db:
            db.close()


def get_citations_for_violation(violation_type, db=None):
    """Returns relevant cases for a specific violation type."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        all_cases = db.query(CaseLawCitation).all()
        matching = []
        for case in all_cases:
            if case.violation_types and violation_type in case.violation_types:
                matching.append(case.to_dict())
        return sorted(matching, key=lambda x: x['relevance_score'], reverse=True)
    finally:
        if close_db:
            db.close()


def get_citations_for_fcra_section(section, db=None):
    """Returns cases for a specific FCRA section."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        all_cases = db.query(CaseLawCitation).all()
        matching = []
        for case in all_cases:
            if case.fcra_sections:
                sections = [s.lower().replace('§', '').strip() for s in case.fcra_sections]
                if section.lower().replace('§', '').strip() in sections:
                    matching.append(case.to_dict())
        return sorted(matching, key=lambda x: x['relevance_score'], reverse=True)
    finally:
        if close_db:
            db.close()


def format_citation_for_letter(case_id, format_type='short', db=None):
    """Formats a citation for insertion into letters."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        case = db.query(CaseLawCitation).filter(CaseLawCitation.id == case_id).first()
        if not case:
            return None
        return case.format_citation(format_type)
    finally:
        if close_db:
            db.close()


def suggest_citations_for_analysis(analysis_id, db=None):
    """Suggests relevant citations based on analysis violations."""
    from database import Analysis, Violation
    
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return []
        
        violations = db.query(Violation).filter(Violation.analysis_id == analysis_id).all()
        
        violation_types = set()
        fcra_sections = set()
        for v in violations:
            if v.violation_type:
                vt = v.violation_type.lower().replace(' ', '_')
                violation_types.add(vt)
            if v.fcra_section:
                fcra_sections.add(v.fcra_section)
        
        all_cases = db.query(CaseLawCitation).all()
        
        suggestions = []
        for case in all_cases:
            score = 0
            matched_reasons = []
            
            if case.violation_types:
                case_vtypes = [vt.lower() for vt in case.violation_types]
                for vt in violation_types:
                    if vt in case_vtypes:
                        score += 3
                        matched_reasons.append(f"violation type: {vt}")
            
            if case.fcra_sections:
                case_sections = [s.lower().replace('§', '').strip() for s in case.fcra_sections]
                for section in fcra_sections:
                    if section.lower().replace('§', '').strip() in case_sections:
                        score += 2
                        matched_reasons.append(f"FCRA section: {section}")
            
            score += case.relevance_score or 0
            
            if score > 0:
                suggestions.append({
                    **case.to_dict(),
                    'match_score': score,
                    'match_reasons': matched_reasons
                })
        
        return sorted(suggestions, key=lambda x: x['match_score'], reverse=True)[:10]
    finally:
        if close_db:
            db.close()


def search_cases(query, db=None):
    """Full-text search across case law database."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        query_lower = query.lower()
        all_cases = db.query(CaseLawCitation).all()
        
        results = []
        for case in all_cases:
            score = 0
            
            if query_lower in case.case_name.lower():
                score += 10
            if case.citation and query_lower in case.citation.lower():
                score += 10
            if case.key_holding and query_lower in case.key_holding.lower():
                score += 5
            if case.full_summary and query_lower in case.full_summary.lower():
                score += 3
            if case.court and query_lower in case.court.lower():
                score += 2
            if case.tags:
                for tag in case.tags:
                    if query_lower in tag.lower():
                        score += 4
            
            if score > 0:
                results.append({
                    **case.to_dict(),
                    'search_score': score
                })
        
        return sorted(results, key=lambda x: x['search_score'], reverse=True)
    finally:
        if close_db:
            db.close()


def get_all_cases(filters=None, db=None):
    """Get all cases with optional filtering."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        query = db.query(CaseLawCitation)
        
        if filters:
            if filters.get('court'):
                query = query.filter(CaseLawCitation.court.ilike(f"%{filters['court']}%"))
            if filters.get('year'):
                query = query.filter(CaseLawCitation.year == int(filters['year']))
            if filters.get('plaintiff_won') is not None:
                query = query.filter(CaseLawCitation.plaintiff_won == filters['plaintiff_won'])
        
        cases = query.order_by(CaseLawCitation.relevance_score.desc(), CaseLawCitation.year.desc()).all()
        
        if filters:
            section = filters.get('section')
            violation_type = filters.get('violation_type')
            
            if section or violation_type:
                filtered = []
                for case in cases:
                    match = True
                    if section and case.fcra_sections:
                        sections = [s.lower().replace('§', '').strip() for s in case.fcra_sections]
                        if section.lower().replace('§', '').strip() not in sections:
                            match = False
                    if violation_type and case.violation_types:
                        if violation_type.lower() not in [vt.lower() for vt in case.violation_types]:
                            match = False
                    if match:
                        filtered.append(case)
                cases = filtered
        
        return [case.to_dict() for case in cases]
    finally:
        if close_db:
            db.close()


def get_case_by_id(case_id, db=None):
    """Get a single case by ID."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        case = db.query(CaseLawCitation).filter(CaseLawCitation.id == case_id).first()
        return case.to_dict() if case else None
    finally:
        if close_db:
            db.close()


def create_case(data, db=None):
    """Create a new case law citation."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        citation = CaseLawCitation(
            case_name=data['case_name'],
            citation=data['citation'],
            court=data.get('court'),
            year=data.get('year'),
            fcra_sections=data.get('fcra_sections', []),
            violation_types=data.get('violation_types', []),
            key_holding=data.get('key_holding'),
            full_summary=data.get('full_summary'),
            quote_snippets=data.get('quote_snippets', []),
            damages_awarded=data.get('damages_awarded'),
            plaintiff_won=data.get('plaintiff_won'),
            relevance_score=data.get('relevance_score', 3),
            tags=data.get('tags', []),
            notes=data.get('notes')
        )
        db.add(citation)
        db.commit()
        db.refresh(citation)
        return citation.to_dict()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if close_db:
            db.close()


def update_case(case_id, data, db=None):
    """Update an existing case law citation."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        case = db.query(CaseLawCitation).filter(CaseLawCitation.id == case_id).first()
        if not case:
            return None
        
        for key, value in data.items():
            if hasattr(case, key) and key not in ['id', 'created_at']:
                setattr(case, key, value)
        
        case.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(case)
        return case.to_dict()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if close_db:
            db.close()


def delete_case(case_id, db=None):
    """Delete a case law citation."""
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    
    try:
        case = db.query(CaseLawCitation).filter(CaseLawCitation.id == case_id).first()
        if not case:
            return False
        
        db.delete(case)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if close_db:
            db.close()
