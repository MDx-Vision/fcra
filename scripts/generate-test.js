#!/usr/bin/env node
/**
 * Generate Cypress test for a route using Claude API
 * Usage: node scripts/generate-test.js /dashboard/new-feature [--auth staff|client|public]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get API key from environment
const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
if (!CLAUDE_API_KEY) {
  console.error('❌ CLAUDE_API_KEY environment variable not set');
  process.exit(1);
}

const CONFIG = {
  testDir: 'cypress/e2e',
  baseUrl: 'http://localhost:5000',
  claudeModel: 'claude-sonnet-4-20250514',

  authPatterns: {
    staff: /^\/dashboard/,
    client: /^\/portal(?!\/login)/,
  }
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

function detectAuthType(route) {
  if (CONFIG.authPatterns.staff.test(route)) return 'staff';
  if (CONFIG.authPatterns.client.test(route)) return 'client';
  return 'public';
}

function getAuthSetup(authType) {
  switch (authType) {
    case 'staff':
      return `
  beforeEach(() => {
    // Staff login required for /dashboard/* routes
    cy.login('test@example.com', 'password123');
  });`;
    case 'client':
      return `
  beforeEach(() => {
    // Client login required for /portal/* routes
    cy.visit('/portal/login');
    cy.get('input[name="email"]').type('client@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/portal');
  });`;
    default:
      return `
  beforeEach(() => {
    // Public route - no auth required
  });`;
  }
}

function generateBaseTemplate(route, authType, featureName) {
  const authSetup = getAuthSetup(authType);

  return `// Auto-generated test for ${route}
// Generated: ${new Date().toISOString()}
// Auth: ${authType}

describe('${featureName} - Full QA Suite', () => {
${authSetup}

  describe('Page Load', () => {
    it('should load ${route} successfully', () => {
      cy.visit('${route}');
      cy.url().should('include', '${route}');
      cy.get('body').should('be.visible');
    });

    it('should not display errors', () => {
      cy.visit('${route}');
      cy.get('body').should('not.contain', 'Error');
      cy.get('body').should('not.contain', 'Exception');
      cy.get('body').should('not.contain', 'Traceback');
    });
  });

  describe('UI Elements', () => {
    it('should have navigation', () => {
      cy.visit('${route}');
      cy.get('nav, .nav, .navbar, .sidebar, [class*="nav"]').should('exist');
    });

    it('should have main content', () => {
      cy.visit('${route}');
      cy.get('main, .main, .content, .container, [class*="content"]').should('exist');
    });
  });

  describe('Responsive Design', () => {
    it('should display on desktop', () => {
      cy.viewport(1280, 720);
      cy.visit('${route}');
      cy.get('body').should('be.visible');
    });

    it('should display on tablet', () => {
      cy.viewport(768, 1024);
      cy.visit('${route}');
      cy.get('body').should('be.visible');
    });

    it('should display on mobile', () => {
      cy.viewport(375, 667);
      cy.visit('${route}');
      cy.get('body').should('be.visible');
    });
  });

  // CLAUDE_GENERATED_TESTS_START
  // Additional tests will be inserted here by Claude API
  // CLAUDE_GENERATED_TESTS_END
});
`;
}

async function analyzePageAndGenerateTests(route, authType) {
  const prompt = `You are a Cypress test expert. I need you to generate comprehensive tests for a Flask web application route.

Route: ${route}
Auth Type: ${authType} (${authType === 'staff' ? 'requires staff login' : authType === 'client' ? 'requires client login' : 'public, no login'})

Based on the route pattern, generate specific Cypress tests. Consider what this page likely contains:

${route.includes('clients') ? '- Client list/table, filters, search, CRUD operations' : ''}
${route.includes('staff') ? '- Staff management, add/edit modals, role selection' : ''}
${route.includes('settlements') ? '- Settlement pipeline, status filters, offers, amounts' : ''}
${route.includes('analytics') ? '- Charts, metrics, statistics, date ranges' : ''}
${route.includes('cases') ? '- Case details, violations, documents, timeline' : ''}
${route.includes('calendar') ? '- Calendar view, events, date navigation' : ''}
${route.includes('documents') ? '- Document list, upload, download, preview' : ''}
${route.includes('settings') ? '- Configuration forms, toggles, save buttons' : ''}
${route.includes('import') ? '- File upload, progress, status messages' : ''}
${route.includes('queue') ? '- Queue items, status, actions, filters' : ''}
${route.includes('report') ? '- Report display, export options, filters' : ''}
${route.includes('signup') ? '- Multi-step form, validation, payment options' : ''}
${route.includes('login') ? '- Login form, validation, forgot password' : ''}

Generate ONLY the test code (no explanation). Output valid JavaScript that goes inside a describe() block.
Use realistic selectors based on common patterns.
Include tests for:
1. Key elements exist on the page
2. Interactive elements work (buttons, forms, modals if applicable)
3. Data displays correctly (tables, cards, stats)
4. Error states handled

Format as valid Cypress test code starting with describe(). Do not include any markdown formatting or code fences.`;

  try {
    const generatedTests = await callClaude(prompt);
    return generatedTests;
  } catch (error) {
    console.error('⚠️  Claude API error:', error.message);
    return null;
  }
}

function routeToFeatureName(route) {
  // /dashboard/credit-tracker -> Credit Tracker
  const parts = route.split('/').filter(Boolean);
  const name = parts[parts.length - 1] || parts[0] || 'page';
  return name
    .split(/[-_]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function routeToFileName(route) {
  // /dashboard/credit-tracker -> credit_tracker_autogen.cy.js
  const parts = route.split('/').filter(Boolean);
  const name = parts[parts.length - 1] || parts[0] || 'page';
  return name.replace(/-/g, '_') + '_autogen.cy.js';
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node scripts/generate-test.js <route> [--auth staff|client|public]');
    console.log('Example: node scripts/generate-test.js /dashboard/new-feature');
    process.exit(1);
  }

  const route = args[0];
  let authType = detectAuthType(route);

  // Override auth if specified
  const authIndex = args.indexOf('--auth');
  if (authIndex !== -1 && args[authIndex + 1]) {
    authType = args[authIndex + 1];
  }

  const featureName = routeToFeatureName(route);
  const fileName = routeToFileName(route);
  const filePath = path.join(CONFIG.testDir, fileName);

  console.log(`🔧 Generating test for: ${route}`);
  console.log(`   Auth type: ${authType}`);
  console.log(`   Feature name: ${featureName}`);
  console.log(`   Output file: ${filePath}`);

  // Generate base template
  console.log('\n📝 Creating base template...');
  let testContent = generateBaseTemplate(route, authType, featureName);

  // Use Claude to generate additional tests
  console.log('🤖 Calling Claude API for intelligent test generation...');
  const claudeTests = await analyzePageAndGenerateTests(route, authType);

  if (claudeTests) {
    // Insert Claude's tests into the template
    testContent = testContent.replace(
      '// CLAUDE_GENERATED_TESTS_START\n  // Additional tests will be inserted here by Claude API\n  // CLAUDE_GENERATED_TESTS_END',
      `// CLAUDE_GENERATED_TESTS_START\n${claudeTests}\n  // CLAUDE_GENERATED_TESTS_END`
    );
    console.log('✅ Claude generated additional tests');
  } else {
    console.log('⚠️  Using base template only (Claude API unavailable)');
  }

  // Write the file
  fs.writeFileSync(filePath, testContent);
  console.log(`\n✅ Test file created: ${filePath}`);

  // Run the test to check for errors
  console.log('\n🧪 Running generated test...');
  try {
    execSync(`npx cypress run --spec "${filePath}" --reporter spec`, {
      stdio: 'inherit',
      timeout: 120000
    });
    console.log('\n✅ All tests passed!');
  } catch (error) {
    console.log('\n⚠️  Some tests failed - you can use auto-fix-tests.js to fix them');
    process.exit(1);
  }
}

main().catch(console.error);
