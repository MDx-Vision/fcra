"""
Credit Report Parser Service
Parses HTML from credit monitoring services into structured three-bureau format.
"""
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CreditReportParser:
    """Parse credit report HTML into structured data."""
    
    def __init__(self, html_content: str, service_name: str = 'unknown'):
        self.html = html_content
        self.service = service_name
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def parse(self) -> Dict:
        """Parse the credit report and return structured data."""
        result = {
            'scores': self._extract_scores(),
            'personal_info': self._extract_personal_info(),
            'accounts': self._extract_accounts(),
            'inquiries': self._extract_inquiries(),
            'public_records': self._extract_public_records(),
            'collections': self._extract_collections(),
            'summary': self._extract_summary(),
        }
        return result
    
    def _extract_scores(self) -> Dict:
        """Extract credit scores for all three bureaus."""
        scores = {
            'transunion': None,
            'experian': None,
            'equifax': None,
        }
        
        text = self.soup.get_text()
        
        tu_patterns = [
            r'transunion[:\s]*(\d{3})',
            r'tu[:\s]*(\d{3})',
            r'trans\s*union[:\s]*(\d{3})',
        ]
        for pattern in tu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 850:
                    scores['transunion'] = score
                    break
        
        exp_patterns = [
            r'experian[:\s]*(\d{3})',
            r'exp[:\s]*(\d{3})',
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 850:
                    scores['experian'] = score
                    break
        
        eq_patterns = [
            r'equifax[:\s]*(\d{3})',
            r'eq[:\s]*(\d{3})',
        ]
        for pattern in eq_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 850:
                    scores['equifax'] = score
                    break
        
        score_elements = self.soup.find_all(class_=re.compile(r'score', re.I))
        for elem in score_elements:
            text = elem.get_text()
            class_names = ' '.join(elem.get('class', []))
            
            match = re.search(r'(\d{3})', text)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 850:
                    if 'transunion' in class_names.lower() or 'tuc' in class_names.lower():
                        scores['transunion'] = scores['transunion'] or score
                    elif 'experian' in class_names.lower() or 'exp' in class_names.lower():
                        scores['experian'] = scores['experian'] or score
                    elif 'equifax' in class_names.lower() or 'eqf' in class_names.lower():
                        scores['equifax'] = scores['equifax'] or score
        
        return scores
    
    def _extract_personal_info(self) -> Dict:
        """Extract personal information from report."""
        info = {
            'name': None,
            'address': None,
            'ssn_last4': None,
            'dob': None,
        }
        
        text = self.soup.get_text()
        
        name_match = re.search(r'name[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', text, re.I)
        if name_match:
            info['name'] = name_match.group(1)
        
        return info
    
    def _extract_accounts(self) -> List[Dict]:
        """Extract all tradeline accounts from Angular-rendered HTML."""
        accounts = []
        seen_creditors = set()
        
        sub_headers = self.soup.find_all('div', class_=re.compile(r'sub_header'))
        
        for header in sub_headers:
            text = header.get_text(strip=True)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\(Original Creditor:.*\)', '', text).strip()
            
            if not text or '{{' in text or len(text) < 3:
                continue
            
            skip_texts = ['THE', 'AND', 'FOR', 'CREDIT REPORT', 'WATCH', 'KNOW', 
                          'FICO', 'PLAN', 'YOUR', 'SCORE', 'REPORT', 'SUMMARY',
                          'SCORE FACTORS', 'FACTORS', 'INQUIRIES', 'COLLECTIONS',
                          'PUBLIC RECORDS', 'PERSONAL INFORMATION', 'SUBSCRIBER']
            if text.upper() in skip_texts or any(text.upper().startswith(s) for s in skip_texts):
                continue
            
            if text in seen_creditors:
                continue
            seen_creditors.add(text)
            
            account = {
                'creditor': text,
                'account_number': None,
                'account_type': None,
                'status': None,
                'balance': None,
                'credit_limit': None,
                'payment_status': None,
                'date_opened': None,
                'bureaus': {
                    'transunion': {'present': True},
                    'experian': {'present': True},
                    'equifax': {'present': True},
                }
            }
            
            parent = header.find_parent('ng-include') or header.parent
            table = None
            if parent:
                table = parent.find('table', class_=re.compile(r'rpt_content'))
            if not table:
                table = header.find_next_sibling('table')
            
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    label_cell = row.find('td', class_='label')
                    info_cells = row.find_all('td', class_=re.compile(r'info'))
                    
                    if label_cell and info_cells:
                        label = label_cell.get_text(strip=True).lower()
                        values = [cell.get_text(strip=True) for cell in info_cells]
                        
                        first_value = next((v for v in values if v and v != '-'), None)
                        
                        if 'account number' in label or label == 'number':
                            account['account_number'] = first_value
                            if len(values) >= 3:
                                if values[0] and values[0] != '-':
                                    account['bureaus']['transunion']['number'] = values[0]
                                if values[1] and values[1] != '-':
                                    account['bureaus']['experian']['number'] = values[1]
                                if values[2] and values[2] != '-':
                                    account['bureaus']['equifax']['number'] = values[2]
                        
                        elif 'classification' in label or 'type' in label:
                            account['account_type'] = first_value
                            if len(values) >= 3:
                                if values[0] and values[0] != '-':
                                    account['bureaus']['transunion']['type'] = values[0]
                                if values[1] and values[1] != '-':
                                    account['bureaus']['experian']['type'] = values[1]
                                if values[2] and values[2] != '-':
                                    account['bureaus']['equifax']['type'] = values[2]
                        
                        elif 'status' in label or 'condition' in label:
                            account['status'] = first_value
                        
                        elif 'balance' in label:
                            account['balance'] = first_value
                        
                        elif 'credit limit' in label or 'high credit' in label:
                            account['credit_limit'] = first_value
            
            accounts.append(account)
        
        if not accounts:
            self._extract_accounts_fallback(accounts)
        
        return accounts
    
    def _extract_accounts_fallback(self, accounts: List[Dict]) -> None:
        """Fallback account extraction using generic patterns."""
        text = self.soup.get_text()
        
        creditor_pattern = r'(?:^|\n)([A-Z][A-Z\s&\'\./-]+(?:BANK|CARD|AUTO|MORTGAGE|LOAN|CREDIT|FINANCIAL|SERVICES|USA|NA))'
        matches = re.findall(creditor_pattern, text)
        
        seen = set()
        for creditor in matches[:30]:
            creditor = creditor.strip()
            if len(creditor) > 5 and creditor not in seen:
                seen.add(creditor)
                accounts.append({
                    'creditor': creditor,
                    'account_number': 'N/A',
                    'account_type': 'Unknown',
                    'status': 'Unknown',
                    'balance': None,
                    'credit_limit': None,
                    'payment_status': None,
                    'date_opened': None,
                    'bureaus': {
                        'transunion': {'present': True},
                        'experian': {'present': True},
                        'equifax': {'present': True},
                    }
                })
    
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
                    
                    key = f"{creditor}_{date}"
                    if key not in seen and creditor:
                        seen.add(key)
                        inquiries.append({
                            'creditor': creditor,
                            'type': inquiry_type,
                            'date': date,
                            'bureau': bureau,
                        })
        
        if not inquiries:
            text = self.soup.get_text()
            inquiry_section = re.search(r'inquir(?:y|ies)(.*?)(?:public records|collections|creditor contacts|$)', text, re.I | re.S)
            if inquiry_section:
                section_text = inquiry_section.group(1)
                date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
                dates = re.findall(date_pattern, section_text)
                for date in dates[:20]:
                    inquiries.append({
                        'date': date,
                        'creditor': 'Unknown',
                        'type': 'Hard Inquiry',
                    })
        
        return inquiries
    
    def _extract_public_records(self) -> List[Dict]:
        """Extract public records (bankruptcies, judgments, etc.)."""
        records = []
        
        text = self.soup.get_text().lower()
        
        if 'bankruptcy' in text:
            records.append({
                'type': 'Bankruptcy',
                'status': 'Found in report',
                'date': None,
            })
        
        if 'judgment' in text or 'civil judgment' in text:
            records.append({
                'type': 'Civil Judgment',
                'status': 'Found in report',
                'date': None,
            })
        
        if 'tax lien' in text:
            records.append({
                'type': 'Tax Lien',
                'status': 'Found in report',
                'date': None,
            })
        
        return records
    
    def _extract_collections(self) -> List[Dict]:
        """Extract collection accounts."""
        collections = []
        
        text = self.soup.get_text()
        collection_section = re.search(r'collection(.*?)(?:inquir|public|$)', text, re.I | re.S)
        
        if collection_section:
            section_text = collection_section.group(1)
            amount_pattern = r'\$[\d,]+\.?\d*'
            amounts = re.findall(amount_pattern, section_text)
            
            for amount in amounts[:10]:
                collections.append({
                    'agency': 'Collection Agency',
                    'original_creditor': 'Unknown',
                    'amount': amount,
                    'status': 'Open',
                })
        
        return collections
    
    def _extract_summary(self) -> Dict:
        """Extract summary statistics."""
        return {
            'total_accounts': len(self._extract_accounts()),
            'total_inquiries': len(self._extract_inquiries()),
            'total_collections': len(self._extract_collections()),
            'total_public_records': len(self._extract_public_records()),
        }


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
                        'account_number': acct.get('account_number', 'N/A'),
                        'account_type': acct.get('account_type', 'Unknown'),
                        'status': acct.get('status', 'Unknown'),
                        'balance': acct.get('balance'),
                        'credit_limit': acct.get('credit_limit'),
                        'payment_status': acct.get('payment_status'),
                        'date_opened': acct.get('date_opened'),
                        'bureaus': acct.get('bureaus', {
                            'transunion': True,
                            'experian': True,
                            'equifax': True,
                        })
                    })
            
            if extracted_data.get('inquiries') and len(extracted_data['inquiries']) > 0:
                parsed['inquiries'] = extracted_data['inquiries']
            
            if extracted_data.get('collections') and len(extracted_data['collections']) > 0:
                parsed['collections'] = extracted_data['collections']
            
            if extracted_data.get('public_records') and len(extracted_data['public_records']) > 0:
                parsed['public_records'] = extracted_data['public_records']
        
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
            'summary': {},
        }
