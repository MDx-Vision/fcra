"""
State Attorney General Complaint Service

Handles filing complaints with State Attorneys General under FCRA §621.
State AGs have independent authority to enforce FCRA provisions.

Key Features:
- All 50 state AG contact database
- Complaint letter generation
- Escalation workflow integration
- Response tracking
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class StateAGServiceError(Exception):
    """Custom exception for State AG service errors"""

    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# FCRA violation types for complaint classification
VIOLATION_TYPES = {
    "failure_to_investigate": "Failure to conduct reasonable investigation (§611)",
    "inaccurate_reporting": "Reporting inaccurate information (§623)",
    "failure_to_correct": "Failure to correct or delete inaccurate information (§611)",
    "reinsertion": "Reinsertion of previously deleted information (§611)",
    "frivolous_response": "Wrongly claiming dispute is frivolous (§611)",
    "failure_to_notify": "Failure to notify of adverse action (§615)",
    "identity_theft": "Failure to block fraudulent accounts (§605B)",
    "obsolete_info": "Reporting obsolete information (§605)",
    "unauthorized_access": "Unauthorized access to credit report (§604)",
    "mixed_files": "Mixed file - reporting data belonging to another consumer",
}

# Complaint status workflow
COMPLAINT_STATUSES = {
    "draft": "Complaint being prepared",
    "ready": "Ready to file",
    "filed": "Complaint filed with AG office",
    "acknowledged": "AG acknowledged receipt",
    "investigating": "AG investigating complaint",
    "resolved": "Complaint resolved",
    "closed": "Complaint closed (no action)",
}

# All 50 State AG Consumer Protection Offices
# Addresses verified as of 2025 - Consumer Protection/Consumer Affairs divisions
STATE_AG_DATABASE = [
    {
        "state_code": "AL",
        "state_name": "Alabama",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Section",
        "address_line1": "501 Washington Avenue",
        "city": "Montgomery",
        "state": "AL",
        "zip_code": "36104",
        "phone": "(334) 242-7334",
        "website": "https://www.alabamaag.gov",
        "complaint_url": "https://www.alabamaag.gov/consumer-protection",
        "accepts_online": True,
    },
    {
        "state_code": "AK",
        "state_name": "Alaska",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Unit",
        "address_line1": "1031 West 4th Avenue, Suite 200",
        "city": "Anchorage",
        "state": "AK",
        "zip_code": "99501",
        "phone": "(907) 269-5100",
        "website": "https://law.alaska.gov",
        "complaint_url": "https://law.alaska.gov/department/civil/consumer.html",
        "accepts_online": True,
    },
    {
        "state_code": "AZ",
        "state_name": "Arizona",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection & Advocacy Section",
        "address_line1": "2005 North Central Avenue",
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85004",
        "phone": "(602) 542-5763",
        "website": "https://www.azag.gov",
        "complaint_url": "https://www.azag.gov/complaints/consumer",
        "accepts_online": True,
    },
    {
        "state_code": "AR",
        "state_name": "Arkansas",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "323 Center Street, Suite 200",
        "city": "Little Rock",
        "state": "AR",
        "zip_code": "72201",
        "phone": "(501) 682-2007",
        "website": "https://arkansasag.gov",
        "complaint_url": "https://arkansasag.gov/consumer-protection/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "CA",
        "state_name": "California",
        "office_name": "Office of the Attorney General",
        "division_name": "Public Inquiry Unit",
        "address_line1": "1300 I Street, Suite 1740",
        "city": "Sacramento",
        "state": "CA",
        "zip_code": "95814",
        "phone": "(916) 210-6276",
        "website": "https://oag.ca.gov",
        "complaint_url": "https://oag.ca.gov/contact/consumer-complaint-against-business-or-company",
        "accepts_online": True,
        "fcra_enforcement_notes": "California has strong consumer protection enforcement. Also has CCPA.",
    },
    {
        "state_code": "CO",
        "state_name": "Colorado",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Section",
        "address_line1": "1300 Broadway, 7th Floor",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80203",
        "phone": "(720) 508-6000",
        "website": "https://coag.gov",
        "complaint_url": "https://coag.gov/file-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "CT",
        "state_name": "Connecticut",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Department",
        "address_line1": "165 Capitol Avenue",
        "city": "Hartford",
        "state": "CT",
        "zip_code": "06106",
        "phone": "(860) 808-5420",
        "website": "https://portal.ct.gov/AG",
        "complaint_url": "https://portal.ct.gov/AG/Common/Complaint-Form-Landing-page",
        "accepts_online": True,
    },
    {
        "state_code": "DE",
        "state_name": "Delaware",
        "office_name": "Department of Justice",
        "division_name": "Consumer Protection Unit",
        "address_line1": "820 North French Street, 5th Floor",
        "city": "Wilmington",
        "state": "DE",
        "zip_code": "19801",
        "phone": "(302) 577-8600",
        "website": "https://attorneygeneral.delaware.gov",
        "complaint_url": "https://attorneygeneral.delaware.gov/fraud/cpu/complaint",
        "accepts_online": True,
    },
    {
        "state_code": "FL",
        "state_name": "Florida",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "The Capitol, PL-01",
        "city": "Tallahassee",
        "state": "FL",
        "zip_code": "32399-1050",
        "phone": "(850) 414-3990",
        "website": "https://www.myfloridalegal.com",
        "complaint_url": "https://www.myfloridalegal.com/pages/File-a-Complaint.page",
        "accepts_online": True,
        "fcra_enforcement_notes": "Active enforcement of consumer protection laws.",
    },
    {
        "state_code": "GA",
        "state_name": "Georgia",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "2 Martin Luther King Jr. Drive, Suite 356",
        "city": "Atlanta",
        "state": "GA",
        "zip_code": "30334",
        "phone": "(404) 651-8600",
        "website": "https://law.georgia.gov",
        "complaint_url": "https://law.georgia.gov/key-issues/consumer-protection",
        "accepts_online": True,
    },
    {
        "state_code": "HI",
        "state_name": "Hawaii",
        "office_name": "Department of Commerce and Consumer Affairs",
        "division_name": "Office of Consumer Protection",
        "address_line1": "335 Merchant Street, Room 310",
        "city": "Honolulu",
        "state": "HI",
        "zip_code": "96813",
        "phone": "(808) 586-2630",
        "website": "https://cca.hawaii.gov/ocp",
        "complaint_url": "https://cca.hawaii.gov/ocp/complaint",
        "accepts_online": True,
    },
    {
        "state_code": "ID",
        "state_name": "Idaho",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "954 W Jefferson Street, 2nd Floor",
        "city": "Boise",
        "state": "ID",
        "zip_code": "83702",
        "phone": "(208) 334-2424",
        "website": "https://www.ag.idaho.gov",
        "complaint_url": "https://www.ag.idaho.gov/consumer-protection/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "IL",
        "state_name": "Illinois",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "100 West Randolph Street",
        "city": "Chicago",
        "state": "IL",
        "zip_code": "60601",
        "phone": "(312) 814-3000",
        "website": "https://www.illinoisattorneygeneral.gov",
        "complaint_url": "https://www.illinoisattorneygeneral.gov/consumers/filecomplaint.html",
        "accepts_online": True,
        "fcra_enforcement_notes": "Strong consumer protection office with active enforcement.",
    },
    {
        "state_code": "IN",
        "state_name": "Indiana",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "302 West Washington Street, 5th Floor",
        "city": "Indianapolis",
        "state": "IN",
        "zip_code": "46204",
        "phone": "(317) 232-6330",
        "website": "https://www.in.gov/attorneygeneral",
        "complaint_url": "https://www.in.gov/attorneygeneral/consumer-protection-division/consumer-complaints",
        "accepts_online": True,
    },
    {
        "state_code": "IA",
        "state_name": "Iowa",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "1305 East Walnut Street",
        "city": "Des Moines",
        "state": "IA",
        "zip_code": "50319",
        "phone": "(515) 281-5926",
        "website": "https://www.iowaattorneygeneral.gov",
        "complaint_url": "https://www.iowaattorneygeneral.gov/for-consumers/file-a-consumer-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "KS",
        "state_name": "Kansas",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "120 SW 10th Avenue, 2nd Floor",
        "city": "Topeka",
        "state": "KS",
        "zip_code": "66612",
        "phone": "(785) 296-3751",
        "website": "https://ag.ks.gov",
        "complaint_url": "https://ag.ks.gov/in-your-corner-kansas/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "KY",
        "state_name": "Kentucky",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "700 Capitol Avenue, Suite 118",
        "city": "Frankfort",
        "state": "KY",
        "zip_code": "40601",
        "phone": "(502) 696-5389",
        "website": "https://ag.ky.gov",
        "complaint_url": "https://ag.ky.gov/Resources/Consumer-Protection/Pages/File-a-Complaint.aspx",
        "accepts_online": True,
    },
    {
        "state_code": "LA",
        "state_name": "Louisiana",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Section",
        "address_line1": "1885 North Third Street",
        "city": "Baton Rouge",
        "state": "LA",
        "zip_code": "70802",
        "phone": "(225) 326-6465",
        "website": "https://www.ag.state.la.us",
        "complaint_url": "https://www.ag.state.la.us/Consumer",
        "accepts_online": True,
    },
    {
        "state_code": "ME",
        "state_name": "Maine",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "6 State House Station",
        "city": "Augusta",
        "state": "ME",
        "zip_code": "04333-0006",
        "phone": "(207) 626-8849",
        "website": "https://www.maine.gov/ag",
        "complaint_url": "https://www.maine.gov/ag/consumer/complaints/index.shtml",
        "accepts_online": True,
    },
    {
        "state_code": "MD",
        "state_name": "Maryland",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "200 Saint Paul Place",
        "city": "Baltimore",
        "state": "MD",
        "zip_code": "21202",
        "phone": "(410) 528-8662",
        "website": "https://www.marylandattorneygeneral.gov",
        "complaint_url": "https://www.marylandattorneygeneral.gov/Pages/CPD/complaint.aspx",
        "accepts_online": True,
    },
    {
        "state_code": "MA",
        "state_name": "Massachusetts",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "One Ashburton Place, 18th Floor",
        "city": "Boston",
        "state": "MA",
        "zip_code": "02108",
        "phone": "(617) 727-8400",
        "website": "https://www.mass.gov/orgs/office-of-the-attorney-general",
        "complaint_url": "https://www.mass.gov/how-to/file-a-consumer-complaint",
        "accepts_online": True,
        "fcra_enforcement_notes": "Very active consumer protection office.",
    },
    {
        "state_code": "MI",
        "state_name": "Michigan",
        "office_name": "Department of Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "525 West Ottawa Street",
        "address_line2": "P.O. Box 30212",
        "city": "Lansing",
        "state": "MI",
        "zip_code": "48909",
        "phone": "(517) 335-7622",
        "website": "https://www.michigan.gov/ag",
        "complaint_url": "https://www.michigan.gov/ag/consumer-protection/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "MN",
        "state_name": "Minnesota",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "445 Minnesota Street, Suite 1400",
        "city": "St. Paul",
        "state": "MN",
        "zip_code": "55101",
        "phone": "(651) 296-3353",
        "website": "https://www.ag.state.mn.us",
        "complaint_url": "https://www.ag.state.mn.us/Office/Complaint.asp",
        "accepts_online": True,
    },
    {
        "state_code": "MS",
        "state_name": "Mississippi",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "Walter Sillers Building",
        "address_line2": "550 High Street, Suite 1200",
        "city": "Jackson",
        "state": "MS",
        "zip_code": "39201",
        "phone": "(601) 359-4230",
        "website": "https://www.ago.state.ms.us",
        "complaint_url": "https://www.ago.state.ms.us/divisions/consumer-protection",
        "accepts_online": True,
    },
    {
        "state_code": "MO",
        "state_name": "Missouri",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "207 West High Street",
        "city": "Jefferson City",
        "state": "MO",
        "zip_code": "65101",
        "phone": "(573) 751-3321",
        "website": "https://ago.mo.gov",
        "complaint_url": "https://ago.mo.gov/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "MT",
        "state_name": "Montana",
        "office_name": "Department of Justice",
        "division_name": "Office of Consumer Protection",
        "address_line1": "555 Fuller Avenue",
        "city": "Helena",
        "state": "MT",
        "zip_code": "59601",
        "phone": "(406) 444-4500",
        "website": "https://dojmt.gov",
        "complaint_url": "https://dojmt.gov/consumer/file-a-consumer-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "NE",
        "state_name": "Nebraska",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "2115 State Capitol",
        "city": "Lincoln",
        "state": "NE",
        "zip_code": "68509",
        "phone": "(402) 471-2682",
        "website": "https://ago.nebraska.gov",
        "complaint_url": "https://ago.nebraska.gov/consumer-protection/file-consumer-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "NV",
        "state_name": "Nevada",
        "office_name": "Office of the Attorney General",
        "division_name": "Bureau of Consumer Protection",
        "address_line1": "555 East Washington Avenue, Suite 3900",
        "city": "Las Vegas",
        "state": "NV",
        "zip_code": "89101",
        "phone": "(702) 486-3132",
        "website": "https://ag.nv.gov",
        "complaint_url": "https://ag.nv.gov/Complaints/File_Complaint",
        "accepts_online": True,
    },
    {
        "state_code": "NH",
        "state_name": "New Hampshire",
        "office_name": "Department of Justice",
        "division_name": "Consumer Protection Bureau",
        "address_line1": "33 Capitol Street",
        "city": "Concord",
        "state": "NH",
        "zip_code": "03301",
        "phone": "(603) 271-3641",
        "website": "https://www.doj.nh.gov",
        "complaint_url": "https://www.doj.nh.gov/consumer/complaints",
        "accepts_online": True,
    },
    {
        "state_code": "NJ",
        "state_name": "New Jersey",
        "office_name": "Office of the Attorney General",
        "division_name": "Division of Consumer Affairs",
        "address_line1": "124 Halsey Street",
        "city": "Newark",
        "state": "NJ",
        "zip_code": "07102",
        "phone": "(973) 504-6200",
        "website": "https://www.njconsumeraffairs.gov",
        "complaint_url": "https://www.njconsumeraffairs.gov/Pages/File-a-Complaint.aspx",
        "accepts_online": True,
        "fcra_enforcement_notes": "Strong consumer protection enforcement with dedicated credit reporting unit.",
    },
    {
        "state_code": "NM",
        "state_name": "New Mexico",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "408 Galisteo Street",
        "city": "Santa Fe",
        "state": "NM",
        "zip_code": "87501",
        "phone": "(505) 490-4060",
        "website": "https://www.nmag.gov",
        "complaint_url": "https://www.nmag.gov/file-a-complaint.aspx",
        "accepts_online": True,
    },
    {
        "state_code": "NY",
        "state_name": "New York",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Frauds Bureau",
        "address_line1": "The Capitol",
        "city": "Albany",
        "state": "NY",
        "zip_code": "12224-0341",
        "phone": "(800) 771-7755",
        "website": "https://ag.ny.gov",
        "complaint_url": "https://ag.ny.gov/consumer-frauds/filing-consumer-complaint",
        "accepts_online": True,
        "fcra_enforcement_notes": "Very active on consumer protection and financial issues. Strong enforcement history.",
    },
    {
        "state_code": "NC",
        "state_name": "North Carolina",
        "office_name": "Department of Justice",
        "division_name": "Consumer Protection Division",
        "address_line1": "114 West Edenton Street",
        "city": "Raleigh",
        "state": "NC",
        "zip_code": "27603",
        "phone": "(919) 716-6000",
        "website": "https://ncdoj.gov",
        "complaint_url": "https://ncdoj.gov/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "ND",
        "state_name": "North Dakota",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "600 E Boulevard Avenue, Dept. 125",
        "city": "Bismarck",
        "state": "ND",
        "zip_code": "58505-0040",
        "phone": "(701) 328-2210",
        "website": "https://attorneygeneral.nd.gov",
        "complaint_url": "https://attorneygeneral.nd.gov/consumer-resources/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "OH",
        "state_name": "Ohio",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Section",
        "address_line1": "30 East Broad Street, 14th Floor",
        "city": "Columbus",
        "state": "OH",
        "zip_code": "43215",
        "phone": "(614) 466-8831",
        "website": "https://www.ohioprotects.org",
        "complaint_url": "https://www.ohioprotects.org/FileAComplaint",
        "accepts_online": True,
    },
    {
        "state_code": "OK",
        "state_name": "Oklahoma",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Unit",
        "address_line1": "313 NE 21st Street",
        "city": "Oklahoma City",
        "state": "OK",
        "zip_code": "73105",
        "phone": "(405) 521-2029",
        "website": "https://www.oag.ok.gov",
        "complaint_url": "https://www.oag.ok.gov/consumer-protection",
        "accepts_online": True,
    },
    {
        "state_code": "OR",
        "state_name": "Oregon",
        "office_name": "Department of Justice",
        "division_name": "Financial Fraud/Consumer Protection",
        "address_line1": "1162 Court Street NE",
        "city": "Salem",
        "state": "OR",
        "zip_code": "97301-4096",
        "phone": "(503) 378-4732",
        "website": "https://www.doj.state.or.us",
        "complaint_url": "https://www.doj.state.or.us/consumer-protection/file-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "PA",
        "state_name": "Pennsylvania",
        "office_name": "Office of the Attorney General",
        "division_name": "Bureau of Consumer Protection",
        "address_line1": "15th Floor, Strawberry Square",
        "city": "Harrisburg",
        "state": "PA",
        "zip_code": "17120",
        "phone": "(717) 787-9707",
        "website": "https://www.attorneygeneral.gov",
        "complaint_url": "https://www.attorneygeneral.gov/submit-a-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "RI",
        "state_name": "Rhode Island",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Unit",
        "address_line1": "150 South Main Street",
        "city": "Providence",
        "state": "RI",
        "zip_code": "02903",
        "phone": "(401) 274-4400",
        "website": "https://riag.ri.gov",
        "complaint_url": "https://riag.ri.gov/consumer-protection/file-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "SC",
        "state_name": "South Carolina",
        "office_name": "Department of Consumer Affairs",
        "division_name": "Consumer Protection Division",
        "address_line1": "293 Greystone Boulevard, Suite 400",
        "city": "Columbia",
        "state": "SC",
        "zip_code": "29210",
        "phone": "(803) 734-4200",
        "website": "https://www.consumer.sc.gov",
        "complaint_url": "https://www.consumer.sc.gov/file-complaint",
        "accepts_online": True,
    },
    {
        "state_code": "SD",
        "state_name": "South Dakota",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "1302 East Highway 14, Suite 1",
        "city": "Pierre",
        "state": "SD",
        "zip_code": "57501",
        "phone": "(605) 773-4400",
        "website": "https://consumer.sd.gov",
        "complaint_url": "https://consumer.sd.gov/complaint.aspx",
        "accepts_online": True,
    },
    {
        "state_code": "TN",
        "state_name": "Tennessee",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "425 5th Avenue North",
        "address_line2": "P.O. Box 20207",
        "city": "Nashville",
        "state": "TN",
        "zip_code": "37202",
        "phone": "(615) 741-4737",
        "website": "https://www.tn.gov/attorneygeneral",
        "complaint_url": "https://www.tn.gov/attorneygeneral/working-for-tennessee/consumer-protection/file-a-complaint.html",
        "accepts_online": True,
    },
    {
        "state_code": "TX",
        "state_name": "Texas",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "300 West 15th Street",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "phone": "(512) 463-2100",
        "website": "https://www.texasattorneygeneral.gov",
        "complaint_url": "https://www.texasattorneygeneral.gov/consumer-protection/file-consumer-complaint",
        "accepts_online": True,
        "fcra_enforcement_notes": "Large consumer protection division with active enforcement.",
    },
    {
        "state_code": "UT",
        "state_name": "Utah",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "160 East 300 South, 5th Floor",
        "city": "Salt Lake City",
        "state": "UT",
        "zip_code": "84114",
        "phone": "(801) 366-0310",
        "website": "https://attorneygeneral.utah.gov",
        "complaint_url": "https://attorneygeneral.utah.gov/contact/consumer-complaint-form",
        "accepts_online": True,
    },
    {
        "state_code": "VT",
        "state_name": "Vermont",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Assistance Program",
        "address_line1": "109 State Street",
        "city": "Montpelier",
        "state": "VT",
        "zip_code": "05609-1001",
        "phone": "(802) 656-3183",
        "website": "https://ago.vermont.gov",
        "complaint_url": "https://ago.vermont.gov/cap/consumer-assistance-program-complaint-form",
        "accepts_online": True,
    },
    {
        "state_code": "VA",
        "state_name": "Virginia",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Section",
        "address_line1": "202 North 9th Street",
        "city": "Richmond",
        "state": "VA",
        "zip_code": "23219",
        "phone": "(804) 786-2071",
        "website": "https://www.oag.state.va.us",
        "complaint_url": "https://www.oag.state.va.us/consumercomplaintform/form/start",
        "accepts_online": True,
    },
    {
        "state_code": "WA",
        "state_name": "Washington",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "800 Fifth Avenue, Suite 2000",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98104",
        "phone": "(206) 464-6684",
        "website": "https://www.atg.wa.gov",
        "complaint_url": "https://www.atg.wa.gov/file-complaint",
        "accepts_online": True,
        "fcra_enforcement_notes": "Active enforcement of consumer protection laws.",
    },
    {
        "state_code": "WV",
        "state_name": "West Virginia",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Division",
        "address_line1": "1900 Kanawha Boulevard East",
        "city": "Charleston",
        "state": "WV",
        "zip_code": "25305",
        "phone": "(304) 558-8986",
        "website": "https://ago.wv.gov",
        "complaint_url": "https://ago.wv.gov/consumerprotection/Pages/File-A-Complaint.aspx",
        "accepts_online": True,
    },
    {
        "state_code": "WI",
        "state_name": "Wisconsin",
        "office_name": "Department of Agriculture, Trade and Consumer Protection",
        "division_name": "Consumer Protection Bureau",
        "address_line1": "2811 Agriculture Drive",
        "city": "Madison",
        "state": "WI",
        "zip_code": "53708",
        "phone": "(608) 224-4953",
        "website": "https://datcp.wi.gov",
        "complaint_url": "https://datcp.wi.gov/Pages/Doing_Business/FileConsumerComplaint.aspx",
        "accepts_online": True,
    },
    {
        "state_code": "WY",
        "state_name": "Wyoming",
        "office_name": "Office of the Attorney General",
        "division_name": "Consumer Protection Unit",
        "address_line1": "109 State Capitol",
        "city": "Cheyenne",
        "state": "WY",
        "zip_code": "82002",
        "phone": "(307) 777-6397",
        "website": "https://ag.wyo.gov",
        "complaint_url": "https://ag.wyo.gov/consumer-protection/file-a-consumer-complaint",
        "accepts_online": True,
    },
    # DC (District of Columbia)
    {
        "state_code": "DC",
        "state_name": "District of Columbia",
        "office_name": "Office of the Attorney General",
        "division_name": "Office of Consumer Protection",
        "address_line1": "400 6th Street NW, Suite 10100",
        "city": "Washington",
        "state": "DC",
        "zip_code": "20001",
        "phone": "(202) 442-9828",
        "website": "https://oag.dc.gov",
        "complaint_url": "https://oag.dc.gov/consumer-protection/submit-consumer-complaint",
        "accepts_online": True,
    },
]


class StateAGService:
    """Service for managing State Attorney General complaints"""

    def __init__(self, session: Session = None):
        """Initialize with optional database session"""
        self._session = session
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session and self._session:
            self._session.close()

    @property
    def session(self) -> Session:
        """Get or create database session"""
        if self._session is None:
            from database import get_db

            self._session = next(get_db())
        return self._session

    def _success_response(
        self, data: Any = None, message: str = None
    ) -> Dict[str, Any]:
        """Create a standardized success response"""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response

    def _error_response(
        self, message: str, error_code: str, details: Dict = None
    ) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "success": False,
            "error": message,
            "error_code": error_code,
            "details": details or {},
        }

    # ==================== AG Contact CRUD ====================

    def seed_ag_contacts(self) -> Dict[str, Any]:
        """Seed database with all 50 state AG contacts"""
        from database import StateAGContact

        try:
            created = 0
            updated = 0

            for ag_data in STATE_AG_DATABASE:
                existing = (
                    self.session.query(StateAGContact)
                    .filter_by(state_code=ag_data["state_code"])
                    .first()
                )

                if existing:
                    # Update existing record
                    for key, value in ag_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated += 1
                else:
                    # Create new record
                    contact = StateAGContact(**ag_data)
                    self.session.add(contact)
                    created += 1

            self.session.commit()
            return self._success_response(
                {
                    "created": created,
                    "updated": updated,
                    "total": len(STATE_AG_DATABASE),
                },
                f"Seeded {created} new, updated {updated} AG contacts",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error seeding AG contacts: {e}")
            return self._error_response(str(e), "SEED_ERROR")

    def get_all_ag_contacts(self) -> List[Dict[str, Any]]:
        """Get all state AG contacts"""
        from database import StateAGContact

        contacts = (
            self.session.query(StateAGContact).order_by(StateAGContact.state_name).all()
        )

        return [c.to_dict() for c in contacts]

    def get_ag_contact_by_state(self, state_code: str) -> Optional[Dict[str, Any]]:
        """Get AG contact for a specific state"""
        from database import StateAGContact

        contact = (
            self.session.query(StateAGContact)
            .filter_by(state_code=state_code.upper())
            .first()
        )

        return contact.to_dict() if contact else None

    def get_ag_contact_by_id(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Get AG contact by ID"""
        from database import StateAGContact

        contact = self.session.query(StateAGContact).filter_by(id=contact_id).first()
        return contact.to_dict() if contact else None

    # ==================== Complaint CRUD ====================

    def create_complaint(
        self,
        client_id: int,
        state_code: str,
        complaint_type: str,
        bureaus: List[str] = None,
        furnishers: List[str] = None,
        violation_types: List[str] = None,
        violation_summary: str = None,
        dispute_rounds: int = 0,
        escalation_id: int = None,
        staff_id: int = None,
    ) -> Dict[str, Any]:
        """Create a new State AG complaint"""
        from database import Client, StateAGComplaint, StateAGContact

        try:
            # Validate client exists
            client = self.session.query(Client).filter_by(id=client_id).first()
            if not client:
                return self._error_response(
                    "Client not found", "CLIENT_NOT_FOUND", {"client_id": client_id}
                )

            # Get AG contact for the state
            ag_contact = (
                self.session.query(StateAGContact)
                .filter_by(state_code=state_code.upper())
                .first()
            )

            if not ag_contact:
                return self._error_response(
                    f"No AG contact found for state: {state_code}",
                    "STATE_NOT_FOUND",
                    {"state_code": state_code},
                )

            # Validate complaint type
            if complaint_type not in ["fcra_violation", "identity_theft", "mixed"]:
                return self._error_response(
                    "Invalid complaint type",
                    "INVALID_COMPLAINT_TYPE",
                    {"valid_types": ["fcra_violation", "identity_theft", "mixed"]},
                )

            # Create complaint
            complaint = StateAGComplaint(
                client_id=client_id,
                state_ag_id=ag_contact.id,
                complaint_type=complaint_type,
                bureaus_complained=bureaus or [],
                furnishers_complained=furnishers or [],
                violation_types=violation_types or [],
                violation_summary=violation_summary,
                dispute_rounds_exhausted=dispute_rounds,
                escalation_id=escalation_id,
                assigned_staff_id=staff_id,
                status="draft",
            )

            self.session.add(complaint)
            self.session.commit()

            logger.info(f"Created AG complaint {complaint.id} for client {client_id}")

            return self._success_response(
                complaint.to_dict(), "Complaint created successfully"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating complaint: {e}")
            return self._error_response(str(e), "CREATE_ERROR")

    def get_complaint(self, complaint_id: int) -> Optional[Dict[str, Any]]:
        """Get a complaint by ID"""
        from database import StateAGComplaint

        complaint = (
            self.session.query(StateAGComplaint).filter_by(id=complaint_id).first()
        )

        return complaint.to_dict() if complaint else None

    def get_client_complaints(self, client_id: int) -> List[Dict[str, Any]]:
        """Get all complaints for a client"""
        from database import StateAGComplaint

        complaints = (
            self.session.query(StateAGComplaint)
            .filter_by(client_id=client_id)
            .order_by(StateAGComplaint.created_at.desc())
            .all()
        )

        return [c.to_dict() for c in complaints]

    def update_complaint(
        self, complaint_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a complaint"""
        from database import StateAGComplaint

        try:
            complaint = (
                self.session.query(StateAGComplaint).filter_by(id=complaint_id).first()
            )

            if not complaint:
                return self._error_response(
                    "Complaint not found",
                    "COMPLAINT_NOT_FOUND",
                    {"complaint_id": complaint_id},
                )

            # Update allowed fields
            allowed_fields = [
                "bureaus_complained",
                "furnishers_complained",
                "violation_types",
                "violation_summary",
                "dispute_rounds_exhausted",
                "status",
                "confirmation_number",
                "tracking_number",
                "notes",
                "assigned_staff_id",
                "resolution_type",
                "resolution_summary",
                "damages_recovered",
                "complaint_letter_path",
                "supporting_docs",
            ]

            for field, value in updates.items():
                if field in allowed_fields and hasattr(complaint, field):
                    setattr(complaint, field, value)

            self.session.commit()

            return self._success_response(
                complaint.to_dict(), "Complaint updated successfully"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating complaint: {e}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def update_complaint_status(
        self, complaint_id: int, new_status: str, notes: str = None
    ) -> Dict[str, Any]:
        """Update complaint status with timestamp tracking"""
        from database import StateAGComplaint

        try:
            complaint = (
                self.session.query(StateAGComplaint).filter_by(id=complaint_id).first()
            )

            if not complaint:
                return self._error_response(
                    "Complaint not found", "COMPLAINT_NOT_FOUND"
                )

            if new_status not in COMPLAINT_STATUSES:
                return self._error_response(
                    "Invalid status",
                    "INVALID_STATUS",
                    {"valid_statuses": list(COMPLAINT_STATUSES.keys())},
                )

            old_status = complaint.status
            complaint.status = new_status

            # Update appropriate timestamp
            now = datetime.utcnow()
            if new_status == "filed":
                complaint.filed_at = now
            elif new_status == "acknowledged":
                complaint.acknowledged_at = now
            elif new_status == "investigating":
                complaint.investigation_started_at = now
            elif new_status in ["resolved", "closed"]:
                complaint.resolved_at = now

            complaint.last_contact_at = now

            if notes:
                existing_notes = complaint.notes or ""
                complaint.notes = f"{existing_notes}\n[{now.isoformat()}] Status: {old_status} -> {new_status}\n{notes}".strip()

            self.session.commit()

            return self._success_response(
                complaint.to_dict(), f"Status updated to {new_status}"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating status: {e}")
            return self._error_response(str(e), "STATUS_UPDATE_ERROR")

    def file_complaint(
        self,
        complaint_id: int,
        filed_method: str,
        tracking_number: str = None,
        confirmation_number: str = None,
    ) -> Dict[str, Any]:
        """Mark complaint as filed"""
        from database import StateAGComplaint

        try:
            complaint = (
                self.session.query(StateAGComplaint).filter_by(id=complaint_id).first()
            )

            if not complaint:
                return self._error_response(
                    "Complaint not found", "COMPLAINT_NOT_FOUND"
                )

            if complaint.status not in ["draft", "ready"]:
                return self._error_response(
                    f"Cannot file complaint with status: {complaint.status}",
                    "INVALID_STATUS_FOR_FILING",
                )

            if filed_method not in ["online", "mail", "email"]:
                return self._error_response(
                    "Invalid filing method",
                    "INVALID_FILING_METHOD",
                    {"valid_methods": ["online", "mail", "email"]},
                )

            complaint.status = "filed"
            complaint.filed_at = datetime.utcnow()
            complaint.filed_method = filed_method
            complaint.tracking_number = tracking_number
            complaint.confirmation_number = confirmation_number

            self.session.commit()

            return self._success_response(
                complaint.to_dict(), "Complaint filed successfully"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error filing complaint: {e}")
            return self._error_response(str(e), "FILE_ERROR")

    def resolve_complaint(
        self,
        complaint_id: int,
        resolution_type: str,
        resolution_summary: str = None,
        damages_recovered: float = None,
    ) -> Dict[str, Any]:
        """Mark complaint as resolved"""
        from database import StateAGComplaint

        try:
            complaint = (
                self.session.query(StateAGComplaint).filter_by(id=complaint_id).first()
            )

            if not complaint:
                return self._error_response(
                    "Complaint not found", "COMPLAINT_NOT_FOUND"
                )

            valid_resolutions = [
                "favorable",
                "unfavorable",
                "referred",
                "no_action",
                "settlement",
            ]
            if resolution_type not in valid_resolutions:
                return self._error_response(
                    "Invalid resolution type",
                    "INVALID_RESOLUTION_TYPE",
                    {"valid_types": valid_resolutions},
                )

            complaint.status = "resolved"
            complaint.resolved_at = datetime.utcnow()
            complaint.resolution_type = resolution_type
            complaint.resolution_summary = resolution_summary
            complaint.damages_recovered = damages_recovered

            self.session.commit()

            return self._success_response(complaint.to_dict(), "Complaint resolved")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error resolving complaint: {e}")
            return self._error_response(str(e), "RESOLVE_ERROR")

    # ==================== Complaint Letter Generation ====================

    def generate_complaint_letter(
        self, complaint_id: int, use_ai: bool = True
    ) -> Dict[str, Any]:
        """Generate AG complaint letter for filing"""
        from database import Client, StateAGComplaint

        try:
            complaint = (
                self.session.query(StateAGComplaint).filter_by(id=complaint_id).first()
            )

            if not complaint:
                return self._error_response(
                    "Complaint not found", "COMPLAINT_NOT_FOUND"
                )

            client = (
                self.session.query(Client).filter_by(id=complaint.client_id).first()
            )
            if not client:
                return self._error_response("Client not found", "CLIENT_NOT_FOUND")

            ag_contact = complaint.ag_contact
            if not ag_contact:
                return self._error_response(
                    "AG contact not found", "AG_CONTACT_NOT_FOUND"
                )

            if use_ai:
                letter_content = self._generate_ai_complaint_letter(
                    complaint, client, ag_contact
                )
            else:
                letter_content = self._generate_template_complaint_letter(
                    complaint, client, ag_contact
                )

            return self._success_response(
                {
                    "letter_content": letter_content,
                    "complaint_id": complaint_id,
                    "ag_contact": ag_contact.to_dict(),
                },
                "Letter generated successfully",
            )

        except Exception as e:
            logger.error(f"Error generating letter: {e}")
            return self._error_response(str(e), "LETTER_GENERATION_ERROR")

    def _generate_template_complaint_letter(self, complaint, client, ag_contact) -> str:
        """Generate complaint letter using template"""
        today = datetime.now().strftime("%B %d, %Y")

        # Build violation list
        violations_text = ""
        for v_type in complaint.violation_types or []:
            if v_type in VIOLATION_TYPES:
                violations_text += f"  - {VIOLATION_TYPES[v_type]}\n"

        # Build bureaus list
        bureaus_text = ", ".join(complaint.bureaus_complained or ["(none specified)"])

        # Build furnishers list
        furnishers_text = ""
        for f in complaint.furnishers_complained or []:
            furnishers_text += f"  - {f}\n"

        letter = f"""
{client.first_name} {client.last_name}
{client.address_street or ''}
{client.address_city or ''}, {client.address_state or ''} {client.address_zip or ''}

{today}

{ag_contact.office_name}
{ag_contact.division_name or ''}
{ag_contact.address_line1}
{ag_contact.address_line2 or ''}
{ag_contact.city}, {ag_contact.state} {ag_contact.zip_code}

RE: Consumer Complaint - Fair Credit Reporting Act Violations

Dear Attorney General:

I am writing to file a formal complaint regarding violations of the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681 et seq.

CONSUMER INFORMATION:
Name: {client.first_name} {client.last_name}
SSN (Last 4): XXX-XX-{client.ssn_last_four or 'XXXX'}
Date of Birth: {client.date_of_birth.strftime('%m/%d/%Y') if client.date_of_birth else 'On file'}

COMPLAINT TYPE: {complaint.complaint_type.replace('_', ' ').title()}

CREDIT BUREAUS INVOLVED:
{bureaus_text}

CREDITORS/FURNISHERS INVOLVED:
{furnishers_text if furnishers_text else '  - (Information to be provided)'}

FCRA VIOLATIONS:
{violations_text if violations_text else '  - Failure to conduct reasonable investigation (§611)'}

SUMMARY OF COMPLAINT:
{complaint.violation_summary or 'The above-named credit reporting agencies and/or furnishers have violated the Fair Credit Reporting Act by failing to conduct reasonable investigations of disputed information, continuing to report inaccurate information after receiving notice of the dispute, and/or failing to follow reasonable procedures to assure maximum possible accuracy of credit information.'}

DISPUTE HISTORY:
I have previously disputed these items directly with the credit bureaus through {complaint.dispute_rounds_exhausted or 'multiple'} rounds of written disputes. Despite providing documentation supporting my position, the bureaus have failed to properly investigate and correct the inaccurate information.

Under FCRA §621 (15 U.S.C. § 1681s), state Attorneys General have independent authority to enforce FCRA provisions. I respectfully request that your office investigate these violations and take appropriate enforcement action.

RELIEF REQUESTED:
1. Investigation of the above violations
2. Enforcement action against the violating parties
3. Correction or deletion of inaccurate information
4. Any appropriate penalties under state and federal law

I am enclosing copies of my dispute letters, responses received, and other relevant documentation. I am happy to provide any additional information your office may need.

Thank you for your attention to this matter.

Respectfully,


____________________________
{client.first_name} {client.last_name}

Enclosures:
- Copy of credit report(s)
- Dispute letters sent to bureaus
- Bureau responses received
- Supporting documentation
"""
        return letter.strip()

    def _generate_ai_complaint_letter(self, complaint, client, ag_contact) -> str:
        """Generate complaint letter using AI"""
        try:
            import anthropic

            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("No Anthropic API key, falling back to template")
                return self._generate_template_complaint_letter(
                    complaint, client, ag_contact
                )

            anthropic_client = anthropic.Anthropic(api_key=api_key)

            violations_list = [
                VIOLATION_TYPES.get(v, v) for v in (complaint.violation_types or [])
            ]
            bureaus_list = complaint.bureaus_complained or []
            furnishers_list = complaint.furnishers_complained or []

            prompt = f"""Generate a formal complaint letter to the {ag_contact.state_name} Attorney General's Office regarding Fair Credit Reporting Act (FCRA) violations.

Consumer Information:
- Name: {client.first_name} {client.last_name}
- Address: {client.address_street}, {client.address_city}, {client.address_state} {client.address_zip}
- SSN Last 4: {client.ssn_last_four or 'XXXX'}

Attorney General Office:
- Office: {ag_contact.office_name}
- Division: {ag_contact.division_name or 'Consumer Protection'}
- Address: {ag_contact.address_line1}, {ag_contact.city}, {ag_contact.state} {ag_contact.zip_code}

Complaint Details:
- Type: {complaint.complaint_type}
- Bureaus: {', '.join(bureaus_list) or 'Not specified'}
- Furnishers: {', '.join(furnishers_list) or 'Not specified'}
- Violations: {', '.join(violations_list) or 'FCRA violations'}
- Summary: {complaint.violation_summary or 'Multiple FCRA violations after exhausting direct dispute process'}
- Prior Dispute Rounds: {complaint.dispute_rounds_exhausted or 0}

Requirements:
1. Write a formal, professional complaint letter
2. Cite specific FCRA sections (§611, §623, §621 for AG enforcement authority)
3. Request investigation and enforcement action
4. Include clear summary of violations
5. Mention enclosures (credit reports, dispute letters, responses)
6. DO NOT include any false or fabricated information
7. Use formal legal language appropriate for AG office
8. Keep the letter concise but comprehensive (1-2 pages)

Generate the complete letter:"""

            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"AI letter generation failed: {e}")
            return self._generate_template_complaint_letter(
                complaint, client, ag_contact
            )

    # ==================== Statistics & Reporting ====================

    def get_complaint_statistics(self) -> Dict[str, Any]:
        """Get overall complaint statistics"""
        from sqlalchemy import func

        from database import StateAGComplaint

        try:
            # Total by status
            status_counts = dict(
                self.session.query(
                    StateAGComplaint.status, func.count(StateAGComplaint.id)
                )
                .group_by(StateAGComplaint.status)
                .all()
            )

            # Total by state
            state_counts = dict(
                self.session.query(
                    StateAGComplaint.state_ag_id, func.count(StateAGComplaint.id)
                )
                .group_by(StateAGComplaint.state_ag_id)
                .all()
            )

            # Resolution outcomes
            resolution_counts = dict(
                self.session.query(
                    StateAGComplaint.resolution_type, func.count(StateAGComplaint.id)
                )
                .filter(StateAGComplaint.resolution_type.isnot(None))
                .group_by(StateAGComplaint.resolution_type)
                .all()
            )

            # Total damages recovered
            total_damages = (
                self.session.query(func.sum(StateAGComplaint.damages_recovered))
                .filter(StateAGComplaint.damages_recovered.isnot(None))
                .scalar()
                or 0
            )

            # Pending complaints (filed but not resolved)
            pending_count = (
                self.session.query(StateAGComplaint)
                .filter(
                    StateAGComplaint.status.in_(
                        ["filed", "acknowledged", "investigating"]
                    )
                )
                .count()
            )

            return self._success_response(
                {
                    "by_status": status_counts,
                    "by_state": state_counts,
                    "by_resolution": resolution_counts,
                    "total_damages_recovered": total_damages,
                    "pending_complaints": pending_count,
                    "total_complaints": sum(status_counts.values()),
                }
            )

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return self._error_response(str(e), "STATS_ERROR")

    def get_overdue_complaints(self, days_threshold: int = 60) -> List[Dict[str, Any]]:
        """Get complaints that are overdue for response"""
        from database import StateAGComplaint

        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

        overdue = (
            self.session.query(StateAGComplaint)
            .filter(
                StateAGComplaint.status.in_(["filed", "acknowledged", "investigating"]),
                StateAGComplaint.filed_at < threshold_date,
            )
            .order_by(StateAGComplaint.filed_at)
            .all()
        )

        return [c.to_dict() for c in overdue]

    def get_escalation_candidates(
        self, min_dispute_rounds: int = 2
    ) -> List[Dict[str, Any]]:
        """Get clients who may be candidates for AG escalation"""
        from sqlalchemy import and_

        from database import Client, StateAGComplaint

        # Get clients with multiple dispute rounds but no AG complaint
        clients_with_complaints = self.session.query(
            StateAGComplaint.client_id
        ).distinct()

        candidates = (
            self.session.query(Client)
            .filter(
                and_(
                    Client.current_dispute_round >= min_dispute_rounds,
                    Client.id.notin_(clients_with_complaints),
                )
            )
            .all()
        )

        return [
            {
                "client_id": c.id,
                "name": f"{c.first_name} {c.last_name}",
                "state": c.address_state,
                "dispute_rounds": c.current_dispute_round,
                "dispute_status": c.dispute_status,
            }
            for c in candidates
        ]


def get_state_ag_service(session: Session = None) -> StateAGService:
    """Factory function to get StateAGService instance"""
    return StateAGService(session=session)
