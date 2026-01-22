"""
FCRA v2.8 Dynamic Prompt Loader
Loads prompts from /knowledge folder - no more hardcoded content
"""

import os
from pathlib import Path

class PromptLoader:
    """Dynamically loads FCRA prompts from the knowledge folder"""

    # Map shortcuts to knowledge files
    PROMPT_FILES = {
        # Core workflows
        'full': 'SUPER_PROMPT_V2_8_COMPLETE_SEPARATE_FILES.md',
        'r1': 'FCRA_PROMPT_02_ROUND1_LETTERS_SEPARATE_FILES.md',
        'r2': 'FCRA_PROMPT_03_ROUND2_MOV_SEPARATE_FILES.md',
        'r3': 'FCRA_PROMPT_04_ROUND3_REGULATORY_SEPARATE_FILES.md',
        'r4': 'FCRA_PROMPT_05_ROUND4_PRE_ARB_SEPARATE_FILES.md',

        # Quick actions
        'quick': 'FCRA_PROMPT_06_QUICK_SINGLE_LETTER_SEPARATE_FILE.md',
        'secondary': 'FCRA_PROMPT_07_SECONDARY_BUREAUS_SEPARATE_FILES.md',
        'secdispute': 'FCRA_PROMPT_08_SECONDARY_DISPUTE_SEPARATE_FILES.md',
        'pii': 'FCRA_PROMPT_09_CRA_PII_CORRECTION_SEPARATE_FILES.md',
        'validation': 'FCRA_PROMPT_10_COLLECTION_VALIDATION_SEPARATE_FILES.md',

        # Reports
        'clientreport': 'FCRA_PROMPT_11_CLIENT_REPORT.md',
        'internalanalysis': 'FCRA_PROMPT_12_INTERNAL_ANALYSIS.md',
        'lawyerpackage': 'FCRA_PROMPT_13_LAWYER_READY_PACKAGE.md',

        # Identity theft & inquiries
        'idtheft': 'FCRA_PROMPT_14_IDENTITY_THEFT_SEPARATE_FILES.md',
        'inquiry': 'FCRA_PROMPT_15A_INQUIRY_PERMISSIBLE_PURPOSE.md',
        'inquirytheft': 'FCRA_PROMPT_15B_INQUIRY_IDENTITY_THEFT.md',
        'portalfix': 'FCRA_PROMPT_16_PORTAL_QUICK_FIX.md',
        '5dayknockout': 'FCRA_PROMPT_17_v6_5DAY_KNOCKOUT_ONLINE_MAIL.md',

        # Reference docs
        'framework': 'FCRA_Litigation_Framework_Complete_v2_0__3_.md',
        'workflow': 'FCRA_WORKFLOW_CHEAT_SHEET.md',
        'checklist': 'FCRA-Violation-Spotter-Checklist.md',
        'quickref': 'FCRA-Quick-Reference-Guide.md',
        'intake': 'FCRA-Case-Intake-Template.md',
    }

    def __init__(self, knowledge_path=None):
        """Initialize with path to knowledge folder"""
        if knowledge_path is None:
            possible_paths = [
                'knowledge',
                './knowledge',
                '/home/runner/workspace/knowledge',
                os.path.join(os.path.dirname(__file__), 'knowledge'),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    knowledge_path = path
                    break

        self.knowledge_path = Path(knowledge_path) if knowledge_path else Path('knowledge')

        if not self.knowledge_path.exists():
            print(f"⚠️ Warning: Knowledge folder not found at {self.knowledge_path}")

    def load_prompt(self, shortcut):
        """Load a prompt file by shortcut name"""
        shortcut = shortcut.lower().strip()

        if shortcut not in self.PROMPT_FILES:
            available = ', '.join(sorted(self.PROMPT_FILES.keys()))
            raise ValueError(f"Unknown shortcut '{shortcut}'. Available: {available}")

        filename = self.PROMPT_FILES[shortcut]
        filepath = self.knowledge_path / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def load_file(self, filename):
        """Load any file from knowledge folder by filename"""
        filepath = self.knowledge_path / filename

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def list_available_prompts(self):
        """List all available prompt shortcuts"""
        return list(self.PROMPT_FILES.keys())

    def list_knowledge_files(self):
        """List all files in knowledge folder"""
        if not self.knowledge_path.exists():
            return []
        return [f.name for f in self.knowledge_path.iterdir() if f.is_file()]

    def get_prompt_info(self, shortcut):
        """Get info about a prompt shortcut"""
        shortcut = shortcut.lower().strip()
        if shortcut not in self.PROMPT_FILES:
            return None

        filename = self.PROMPT_FILES[shortcut]
        filepath = self.knowledge_path / filename

        return {
            'shortcut': shortcut,
            'filename': filename,
            'exists': filepath.exists(),
            'path': str(filepath),
            'size': filepath.stat().st_size if filepath.exists() else 0
        }

    # =========================================================================
    # CONVENIENCE METHODS - Match old API for backward compatibility
    # =========================================================================

    def build_comprehensive_stage2_prompt(self, dispute_round=1):
        """
        DEPRECATED: Use load_prompt('full') or load_prompt('r1') etc.
        Maintained for backward compatibility - loads from knowledge folder now
        """
        round_map = {1: 'r1', 2: 'r2', 3: 'r3', 4: 'r4'}
        shortcut = round_map.get(dispute_round, 'r1')

        try:
            return self.load_prompt(shortcut)
        except FileNotFoundError:
            return self.load_prompt('full')

    def get_round_prompt(self, round_number):
        """Get dispute letter prompt for specific round (1-4)"""
        round_map = {1: 'r1', 2: 'r2', 3: 'r3', 4: 'r4'}
        shortcut = round_map.get(round_number, 'r1')
        return self.load_prompt(shortcut)

    def get_client_report_prompt(self):
        """Get the 40-50 page client report prompt"""
        return self.load_prompt('clientreport')

    def get_internal_analysis_prompt(self):
        """Get the 3-5 page staff analysis prompt"""
        return self.load_prompt('internalanalysis')

    def get_lawyer_package_prompt(self, include_templates=True):
        """
        Get the complete 4-document lawyer-ready package prompt

        Args:
            include_templates: If True, embeds the actual HTML reference templates
        """
        prompt = self.load_prompt('lawyerpackage')

        if include_templates:
            # Embed the reference HTML templates into the prompt
            template_files = [
                'templates/reference/Internal_Analysis_PERDOMO_WE_12122025.html',
                'templates/reference/Email_Client_PERDOMO_WE_12122025.html',
                'templates/reference/Client_Report_PERDOMO_WE_12122025.html',
                'templates/reference/Legal_Memorandum_PERDOMO_WE_12122025.html'
            ]

            embedded_templates = "\n\n## REFERENCE HTML TEMPLATES\n\n"
            embedded_templates += "Use these as styling and structure references:\n\n"

            for template_path in template_files:
                try:
                    # Try to read from project root
                    full_path = Path(template_path)
                    if not full_path.exists():
                        # Try relative to knowledge folder
                        full_path = self.knowledge_path.parent / template_path

                    if full_path.exists():
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        template_name = full_path.name
                        embedded_templates += f"\n### {template_name}\n\n```html\n{content}\n```\n\n"
                except Exception as e:
                    print(f"⚠️ Could not load template {template_path}: {e}")

            prompt += embedded_templates

        return prompt

    def get_litigation_framework(self):
        """Get the 36K word litigation framework with 210+ cases"""
        return self.load_prompt('framework')

    def get_5day_knockout_prompt(self):
        """Get the 5-Day Knock-Out identity theft dispute prompt (§605B)"""
        return self.load_prompt('5dayknockout')

    def get_identity_theft_prompt(self):
        """Get the identity theft dispute prompt (Prompt 14)"""
        return self.load_prompt('idtheft')

    def get_inquiry_dispute_prompt(self, identity_theft=False):
        """Get inquiry dispute prompt - permissible purpose (15A) or identity theft (15B)"""
        return self.load_prompt('inquirytheft' if identity_theft else 'inquiry')

    def get_portal_quick_fix_prompt(self):
        """Get the portal quick fix prompt for fast PII/inquiry disputes"""
        return self.load_prompt('portalfix')

    def get_violation_checklist(self):
        """Get the violation spotter checklist"""
        return self.load_prompt('checklist')

    def get_workflow_cheatsheet(self):
        """Get the workflow cheat sheet"""
        return self.load_prompt('workflow')


def get_prompt_loader(knowledge_path=None):
    """Factory function to get PromptLoader instance"""
    return PromptLoader(knowledge_path)


if __name__ == '__main__':
    loader = PromptLoader()

    print("=" * 60)
    print("FCRA PROMPT LOADER v2.8")
    print("=" * 60)
    print(f"\nKnowledge folder: {loader.knowledge_path}")
    print(f"Folder exists: {loader.knowledge_path.exists()}")

    print("\n📋 AVAILABLE SHORTCUTS:")
    print("-" * 40)

    categories = {
        'Core Workflows': ['full', 'r1', 'r2', 'r3', 'r4'],
        'Quick Actions': ['quick', 'secondary', 'secdispute', 'pii', 'validation'],
        'Reports': ['clientreport', 'internalanalysis', 'lawyerpackage'],
        'Identity Theft & Inquiries': ['idtheft', 'inquiry', 'inquirytheft', 'portalfix', '5dayknockout'],
        'Reference': ['framework', 'workflow', 'checklist', 'quickref', 'intake']
    }

    for category, shortcuts in categories.items():
        print(f"\n{category}:")
        for sc in shortcuts:
            info = loader.get_prompt_info(sc)
            status = "✓" if info['exists'] else "✗"
            print(f"  {status} {sc:20} → {info['filename']}")

    print("\n" + "=" * 60)