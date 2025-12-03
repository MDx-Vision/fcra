"""
Claude AI Assistant for Exhaustive E2E Test Generation and Auto-Fixing
Generates 30-50+ comprehensive tests per feature with full edge case coverage
"""

import os
import sys
import json
import re
import subprocess
from anthropic import Anthropic

MAX_CONTEXT_CHARS = 50000
MAX_ERROR_LOG_CHARS = 10000

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

EXHAUSTIVE_TEST_GENERATION_PROMPT = """You are an expert Cypress E2E test engineer. Your job is to generate EXHAUSTIVE, COMPREHENSIVE test suites that achieve production-grade coverage.

## CRITICAL REQUIREMENTS - YOU MUST FOLLOW ALL OF THESE:

### Test Quantity Requirements:
- Generate 30-50+ test cases per feature/module
- Every possible user interaction must be tested
- Every form field must have 5+ validation tests
- Every button, link, and clickable element must be tested

### Coverage Requirements:
1. **Happy Path Tests** (5-10 tests per feature)
   - Standard successful workflows
   - All variations of valid input

2. **Negative/Error Tests** (10-15 tests per feature)
   - Empty field submissions
   - Invalid data formats (emails, phones, dates, SSNs)
   - Boundary conditions (min/max lengths)
   - SQL injection attempts
   - XSS attempts
   - Special characters in all fields

3. **Role-Based Tests** (5-10 tests per feature)
   - Admin user access and actions
   - Manager user access and actions
   - Staff user access and actions
   - Unauthorized access attempts
   - Permission boundaries

4. **State Tests** (5-10 tests per feature)
   - Empty state (no data)
   - Single item state
   - Many items state (pagination)
   - Loading states
   - Error states

5. **Edge Case Tests** (5-10 tests per feature)
   - Very long input strings
   - Unicode characters
   - Concurrent operations
   - Network timeout handling
   - Session expiration

### Test Structure Requirements:
- Use descriptive test names that explain what is being tested
- Group related tests in describe blocks by feature area
- Use beforeEach for common setup
- Include data-cy attributes in your analysis
- Add comments explaining complex test logic

### Assertion Requirements:
- Every test must have 3+ assertions minimum
- Check URL changes after navigation
- Verify success/error messages appear
- Confirm data persistence (check it's actually saved)
- Validate UI state changes (buttons disabled, loading indicators)

## CURRENT APPLICATION CONTEXT:

This is a Flask/Python FCRA (Fair Credit Reporting Act) litigation platform with:

**Models:**
- Staff (users): id, name, email, role (admin/manager/staff), password
- Client: id, first_name, last_name, email, phone, address, city, state, zip_code, ssn_last_four, date_of_birth, staff_id
- Case: id, client_id, case_type, status, description, bureau, creditor
- Violation: id, case_id, violation_type, description, statute, damages_estimate
- Analysis: id, case_id, analysis_type, findings, recommendations
- DisputeLetter: id, case_id, letter_type, recipient, content, status

**Test Data Available:**
- Admin: test@example.com / testpass123
- Test Client: John Doe (ID 1)

## OUTPUT FORMAT:

Return ONLY valid JavaScript code for Cypress tests. No explanations, no markdown code blocks, just the raw JavaScript.

Start with:
/// <reference types="cypress" />

## ANALYZE THIS CODE AND GENERATE EXHAUSTIVE TESTS:

{code_content}

Remember: 30-50+ tests minimum. Test EVERYTHING. Miss nothing. Production-grade quality."""


EXHAUSTIVE_FIX_PROMPT = """You are an expert at fixing code to make Cypress E2E tests pass. Analyze the failing test and fix the application code.

## ERROR LOG:
{error_log}

## RELEVANT CODE (file that needs fixing):
{app_code}

## INSTRUCTIONS:
1. Identify the root cause of the failure
2. Determine if it's a CODE issue or a TEST issue
3. Fix the appropriate file

## OUTPUT FORMAT:
Return a JSON object with this exact structure:
{{
    "diagnosis": "Brief explanation of what's wrong",
    "fix_type": "code" or "test",
    "file_path": "path/to/file/to/fix",
    "original_code": "the exact code segment to replace",
    "fixed_code": "the corrected code segment"
}}

Return ONLY the JSON object, no other text."""


def truncate_content(content, max_chars=MAX_CONTEXT_CHARS):
    """Truncate content to max characters with a note"""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + f"\n\n... [TRUNCATED - {len(content) - max_chars} chars removed]"


def get_all_python_files():
    python_files = []
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', 'ci_helpers'}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def get_all_template_files():
    template_files = []
    if os.path.exists('./templates'):
        for root, dirs, files in os.walk('./templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
    return template_files


def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {filepath}: {e}"


def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)


def get_changed_files():
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True, text=True
        )
        return [f for f in result.stdout.strip().split('\n') if f]
    except:
        return []


def extract_failing_file_from_error(error_log):
    """Extract the specific file that's failing from error log"""
    patterns = [
        r'at\s+(?:Object\.)?<anonymous>\s+\(([^:]+):',
        r'Error:.*?(?:in|at)\s+([^\s:]+\.(?:py|js|ts|html))',
        r'File\s+"([^"]+)"',
        r'cypress/e2e/([^\s:]+\.cy\.js)',
        r'([^\s]+\.(?:py|js|ts|html)):\d+:\d+',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, error_log)
        if matches:
            for match in matches:
                if os.path.exists(match):
                    return match
                if match.startswith('cypress/') and os.path.exists(match):
                    return match
    
    return None


def generate_tests_for_new_features():
    changed_files = get_changed_files()
    relevant_changes = [f for f in changed_files if f.endswith('.py') or f.endswith('.html')]
    
    if not relevant_changes:
        print("No relevant changes detected, skipping test generation")
        return
    
    print(f"Generating exhaustive tests for: {relevant_changes}")
    
    all_code = []
    total_chars = 0
    
    for filepath in relevant_changes[:5]:
        if os.path.exists(filepath):
            content = read_file(filepath)
            if total_chars + len(content) < MAX_CONTEXT_CHARS:
                all_code.append(f"\n\n=== {filepath} ===\n{content}")
                total_chars += len(content)
    
    for template in get_all_template_files()[:3]:
        content = read_file(template)
        if total_chars + len(content) < MAX_CONTEXT_CHARS:
            all_code.append(f"\n\n=== {template} ===\n{content}")
            total_chars += len(content)
    
    combined_code = truncate_content('\n'.join(all_code))
    feature_name = changed_files[0].replace('.py', '').replace('/', '_').replace('.', '_')
    
    print(f"Sending {len(combined_code)} characters to API...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": EXHAUSTIVE_TEST_GENERATION_PROMPT.format(code_content=combined_code)
        }]
    )
    
    test_code = response.content[0].text
    if test_code.startswith('```'):
        test_code = test_code.split('\n', 1)[1]
        test_code = test_code.rsplit('```', 1)[0]
    
    timestamp = subprocess.run(['date', '+%Y%m%d_%H%M%S'], capture_output=True, text=True).stdout.strip()
    test_filename = f"cypress/e2e/auto_{feature_name}_{timestamp}.cy.js"
    
    write_file(test_filename, test_code)
    print(f"Generated exhaustive test file: {test_filename}")
    return test_filename


def generate_tests_for_entire_app():
    print("Generating exhaustive tests for ENTIRE application...")
    
    modules = [
        ('authentication', 'login, logout, session management', ['app.py']),
        ('clients', 'client CRUD, listing, search', ['app.py']),
        ('cases', 'case CRUD, status, assignment', ['app.py']),
        ('violations', 'violation CRUD, types, statutes', ['app.py']),
        ('analysis', 'analysis CRUD, findings', ['app.py']),
        ('dispute_letters', 'letter generation, CRUD', ['app.py']),
        ('staff', 'staff management, roles', ['app.py']),
        ('dashboard', 'widgets, statistics', ['app.py']),
    ]
    
    generated_files = []
    
    for module_name, module_desc, relevant_files in modules:
        print(f"Generating tests for: {module_name}")
        
        all_code = []
        total_chars = 0
        
        for filepath in relevant_files:
            if os.path.exists(filepath):
                content = read_file(filepath)
                if total_chars + len(content) < MAX_CONTEXT_CHARS:
                    all_code.append(f"\n\n=== {filepath} ===\n{content}")
                    total_chars += len(content)
                else:
                    all_code.append(f"\n\n=== {filepath} (truncated) ===\n{content[:MAX_CONTEXT_CHARS - total_chars]}")
                    break
        
        combined_code = truncate_content('\n'.join(all_code))
        
        module_prompt = f"Focus on {module_name.upper()} ({module_desc}). Generate 30-50+ exhaustive tests.\n\n{EXHAUSTIVE_TEST_GENERATION_PROMPT.format(code_content=combined_code)}"
        
        print(f"Sending {len(module_prompt)} characters to API...")
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": module_prompt}]
        )
        
        test_code = response.content[0].text
        if test_code.startswith('```'):
            test_code = test_code.split('\n', 1)[1]
            test_code = test_code.rsplit('```', 1)[0]
        
        test_filename = f"cypress/e2e/{module_name}_exhaustive.cy.js"
        write_file(test_filename, test_code)
        generated_files.append(test_filename)
        print(f"Generated: {test_filename}")
    
    print(f"\nGenerated {len(generated_files)} exhaustive test files")
    return generated_files


def fix_failing_tests(error_log_path, screenshot_path=None):
    """Fix failing tests by analyzing ONLY the error and the specific failing file"""
    
    error_log = ""
    if os.path.exists(error_log_path):
        error_log = read_file(error_log_path)
    else:
        print(f"Error log not found: {error_log_path}")
        return False
    
    error_log = truncate_content(error_log, MAX_ERROR_LOG_CHARS)
    print(f"Error log: {len(error_log)} characters")
    
    failing_file = extract_failing_file_from_error(error_log)
    
    if failing_file and os.path.exists(failing_file):
        print(f"Identified failing file: {failing_file}")
        file_content = read_file(failing_file)
        code_context = truncate_content(f"=== {failing_file} ===\n{file_content}", MAX_CONTEXT_CHARS)
    else:
        print("Could not identify specific failing file, using minimal context")
        code_context = "Unable to identify specific file. Please analyze the error log to determine the fix."
    
    total_prompt_size = len(error_log) + len(code_context) + len(EXHAUSTIVE_FIX_PROMPT)
    print(f"Total prompt size: {total_prompt_size} characters")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": EXHAUSTIVE_FIX_PROMPT.format(error_log=error_log, app_code=code_context)
        }]
    )
    
    fix_response = response.content[0].text
    if fix_response.startswith('```'):
        fix_response = fix_response.split('\n', 1)[1]
        fix_response = fix_response.rsplit('```', 1)[0]
    
    try:
        fix_data = json.loads(fix_response)
        print(f"Diagnosis: {fix_data['diagnosis']}")
        print(f"Fixing: {fix_data['file_path']}")
        
        file_content = read_file(fix_data['file_path'])
        fixed_content = file_content.replace(fix_data['original_code'], fix_data['fixed_code'])
        write_file(fix_data['file_path'], fixed_content)
        print(f"Applied fix to {fix_data['file_path']}")
        return True
    except json.JSONDecodeError as e:
        print(f"Failed to parse fix response: {e}")
        print(f"Response was: {fix_response[:500]}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python claude_assistant.py [generate|generate-all|fix]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        generate_tests_for_new_features()
    elif command == "generate-all":
        generate_tests_for_entire_app()
    elif command == "fix":
        error_log = sys.argv[2] if len(sys.argv) > 2 else "cypress/logs/error.log"
        fix_failing_tests(error_log)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
