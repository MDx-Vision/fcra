#!/usr/bin/env node
/**
 * Detect Flask routes without Cypress test coverage
 * Usage: node scripts/detect-new-routes.js
 */

const fs = require('fs');
const path = require('path');

// Config for FCRA Flask app
const CONFIG = {
  routeFile: 'app.py',
  testDir: 'cypress/e2e',

  // Routes to ignore (webhooks, API, static)
  ignorePatterns: [
    /^\/api\//,           // API routes (covered by api_endpoints.cy.js)
    /^\/webhook/,         // Webhook endpoints
    /^\/static/,          // Static files
    /^\/favicon/,         // Favicon
    /\/<.*>/,             // Dynamic params like /<int:id> (need specific handling)
  ],

  // Auth patterns
  authPatterns: {
    staff: /^\/dashboard/,
    client: /^\/portal(?!\/login)/,
    public: /^(\/signup|\/staff\/login|\/portal\/login|\/clear|\/admin|\/scanner|\/preview)/
  }
};

function extractRoutes() {
  const content = fs.readFileSync(CONFIG.routeFile, 'utf8');
  const routeRegex = /@app\.route\(['"]([^'"]+)['"]/g;
  const routes = [];
  let match;

  while ((match = routeRegex.exec(content)) !== null) {
    const route = match[1];

    // Skip ignored patterns
    const shouldIgnore = CONFIG.ignorePatterns.some(pattern => pattern.test(route));
    if (shouldIgnore) continue;

    // Determine auth type
    let authType = 'public';
    if (CONFIG.authPatterns.staff.test(route)) authType = 'staff';
    else if (CONFIG.authPatterns.client.test(route)) authType = 'client';

    routes.push({ route, authType });
  }

  return routes;
}

function getExistingTestRoutes() {
  const testDir = CONFIG.testDir;
  const testedRoutes = new Set();

  const testFiles = fs.readdirSync(testDir).filter(f => f.endsWith('.cy.js'));

  for (const file of testFiles) {
    const content = fs.readFileSync(path.join(testDir, file), 'utf8');

    // Find cy.visit() calls
    const visitRegex = /cy\.visit\(['"]([^'"]+)['"]\)/g;
    let match;
    while ((match = visitRegex.exec(content)) !== null) {
      testedRoutes.add(match[1]);
    }

    // Find route comments like "// Tests: /dashboard/clients"
    const commentRegex = /\/\/\s*(?:Tests?|Route):\s*([^\s\n]+)/gi;
    while ((match = commentRegex.exec(content)) !== null) {
      testedRoutes.add(match[1]);
    }
  }

  return testedRoutes;
}

function main() {
  console.log('🔍 Detecting routes without test coverage...\n');

  const allRoutes = extractRoutes();
  const testedRoutes = getExistingTestRoutes();

  const untestedRoutes = allRoutes.filter(r => !testedRoutes.has(r.route));

  console.log(`📊 Summary:`);
  console.log(`   Total HTML routes: ${allRoutes.length}`);
  console.log(`   Routes with tests: ${allRoutes.length - untestedRoutes.length}`);
  console.log(`   Routes missing tests: ${untestedRoutes.length}\n`);

  if (untestedRoutes.length === 0) {
    console.log('✅ All routes have test coverage!');
    return;
  }

  console.log('❌ Routes without tests:\n');

  // Group by auth type
  const byAuth = { staff: [], client: [], public: [] };
  untestedRoutes.forEach(r => byAuth[r.authType].push(r.route));

  if (byAuth.staff.length > 0) {
    console.log('   Staff-protected (/dashboard/*):');
    byAuth.staff.forEach(r => console.log(`     - ${r}`));
  }

  if (byAuth.client.length > 0) {
    console.log('\n   Client-protected (/portal/*):');
    byAuth.client.forEach(r => console.log(`     - ${r}`));
  }

  if (byAuth.public.length > 0) {
    console.log('\n   Public routes:');
    byAuth.public.forEach(r => console.log(`     - ${r}`));
  }

  // Output JSON for other scripts
  const outputPath = 'scripts/.untested-routes.json';
  fs.writeFileSync(outputPath, JSON.stringify(untestedRoutes, null, 2));
  console.log(`\n📁 Route list saved to: ${outputPath}`);
}

main();
