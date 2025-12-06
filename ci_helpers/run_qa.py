#!/usr/bin/env python3
"""
Complete QA Runner - Runs tests, analyzes failures, fixes, and re-runs
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_cypress_tests(spec=None):
    """Run Cypress tests and capture output"""
    cmd = ["npx", "cypress", "run"]
    if spec:
        cmd.extend(["--spec", spec])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        'success': result.returncode == 0,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    }

def run_full_qa(max_iterations=3):
    """Run full QA cycle with auto-fix"""
    print("=" * 60)
    print("Starting Full QA Cycle")
    print("=" * 60)
    
    for iteration in range(1, max_iterations + 1):
        print(f"\nIteration {iteration}/{max_iterations}")
        
        result = run_cypress_tests()
        
        if result['success']:
            print("ALL TESTS PASSED!")
            return True
        
        print("Tests failed, sending to Claude...")
        error_text = result['stdout'] + result['stderr']
        
        fix_result = subprocess.run(
            ["python", "ci_helpers/claude_assistant.py", "fix", error_text[:5000]],
            capture_output=True,
            text=True
        )
        print(fix_result.stdout)
    
    return False

if __name__ == '__main__':
    run_full_qa()
