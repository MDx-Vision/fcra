"""
Credit Report Parser Service
Parses HTML from credit monitoring services into structured three-bureau format.
Specifically optimized for MyScoreIQ Angular-rendered reports.
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CreditReportParser:
    """Parse credit report HTML into structured data."""
    
    SKIP_HEADERS = {
        'THE', 'AND', 'FOR', 'CREDIT REPORT', 'WATCH', 'KNOW', 
        'FICO', 'PLAN', 'YOUR', 'SCORE', 'REPORT', 'SUMMARY',
        'SCORE FACTORS', 'FACTORS', 'INQUIRIES', 'COLLECTIONS',
        'PUBLIC RECORDS', 'PERSONAL INFORMATION', 'SUBSCRIBER',
        'ACCOUNT HISTORY', 'CREDITOR CONTACTS', 'EXTENDED PAYMENT HISTORY',
        'QUICK LINKS', 'BACK TO TOP', 'CREDIT SCORE', 'MONTH', 'YEAR',
        'TRANSUNION', 'EXPERIAN', 'EQUIFAX'
    }
    
    def __init__(self, html_content: str, service_name: str = 'unknown'):
        self.html = html_content
        self.service = service_name
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self._summary_counts = None
        
    def parse(self) -> Dict:
        """Parse the credit report and return structured data."""
        self._summary_counts = self._extract_summary_counts()
        
        result = {
            'scores': self._extract_scores(),
            'personal_info': self._extract_personal_info(),
            'accounts': self._extract_accounts(),
            'inquiries': self._extract_inquiries(),
            'public_records': self._extract_public_records(),
            'collections': self._extract_collections(),
            'creditor_contacts': self._extract_creditor_contacts(),
            'summary': {},
        }
        
        result['summary'] = {
            'total_accounts': len(result['accounts']),
            'total_inquiries': len(result['inquiries']),
            'total_collections': len(result['collections']),
            'total_public_records': len(result['public_records']),
        }
        
        return result
    
    def _extract_summary_counts(self) -> Dict:
        """Extract summary counts from the report to determine if collections/public records exist."""
        counts = {
            'collections': 0,
            'public_records': 0,
            'open_accounts': 0,
            'closed_accounts': 0,
        }
        
        summary_section = self.soup.find('div', id='Summary')
        if not summary_section:
            summary_section = self.soup
        
        rows = summary_section.find_all('tr') if summary_section else []
        for row in rows:
            label_cell = row.find('td', class_='label')
            if not label_cell:
                continue
            label = label_cell.get_text(strip=True).lower()
            
            info_cells = row.find_all('td', class_=re.compile(r'info'))
            values = [cell.get_text(strip=True) for cell in info_cells]
            
            if 'collection' in label and 'chargeoff' not in label:
                for v in values:
                    if v and v != '-':
                        digits = re.sub(r'\D', '', v)
                        if digits:
                            counts['collections'] = max(counts['collections'], int(digits))
                            break
            
            elif 'public record' in label:
                for v in values:
                    if v and v != '-':
                        digits = re.sub(r'\D', '', v)
                        if digits:
                            counts['public_records'] = max(counts['public_records'], int(digits))
                            break
        
        logger.info(f"Summary counts extracted: {counts}")
        return counts
    
    def _extract_scores(self) -> Dict:
        """Extract credit scores for all three bureaus."""
        scores = {
            'transunion': None,
            'experian': None,
            'equifax': None,
        }
        
        # Method 1: Look for CreditScore section with FICO Score 8 table row
        score_section = self.soup.find('div', id='CreditScore')
        if score_section:
            tables = score_section.find_all('table', class_=re.compile(r'rpt_content_table'))
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    label_cell = row.find('td', class_='label')
                    if label_cell:
                        label_text = label_cell.get_text(strip=True).lower()
                        # Look for "FICO Score 8:" row
                        if 'fico' in label_text and 'score' in label_text and '8' in label_text:
                            info_cells = row.find_all('td', class_=re.compile(r'info'))
                            if len(info_cells) >= 3:
                                # Order: TransUnion, Experian, Equifax
                                for i, bureau in enumerate(['transunion', 'experian', 'equifax']):
                                    if i < len(info_cells):
                                        score_text = info_cells[i].get_text(strip=True)
                                        if score_text and score_text != '-':
                                            try:
                                                score = int(score_text)
                                                if 300 <= score <= 850:
                                                    scores[bureau] = score
                                            except ValueError:
                                                pass
                            break
        
        # Method 2: Fallback - search by bureau name in tables
        if not any(scores.values()) and score_section:
            tables = score_section.find_all('table')
            for table in tables:
                text = table.get_text()
                
                if 'transunion' in text.lower() and not scores['transunion']:
                    match = re.search(r'(\d{3})', text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores['transunion'] = score
                
                elif 'experian' in text.lower() and not scores['experian']:
                    match = re.search(r'(\d{3})', text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores['experian'] = score
                
                elif 'equifax' in text.lower() and not scores['equifax']:
                    match = re.search(r'(\d{3})', text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores['equifax'] = score
        
        # Method 3: Fallback - regex on full text
        if not any(scores.values()):
            text = self.soup.get_text()
            
            tu_match = re.search(r'transunion[:\s]*(\d{3})', text, re.I)
            if tu_match:
                score = int(tu_match.group(1))
                if 300 <= score <= 850:
                    scores['transunion'] = score
            
            exp_match = re.search(r'experian[:\s]*(\d{3})', text, re.I)
            if exp_match:
                score = int(exp_match.group(1))
                if 300 <= score <= 850:
                    scores['experian'] = score
            
            eq_match = re.search(r'equifax[:\s]*(\d{3})', text, re.I)
            if eq_match:
                score = int(eq_match.group(1))
                if 300 <= score <= 850:
                    scores['equifax'] = score
        
        return scores
    
    def _extract_personal_info(self) -> Dict:
        """Extract personal information from report."""
        info = {
            'name': None,
            'address': None,
            'ssn_last4': None,
            'dob': None,
        }
        
        personal_section = self.soup.find('div', id='PersonalInformation')
        if personal_section:
            name_row = personal_section.find('td', string=re.compile(r'name', re.I))
            if name_row:
                parent_row = name_row.find_parent('tr')
                if parent_row:
                    cells = parent_row.find_all('td', class_=re.compile(r'info'))
                    for cell in cells:
                        name_text = cell.get_text(strip=True)
                        if name_text and name_text != '-':
                            info['name'] = name_text
                            break
        
        return info
    
    def _is_valid_creditor_name(self, name: str) -> bool:
        """Check if a name is a valid creditor (not a section header or label)."""
        if not name or len(name) < 3:
            return False
        
        clean_name = name.upper().strip()
        
        if clean_name in self.SKIP_HEADERS:
            return False
        
        for skip in self.SKIP_HEADERS:
            if clean_name == skip or clean_name.startswith(skip + ' '):
                return False
        
        if '{{' in name or '}}' in name:
            return False
        
        if re.match(r'^[A-Z]{1,3}$', clean_name):
            return False
        
        return True
    
    def _extract_accounts(self) -> List[Dict]:
        """Extract all tradeline accounts from Angular-rendered HTML."""
        accounts = []
        seen_creditors = set()
        
        account_section = self.soup.find('div', id='AccountHistory')
        search_area = self.soup
        
        if account_section:
            parent_wrapper = account_section.find_parent('div', class_=re.compile(r'rpt_content_wrapper'))
            if parent_wrapper:
                search_area = parent_wrapper
        
        sub_headers = search_area.find_all('div', class_=re.compile(r'sub_header.*ng-binding|sub_header'))
        
        for header in sub_headers:
            text = header.get_text(strip=True)
            text = re.sub(r'\s+', ' ', text)
            
            original_creditor = None
            orig_match = re.search(r'\(Original Creditor:\s*([^)]+)\)', text)
            if orig_match:
                original_creditor = orig_match.group(1).strip()
            
            text = re.sub(r'\(Original Creditor:.*\)', '', text).strip()
            
            if not self._is_valid_creditor_name(text):
                continue
            
            account_key = text
            
            parent_for_key = header.find_parent('table', class_='crPrint')
            if parent_for_key:
                table_for_key = parent_for_key.find('table', class_=re.compile(r'rpt_content_table'))
                if table_for_key:
                    for row in table_for_key.find_all('tr')[:5]:
                        label_cell = row.find('td', class_='label')
                        if label_cell and 'account' in label_cell.get_text(strip=True).lower() and '#' in label_cell.get_text(strip=True):
                            info_cells = row.find_all('td', class_=re.compile(r'info'))
                            for cell in info_cells:
                                acct_num = cell.get_text(strip=True)
                                if acct_num and acct_num != '-':
                                    account_key = f"{text}_{acct_num}"
                                    break
                            break
            
            if account_key in seen_creditors:
                continue
            seen_creditors.add(account_key)
            
            account = {
                'creditor': text,
                'original_creditor': original_creditor,
                'account_number': None,
                'account_type': None,
                'account_type_detail': None,
                'status': None,
                'balance': None,
                'credit_limit': None,
                'high_balance': None,
                'monthly_payment': None,
                'payment_status': None,
                'date_opened': None,
                'date_reported': None,
                'past_due_amount': None,
                'times_30_late': None,
                'times_60_late': None,
                'times_90_late': None,
                'is_authorized_user': False,
                'responsibility': None,
                'payment_history': [],
                'discrepancies': [],
                'has_discrepancy': False,
                'bureaus': {
                    'transunion': {'present': False, 'balance': None, 'credit_limit': None, 'date_opened': None, 'status': None},
                    'experian': {'present': False, 'balance': None, 'credit_limit': None, 'date_opened': None, 'status': None},
                    'equifax': {'present': False, 'balance': None, 'credit_limit': None, 'date_opened': None, 'status': None},
                }
            }
            
            parent = header.find_parent('table', class_='crPrint')
            if not parent:
                parent = header.find_parent('ng-include')
            if not parent:
                parent = header.parent
            
            table = None
            if parent:
                table = parent.find('table', class_=re.compile(r'rpt_content_table'))
            if not table:
                table = header.find_next('table', class_=re.compile(r'rpt_content'))
            
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    label_cell = row.find('td', class_='label')
                    info_cells = row.find_all('td', class_=re.compile(r'info'))
                    
                    if label_cell and info_cells:
                        label = label_cell.get_text(strip=True).lower()
                        values = [cell.get_text(strip=True) for cell in info_cells]
                        
                        first_value = next((v for v in values if v and v != '-'), None)
                        
                        if len(values) >= 3:
                            if values[0] and values[0] != '-':
                                account['bureaus']['transunion']['present'] = True
                            if values[1] and values[1] != '-':
                                account['bureaus']['experian']['present'] = True
                            if values[2] and values[2] != '-':
                                account['bureaus']['equifax']['present'] = True
                        
                        if 'account' in label and '#' in label or label == 'account #:':
                            account['account_number'] = first_value
                            if len(values) >= 3:
                                if values[0] and values[0] != '-':
                                    account['bureaus']['transunion']['number'] = values[0]
                                if values[1] and values[1] != '-':
                                    account['bureaus']['experian']['number'] = values[1]
                                if values[2] and values[2] != '-':
                                    account['bureaus']['equifax']['number'] = values[2]
                        
                        elif 'account type - detail' in label:
                            account['account_type_detail'] = first_value
                        
                        elif 'account type' in label or 'classification' in label:
                            account['account_type'] = first_value
                            if len(values) >= 3:
                                if values[0] and values[0] != '-':
                                    account['bureaus']['transunion']['type'] = values[0]
                                if values[1] and values[1] != '-':
                                    account['bureaus']['experian']['type'] = values[1]
                                if values[2] and values[2] != '-':
                                    account['bureaus']['equifax']['type'] = values[2]
                        
                        elif 'status' in label or 'condition' in label or 'pay status' in label:
                            account['status'] = first_value
                        
                        elif label == 'balance:' or label == 'balances:':
                            account['balance'] = first_value
                            # Store bureau-specific balances
                            if len(values) >= 1 and values[0] and values[0] != '-':
                                account['bureaus']['transunion']['balance'] = values[0]
                            if len(values) >= 2 and values[1] and values[1] != '-':
                                account['bureaus']['experian']['balance'] = values[1]
                            if len(values) >= 3 and values[2] and values[2] != '-':
                                account['bureaus']['equifax']['balance'] = values[2]
                        
                        elif 'credit limit' in label:
                            account['credit_limit'] = first_value
                            # Store bureau-specific limits
                            if len(values) >= 1 and values[0] and values[0] != '-':
                                account['bureaus']['transunion']['credit_limit'] = values[0]
                            if len(values) >= 2 and values[1] and values[1] != '-':
                                account['bureaus']['experian']['credit_limit'] = values[1]
                            if len(values) >= 3 and values[2] and values[2] != '-':
                                account['bureaus']['equifax']['credit_limit'] = values[2]
                        
                        elif 'high balance' in label or 'high credit' in label:
                            account['high_balance'] = first_value
                        
                        elif 'monthly payment' in label:
                            account['monthly_payment'] = first_value
                        
                        elif 'date opened' in label:
                            account['date_opened'] = first_value
                            # Store bureau-specific dates
                            if len(values) >= 1 and values[0] and values[0] != '-':
                                account['bureaus']['transunion']['date_opened'] = values[0]
                            if len(values) >= 2 and values[1] and values[1] != '-':
                                account['bureaus']['experian']['date_opened'] = values[1]
                            if len(values) >= 3 and values[2] and values[2] != '-':
                                account['bureaus']['equifax']['date_opened'] = values[2]
                        
                        elif 'date reported' in label:
                            account['date_reported'] = first_value
                        
                        elif 'past due' in label:
                            account['past_due_amount'] = first_value
                        
                        elif '30' in label and 'late' in label:
                            account['times_30_late'] = first_value
                        
                        elif '60' in label and 'late' in label:
                            account['times_60_late'] = first_value
                        
                        elif '90' in label and 'late' in label:
                            account['times_90_late'] = first_value
                        
                        elif 'bureau code' in label or 'responsibility' in label:
                            account['responsibility'] = first_value
                            # Check if any value indicates authorized user
                            for v in values:
                                if v and ('authorized' in v.lower() or 'auth user' in v.lower()):
                                    account['is_authorized_user'] = True
                                    break
            
            # Extract payment history directly from crPrint table
            crprint_table = header.find_parent('table', class_='crPrint')
            if crprint_table:
                history_table = crprint_table.find('table', class_=re.compile(r'addr_hsrty'))
                if history_table:
                    rows = history_table.find_all('tr')
                    months, years, tu, exp, eqf = [], [], [], [], []
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) < 2:
                            continue
                        label = cells[0].get_text(strip=True).lower()
                        values = [c.get_text(strip=True) for c in cells[1:]]
                        if 'month' in label: months = values
                        elif 'year' in label: years = values
                        elif 'transunion' in label: tu = values
                        elif 'experian' in label: exp = values
                        elif 'equifax' in label: eqf = values
                    for i in range(min(len(months), len(years))):
                        account['payment_history'].append({
                            'month': months[i],
                            'year': years[i],
                            'transunion': tu[i].strip() if i < len(tu) and tu[i].strip() else None,
                            'experian': exp[i].strip() if i < len(exp) and exp[i].strip() else None,
                            'equifax': eqf[i].strip() if i < len(eqf) and eqf[i].strip() else None,
                        })
            
            accounts.append(account)
        
        return accounts
    
    def _extract_payment_history_for_account(self, parent_element) -> List[Dict]:
        """Extract 2-year payment history grid for an account."""
        history = []
        
        # Try to find payment history tables within the parent element
        history_tables = parent_element.find_all('table', class_=re.compile(r'addr_hsrty'))
        
        # If not found in parent, try to find in the next sibling crPrint table
        if not history_tables:
            # Look for Extended Payment History section
            ext_history = parent_element.find_all(string=re.compile(r'Extended Payment History'))
            for eh in ext_history:
                parent_td = eh.find_parent('td')
                if parent_td:
                    history_tables = parent_td.find_all('table', class_=re.compile(r'addr_hsrty'))
                    if history_tables:
                        break
        
        for table in history_tables:
            rows = table.find_all('tr')
            if len(rows) < 3:
                continue
            
            months = []
            years = []
            tu_status = []
            exp_status = []
            eqf_status = []
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue
                
                # First cell contains the label (Month, Year, TransUnion, etc.)
                first_cell_text = cells[0].get_text(strip=True).lower()
                # Remaining cells contain the values
                values = [cell.get_text(strip=True) for cell in cells[1:]]
                
                if 'month' in first_cell_text:
                    months = values
                elif 'year' in first_cell_text:
                    years = values
                elif 'transunion' in first_cell_text:
                    tu_status = values
                elif 'experian' in first_cell_text:
                    exp_status = values
                elif 'equifax' in first_cell_text:
                    eqf_status = values
            
            # Build history entries
            for i in range(min(len(months), len(years))):
                # Get status, converting empty strings to None
                tu_val = tu_status[i].strip() if i < len(tu_status) and tu_status[i].strip() else None
                exp_val = exp_status[i].strip() if i < len(exp_status) and exp_status[i].strip() else None
                eqf_val = eqf_status[i].strip() if i < len(eqf_status) and eqf_status[i].strip() else None
                
                entry = {
                    'month': months[i] if i < len(months) else None,
                    'year': years[i] if i < len(years) else None,
                    'transunion': tu_val,
                    'experian': exp_val,
                    'equifax': eqf_val,
                }
                if entry['month'] and entry['year']:
                    history.append(entry)
        
        return history
    
    def _extract_inquiries(self) -> List[Dict]:
        """Extract credit inquiries from Angular-rendered HTML."""
        inquiries = []
        seen = set()
        
        inquiry_section = self.soup.find('div', id='Inquiries')
        if inquiry_section:
            rows = inquiry_section.find_all('tr', class_=re.compile(r'ng-scope'))
            for row in rows:
                cells = row.find_all('td', class_=re.compile(r'info'))
                if len(cells) >= 3:
                    creditor = cells[0].get_text(strip=True)
                    inquiry_type = cells[1].get_text(strip=True) if len(cells) > 1 else 'Hard Inquiry'
                    date = cells[2].get_text(strip=True) if len(cells) > 2 else None
                    bureau = cells[3].get_text(strip=True) if len(cells) > 3 else None
                    
                    if creditor and not self._is_valid_creditor_name(creditor):
                        continue
                    
                    key = f"{creditor}_{date}"
                    if key not in seen and creditor:
                        seen.add(key)
                        inquiries.append({
                            'creditor': creditor,
                            'type': inquiry_type,
                            'date': date,
                            'bureau': bureau,
                        })
        
        return inquiries
    
    def _extract_public_records(self) -> List[Dict]:
        """Extract public records ONLY if they actually exist in the report."""
        records = []
        
        if self._summary_counts and self._summary_counts.get('public_records', 0) == 0:
            logger.info("No public records found in summary - skipping extraction")
            return records
        
        public_section = self.soup.find('div', id='PublicRecords')
        if not public_section:
            return records
        
        record_headers = public_section.find_all('div', class_=re.compile(r'sub_header'))
        for header in record_headers:
            text = header.get_text(strip=True)
            if text and '{{' not in text:
                record_type = 'Public Record'
                if 'bankruptcy' in text.lower():
                    record_type = 'Bankruptcy'
                elif 'judgment' in text.lower():
                    record_type = 'Civil Judgment'
                elif 'lien' in text.lower():
                    record_type = 'Tax Lien'
                
                table = header.find_next('table', class_=re.compile(r'rpt_content'))
                filed_date = None
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        label_cell = row.find('td', class_='label')
                        if label_cell and 'filed' in label_cell.get_text(strip=True).lower():
                            info_cells = row.find_all('td', class_=re.compile(r'info'))
                            for cell in info_cells:
                                date_text = cell.get_text(strip=True)
                                if date_text and date_text != '-':
                                    filed_date = date_text
                                    break
                
                records.append({
                    'type': record_type,
                    'description': text,
                    'date': filed_date,
                    'status': 'On Record',
                })
        
        return records
    
    def _extract_collections(self) -> List[Dict]:
        """Extract collection accounts ONLY if they actually exist in the report."""
        collections = []
        
        if self._summary_counts and self._summary_counts.get('collections', 0) == 0:
            logger.info("No collections found in summary - skipping extraction")
            return collections
        
        accounts = self._extract_accounts()
        for account in accounts:
            status = (account.get('status') or '').lower()
            account_type = (account.get('account_type') or '').lower()
            
            if 'collection' in status or 'collection' in account_type:
                collections.append({
                    'agency': account.get('creditor', 'Collection Agency'),
                    'original_creditor': account.get('original_creditor', 'Unknown'),
                    'amount': account.get('balance', 'Unknown'),
                    'status': account.get('status', 'Open'),
                    'date_opened': account.get('date_opened'),
                })
        
        return collections
    
    def _extract_creditor_contacts(self) -> List[Dict]:
        """Extract creditor contact information including addresses and phone numbers."""
        contacts = []
        
        contact_section = self.soup.find('div', id='CreditorContacts')
        if not contact_section:
            contact_section = self.soup.find('div', class_=re.compile(r'rpt_content_contacts'))
        
        if not contact_section:
            return contacts
        
        table = contact_section.find('table', class_=re.compile(r'rpt_content'))
        if not table:
            return contacts
        
        rows = table.find_all('tr', class_=re.compile(r'ng-scope'))
        for row in rows:
            cells = row.find_all('td', class_=re.compile(r'info'))
            if len(cells) >= 3:
                creditor_name = cells[0].get_text(strip=True)
                
                address_cell = cells[1]
                address_parts = []
                for content in address_cell.stripped_strings:
                    if content:
                        address_parts.append(content)
                full_address = ' '.join(address_parts)
                full_address = re.sub(r'\s*,\s*', ', ', full_address)
                full_address = re.sub(r'\s+', ' ', full_address).strip()
                
                phone = cells[2].get_text(strip=True) if len(cells) > 2 else None
                
                if creditor_name and creditor_name != '-':
                    contacts.append({
                        'creditor': creditor_name,
                        'address': full_address if full_address else None,
                        'phone': phone if phone and phone != '-' else None,
                    })
        
        return contacts


def parse_credit_report(html_path: str, service_name: str = 'unknown') -> Dict:
    """Parse a credit report file and return structured data."""
    import json
    import os
    
    try:
        json_path = html_path.replace('.html', '.json')
        extracted_data = None
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    extracted_data = json.load(f)
                logger.info(f"Loaded extracted data from {json_path}")
            except Exception as e:
                logger.warning(f"Failed to load JSON data: {e}")
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = CreditReportParser(html_content, service_name)
        parsed = parser.parse()
        
        if extracted_data:
            if extracted_data.get('scores'):
                for bureau, score in extracted_data['scores'].items():
                    if score:
                        parsed['scores'][bureau] = score
            
            # Only use JSON accounts if they have payment_history, otherwise keep parsed accounts
            if extracted_data.get('accounts') and len(extracted_data['accounts']) > 0:
                # Check if JSON has payment history
                has_payment_history = any(acct.get('payment_history') for acct in extracted_data['accounts'])
                if has_payment_history:
                    parsed['accounts'] = []
                    for acct in extracted_data['accounts']:
                        parsed['accounts'].append({
                            'creditor': acct.get('creditor', 'Unknown'),
                            'original_creditor': acct.get('original_creditor'),
                            'account_number': acct.get('account_number', 'N/A'),
                            'account_type': acct.get('account_type', 'Unknown'),
                            'account_type_detail': acct.get('account_type_detail'),
                            'status': acct.get('status', 'Unknown'),
                            'balance': acct.get('balance'),
                            'credit_limit': acct.get('credit_limit'),
                            'high_balance': acct.get('high_balance'),
                            'monthly_payment': acct.get('monthly_payment'),
                            'payment_status': acct.get('payment_status'),
                            'date_opened': acct.get('date_opened'),
                            'date_reported': acct.get('date_reported'),
                            'past_due_amount': acct.get('past_due_amount'),
                            'times_30_late': acct.get('times_30_late'),
                            'times_60_late': acct.get('times_60_late'),
                            'times_90_late': acct.get('times_90_late'),
                            'payment_history': acct.get('payment_history', []),
                            'bureaus': acct.get('bureaus', {
                                'transunion': {'present': True},
                                'experian': {'present': True},
                                'equifax': {'present': True},
                            })
                        })
            
            if extracted_data.get('inquiries') and len(extracted_data['inquiries']) > 0:
                parsed['inquiries'] = extracted_data['inquiries']
            
            if 'collections' in extracted_data:
                parsed['collections'] = extracted_data.get('collections', [])
            
            if 'public_records' in extracted_data:
                parsed['public_records'] = extracted_data.get('public_records', [])
            
            if extracted_data.get('creditor_contacts'):
                parsed['creditor_contacts'] = extracted_data['creditor_contacts']
        
        # Detect discrepancies between bureaus
        def normalize_value(val):
            if not val or val == '-':
                return None
            # Remove $ and commas for comparison
            return val.replace('$', '').replace(',', '').strip()
        
        for acct in parsed.get('accounts', []):
            discrepancies = []
            bureaus = acct.get('bureaus', {})
            
            # Check balance discrepancy
            balances = {}
            for bureau in ['transunion', 'experian', 'equifax']:
                bal = normalize_value(bureaus.get(bureau, {}).get('balance'))
                if bal:
                    balances[bureau] = bal
            if len(set(balances.values())) > 1 and len(balances) > 1:
                discrepancies.append({'field': 'Balance', 'bureau_values': balances})
            
            # Check credit limit discrepancy
            limits = {}
            for bureau in ['transunion', 'experian', 'equifax']:
                lim = normalize_value(bureaus.get(bureau, {}).get('credit_limit'))
                if lim:
                    limits[bureau] = lim
            if len(set(limits.values())) > 1 and len(limits) > 1:
                discrepancies.append({'field': 'Credit Limit', 'bureau_values': limits})
            
            # Check date opened discrepancy
            dates = {}
            for bureau in ['transunion', 'experian', 'equifax']:
                dt = bureaus.get(bureau, {}).get('date_opened')
                if dt and dt != '-':
                    dates[bureau] = dt
            if len(set(dates.values())) > 1 and len(dates) > 1:
                discrepancies.append({'field': 'Date Opened', 'bureau_values': dates})
            
            acct['discrepancies'] = discrepancies
            acct['has_discrepancy'] = len(discrepancies) > 0
        
        # Count late payments from payment history
        late_count = 0
        on_time_count = 0
        total_payments = 0
        for acct in parsed.get('accounts', []):
            for entry in acct.get('payment_history', []):
                has_data = False
                is_late = False
                is_ok = False
                for bureau in ['transunion', 'experian', 'equifax']:
                    val = entry.get(bureau, '')
                    if val:
                        has_data = True
                        if val in ['30', '60', '90', '120', '150', '180']:
                            is_late = True
                        elif val == 'OK':
                            is_ok = True
                if has_data:
                    total_payments += 1
                    if is_late:
                        late_count += 1
                    elif is_ok:
                        on_time_count += 1
        
        # Calculate credit utilization
        total_balance = 0
        total_limit = 0
        for acct in parsed.get('accounts', []):
            balance_str = acct.get('balance', '') or ''
            limit_str = acct.get('credit_limit', '') or ''
            # Parse dollar amounts
            balance_clean = ''.join(c for c in balance_str if c.isdigit() or c == '.')
            limit_clean = ''.join(c for c in limit_str if c.isdigit() or c == '.')
            try:
                if balance_clean:
                    total_balance += float(balance_clean)
                if limit_clean:
                    total_limit += float(limit_clean)
            except:
                pass
        
        utilization = 0
        if total_limit > 0:
            utilization = round((total_balance / total_limit) * 100)
        
        # Payment score
        payment_score = 100
        if total_payments > 0:
            payment_score = round((on_time_count / total_payments) * 100)
        
        # Account age (simplified - would need date parsing for accurate)
        parsed['analytics'] = {
            'utilization': utilization,
            'total_balance': f"${total_balance:,.0f}",
            'total_limit': f"${total_limit:,.0f}" if total_limit > 0 else "N/A",
            'payment_score': payment_score,
            'on_time_count': on_time_count,
            'total_payments': total_payments,
            'avg_account_age': "N/A",  # Would need date parsing
            'oldest_account': "N/A",   # Would need date parsing
        }
        
        parsed['summary'] = {
            'total_accounts': len(parsed.get('accounts', [])),
            'total_inquiries': len(parsed.get('inquiries', [])),
            'total_collections': len(parsed.get('collections', [])),
            'total_public_records': len(parsed.get('public_records', [])),
            'total_late_payments': late_count,
        }
        
        return parsed
        
    except Exception as e:
        logger.error(f"Failed to parse credit report: {e}")
        return {
            'error': str(e),
            'scores': {'transunion': None, 'experian': None, 'equifax': None},
            'accounts': [],
            'inquiries': [],
            'public_records': [],
            'collections': [],
            'creditor_contacts': [],
            'summary': {},
        }
