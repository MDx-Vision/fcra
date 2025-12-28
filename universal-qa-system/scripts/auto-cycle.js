#!/usr/bin/env node
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log(`
╔════════════════════════════════════════════════════════════╗
║     Universal QA System - FULL AUTO CYCLE                  ║
║     Run → Categorize → Fix → Commit                        ║
╚════════════════════════════════════════════════════════════╝
`);

// Step 1: Run tests
console.log('📋 STEP 1: Running all tests...\n');
let testOutput = '';
try {
  testOutput = execSync('npx cypress run --headless --browser electron 2>&1', {
    encoding: 'utf8',
    timeout: 1800000
  });
} catch (e) {
  testOutput = e.stdout || '';
}

// Step 2: Parse results
const passMatch = testOutput.match(/(\d+)\s+passing/);
const failMatch = testOutput.match(/(\d+)\s+failing/);
const skipMatch = testOutput.match(/(\d+)\s+skipped/);
const passed = passMatch ? parseInt(passMatch[1]) : 0;
const failed = failMatch ? parseInt(failMatch[1]) : 0;
const skipped = skipMatch ? parseInt(skipMatch[1]) : 0;

console.log(`\n📊 STEP 2: Results`);
console.log(`   ✅ Passed: ${passed}`);
console.log(`   ❌ Failed: ${failed}`);
console.log(`   ⏭️  Skipped: ${skipped}\n`);

if (failed === 0) {
  console.log('🎉 All tests passing! Nothing to fix.');
  process.exit(0);
}

// Step 3: Categorize failures
console.log('🔍 STEP 3: Categorizing failures...\n');
const screenshotDir = 'cypress/screenshots';
const categories = {
  auth: [],
  notBuilt: [],
  selector: [],
  timeout: [],
  rateLimit: [],
  other: []
};

if (fs.existsSync(screenshotDir)) {
  const folders = fs.readdirSync(screenshotDir);
  folders.forEach(folder => {
    const files = fs.readdirSync(path.join(screenshotDir, folder));
    files.forEach(file => {
      const name = file.toLowerCase();
      if (name.includes('login') || name.includes('hook') || name.includes('redirect')) {
        categories.auth.push({ folder, file });
      } else if (name.includes('404') || name.includes('not found')) {
        categories.notBuilt.push({ folder, file });
      } else if (name.includes('element') || name.includes('selector') || name.includes('testid')) {
        categories.selector.push({ folder, file });
      } else if (name.includes('timeout')) {
        categories.timeout.push({ folder, file });
      } else if (name.includes('429') || name.includes('rate')) {
        categories.rateLimit.push({ folder, file });
      } else {
        categories.other.push({ folder, file });
      }
    });
  });
}

console.log('   📁 Categorization:');
console.log(`   🔐 Auth issues: ${categories.auth.length} (fix login first)`);
console.log(`   🚧 Not built: ${categories.notBuilt.length} (need features)`);
console.log(`   🎯 Selector: ${categories.selector.length} (add data-testid)`);
console.log(`   ⏱️  Timeout: ${categories.timeout.length} (slow/hanging)`);
console.log(`   🚦 Rate limit: ${categories.rateLimit.length} (server issue)`);
console.log(`   ❓ Other: ${categories.other.length} (needs review)\n`);

// Step 4: Recommendations
console.log('💡 STEP 4: Recommendations\n');

if (categories.auth.length > 10) {
  console.log('   🔴 PRIORITY: Fix auth/login flow first');
  console.log('      Most failures are auth-related. Fix login → unlock other tests.\n');
}

if (categories.selector.length > 0) {
  console.log(`   🟡 AUTO-FIXABLE: ${categories.selector.length} selector issues`);
  console.log('      Run: node universal-qa-system/auto-fix/fix-engine.js --type=selector\n');
}

if (categories.notBuilt.length > 0) {
  console.log(`   ⚪ NOT FIXABLE: ${categories.notBuilt.length} features not built`);
  console.log('      These tests expect routes/features that don\'t exist yet.\n');
}

// Step 5: Save report
const resultsDir = '.qa-results';
if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir, { recursive: true });

const report = {
  timestamp: new Date().toISOString(),
  summary: { passed, failed, skipped },
  categories,
  recommendation: categories.auth.length > 10 ? 'Fix auth first' : 'Run auto-fix'
};

fs.writeFileSync(path.join(resultsDir, 'auto-cycle-report.json'), JSON.stringify(report, null, 2));
console.log('📁 Report saved: .qa-results/auto-cycle-report.json\n');

// Step 6: What to do next
console.log('🚀 NEXT STEPS:\n');
if (categories.auth.length > 10) {
  console.log('   1. Fix the login/auth flow in the app');
  console.log('   2. Run: node universal-qa-system/scripts/auto-cycle.js');
} else if (categories.selector.length > 0) {
  console.log('   1. Run auto-fix: node universal-qa-system/auto-fix/fix-engine.js');
  console.log('   2. Review changes: git diff');
  console.log('   3. Commit: git add -A && git commit -m "fix: auto-fix test selectors"');
}
