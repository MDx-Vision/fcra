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
                    if v and v != '-' and v.isdigit():
                        counts['collections'] = max(counts['collections'], int(v))
                        break
            
            elif 'public record' in label:
                for v in values:
                    if v and v != '-' and v.isdigit():
                        counts['public_records'] = max(counts['public_records'], int(v))
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
        
        score_section = self.soup.find('div', id='CreditScore')
        if score_section:
            tables = score_section.find_all('table')
            for table in tables:
                text = table.get_text()
                
                if 'transunion' in text.lower():
                    match = re.search(r'(\d{3})', text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores['transunion'] = score
                
                elif 'experian' in text.lower():
                    match = re.search(r'(\d{3})', text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores['experian'] = score
                
                elif 'equifax' in text.lower():
                    match = re.search(r'(\d{3})', text)
                    if match:
                        score = int(match.group(1))
                        if 300 <= score <= 850:
                            scores['equifax'] = score
        
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
            
            if text in seen_creditors:
                continue
            seen_creditors.add(text)
            
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
                'payment_history': [],
                'bureaus': {
                    'transunion': {'present': False},
                    'experian': {'present': False},
                    'equifax': {'present': False},
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
                        
                        elif 'credit limit' in label:
                            account['credit_limit'] = first_value
                        
                        elif 'high balance' in label or 'high credit' in label:
                            account['high_balance'] = first_value
                        
                        elif 'monthly payment' in label:
                            account['monthly_payment'] = first_value
                        
                        elif 'date opened' in label:
                            account['date_opened'] = first_value
                        
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
            
            payment_history = self._extract_payment_history_for_account(parent or header)
            if payment_history:
                account['payment_history'] = payment_history
            
            accounts.append(account)
        
        return accounts
    
    def _extract_payment_history_for_account(self, parent_element) -> List[Dict]:
        """Extract 2-year payment history grid for an account."""
        history = []
        
        history_tables = parent_element.find_all('table', class_=re.compile(r'addr_hsrty'))
        
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
                
                first_cell = cells[0].get_text(strip=True).lower()
                values = [cell.get_text(strip=True) for cell in cells[1:]]
                
                if 'month' in first_cell:
                    months = values
                elif 'year' in first_cell:
                    years = values
                elif 'transunion' in first_cell:
                    tu_status = values
                elif 'experian' in first_cell:
                    exp_status = values
                elif 'equifax' in first_cell:
                    eqf_status = values
            
            for i in range(min(len(months), len(years))):
                entry = {
                    'month': months[i] if i < len(months) else None,
                    'year': years[i] if i < len(years) else None,
                    'transunion': tu_status[i] if i < len(tu_status) else None,
                    'experian': exp_status[i] if i < len(exp_status) else None,
                    'equifax': eqf_status[i] if i < len(eqf_status) else None,
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
            
            if extracted_data.get('accounts') and len(extracted_data['accounts']) > 0:
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
        
        parsed['summary'] = {
            'total_accounts': len(parsed.get('accounts', [])),
            'total_inquiries': len(parsed.get('inquiries', [])),
            'total_collections': len(parsed.get('collections', [])),
            'total_public_records': len(parsed.get('public_records', [])),
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
