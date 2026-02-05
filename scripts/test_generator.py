#!/usr/bin/env python3
"""
Auto-generate Cypress tests for new features by scanning templates and routes
"""

import os
import re
import anthropic
from pathlib import Path

def scan_routes(app_file='app.py'):
    """Extract all Flask routes from app.py"""
    routes = []
    with open(app_file, 'r') as f:
        content = f.read()

    # Find @app.route decorators
    pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
    matches = re.findall(pattern, content)
    return list(set(matches))

def scan_templates(template_dir='templates'):
    """Scan templates for testable elements"""
    elements = {}
    for filepath in Path(template_dir).glob('*.html'):
        with open(filepath, 'r') as f:
            content = f.read()

        # Find data-testid attributes
        testids = re.findall(r'data-testid="([^"]+)"', content)

        # Find form elements
        forms = re.findall(r'<form[^>]*id="([^"]+)"', content)

        # Find buttons with onclick
        buttons = re.findall(r'onclick="([^"(]+)\(', content)

        # Find input fields
        inputs = re.findall(r'<input[^>]*id="([^"]+)"', content)

        elements[filepath.name] = {
            'testids': testids,
            'forms': forms,
            'buttons': list(set(buttons)),
            'inputs': inputs
        }

    return elements

def get_existing_tests(test_dir='cypress/e2e'):
    """Get list of existing test files and what they cover"""
    tests = {}
    for filepath in Path(test_dir).glob('*.cy.js'):
        with open(filepath, 'r') as f:
            content = f.read()

        # Extract describe blocks
        describes = re.findall(r"describe\(['\"]([^'\"]+)['\"]", content)

        # Extract it blocks
        its = re.findall(r"it\(['\"]([^'\"]+)['\"]", content)

        tests[filepath.name] = {
            'describes': describes,
            'test_count': len(its),
            'tests': its
        }

    return tests

def generate_tests_for_template(template_name, elements, client=None):
    """Use Claude to generate tests for a template"""
    if not client:
        client = anthropic.Anthropic()

    prompt = f"""Generate Cypress E2E tests for this template: {template_name}

Elements found:
- data-testid attributes: {elements.get('testids', [])}
- Forms: {elements.get('forms', [])}
- Buttons/functions: {elements.get('buttons', [])}
- Input fields: {elements.get('inputs', [])}

Generate comprehensive Cypress tests that:
1. Test page load
2. Test all interactive elements
3. Test form submissions
4. Test error states
5. Test edge cases

Output ONLY the Cypress test code, no explanation.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

def find_untested_features():
    """Find features that don't have tests"""
    routes = scan_routes()
    templates = scan_templates()
    existing = get_existing_tests()

    # Check which templates have tests
    tested_templates = set()
    for test_file, data in existing.items():
        for desc in data['describes']:
            tested_templates.add(desc.lower())

    untested = []
    for template, elements in templates.items():
        template_name = template.replace('.html', '').replace('_', ' ')
        if template_name.lower() not in tested_templates:
            if elements['testids'] or elements['forms'] or elements['buttons']:
                untested.append({
                    'template': template,
                    'elements': elements
                })

    return untested

def main():
    print("🔍 Scanning for untested features...")

    untested = find_untested_features()

    if not untested:
        print("✅ All features appear to have tests!")
        return

    print(f"Found {len(untested)} templates without comprehensive tests:")
    for item in untested:
        print(f"  - {item['template']}")
        print(f"    Elements: {len(item['elements'].get('testids', []))} testids, "
              f"{len(item['elements'].get('buttons', []))} buttons, "
              f"{len(item['elements'].get('forms', []))} forms")

    # Generate tests for first untested template
    if untested:
        print(f"\n🔧 Generating tests for {untested[0]['template']}...")
        # Uncomment to actually generate:
        # tests = generate_tests_for_template(untested[0]['template'], untested[0]['elements'])
        # print(tests)

if __name__ == '__main__':
    main()
