#!/usr/bin/env node
/**
 * Auto-fix failing Cypress tests using Claude API
 * Usage: node scripts/auto-fix-tests.js <test-file> [--max-attempts 5]
 */

const fs = require('fs');
const { execSync, spawnSync } = require('child_process');
const path = require('path');

const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
if (!CLAUDE_API_KEY) {
  console.error('❌ CLAUDE_API_KEY environment variable not set');
  process.exit(1);
}

const CONFIG = {
  maxAttempts: 5,
  claudeModel: 'claude-sonnet-4-20250514',
};

async function callClaude(prompt) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: CONFIG.claudeModel,
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }]
    })
  });

  const data = await response.json();
  if (data.error) {
    throw new Error(data.error.message);
  }
  return data.content[0].text;
}

function runTest(testFile) {
  const result = spawnSync('npx', ['cypress', 'run', '--spec', testFile, '--reporter', 'json'], {
    encoding: 'utf8',
    timeout: 120000
  });

  return {
    success: result.status === 0,
    stdout: result.stdout,
    stderr: result.stderr
  };
}

function extractFailures(output) {
  // Parse Cypress JSON output for failures
  try {
    const jsonMatch = output.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const results = JSON.parse(jsonMatch[0]);
      const failures = [];

      if (results.runs) {
        for (const run of results.runs) {
          for (const test of run.tests || []) {
            if (test.state === 'failed') {
              failures.push({
                title: test.title.join(' > '),
                error: test.displayError || test.err?.message || 'Unknown error'
              });
            }
          }
        }
      }
      return failures;
    }
  } catch (e) {
    // Fall back to regex parsing
  }

  // Regex fallback for error extraction
  const failures = [];
  const errorRegex = /AssertionError:([^\n]+)/g;
  let match;
  while ((match = errorRegex.exec(output)) !== null) {
    failures.push({
      title: 'Unknown test',
      error: match[1].trim()
    });
  }

  return failures;
}

async function fixTest(testFile, failures) {
  const testContent = fs.readFileSync(testFile, 'utf8');

  const prompt = `You are a Cypress test expert. Fix the following failing tests.

CURRENT TEST FILE:
\`\`\`javascript
${testContent}
\`\`\`

FAILURES:
${failures.map((f, i) => `${i + 1}. Test: "${f.title}"\n   Error: ${f.error}`).join('\n\n')}

COMMON FIXES:
1. "element not found" → Use broader selector or check if element exists conditionally
2. "not visible" → Element may be in a tab/modal that needs to be opened first
3. "timeout" → Add cy.wait() or increase timeout
4. "Cannot read properties" → Add null checks or beforeEach setup
5. Modal tests on pages without modals → Skip the test with reason

RULES:
- Return ONLY the complete fixed JavaScript file
- No explanations, no markdown code fences
- If a test cannot be fixed, skip it with: it.skip('test name - reason', () => {});
- Preserve all working tests unchanged
- Make minimal changes to fix issues

Return the complete fixed test file:`;

  const fixedContent = await callClaude(prompt);

  // Clean up any markdown formatting Claude might add
  let cleaned = fixedContent
    .replace(/^```javascript\n?/gm, '')
    .replace(/^```\n?/gm, '')
    .trim();

  return cleaned;
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node scripts/auto-fix-tests.js <test-file> [--max-attempts N]');
    process.exit(1);
  }

  const testFile = args[0];

  // Parse max attempts
  const maxIndex = args.indexOf('--max-attempts');
  const maxAttempts = maxIndex !== -1 ? parseInt(args[maxIndex + 1]) : CONFIG.maxAttempts;

  if (!fs.existsSync(testFile)) {
    console.error(`❌ Test file not found: ${testFile}`);
    process.exit(1);
  }

  console.log(`🔧 Auto-fixing: ${testFile}`);
  console.log(`   Max attempts: ${maxAttempts}\n`);

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`\n📍 Attempt ${attempt}/${maxAttempts}`);
    console.log('   Running tests...');

    const result = runTest(testFile);

    if (result.success) {
      console.log('\n✅ All tests passing!');
      return;
    }

    const failures = extractFailures(result.stdout + result.stderr);

    if (failures.length === 0) {
      console.log('⚠️  Test failed but could not extract failure details');
      console.log('   Stderr:', result.stderr?.slice(0, 500));
      break;
    }

    console.log(`   Found ${failures.length} failing test(s)`);
    failures.forEach(f => console.log(`   - ${f.title}: ${f.error.slice(0, 80)}...`));

    if (attempt === maxAttempts) {
      console.log('\n❌ Max attempts reached. Some tests still failing.');
      process.exit(1);
    }

    console.log('\n🤖 Calling Claude API to fix tests...');

    try {
      const fixedContent = await fixTest(testFile, failures);

      // Backup original
      const backupPath = testFile + '.backup';
      if (attempt === 1) {
        fs.copyFileSync(testFile, backupPath);
        console.log(`   Backup saved: ${backupPath}`);
      }

      // Write fixed content
      fs.writeFileSync(testFile, fixedContent);
      console.log('   Fixed test written');

    } catch (error) {
      console.error('❌ Claude API error:', error.message);
      process.exit(1);
    }
  }
}

main().catch(console.error);
