#!/usr/bin/env node
/**
 * EXHAUSTIVE Test Generator - Analyzes REAL page content
 *
 * This script:
 * 1. Visits the actual route in a real browser
 * 2. Captures the rendered HTML
 * 3. Sends to Claude for exhaustive analysis
 * 4. Generates tests for EVERY element found
 *
 * Usage: node scripts/generate-test.js /dashboard/feature [--auth staff|client|public]
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const { execSync, spawn } = require('child_process');

const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
if (!CLAUDE_API_KEY) {
  console.error('❌ CLAUDE_API_KEY environment variable not set');
  console.error('   Set it with: export CLAUDE_API_KEY="sk-ant-..."');
  process.exit(1);
}

const CONFIG = {
  testDir: 'cypress/e2e',
  baseUrl: 'http://localhost:5000',
  claudeModel: 'claude-sonnet-4-20250514',

  // Auth credentials (should match your test fixtures)
  auth: {
    staff: {
      loginUrl: '/staff/login',
      email: 'admin@example.com',
      password: 'password123',
      successUrl: '/dashboard'
    },
    client: {
      loginUrl: '/portal/login',
      email: 'client@example.com',
      password: 'password123',
      successUrl: '/portal'
    }
  },

  authPatterns: {
    staff: /^\/dashboard/,
    client: /^\/portal(?!\/login)/,
  }
};

// ============================================
// CLAUDE API
// ============================================

async function callClaude(prompt, maxTokens = 8192) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: CONFIG.claudeModel,
      max_tokens: maxTokens,
      messages: [{ role: 'user', content: prompt }]
    })
  });

  const data = await response.json();
  if (data.error) {
    throw new Error(data.error.message);
  }
  return data.content[0].text;
}

// ============================================
// PAGE CAPTURE WITH PUPPETEER
// ============================================

async function capturePageContent(route, authType) {
  console.log('🌐 Launching browser...');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  try {
    // Handle authentication if needed
    if (authType === 'staff' || authType === 'client') {
      console.log(`🔐 Logging in as ${authType}...`);
      const authConfig = CONFIG.auth[authType];

      await page.goto(CONFIG.baseUrl + authConfig.loginUrl, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      // Fill login form
      await page.type('input[name="email"], input[type="email"], #email', authConfig.email);
      await page.type('input[name="password"], input[type="password"], #password', authConfig.password);

      // Submit and wait for navigation
      await Promise.all([
        page.click('button[type="submit"], input[type="submit"], .login-btn, .btn-login'),
        page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 })
      ]);

      console.log('   ✓ Login successful');
    }

    // Visit the target route
    console.log(`📄 Visiting ${route}...`);
    const response = await page.goto(CONFIG.baseUrl + route, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    const statusCode = response.status();
    console.log(`   Status: ${statusCode}`);

    if (statusCode >= 400) {
      throw new Error(`Page returned ${statusCode} error`);
    }

    // Wait for dynamic content
    await page.waitForTimeout(1000);

    // Capture page data
    const pageData = await page.evaluate(() => {
      // Get all interactive elements
      const getElements = (selector) => {
        return Array.from(document.querySelectorAll(selector)).map(el => ({
          tag: el.tagName.toLowerCase(),
          id: el.id || null,
          name: el.name || null,
          class: el.className || null,
          type: el.type || null,
          text: el.innerText?.slice(0, 100) || null,
          placeholder: el.placeholder || null,
          href: el.href || null,
          'data-testid': el.getAttribute('data-testid') || null,
          'aria-label': el.getAttribute('aria-label') || null,
        }));
      };

      return {
        title: document.title,
        url: window.location.href,

        // Page structure
        hasNav: !!document.querySelector('nav, .nav, .navbar, .sidebar'),
        hasFooter: !!document.querySelector('footer, .footer'),
        hasMain: !!document.querySelector('main, .main, .content'),

        // Forms
        forms: Array.from(document.querySelectorAll('form')).map(form => ({
          id: form.id,
          action: form.action,
          method: form.method,
          inputs: Array.from(form.querySelectorAll('input, select, textarea')).map(input => ({
            tag: input.tagName.toLowerCase(),
            type: input.type,
            name: input.name,
            id: input.id,
            required: input.required,
            placeholder: input.placeholder
          }))
        })),

        // Tables
        tables: Array.from(document.querySelectorAll('table')).map(table => ({
          id: table.id,
          class: table.className,
          headers: Array.from(table.querySelectorAll('th')).map(th => th.innerText),
          rowCount: table.querySelectorAll('tbody tr').length
        })),

        // Buttons
        buttons: getElements('button, .btn, [role="button"], input[type="submit"]'),

        // Links
        links: getElements('a[href]').filter(l => l.href && !l.href.startsWith('javascript:')),

        // Inputs outside forms
        standaloneInputs: getElements('input:not(form input), select:not(form select)'),

        // Modals
        modals: getElements('.modal, [role="dialog"], .dialog, .popup'),

        // Cards/Panels
        cards: document.querySelectorAll('.card, .panel, .tile, .widget').length,

        // Charts/Graphs
        hasCharts: !!document.querySelector('canvas, .chart, .graph, svg.recharts-surface'),

        // Tabs
        tabs: getElements('.tab, [role="tab"], .nav-tab'),

        // Alerts/Messages
        alerts: getElements('.alert, .message, .notification, .toast'),

        // Dropdowns
        dropdowns: getElements('select, .dropdown, [role="listbox"]'),

        // Search
        hasSearch: !!document.querySelector('input[type="search"], .search-input, [placeholder*="search" i]'),

        // Pagination
        hasPagination: !!document.querySelector('.pagination, .pager, [aria-label="pagination"]'),

        // File upload
        hasFileUpload: !!document.querySelector('input[type="file"]'),

        // Date pickers
        hasDatePicker: !!document.querySelector('input[type="date"], .datepicker, .date-picker'),

        // Text content summary
        headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
          level: h.tagName,
          text: h.innerText?.slice(0, 100)
        })),

        // Data attributes that might be useful for testing
        dataTestIds: Array.from(document.querySelectorAll('[data-testid]')).map(el => el.getAttribute('data-testid')),

        // Full HTML (truncated for API limits)
        bodyHTML: document.body.innerHTML.slice(0, 50000)
      };
    });

    // Take screenshot for reference
    const screenshotPath = path.join('scripts', '.page-screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`   📸 Screenshot saved: ${screenshotPath}`);

    await browser.close();
    return pageData;

  } catch (error) {
    await browser.close();
    throw error;
  }
}

// ============================================
// EXHAUSTIVE TEST GENERATION
// ============================================

async function generateExhaustiveTests(route, authType, pageData) {
  console.log('\n🤖 Sending page data to Claude for exhaustive analysis...');

  const prompt = `You are an expert QA engineer creating EXHAUSTIVE Cypress tests. You must test EVERY feature on this page.

## PAGE INFORMATION

Route: ${route}
Auth Required: ${authType}
Page Title: ${pageData.title}

## ACTUAL PAGE CONTENT (from real browser capture)

### Structure
- Has Navigation: ${pageData.hasNav}
- Has Footer: ${pageData.hasFooter}
- Has Main Content: ${pageData.hasMain}
- Has Search: ${pageData.hasSearch}
- Has Pagination: ${pageData.hasPagination}
- Has File Upload: ${pageData.hasFileUpload}
- Has Date Picker: ${pageData.hasDatePicker}
- Has Charts: ${pageData.hasCharts}
- Card/Panel Count: ${pageData.cards}

### Headings Found
${pageData.headings.map(h => `- ${h.level}: "${h.text}"`).join('\n') || 'None'}

### Forms Found (${pageData.forms.length})
${JSON.stringify(pageData.forms, null, 2)}

### Tables Found (${pageData.tables.length})
${JSON.stringify(pageData.tables, null, 2)}

### Buttons Found (${pageData.buttons.length})
${JSON.stringify(pageData.buttons.slice(0, 20), null, 2)}

### Tabs Found (${pageData.tabs.length})
${JSON.stringify(pageData.tabs, null, 2)}

### Modals Found (${pageData.modals.length})
${JSON.stringify(pageData.modals, null, 2)}

### Dropdowns Found (${pageData.dropdowns.length})
${JSON.stringify(pageData.dropdowns, null, 2)}

### Data-TestIDs Available
${pageData.dataTestIds.join(', ') || 'None'}

### HTML Snippet (for context)
${pageData.bodyHTML.slice(0, 15000)}

---

## YOUR TASK

Generate a COMPLETE Cypress test file that tests EVERY element and feature found above. Be exhaustive.

### Authentication Setup
${authType === 'staff' ? `
beforeEach(() => {
  cy.login('test@example.com', 'password123');
});` : authType === 'client' ? `
beforeEach(() => {
  cy.visit('/portal/login');
  cy.get('input[name="email"]').type('client@example.com');
  cy.get('input[name="password"]').type('password123');
  cy.get('button[type="submit"]').click();
  cy.url().should('include', '/portal');
});` : `
beforeEach(() => {
  // Public route - no auth required
});`}

### Required Test Categories

1. **Page Load Tests**
   - Page loads without errors
   - Correct URL
   - No console errors
   - No server errors (500, 404)

2. **UI Element Tests** (test EVERY element found)
   - All headings present
   - All buttons visible and clickable
   - All forms have required fields
   - All tables render with headers
   - Navigation works

3. **Form Tests** (for EACH form found)
   - All inputs accept text
   - Required field validation
   - Submit button works
   - Error messages display
   - Success feedback

4. **Table Tests** (for EACH table found)
   - Headers match expected
   - Rows render
   - Sorting works (if available)
   - Filtering works (if available)
   - Pagination works (if available)

5. **Interactive Element Tests**
   - Buttons trigger actions
   - Dropdowns open and select
   - Modals open and close
   - Tabs switch content
   - Search filters results

6. **Responsive Tests**
   - Desktop (1280px)
   - Tablet (768px)
   - Mobile (375px)

7. **Error Handling Tests**
   - Invalid form submissions
   - Network error handling
   - Empty states

### Output Format

Return ONLY valid JavaScript code. No markdown, no explanations.
Start with: // Exhaustive test for ${route}
Use specific selectors from the page data above.
Prefer data-testid, then id, then name, then class selectors.

Generate the complete test file now:`;

  const generatedCode = await callClaude(prompt);

  // Clean up any markdown formatting
  let cleaned = generatedCode
    .replace(/^```javascript\n?/gm, '')
    .replace(/^```\n?/gm, '')
    .trim();

  return cleaned;
}

// ============================================
// FILE UTILITIES
// ============================================

function routeToFileName(route) {
  const parts = route.split('/').filter(Boolean);
  const name = parts[parts.length - 1] || parts[0] || 'page';
  return name.replace(/-/g, '_') + '_exhaustive.cy.js';
}

function detectAuthType(route) {
  if (CONFIG.authPatterns.staff.test(route)) return 'staff';
  if (CONFIG.authPatterns.client.test(route)) return 'client';
  return 'public';
}

// ============================================
// SERVER CHECK
// ============================================

async function checkServer() {
  try {
    const response = await fetch(CONFIG.baseUrl, { method: 'HEAD', timeout: 5000 });
    return response.ok || response.status < 500;
  } catch {
    return false;
  }
}

async function startServer() {
  console.log('🚀 Starting Flask server...');

  const server = spawn('python', ['app.py'], {
    detached: true,
    stdio: 'ignore',
    env: { ...process.env, FLASK_ENV: 'testing' }
  });

  server.unref();

  // Wait for server to be ready
  for (let i = 0; i < 30; i++) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    if (await checkServer()) {
      console.log('   ✓ Server ready');
      return server;
    }
  }

  throw new Error('Server failed to start within 30 seconds');
}

// ============================================
// MAIN
// ============================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help') {
    console.log(`
EXHAUSTIVE Test Generator - Analyzes REAL page content

Usage: node scripts/generate-test.js <route> [options]

Options:
  --auth <type>     Force auth type: staff, client, or public
  --no-server       Don't auto-start server (assume it's running)

Examples:
  node scripts/generate-test.js /dashboard/clients
  node scripts/generate-test.js /portal/documents --auth client
  node scripts/generate-test.js /signup --auth public
    `);
    process.exit(0);
  }

  const route = args[0];
  let authType = detectAuthType(route);
  const noServer = args.includes('--no-server');

  // Override auth if specified
  const authIndex = args.indexOf('--auth');
  if (authIndex !== -1 && args[authIndex + 1]) {
    authType = args[authIndex + 1];
  }

  const fileName = routeToFileName(route);
  const filePath = path.join(CONFIG.testDir, fileName);

  console.log('═'.repeat(60));
  console.log('EXHAUSTIVE TEST GENERATOR');
  console.log('═'.repeat(60));
  console.log(`Route: ${route}`);
  console.log(`Auth: ${authType}`);
  console.log(`Output: ${filePath}`);
  console.log('═'.repeat(60));

  // Check/start server
  if (!noServer) {
    const serverRunning = await checkServer();
    if (!serverRunning) {
      await startServer();
    } else {
      console.log('✓ Server already running');
    }
  }

  // Capture real page content
  console.log('\n📸 PHASE 1: Capturing real page content...');
  const pageData = await capturePageContent(route, authType);

  console.log('\n📊 Page Analysis:');
  console.log(`   - Forms: ${pageData.forms.length}`);
  console.log(`   - Tables: ${pageData.tables.length}`);
  console.log(`   - Buttons: ${pageData.buttons.length}`);
  console.log(`   - Links: ${pageData.links.length}`);
  console.log(`   - Tabs: ${pageData.tabs.length}`);
  console.log(`   - Modals: ${pageData.modals.length}`);
  console.log(`   - Cards: ${pageData.cards}`);
  console.log(`   - Has Search: ${pageData.hasSearch}`);
  console.log(`   - Has Pagination: ${pageData.hasPagination}`);
  console.log(`   - Has Charts: ${pageData.hasCharts}`);

  // Generate exhaustive tests
  console.log('\n🤖 PHASE 2: Generating exhaustive tests with Claude...');
  const testCode = await generateExhaustiveTests(route, authType, pageData);

  // Write test file
  fs.writeFileSync(filePath, testCode);
  console.log(`\n✅ Test file created: ${filePath}`);

  // Count what was generated
  const testCount = (testCode.match(/it\(/g) || []).length;
  const describeCount = (testCode.match(/describe\(/g) || []).length;
  console.log(`   - ${describeCount} describe blocks`);
  console.log(`   - ${testCount} individual tests`);

  // Run the tests
  console.log('\n🧪 PHASE 3: Running generated tests...');
  try {
    execSync(`npx cypress run --spec "${filePath}"`, {
      stdio: 'inherit',
      timeout: 180000
    });
    console.log('\n✅ All tests passed!');
  } catch (error) {
    console.log('\n⚠️  Some tests failed. Run auto-fix:');
    console.log(`   node scripts/auto-fix-tests.js ${filePath}`);
    process.exit(1);
  }
}

main().catch(error => {
  console.error('\n❌ Error:', error.message);
  process.exit(1);
});
