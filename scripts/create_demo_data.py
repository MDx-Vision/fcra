"""
Demo Data Script for Brightpath Ascend FCRA Platform
Creates realistic demo data for SOP creation and training purposes
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, date
import random
import string
import secrets
from database import (
    SessionLocal, Client, Analysis, Violation, Settlement, Case,
    Affiliate, Commission, DisputeItem, CRAResponse, DisputeLetter,
    Furnisher, FurnisherStats
)
from werkzeug.security import generate_password_hash

def generate_token():
    return secrets.token_urlsafe(32)

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

DEMO_CLIENTS = [
    {
        "first_name": "Marcus", "last_name": "Thompson", 
        "email": "marcus.thompson@demo.brightpath.com", "phone": "(404) 555-0101",
        "address_street": "1234 Peachtree Lane", "address_city": "Atlanta", 
        "address_state": "GA", "address_zip": "30301",
        "status": "stage2_complete", "score": 9, "exposure": 125000,
        "violations_count": 8, "profile": "high_value"
    },
    {
        "first_name": "Jennifer", "last_name": "Williams",
        "email": "jennifer.williams@demo.brightpath.com", "phone": "(312) 555-0202",
        "address_street": "567 Michigan Ave", "address_city": "Chicago",
        "address_state": "IL", "address_zip": "60601",
        "status": "stage1_complete", "score": 7, "exposure": 85000,
        "violations_count": 5, "profile": "standard"
    },
    {
        "first_name": "Robert", "last_name": "Garcia",
        "email": "robert.garcia@demo.brightpath.com", "phone": "(214) 555-0303",
        "address_street": "890 Commerce St", "address_city": "Dallas",
        "address_state": "TX", "address_zip": "75201",
        "status": "stage2_complete", "score": 10, "exposure": 175000,
        "violations_count": 12, "profile": "high_value"
    },
    {
        "first_name": "Sarah", "last_name": "Johnson",
        "email": "sarah.johnson@demo.brightpath.com", "phone": "(602) 555-0404",
        "address_street": "456 Camelback Rd", "address_city": "Phoenix",
        "address_state": "AZ", "address_zip": "85001",
        "status": "delivered", "score": 8, "exposure": 95000,
        "violations_count": 6, "profile": "settled"
    },
    {
        "first_name": "David", "last_name": "Martinez",
        "email": "david.martinez@demo.brightpath.com", "phone": "(305) 555-0505",
        "address_street": "789 Ocean Drive", "address_city": "Miami",
        "address_state": "FL", "address_zip": "33101",
        "status": "stage1_complete", "score": 6, "exposure": 45000,
        "violations_count": 3, "profile": "review_needed"
    },
    {
        "first_name": "Michelle", "last_name": "Lee",
        "email": "michelle.lee@demo.brightpath.com", "phone": "(206) 555-0606",
        "address_street": "321 Pike St", "address_city": "Seattle",
        "address_state": "WA", "address_zip": "98101",
        "status": "active", "score": 8, "exposure": 110000,
        "violations_count": 7, "profile": "in_dispute"
    },
    {
        "first_name": "James", "last_name": "Brown",
        "email": "james.brown@demo.brightpath.com", "phone": "(720) 555-0707",
        "address_street": "654 Denver Lane", "address_city": "Denver",
        "address_state": "CO", "address_zip": "80201",
        "status": "intake", "score": 0, "exposure": 0,
        "violations_count": 0, "profile": "new_signup"
    },
    {
        "first_name": "Patricia", "last_name": "Davis",
        "email": "patricia.davis@demo.brightpath.com", "phone": "(615) 555-0808",
        "address_street": "987 Broadway", "address_city": "Nashville",
        "address_state": "TN", "address_zip": "37201",
        "status": "stage2_complete", "score": 9, "exposure": 135000,
        "violations_count": 9, "profile": "high_value"
    },
    {
        "first_name": "Christopher", "last_name": "Wilson",
        "email": "christopher.wilson@demo.brightpath.com", "phone": "(702) 555-0909",
        "address_street": "246 Strip Blvd", "address_city": "Las Vegas",
        "address_state": "NV", "address_zip": "89101",
        "status": "delivered", "score": 7, "exposure": 78000,
        "violations_count": 5, "profile": "complete"
    },
    {
        "first_name": "Amanda", "last_name": "Taylor",
        "email": "amanda.taylor@demo.brightpath.com", "phone": "(503) 555-1010",
        "address_street": "135 Rose Lane", "address_city": "Portland",
        "address_state": "OR", "address_zip": "97201",
        "status": "stage1_complete", "score": 5, "exposure": 35000,
        "violations_count": 2, "profile": "low_value"
    }
]

VIOLATION_TYPES = [
    {"type": "Inaccurate Balance Reporting", "section": "§ 1681e(b)", "min": 1000, "max": 2500},
    {"type": "Mixed File - Wrong Consumer Data", "section": "§ 1681e(b)", "min": 5000, "max": 15000},
    {"type": "Failure to Investigate", "section": "§ 1681i", "min": 1000, "max": 5000},
    {"type": "Reporting Beyond 7-Year Limit", "section": "§ 1681c", "min": 2000, "max": 8000},
    {"type": "Duplicate Account Reporting", "section": "§ 1681e(b)", "min": 1500, "max": 4000},
    {"type": "Incorrect Payment Status", "section": "§ 1681s-2", "min": 1000, "max": 3500},
    {"type": "Wrong Date of First Delinquency", "section": "§ 1681c", "min": 2500, "max": 7500},
    {"type": "Unauthorized Hard Inquiry", "section": "§ 1681b", "min": 500, "max": 2000},
    {"type": "Identity Theft - Fraudulent Account", "section": "§ 1681c-2", "min": 5000, "max": 25000},
    {"type": "Failure to Mark Account as Disputed", "section": "§ 1681s-2(a)(3)", "min": 1000, "max": 3000},
    {"type": "Re-aging Debt After Dispute", "section": "§ 1681i", "min": 3000, "max": 10000},
    {"type": "Metro2 Field Violation - Invalid Code", "section": "§ 1681e(b)", "min": 1000, "max": 2500}
]

CREDITORS = [
    "Capital One", "Chase Bank", "Bank of America", "Wells Fargo", "Discover",
    "American Express", "Citi", "Synchrony Bank", "Ally Financial",
    "Portfolio Recovery Associates", "LVNV Funding", "Midland Credit Management",
    "Cavalry SPV", "Enhanced Recovery Company", "IC System",
    "Mortgage Electronic Registration Systems", "Caliber Home Loans",
    "Mr. Cooper", "Navient", "Great Lakes Educational Loan"
]

BUREAUS = ["Experian", "TransUnion", "Equifax"]

def create_demo_data():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("BRIGHTPATH ASCEND DEMO DATA GENERATOR")
        print("Creating realistic demo data for SOP and training...")
        print("=" * 60)
        
        created_clients = []
        created_analyses = []
        
        print("\n[1/6] Creating Demo Clients...")
        for i, client_data in enumerate(DEMO_CLIENTS):
            existing = db.query(Client).filter(Client.email == client_data["email"]).first()
            if existing:
                print(f"  - Client {client_data['first_name']} {client_data['last_name']} already exists, skipping...")
                created_clients.append(existing)
                continue
            
            client = Client(
                name=f"{client_data['first_name']} {client_data['last_name']}",
                first_name=client_data["first_name"],
                last_name=client_data["last_name"],
                email=client_data["email"],
                phone=client_data["phone"],
                address_street=client_data["address_street"],
                address_city=client_data["address_city"],
                address_state=client_data["address_state"],
                address_zip=client_data["address_zip"],
                ssn_last_four=str(random.randint(1000, 9999)),
                date_of_birth=date(random.randint(1960, 1995), random.randint(1, 12), random.randint(1, 28)),
                status=client_data["status"],
                portal_token=generate_token(),
                portal_password_hash=generate_password_hash("Demo123!"),
                referral_code=generate_referral_code(),
                signup_completed=True,
                agreement_signed=True,
                agreement_signed_at=datetime.utcnow() - timedelta(days=random.randint(30, 180)),
                current_dispute_round=random.randint(1, 3) if client_data["status"] in ["active", "stage1_complete", "stage2_complete"] else 0,
                dispute_status="active" if client_data["status"] in ["active", "stage1_complete", "stage2_complete"] else "new",
                credit_monitoring_service=random.choice(["IdentityIQ", "MyScoreIQ", "SmartCredit"]),
                admin_notes=f"Demo client - {client_data['profile'].replace('_', ' ').title()} profile"
            )
            db.add(client)
            db.flush()
            created_clients.append(client)
            print(f"  + Created: {client.name} ({client_data['status']}) - {client_data['profile']}")
        
        print("\n[2/6] Creating Analyses and Cases...")
        for i, (client, client_data) in enumerate(zip(created_clients, DEMO_CLIENTS)):
            if client_data["profile"] == "new_signup":
                continue
                
            existing_analysis = db.query(Analysis).filter(Analysis.client_id == client.id).first()
            if existing_analysis:
                print(f"  - Analysis for {client.name} already exists, skipping...")
                created_analyses.append(existing_analysis)
                continue
            
            stage1_data = {
                "violations_found": client_data["violations_count"],
                "statutory_damages_min": client_data["exposure"] * 0.4,
                "statutory_damages_max": client_data["exposure"] * 0.8,
                "case_score": client_data["score"],
                "standing_met": True,
                "willfulness_indicators": random.randint(2, 5)
            }
            
            analysis = Analysis(
                credit_report_id=random.randint(1000, 9999),
                client_id=client.id,
                client_name=client.name,
                dispute_round=random.randint(1, 3),
                analysis_mode="comprehensive",
                stage=2 if client_data["status"] in ["stage2_complete", "delivered"] else 1,
                stage_1_analysis=str(stage1_data),
                full_analysis=f"Comprehensive FCRA analysis completed. {client_data['violations_count']} violations identified across all three bureaus.",
                cost=random.uniform(1.5, 3.0),
                tokens_used=random.randint(15000, 45000),
                cache_read=random.choice([True, False]),
                approved_at=datetime.utcnow() - timedelta(days=random.randint(3, 30)),
                created_at=datetime.utcnow() - timedelta(days=random.randint(7, 60))
            )
            db.add(analysis)
            db.flush()
            created_analyses.append(analysis)
            
            existing_case = db.query(Case).filter(Case.client_id == client.id).first()
            if not existing_case:
                case_number = f"BP-{datetime.now().year}-{random.randint(10000, 99999)}-{secrets.token_hex(2)}"
                case = Case(
                    client_id=client.id,
                    analysis_id=analysis.id,
                    case_number=case_number,
                    status=client_data["status"],
                    pricing_tier=random.choice(["tier1", "tier2", "tier3"]),
                    base_fee=random.choice([600, 1200, 2500]),
                    contingency_percent=random.choice([25, 30, 33]),
                    intake_at=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                    stage1_completed_at=datetime.utcnow() - timedelta(days=random.randint(14, 30)) if client_data["status"] != "intake" else None,
                    stage2_completed_at=datetime.utcnow() - timedelta(days=random.randint(7, 14)) if client_data["status"] in ["stage2_complete", "delivered"] else None,
                    delivered_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)) if client_data["status"] == "delivered" else None,
                    admin_notes=f"Demo case - {client_data['profile'].replace('_', ' ').title()}",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(7, 60))
                )
                db.add(case)
                db.flush()
            
            print(f"  + Created analysis for: {client.name} (Score: {client_data['score']}, Exposure: ${client_data['exposure']:,})")
        
        print("\n[3/6] Creating Violations...")
        for analysis, client_data in zip(created_analyses, [c for c in DEMO_CLIENTS if c["profile"] != "new_signup"]):
            existing_violations = db.query(Violation).filter(Violation.analysis_id == analysis.id).count()
            if existing_violations > 0:
                print(f"  - Violations for analysis {analysis.id} already exist, skipping...")
                continue
            
            num_violations = client_data["violations_count"]
            used_types = []
            
            for v in range(num_violations):
                vtype = random.choice([t for t in VIOLATION_TYPES if t["type"] not in used_types])
                used_types.append(vtype["type"])
                
                violation = Violation(
                    analysis_id=analysis.id,
                    client_id=analysis.client_id,
                    bureau=random.choice(BUREAUS),
                    account_name=random.choice(CREDITORS),
                    fcra_section=vtype["section"],
                    violation_type=vtype["type"],
                    description=f"Verified {vtype['type'].lower()} affecting consumer's credit report. Documentation supports willful non-compliance.",
                    statutory_damages_min=vtype["min"],
                    statutory_damages_max=vtype["max"],
                    is_willful=random.choice([True, True, False]),
                    violation_date=date.today() - timedelta(days=random.randint(30, 365)),
                    discovery_date=date.today() - timedelta(days=random.randint(7, 30)),
                    created_at=datetime.utcnow()
                )
                db.add(violation)
            
            print(f"  + Created {num_violations} violations for analysis {analysis.id}")
        
        print("\n[4/6] Creating Dispute Items and CRA Responses...")
        for client, client_data in zip(created_clients, DEMO_CLIENTS):
            if client_data["profile"] in ["new_signup", "settled", "complete"]:
                continue
            
            existing_items = db.query(DisputeItem).filter(DisputeItem.client_id == client.id).count()
            if existing_items > 0:
                print(f"  - Dispute items for {client.name} already exist, skipping...")
                continue
            
            dispute_round = random.randint(1, 3)
            
            for bureau in BUREAUS:
                for _ in range(random.randint(2, 5)):
                    status = random.choice(["sent", "deleted", "verified", "in_progress", "updated"])
                    escalation = random.choice(["section_611", "section_611", "section_623", "section_621"])
                    
                    item = DisputeItem(
                        client_id=client.id,
                        bureau=bureau,
                        dispute_round=dispute_round,
                        item_type=random.choice(["collection", "late_payment", "inquiry", "public_record"]),
                        creditor_name=random.choice(CREDITORS),
                        account_id=f"****{random.randint(1000, 9999)}",
                        status=status,
                        escalation_stage=escalation,
                        sent_date=date.today() - timedelta(days=random.randint(15, 60)),
                        response_date=date.today() - timedelta(days=random.randint(1, 14)) if status != "sent" else None,
                        reason=f"Disputed as {random.choice(['inaccurate', 'not mine', 'obsolete', 'unverifiable'])}",
                        furnisher_dispute_sent=escalation in ["section_623", "section_621"],
                        method_of_verification_requested=random.choice([True, False]),
                        created_at=datetime.utcnow()
                    )
                    db.add(item)
            
            for bureau in random.sample(BUREAUS, random.randint(1, 3)):
                response = CRAResponse(
                    client_id=client.id,
                    bureau=bureau,
                    dispute_round=dispute_round,
                    response_type=random.choice(["verified", "deleted", "updated", "investigating"]),
                    response_date=date.today() - timedelta(days=random.randint(1, 14)),
                    received_date=date.today() - timedelta(days=random.randint(1, 7)),
                    items_verified=random.randint(0, 3),
                    items_deleted=random.randint(0, 2),
                    items_updated=random.randint(0, 2),
                    requires_follow_up=random.choice([True, False]),
                    follow_up_deadline=datetime.utcnow() + timedelta(days=30),
                    admin_notes="Demo CRA response for training purposes",
                    created_at=datetime.utcnow()
                )
                db.add(response)
            
            print(f"  + Created dispute items and CRA responses for: {client.name}")
        
        print("\n[5/6] Creating Settlements...")
        for client, client_data in zip(created_clients, DEMO_CLIENTS):
            if client_data["profile"] not in ["settled", "complete", "high_value"]:
                continue
            
            case = db.query(Case).filter(Case.client_id == client.id).first()
            if not case:
                continue
            
            existing_settlement = db.query(Settlement).filter(Settlement.case_id == case.id).first()
            if existing_settlement:
                print(f"  - Settlement for {client.name} already exists, skipping...")
                continue
            
            if client_data["profile"] == "settled":
                status = "accepted"
                final_amount = client_data["exposure"] * random.uniform(0.4, 0.7)
            elif client_data["profile"] == "complete":
                status = "accepted"
                final_amount = client_data["exposure"] * random.uniform(0.5, 0.8)
            else:
                status = random.choice(["demand_sent", "negotiating"])
                final_amount = 0
            
            settlement = Settlement(
                case_id=case.id,
                target_amount=client_data["exposure"],
                minimum_acceptable=client_data["exposure"] * 0.4,
                transunion_target=client_data["exposure"] * 0.35,
                experian_target=client_data["exposure"] * 0.35,
                equifax_target=client_data["exposure"] * 0.30,
                status=status,
                initial_demand=client_data["exposure"] * 0.9,
                initial_demand_date=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                final_amount=final_amount,
                settled_at=datetime.utcnow() - timedelta(days=random.randint(7, 30)) if status == "accepted" else None,
                payment_received=status == "accepted" and random.choice([True, False]),
                payment_amount=final_amount * 0.95 if status == "accepted" else 0,
                contingency_earned=final_amount * 0.33 if status == "accepted" else 0,
                settlement_notes="Demo settlement for SOP training",
                created_at=datetime.utcnow()
            )
            db.add(settlement)
            print(f"  + Created settlement for: {client.name} (Status: {status}, Amount: ${final_amount:,.0f})")
        
        print("\n[6/6] Creating Affiliates and Commissions...")
        demo_affiliates = [
            {"name": "Michael Roberts", "email": "michael.roberts@demo.brightpath.com", 
             "company": "Roberts Legal Marketing", "code": "ROBERTS25", "referrals": 8, "earnings": 4800},
            {"name": "Lisa Chen", "email": "lisa.chen@demo.brightpath.com",
             "company": "Chen Credit Solutions", "code": "CHEN2024", "referrals": 15, "earnings": 9000},
            {"name": "William Foster", "email": "william.foster@demo.brightpath.com",
             "company": "Foster & Associates", "code": "FOSTER10", "referrals": 5, "earnings": 3000, "parent": "CHEN2024"},
        ]
        
        for aff_data in demo_affiliates:
            existing = db.query(Affiliate).filter(Affiliate.email == aff_data["email"]).first()
            if existing:
                print(f"  - Affiliate {aff_data['name']} already exists, skipping...")
                continue
            
            parent_id = None
            if "parent" in aff_data:
                parent = db.query(Affiliate).filter(Affiliate.affiliate_code == aff_data["parent"]).first()
                if parent:
                    parent_id = parent.id
            
            affiliate = Affiliate(
                name=aff_data["name"],
                email=aff_data["email"],
                phone=f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
                company_name=aff_data["company"],
                affiliate_code=aff_data["code"],
                parent_affiliate_id=parent_id,
                commission_rate_1=0.10,
                commission_rate_2=0.05,
                status="active",
                payout_method="bank_transfer",
                total_referrals=aff_data["referrals"],
                total_earnings=aff_data["earnings"],
                pending_earnings=aff_data["earnings"] * 0.3,
                paid_out=aff_data["earnings"] * 0.7,
                created_at=datetime.utcnow() - timedelta(days=random.randint(60, 180))
            )
            db.add(affiliate)
            print(f"  + Created affiliate: {aff_data['name']} ({aff_data['code']})")
        
        print("\n[BONUS] Creating Furnisher Intelligence Data...")
        demo_furnishers = [
            {"name": "Capital One", "industry": "Credit Card", "disputes": 45, "deletions": 28, "settlements": 12, "avg_settlement": 8500},
            {"name": "Portfolio Recovery Associates", "industry": "Collection Agency", "disputes": 120, "deletions": 85, "settlements": 35, "avg_settlement": 4200},
            {"name": "Midland Credit Management", "industry": "Collection Agency", "disputes": 95, "deletions": 62, "settlements": 28, "avg_settlement": 3800},
            {"name": "Chase Bank", "industry": "Bank", "disputes": 38, "deletions": 15, "settlements": 8, "avg_settlement": 12000},
            {"name": "Synchrony Bank", "industry": "Credit Card", "disputes": 52, "deletions": 31, "settlements": 15, "avg_settlement": 5500},
        ]
        
        for f_data in demo_furnishers:
            existing = db.query(Furnisher).filter(Furnisher.name == f_data["name"]).first()
            if existing:
                print(f"  - Furnisher {f_data['name']} already exists, skipping...")
                continue
            
            furnisher = Furnisher(
                name=f_data["name"],
                industry=f_data["industry"],
                notes=f"Demo data - {f_data['industry']} furnisher profile",
                created_at=datetime.utcnow()
            )
            db.add(furnisher)
            db.flush()
            
            stats = FurnisherStats(
                furnisher_id=furnisher.id,
                total_disputes=f_data["disputes"],
                round_1_verified=f_data["disputes"] - f_data["deletions"],
                round_1_deleted=f_data["deletions"],
                settlement_count=f_data["settlements"],
                settlement_total=f_data["settlements"] * f_data["avg_settlement"],
                settlement_avg=f_data["avg_settlement"],
                avg_response_days=random.randint(15, 35)
            )
            db.add(stats)
            print(f"  + Created furnisher: {f_data['name']} ({f_data['industry']})")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("DEMO DATA CREATION COMPLETE!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Clients created: {len([c for c in created_clients if c])}")
        print(f"  - Analyses created: {len(created_analyses)}")
        print(f"  - Affiliates created: {len(demo_affiliates)}")
        print(f"  - Furnishers created: {len(demo_furnishers)}")
        print("\nDemo Login Credentials:")
        print("  - Staff: admin@brightpathascend.com / Admin123!")
        print("  - Client Portal: [any demo client email] / Demo123!")
        print("\nView at: /dashboard")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_data()
