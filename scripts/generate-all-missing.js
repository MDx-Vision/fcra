#!/usr/bin/env node
/**
 * Generate tests for all routes missing coverage
 * Usage: node scripts/generate-all-missing.js [--dry-run] [--limit N]
 */

const { execSync } = require('child_process');
const fs = require('fs');

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const limitIndex = args.indexOf('--limit');
  const limit = limitIndex !== -1 ? parseInt(args[limitIndex + 1]) : Infinity;

  console.log('🔍 Detecting routes without tests...\n');

  // Run detection
  execSync('node scripts/detect-new-routes.js', { stdio: 'inherit' });

  // Read the output
  const untestedFile = 'scripts/.untested-routes.json';
  if (!fs.existsSync(untestedFile)) {
    console.log('\n✅ All routes have tests!');
    return;
  }

  const untested = JSON.parse(fs.readFileSync(untestedFile, 'utf8'));
  const toProcess = untested.slice(0, limit);

  console.log(`\n📝 Will generate tests for ${toProcess.length} routes`);

  if (dryRun) {
    console.log('\n🔍 Dry run - no tests generated');
    toProcess.forEach(r => console.log(`   Would generate: ${r.route}`));
    return;
  }

  const results = { success: [], failed: [] };

  for (const { route, authType } of toProcess) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`📝 Generating test for: ${route}`);
    console.log(`${'='.repeat(60)}`);

    try {
      execSync(`node scripts/generate-test.js "${route}" --auth ${authType}`, {
        stdio: 'inherit',
        timeout: 180000
      });
      results.success.push(route);
    } catch (error) {
      console.log(`\n⚠️  Test generation had issues for ${route}`);

      // Try auto-fix
      const fileName = route.split('/').pop().replace(/-/g, '_') + '_autogen.cy.js';
      const testPath = `cypress/e2e/${fileName}`;

      if (fs.existsSync(testPath)) {
        console.log('🔧 Attempting auto-fix...');
        try {
          execSync(`node scripts/auto-fix-tests.js "${testPath}"`, {
            stdio: 'inherit',
            timeout: 300000
          });
          results.success.push(route);
        } catch (fixError) {
          results.failed.push(route);
        }
      } else {
        results.failed.push(route);
      }
    }
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log('📊 SUMMARY');
  console.log(`${'='.repeat(60)}`);
  console.log(`✅ Success: ${results.success.length}`);
  console.log(`❌ Failed: ${results.failed.length}`);

  if (results.failed.length > 0) {
    console.log('\nFailed routes:');
    results.failed.forEach(r => console.log(`   - ${r}`));
  }
}

main().catch(console.error);
