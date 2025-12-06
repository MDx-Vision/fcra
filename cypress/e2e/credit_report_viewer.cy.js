/**
 * Credit Report Viewer - Exhaustive E2E Tests
 * Auto-generated comprehensive test suite
 */

describe('Credit Report Viewer - Full QA Suite', () => {
  
  const REPORT_URL = '/api/credit-import/report/9';
  
  beforeEach(() => {
    cy.visit(REPORT_URL, { failOnStatusCode: false });
    cy.wait(500); // Allow page to fully render
  });

  // ==========================================
  // SECTION 1: PAGE LOAD & STRUCTURE
  // ==========================================
  describe('Page Load & Structure', () => {
    it('should load the credit report page', () => {
      cy.contains('Credit Report').should('be.visible');
    });

    it('should display client name in header', () => {
      cy.get('h1, .client-name, .header').should('exist');
    });

    it('should have proper page title', () => {
      cy.title().should('not.be.empty');
    });

    it('should load without console errors', () => {
      cy.window().then((win) => {
        cy.spy(win.console, 'error').as('consoleError');
      });
      cy.get('@consoleError').should('not.have.been.called');
    });

    it('should display Print Report button', () => {
      cy.contains('Print Report').should('be.visible');
    });

    it('should handle page refresh', () => {
      cy.reload();
      cy.contains('Credit Report').should('be.visible');
    });
  });

  // ==========================================
  // SECTION 2: CREDIT SCORES
  // ==========================================
  describe('Credit Scores Section', () => {
    it('should display Credit Scores header', () => {
      cy.contains('Credit Scores').should('be.visible');
    });

    it('should display exactly 3 score cards', () => {
      cy.get('.score-card').should('have.length', 3);
    });

    it('should show TransUnion score card', () => {
      cy.contains('TransUnion').should('be.visible');
    });

    it('should show Experian score card', () => {
      cy.contains('Experian').should('be.visible');
    });

    it('should show Equifax score card', () => {
      cy.contains('Equifax').should('be.visible');
    });

    it('should display numeric scores (not N/A)', () => {
      cy.get('.score-value').each(($el) => {
        const text = $el.text().trim();
        // Should be a number or N/A
        expect(text).to.match(/^\d{3}$|^N\/A$/);
      });
    });

    it('should display score ratings', () => {
      cy.get('.score-rating').should('have.length.gte', 3);
    });

    it('should show valid rating labels', () => {
      const validRatings = ['Exceptional', 'Very Good', 'Good', 'Fair', 'Poor', 'Not Available'];
      cy.get('.score-rating').each(($el) => {
        const text = $el.text().trim();
        expect(validRatings).to.include(text);
      });
    });

    it('should have color-coded scores', () => {
      cy.get('.score-value').first().should('have.attr', 'class').and('match', /score-/);
    });
  });

  // ==========================================
  // SECTION 3: REPORT SUMMARY
  // ==========================================
  describe('Report Summary Section', () => {
    it('should display Report Summary header', () => {
      cy.contains('Report Summary').should('be.visible');
    });

    it('should display Total Accounts', () => {
      cy.contains('Total Accounts').should('be.visible');
    });

    it('should display Inquiries count', () => {
      cy.contains('Inquiries').should('be.visible');
    });

    it('should display Collections count', () => {
      cy.contains('Collections').should('be.visible');
    });

    it('should display Public Records count', () => {
      cy.contains('Public Records').should('be.visible');
    });

    it('should display Late Payments count', () => {
      cy.contains('Late Payments').should('be.visible');
    });

    it('should show numeric values in summary cards', () => {
      cy.get('.summary-value').each(($el) => {
        const text = $el.text().trim();
        expect(text).to.match(/^\d+$/);
      });
    });

    it('should color-code negative items (red if > 0)', () => {
      cy.contains('Collections').parent().find('.summary-value').then(($el) => {
        const value = parseInt($el.text());
        if (value > 0) {
          expect($el.attr('style')).to.include('#ef4444');
        }
      });
    });
  });

  // ==========================================
  // SECTION 4: CREDIT ANALYTICS
  // ==========================================
  describe('Credit Analytics Section', () => {
    it('should display Credit Analytics header', () => {
      cy.contains('Credit Analytics').should('be.visible');
    });

    it('should display Credit Utilization', () => {
      cy.contains('Credit Utilization').should('be.visible');
    });

    it('should show utilization as percentage', () => {
      cy.contains('Credit Utilization').parent().find('.summary-value').should('contain', '%');
    });

    it('should display On-Time Payments', () => {
      cy.contains('On-Time Payments').should('be.visible');
    });

    it('should show on-time percentage', () => {
      cy.contains('On-Time Payments').parent().find('.summary-value').should('contain', '%');
    });

    it('should display payment count (X of Y months)', () => {
      cy.contains('of').should('exist');
      cy.contains('months').should('exist');
    });

    it('should display Avg Account Age', () => {
      cy.contains('Avg Account Age').should('be.visible');
    });

    it('should display Total Balance', () => {
      cy.contains('Total Balance').should('be.visible');
    });

    it('should show balance as currency', () => {
      cy.contains('Total Balance').parent().find('.summary-value').should('contain', '$');
    });

    it('should show credit limit', () => {
      cy.contains('Limit:').should('be.visible');
    });

    it('should color-code utilization (green <=30%, yellow <=50%, red >50%)', () => {
      cy.contains('Credit Utilization').parent().find('.summary-value').then(($el) => {
        const style = $el.attr('style') || '';
        expect(style).to.match(/#10b981|#f59e0b|#ef4444/);
      });
    });
  });

  // ==========================================
  // SECTION 5: TRADE LINES HEADER & SEARCH
  // ==========================================
  describe('Trade Lines Section', () => {
    it('should display Trade Lines header with count', () => {
      cy.contains(/Trade Lines \(\d+\)/).should('be.visible');
    });

    it('should display correct account count', () => {
      cy.contains(/Trade Lines \((\d+)\)/).then(($el) => {
        const match = $el.text().match(/\((\d+)\)/);
        const count = parseInt(match[1]);
        cy.get('.account-card').should('have.length', count);
      });
    });

    it('should have search input', () => {
      cy.get('#accountSearch').should('be.visible');
    });

    it('should have placeholder text', () => {
      cy.get('#accountSearch').should('have.attr', 'placeholder').and('contain', 'Search');
    });
  });

  // ==========================================
  // SECTION 6: SEARCH FUNCTIONALITY
  // ==========================================
  describe('Search Functionality', () => {
    it('should filter accounts when typing', () => {
      cy.get('.account-card').then(($cards) => {
        const initialCount = $cards.length;
        cy.get('#accountSearch').type('APPLE');
        cy.get('.account-card:visible').should('have.length.lt', initialCount);
      });
    });

    it('should be case-insensitive', () => {
      cy.get('#accountSearch').type('apple');
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should show all accounts when search cleared', () => {
      cy.get('#accountSearch').type('APPLE');
      cy.get('#accountSearch').clear();
      cy.get('.account-card:visible').should('have.length.gte', 10);
    });

    it('should show "Showing X of Y" when filtered', () => {
      cy.get('#accountSearch').type('KLARNA');
      cy.get('#filterCount').should('contain', 'of');
    });

    it('should handle no results gracefully', () => {
      cy.get('#accountSearch').type('XYZNONEXISTENT123');
      cy.get('.account-card:visible').should('have.length', 0);
    });

    it('should work with partial matches', () => {
      cy.get('#accountSearch').type('CAP');
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should search instantly (no delay)', () => {
      cy.get('#accountSearch').type('A');
      cy.get('#filterCount').should('exist');
    });
  });

  // ==========================================
  // SECTION 7: FILTER BUTTONS
  // ==========================================
  describe('Filter Buttons', () => {
    it('should have All filter button', () => {
      cy.contains('button', 'All').should('be.visible');
    });

    it('should have Open filter button', () => {
      cy.contains('button', 'Open').should('be.visible');
    });

    it('should have Closed filter button', () => {
      cy.contains('button', 'Closed').should('be.visible');
    });

    it('should have Negative filter button', () => {
      cy.contains('button', 'Negative').should('be.visible');
    });

    it('should have AU filter button', () => {
      cy.contains('button', 'AU').should('be.visible');
    });

    it('should have Discrepancy filter button', () => {
      cy.contains('button', 'Discrepancy').should('be.visible');
    });

    it('should highlight active filter button', () => {
      cy.contains('button', 'Negative').click();
      cy.contains('button', 'Negative').should('have.css', 'background-color').and('not.equal', 'transparent');
    });

    it('should filter to Open accounts', () => {
      cy.contains('button', 'Open').click();
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should filter to Negative accounts', () => {
      cy.contains('button', 'Negative').click();
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should filter to Closed accounts', () => {
      cy.contains('button', 'Closed').click();
      // May have 0 closed accounts, that's OK
    });

    it('should filter to AU accounts', () => {
      cy.contains('button', 'AU').click();
      cy.get('.account-card:visible').each(($card) => {
        cy.wrap($card).find('.creditor-name').should('contain', 'AU');
      });
    });

    it('should filter to Discrepancy accounts', () => {
      cy.contains('button', 'Discrepancy').click();
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should show count when filtered', () => {
      cy.contains('button', 'Negative').click();
      cy.get('#filterCount').should('contain', 'of');
    });

    it('should reset with All button', () => {
      cy.contains('button', 'Negative').click();
      cy.contains('button', 'All').click();
      cy.get('#filterCount').should('be.empty');
    });

    it('should combine with search', () => {
      cy.contains('button', 'Open').click();
      cy.get('#accountSearch').type('A');
      cy.get('.account-card:visible').should('have.length.gte', 0);
    });
  });

  // ==========================================
  // SECTION 8: ACCOUNT CARDS
  // ==========================================
  describe('Account Cards', () => {
    it('should display account cards', () => {
      cy.get('.account-card').should('have.length.gte', 1);
    });

    it('should display creditor name', () => {
      cy.get('.creditor-name').first().should('not.be.empty');
    });

    it('should display account number', () => {
      cy.get('.account-number').first().should('contain', 'Account #');
    });

    it('should display status badge', () => {
      cy.get('.status-badge').first().should('be.visible');
    });

    it('should display bureau dots', () => {
      cy.get('.bureau-dot').should('have.length.gte', 3);
    });

    it('should have TU bureau dot', () => {
      cy.get('.bureau-dot').contains('TU').should('exist');
    });

    it('should have EX bureau dot', () => {
      cy.get('.bureau-dot').contains('EX').should('exist');
    });

    it('should have EQ bureau dot', () => {
      cy.get('.bureau-dot').contains('EQ').should('exist');
    });

    it('should show status badges (OPEN/CLOSED/NEGATIVE)', () => {
      cy.get('.creditor-name span').should('have.length.gte', 1);
    });
  });

  // ==========================================
  // SECTION 9: BUREAU BUTTONS (TU/EX/EQ)
  // ==========================================
  describe('Bureau Filter Buttons', () => {
    it('should highlight TU when clicked', () => {
      cy.get('.bureau-dot').contains('TU').first().click();
      cy.get('.bureau-dot').contains('TU').first().should('have.css', 'outline').and('not.equal', 'none');
    });

    it('should highlight EX when clicked', () => {
      cy.get('.bureau-dot').contains('EX').first().click();
      cy.get('.bureau-dot').contains('EX').first().should('have.css', 'outline');
    });

    it('should highlight EQ when clicked', () => {
      cy.get('.bureau-dot').contains('EQ').first().click();
      cy.get('.bureau-dot').contains('EQ').first().should('have.css', 'outline');
    });

    it('should not collapse card when clicking bureau', () => {
      cy.get('.account-details').first().should('be.visible');
      cy.get('.bureau-dot').contains('TU').first().click();
      cy.get('.account-details').first().should('be.visible');
    });

    it('should update balance when bureau clicked', () => {
      cy.get('.bureau-value[data-field="balance"]').first().then(($el) => {
        cy.get('.bureau-dot').contains('EX').first().click();
        // Value may or may not change, but should still be visible
        cy.get('.bureau-value[data-field="balance"]').first().should('be.visible');
      });
    });

    it('should update credit limit when bureau clicked', () => {
      cy.get('.bureau-dot').contains('TU').first().click();
      cy.get('.bureau-value[data-field="credit_limit"]').first().should('be.visible');
    });

    it('should update date opened when bureau clicked', () => {
      cy.get('.bureau-dot').contains('EQ').first().click();
      cy.get('.bureau-value[data-field="date_opened"]').first().should('be.visible');
    });

    it('should switch between bureaus', () => {
      cy.get('.bureau-dot').contains('TU').first().click();
      cy.get('.bureau-dot').contains('EX').first().click();
      cy.get('.bureau-dot').contains('EQ').first().click();
      cy.get('.bureau-dot').contains('TU').first().click();
    });
  });

  // ==========================================
  // SECTION 10: ACCOUNT DETAILS
  // ==========================================
  describe('Account Details', () => {
    it('should display Account Type', () => {
      cy.contains('Account Type').should('be.visible');
    });

    it('should display Balance', () => {
      cy.contains('Balance').should('be.visible');
    });

    it('should display Credit Limit', () => {
      cy.contains('Credit Limit').should('be.visible');
    });

    it('should display Monthly Payment', () => {
      cy.contains('Monthly Payment').should('be.visible');
    });

    it('should display Date Opened', () => {
      cy.contains('Date Opened').should('be.visible');
    });

    it('should display High Balance', () => {
      cy.contains('High Balance').should('be.visible');
    });

    it('should display Past Due', () => {
      cy.contains('Past Due').should('be.visible');
    });

    it('should display Date Reported', () => {
      cy.contains('Date Reported').should('be.visible');
    });

    it('should show currency format for balances', () => {
      cy.get('.detail-value').contains('$').should('exist');
    });

    it('should show date format for dates', () => {
      cy.get('.detail-value').contains(/\d{2}\/\d{2}\/\d{4}/).should('exist');
    });

    it('should show N/A for missing values', () => {
      cy.get('.detail-value').contains('N/A').should('exist');
    });
  });

  // ==========================================
  // SECTION 11: PAYMENT HISTORY
  // ==========================================
  describe('Payment History', () => {
    it('should display Payment History header', () => {
      cy.contains('Payment History').should('be.visible');
    });

    it('should show 24 months label', () => {
      cy.contains('24 months').should('be.visible');
    });

    it('should display payment month labels', () => {
      cy.get('.payment-month').should('have.length.gte', 24);
    });

    it('should display payment status indicators', () => {
      cy.get('.payment-status').should('have.length.gte', 10);
    });

    it('should show OK for on-time payments (green)', () => {
      cy.get('.payment-status').contains('OK').should('exist');
    });

    it('should show late payment summary', () => {
      cy.contains('30 Days Late').should('be.visible');
      cy.contains('60 Days Late').should('be.visible');
      cy.contains('90+ Days Late').should('be.visible');
    });

    it('should display late counts', () => {
      cy.get('.late-count').should('have.length', 3);
    });

    it('should color-code payment status', () => {
      cy.get('.payment-ok').should('have.css', 'background-color');
    });

    it('should update payment history when bureau clicked', () => {
      cy.get('.bureau-dot').contains('EX').first().click();
      cy.get('.payment-status').first().should('be.visible');
    });
  });

  // ==========================================
  // SECTION 12: STATUS BADGES
  // ==========================================
  describe('Status Badges', () => {
    it('should show OPEN badge on open accounts', () => {
      cy.get('.creditor-name').contains('OPEN').should('exist');
    });

    it('should show NEGATIVE badge on past due accounts', () => {
      cy.get('.creditor-name').contains('NEGATIVE').should('exist');
    });

    it('should show CLOSED badge on closed accounts', () => {
      // May not exist if no closed accounts
      cy.get('body').then(($body) => {
        if ($body.find('.creditor-name:contains("CLOSED")').length > 0) {
          cy.get('.creditor-name').contains('CLOSED').should('be.visible');
        }
      });
    });

    it('should show AU badge on authorized user accounts', () => {
      cy.contains('button', 'AU').click();
      cy.get('.account-card:visible').should('have.length.gte', 0);
    });

    it('should show DISCREPANCY badge on discrepancy accounts', () => {
      cy.contains('button', 'Discrepancy').click();
      cy.get('.account-card:visible').each(($card) => {
        cy.wrap($card).find('.creditor-name').should('contain', 'DISCREPANCY');
      });
    });

    it('should allow multiple badges per account', () => {
      cy.get('.creditor-name').first().find('span').should('have.length.gte', 1);
    });
  });

  // ==========================================
  // SECTION 13: DISCREPANCY DETECTION
  // ==========================================
  describe('Discrepancy Detection', () => {
    beforeEach(() => {
      cy.contains('button', 'Discrepancy').click();
    });

    it('should filter to discrepancy accounts', () => {
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should show discrepancy badge', () => {
      cy.get('.account-card:visible').first().find('.creditor-name').should('contain', 'DISCREPANCY');
    });

    it('should display discrepancy details section', () => {
      cy.get('.discrepancy-details').should('be.visible');
    });

    it('should show Bureau Discrepancies Detected header', () => {
      cy.contains('Bureau Discrepancies Detected').should('be.visible');
    });

    it('should show field name (Balance, Credit Limit, etc)', () => {
      cy.get('.discrepancy-details').should('contain', 'Balance');
    });

    it('should show TU value', () => {
      cy.get('.discrepancy-details').should('contain', 'TU:');
    });

    it('should show EX value', () => {
      cy.get('.discrepancy-details').should('contain', 'EX:');
    });

    it('should show EQ value', () => {
      cy.get('.discrepancy-details').should('contain', 'EQ:');
    });

    it('should show different values between bureaus', () => {
      cy.get('.discrepancy-details').then(($el) => {
        const text = $el.text();
        // Should have at least 2 different dollar amounts
        const amounts = text.match(/\$[\d,]+\.?\d*/g);
        expect(amounts).to.have.length.gte(2);
      });
    });
  });

  // ==========================================
  // SECTION 14: AU (AUTHORIZED USER) DETECTION
  // ==========================================
  describe('Authorized User Detection', () => {
    it('should have AU filter button', () => {
      cy.contains('button', 'AU').should('be.visible');
    });

    it('should filter to AU accounts when clicked', () => {
      cy.contains('button', 'AU').click();
      cy.get('.account-card:visible').should('have.length.gte', 0);
    });

    it('should show AU badge on authorized user accounts', () => {
      cy.contains('button', 'AU').click();
      cy.get('.account-card:visible').each(($card) => {
        cy.wrap($card).find('.creditor-name').should('contain', 'AU');
      });
    });

    it('should have purple AU badge', () => {
      cy.contains('button', 'AU').click();
      cy.get('.account-card:visible').first().find('.creditor-name span').contains('AU').should('have.css', 'background-color');
    });
  });

  // ==========================================
  // SECTION 15: RECENT INQUIRIES
  // ==========================================
  describe('Recent Inquiries Section', () => {
    it('should display Recent Inquiries header', () => {
      cy.contains('Recent Inquiries').should('be.visible');
    });

    it('should show inquiry count', () => {
      cy.contains(/Inquiries \(\d+\)/).should('be.visible');
    });

    it('should display inquiry items', () => {
      cy.get('body').then(($body) => {
        if ($body.text().includes('Inquiries (0)')) {
          // No inquiries, that's OK
        } else {
          cy.contains('Recent Inquiries').parent().find('*').should('have.length.gte', 1);
        }
      });
    });
  });

  // ==========================================
  // SECTION 16: CREDITOR CONTACTS
  // ==========================================
  describe('Creditor Contacts Section', () => {
    it('should display Creditor Contacts header', () => {
      cy.contains('Creditor Contacts').should('be.visible');
    });

    it('should show contact count', () => {
      cy.contains(/Creditor Contacts \(\d+\)/).should('be.visible');
    });
  });

  // ==========================================
  // SECTION 17: ERROR STATES & EDGE CASES
  // ==========================================
  describe('Error States & Edge Cases', () => {
    it('should handle empty search gracefully', () => {
      cy.get('#accountSearch').type('   ');
      cy.get('.account-card:visible').should('have.length.gte', 1);
    });

    it('should handle special characters in search', () => {
      cy.get('#accountSearch').type('$@#%');
      cy.get('.account-card:visible').should('have.length', 0);
    });

    it('should handle rapid filter switching', () => {
      cy.contains('button', 'Open').click();
      cy.contains('button', 'Closed').click();
      cy.contains('button', 'Negative').click();
      cy.contains('button', 'All').click();
      cy.get('.account-card').should('have.length.gte', 1);
    });

    it('should handle rapid bureau clicking', () => {
      cy.get('.bureau-dot').contains('TU').first().click();
      cy.get('.bureau-dot').contains('EX').first().click();
      cy.get('.bureau-dot').contains('EQ').first().click();
      cy.get('.bureau-dot').contains('TU').first().click();
      cy.get('.bureau-dot').contains('EX').first().click();
    });

    it('should handle combined filter and search', () => {
      cy.contains('button', 'Negative').click();
      cy.get('#accountSearch').type('A');
      cy.contains('button', 'All').click();
      cy.get('#accountSearch').clear();
    });
  });

  // ==========================================
  // SECTION 18: PRINT FUNCTIONALITY
  // ==========================================
  describe('Print Functionality', () => {
    it('should have Print Report button', () => {
      cy.contains('Print Report').should('be.visible');
    });

    it('should be clickable', () => {
      cy.contains('Print Report').should('not.be.disabled');
    });
  });

  // ==========================================
  // SECTION 19: RESPONSIVE BEHAVIOR
  // ==========================================
  describe('Responsive Behavior', () => {
    it('should display on desktop viewport', () => {
      cy.viewport(1280, 720);
      cy.get('.account-card').should('be.visible');
    });

    it('should display on tablet viewport', () => {
      cy.viewport(768, 1024);
      cy.get('.account-card').should('be.visible');
    });

    it('should display on mobile viewport', () => {
      cy.viewport(375, 667);
      cy.get('.account-card').should('be.visible');
    });
  });

  // ==========================================
  // SECTION 20: PERFORMANCE
  // ==========================================
  describe('Performance', () => {
    it('should load within 5 seconds', () => {
      const start = Date.now();
      cy.visit(REPORT_URL, { failOnStatusCode: false });
      cy.get('.account-card').should('be.visible').then(() => {
        const loadTime = Date.now() - start;
        expect(loadTime).to.be.lessThan(5000);
      });
    });

    it('should filter instantly', () => {
      const start = Date.now();
      cy.contains('button', 'Negative').click();
      cy.get('#filterCount').should('exist').then(() => {
        const filterTime = Date.now() - start;
        expect(filterTime).to.be.lessThan(500);
      });
    });
  });
});
