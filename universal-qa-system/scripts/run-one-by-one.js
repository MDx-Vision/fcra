#!/usr/bin/env node
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const specDir = 'cypress/e2e';
const files = fs.readdirSync(specDir).filter(f => f.endsWith('.cy.js'));

console.log(`\n🧪 Running ${files.length} test files one at a time\n`);

const results = [];

files.forEach((file, i) => {
  console.log(`\n[${i+1}/${files.length}] ${file}`);
  const start = Date.now();
  
  try {
    execSync(`npx cypress run --headless --browser electron --spec "cypress/e2e/${file}"`, {
      encoding: 'utf8',
      stdio: 'pipe',
      timeout: 120000
    });
    results.push({ file, status: '✅ PASS', duration: ((Date.now() - start) / 1000).toFixed(1) });
    console.log(`   ✅ PASS (${results[results.length-1].duration}s)`);
  } catch (e) {
    results.push({ file, status: '❌ FAIL', duration: ((Date.now() - start) / 1000).toFixed(1) });
    console.log(`   ❌ FAIL (${results[results.length-1].duration}s)`);
  }
});

console.log(`\n${'='.repeat(50)}`);
console.log('SUMMARY\n');
const passed = results.filter(r => r.status.includes('PASS')).length;
const failed = results.filter(r => r.status.includes('FAIL')).length;
console.log(`✅ Passed: ${passed}`);
console.log(`❌ Failed: ${failed}`);
console.log(`📊 Rate: ${((passed / files.length) * 100).toFixed(1)}%\n`);

fs.writeFileSync('.qa-results/one-by-one.json', JSON.stringify({ timestamp: new Date().toISOString(), results }, null, 2));
