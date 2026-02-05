#!/usr/bin/env node
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.replace('--', '').split('=');
  acc[key] = value;
  return acc;
}, {});

if (!args.project) {
  console.error('❌ Error: --project is required');
  process.exit(1);
}

const configPath = path.join(__dirname, '..', 'config', 'projects', `${args.project}.json`);
if (!fs.existsSync(configPath)) {
  console.error(`❌ Error: Project config not found: ${configPath}`);
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const testFramework = config.test_framework;
const timeoutSeconds = parseInt(args.timeout, 10) || 300;
const timeoutMs = timeoutSeconds * 1000;

console.log(`
╔════════════════════════════════════════════════════════════╗
║        Universal QA System - Test Validator                ║
║   🚨 THIS ACTUALLY RUNS YOUR TESTS! 🚨                     ║
╚════════════════════════════════════════════════════════════╝
Project: ${config.display_name}
Framework: ${testFramework}
Timeout: ${timeoutSeconds} seconds
`);

let command = '';
if (testFramework === 'cypress') {
  command = 'npx cypress run --headless --browser electron';
  if (args.spec) command += ` --spec "${args.spec}"`;
} else if (testFramework === 'pytest') {
  command = 'python -m pytest -v --tb=short';
  if (args.module) command += ` tests/test_${args.module}.py`;
}

console.log(`🏃 Running: ${command}\n`);

const startTime = Date.now();
const result = { success: false, passed: 0, failed: 0, skipped: 0, timedOut: false, output: '' };

try {
  result.output = execSync(command, { cwd: process.cwd(), encoding: 'utf8', stdio: 'pipe', timeout: timeoutMs });
  result.success = true;
} catch (error) {
  if (error.killed) { result.timedOut = true; result.output = 'Timeout'; }
  else { result.output = error.stdout || ''; }
}

result.duration = ((Date.now() - startTime) / 1000).toFixed(2);

const passingMatch = result.output.match(/(\d+)\s+passing/);
const failingMatch = result.output.match(/(\d+)\s+failing/);
const pendingMatch = result.output.match(/(\d+)\s+pending/);
result.passed = passingMatch ? parseInt(passingMatch[1], 10) : 0;
result.failed = failingMatch ? parseInt(failingMatch[1], 10) : 0;
result.skipped = pendingMatch ? parseInt(pendingMatch[1], 10) : 0;

if (result.timedOut) {
  console.log(`⏱️ TIMEOUT after ${timeoutSeconds}s. Use --timeout=600 for longer.`);
} else {
  console.log(`
✅ Passed:  ${result.passed}
❌ Failed:  ${result.failed}
⏭️  Skipped: ${result.skipped}
⏱️  Duration: ${result.duration}s
${result.success ? '🎉 ALL TESTS PASSED!' : '💥 SOME TESTS FAILED'}
`);
}

const total = result.passed + result.failed;
console.log(`📊 Coverage: ${total > 0 ? ((result.passed / total) * 100).toFixed(1) : 0}%`);

const resultsDir = path.join(process.cwd(), '.qa-results');
if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });
fs.writeFileSync(path.join(resultsDir, `${args.project}-latest.json`), JSON.stringify({ project: args.project, timestamp: new Date().toISOString(), results: { passed: result.passed, failed: result.failed, skipped: result.skipped, duration: result.duration }, success: result.success }, null, 2));

process.exit(result.success ? 0 : 1);
