#!/usr/bin/env python3
"""
Claude AI Test Generation Assistant for Cypress E2E Tests

Commands:
  generate     - Generate a single test for a specific feature
  generate-all - Generate tests for all major features
  fix          - Analyze and fix failing tests

Usage:
  python ci_helpers/claude_assistant.py generate --feature "staff login"
  python ci_helpers/claude_assistant.py generate-all
  python ci_helpers/claude_assistant.py fix --test "cypress/e2e/login.cy.js" --error "element not found"
"""

import os
import sys
import argparse
import json
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


def get_client():
    """Initialize Anthropic client"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    return Anthropic(api_key=api_key)


def read_app_routes():
    """Read app.py to extract route information"""
    app_path = Path(__file__).parent.parent / 'app.py'
    if not app_path.exists():
        return "Could not read app.py"
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    routes = []
    for line in content.split('\n'):
        if '@app.route' in line:
            routes.append(line.strip())
    
    return '\n'.join(routes[:100])


def read_existing_tests():
    """Read existing Cypress test files"""
    tests_dir = Path(__file__).parent.parent / 'cypress' / 'e2e'
    if not tests_dir.exists():
        return "No existing tests found"
    
    tests = []
    for test_file in tests_dir.glob('*.cy.js'):
        with open(test_file, 'r') as f:
            tests.append(f"// {test_file.name}\n{f.read()[:2000]}")
    
    return '\n\n'.join(tests)


def generate_test(feature: str):
    """Generate a Cypress test for a specific feature"""
    client = get_client()
    
    routes = read_app_routes()
    existing_tests = read_existing_tests()
    
    prompt = f"""You are a Cypress E2E test expert. Generate a comprehensive Cypress test for the following feature.

FEATURE TO TEST: {feature}

AVAILABLE ROUTES (from app.py):
{routes}

EXISTING TEST EXAMPLES:
{existing_tests}

REQUIREMENTS:
1. Use Cypress best practices
2. Include proper selectors (data-cy attributes preferred, or CSS selectors)
3. Handle authentication if needed (session management)
4. Include positive and negative test cases
5. Add appropriate assertions
6. Use beforeEach for setup
7. Clean up any test data created

Generate a complete, working Cypress test file. Output ONLY the JavaScript code, no explanations."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    test_code = response.content[0].text
    
    if test_code.startswith('```'):
        lines = test_code.split('\n')
        test_code = '\n'.join(lines[1:-1])
    
    feature_slug = feature.lower().replace(' ', '_').replace('-', '_')
    output_path = Path(__file__).parent.parent / 'cypress' / 'e2e' / f'{feature_slug}.cy.js'
    
    with open(output_path, 'w') as f:
        f.write(test_code)
    
    print(f"✅ Generated test: {output_path}")
    return output_path


def generate_all_tests():
    """Generate tests for all major platform features"""
    features = [
        "staff login authentication",
        "client management CRUD",
        "dashboard navigation",
        "frivolousness tracker",
        "suspense accounts detection",
        "violation patterns",
        "analytics dashboard",
        "settlement tracking"
    ]
    
    generated = []
    for feature in features:
        try:
            path = generate_test(feature)
            generated.append(str(path))
        except Exception as e:
            print(f"❌ Failed to generate test for {feature}: {e}")
    
    print(f"\n✅ Generated {len(generated)} tests")
    return generated


def fix_test(test_file: str, error_message: str):
    """Analyze and fix a failing test"""
    client = get_client()
    
    test_path = Path(test_file)
    if not test_path.exists():
        print(f"Error: Test file not found: {test_file}")
        sys.exit(1)
    
    with open(test_path, 'r') as f:
        test_code = f.read()
    
    routes = read_app_routes()
    
    prompt = f"""You are a Cypress E2E test debugging expert. A test is failing and needs to be fixed.

FAILING TEST FILE: {test_file}
ERROR MESSAGE: {error_message}

CURRENT TEST CODE:
{test_code}

AVAILABLE ROUTES (from app.py):
{routes}

REQUIREMENTS:
1. Identify the root cause of the failure
2. Fix the test code
3. Ensure proper selectors and timing
4. Add cy.wait() if needed for async operations
5. Verify correct element visibility before interaction

Provide:
1. Brief explanation of what was wrong
2. The complete fixed test code

Format your response as:
EXPLANATION:
[Your explanation here]

FIXED CODE:
```javascript
[Fixed test code here]
```"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.content[0].text
    
    print("\n" + "="*60)
    print("ANALYSIS AND FIX")
    print("="*60)
    
    if "FIXED CODE:" in result:
        parts = result.split("FIXED CODE:")
        print(parts[0])
        
        code_part = parts[1]
        if '```' in code_part:
            lines = code_part.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith('```javascript'):
                    in_code = True
                    continue
                elif line.strip() == '```':
                    in_code = False
                    continue
                if in_code:
                    code_lines.append(line)
            fixed_code = '\n'.join(code_lines)
        else:
            fixed_code = code_part.strip()
        
        backup_path = test_path.with_suffix('.cy.js.bak')
        with open(backup_path, 'w') as f:
            f.write(test_code)
        print(f"📁 Backed up original to: {backup_path}")
        
        with open(test_path, 'w') as f:
            f.write(fixed_code)
        print(f"✅ Fixed test saved to: {test_path}")
    else:
        print(result)
    
    return test_path


def main():
    parser = argparse.ArgumentParser(
        description='Claude AI Test Generation Assistant for Cypress E2E Tests'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    gen_parser = subparsers.add_parser('generate', help='Generate a test for a specific feature')
    gen_parser.add_argument('--feature', '-f', required=True, help='Feature to generate test for')
    
    subparsers.add_parser('generate-all', help='Generate tests for all major features')
    
    fix_parser = subparsers.add_parser('fix', help='Analyze and fix a failing test')
    fix_parser.add_argument('--test', '-t', required=True, help='Path to failing test file')
    fix_parser.add_argument('--error', '-e', required=True, help='Error message from test failure')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        generate_test(args.feature)
    elif args.command == 'generate-all':
        generate_all_tests()
    elif args.command == 'fix':
        fix_test(args.test, args.error)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
