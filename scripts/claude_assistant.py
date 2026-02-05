#!/usr/bin/env python3
"""
Claude Auto-Fix Assistant
Analyzes test failures and generates fixes using Claude API
"""

import os
import sys
import json
import anthropic
from pathlib import Path

def get_relevant_files(error_text):
    """Extract file paths mentioned in error output"""
    files = set()
    keywords = ['.py', '.html', '.js', '.cy.js']

    for line in error_text.split('\n'):
        for kw in keywords:
            if kw in line:
                # Extract path
                parts = line.split()
                for part in parts:
                    if kw in part:
                        # Clean up path
                        path = part.strip('():,\'"')
                        if os.path.exists(path):
                            files.add(path)

    # Also check common locations
    common_files = [
        'templates/credit_report_view.html',
        'services/credit_report_parser.py',
        'app.py'
    ]
    for f in common_files:
        if os.path.exists(f):
            files.add(f)

    return list(files)[:5]  # Limit to 5 files

def read_file_content(filepath, max_lines=200):
    """Read file content, truncated if too long"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if len(lines) > max_lines:
                return ''.join(lines[:100]) + '\n... [truncated] ...\n' + ''.join(lines[-100:])
            return ''.join(lines)
    except:
        return f"[Could not read {filepath}]"

def analyze_and_fix(error_output):
    """Send error to Claude and get fix"""
    client = anthropic.Anthropic()

    # Get relevant files
    relevant_files = get_relevant_files(error_output)
    file_contents = {f: read_file_content(f) for f in relevant_files}

    prompt = f"""You are a QA automation engineer. Analyze this test failure and provide a fix.

## Test Failure Output:
```
{error_output[:5000]}
```

## Relevant Files:
"""

    for filepath, content in file_contents.items():
        prompt += f"\n### {filepath}\n```\n{content[:3000]}\n```\n"

    prompt += """

## Instructions:
1. Identify the root cause of the test failure
2. Provide the EXACT fix needed
3. Output your fix in this JSON format:
```json
{
  "analysis": "Brief explanation of the issue",
  "fixes": [
    {
      "file": "path/to/file.py",
      "action": "replace",
      "old_text": "exact text to find",
      "new_text": "replacement text"
    }
  ]
}
```

Only output the JSON, nothing else.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

def apply_fixes(fix_json):
    """Apply fixes from Claude's response"""
    try:
        # Extract JSON from response
        json_str = fix_json
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]

        data = json.loads(json_str.strip())

        print(f"Analysis: {data.get('analysis', 'N/A')}")

        for fix in data.get('fixes', []):
            filepath = fix['file']
            action = fix['action']

            if action == 'replace' and os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()

                old_text = fix['old_text']
                new_text = fix['new_text']

                if old_text in content:
                    content = content.replace(old_text, new_text)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"✅ Fixed {filepath}")
                else:
                    print(f"⚠️ Could not find text in {filepath}")

            elif action == 'create':
                with open(filepath, 'w') as f:
                    f.write(fix.get('content', ''))
                print(f"✅ Created {filepath}")

        return True
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python claude_assistant.py fix 'error output'")
        sys.exit(1)

    command = sys.argv[1]
    error_output = sys.argv[2]

    if command == 'fix':
        print("🔍 Analyzing test failure...")
        fix_response = analyze_and_fix(error_output)
        print("🔧 Applying fixes...")
        success = apply_fixes(fix_response)
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
