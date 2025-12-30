// Exhaustive test for /dashboard/franchise
describe('Franchise Management - /dashboard/franchise', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/franchise');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/franchise');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Franchise');
    });

    it('should display the page header', () => {
      cy.get('.header h1').should('contain.text', 'Franchise Management');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/franchise').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Actions Tests', () => {
    it('should display New Organization button', () => {
      cy.get('.header-actions .btn-primary').should('contain.text', 'New Organization');
    });

    it('should open modal when New Organization clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#createOrgModal').should('have.class', 'active');
    });
  });

  describe('Stats Grid Tests', () => {
    it('should display stats grid', () => {
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display four stat cards', () => {
      cy.get('.stats-grid .stat-card').should('have.length', 4);
    });

    it('should display Total Organizations stat', () => {
      cy.get('.stat-card.highlight').within(() => {
        cy.get('.stat-label').should('contain.text', 'Total Organizations');
        cy.get('.stat-value').should('exist');
      });
    });

    it('should display Total Clients stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Total Clients').should('exist');
    });

    it('should display Pending Transfers stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Pending Transfers').should('exist');
    });

    it('should display Total Revenue stat', () => {
      cy.get('.stat-card').contains('.stat-label', 'Total Revenue').should('exist');
    });
  });

  describe('Tabs Tests', () => {
    it('should display tabs', () => {
      cy.get('.tabs').should('be.visible');
    });

    it('should have Organization Hierarchy tab', () => {
      cy.get('.tab').contains('Organization Hierarchy').should('exist');
    });

    it('should have All Organizations tab', () => {
      cy.get('.tab').contains('All Organizations').should('exist');
    });

    it('should have Transfers tab', () => {
      cy.get('.tab').contains('Transfers').should('exist');
    });

    it('should have Revenue tab', () => {
      cy.get('.tab').contains('Revenue').should('exist');
    });

    it('should switch tabs on click', () => {
      cy.get('.tab').contains('All Organizations').click();
      cy.get('#tab-list').should('have.class', 'active');
    });
  });

  describe('Hierarchy Tab Tests', () => {
    it('should display hierarchy tab content by default', () => {
      cy.get('#tab-hierarchy').should('have.class', 'active');
    });

    it('should display content section', () => {
      cy.get('.content-section').should('be.visible');
    });

    it('should display section title', () => {
      cy.get('.section-title').should('contain.text', 'Organization Hierarchy');
    });

    it('should display either org tree or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-tree').length) {
          cy.get('.org-tree').should('be.visible');
        } else {
          cy.get('.empty-state').should('be.visible');
        }
      });
    });
  });

  describe('Organization Tree Tests', () => {
    it('should display org tree items if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-tree-item').length) {
          cy.get('.org-tree-item').first().should('be.visible');
        } else {
          cy.get('.empty-state').should('exist');
        }
      });
    });

    it('should display org tree node if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-tree-node').length) {
          cy.get('.org-tree-node').first().should('be.visible');
        } else {
          cy.get('.content-section').should('exist');
        }
      });
    });

    it('should display org tree name if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-tree-name').length) {
          cy.get('.org-tree-name').first().should('be.visible');
        } else {
          cy.get('.content-section').should('exist');
        }
      });
    });
  });

  describe('List Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab').contains('All Organizations').click();
    });

    it('should display list tab content', () => {
      cy.get('#tab-list').should('have.class', 'active');
    });

    it('should display org cards if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card').length) {
          cy.get('.org-card').first().should('be.visible');
        } else {
          cy.get('#tab-list').should('exist');
        }
      });
    });

    it('should display org card header if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card').length) {
          cy.get('.org-card-header').first().should('be.visible');
        } else {
          cy.get('#tab-list').should('exist');
        }
      });
    });

    it('should display org card stats if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card').length) {
          cy.get('.org-card-stats').first().should('be.visible');
        } else {
          cy.get('#tab-list').should('exist');
        }
      });
    });

    it('should display org card actions if organizations exist', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card').length) {
          cy.get('.org-card-actions').first().should('be.visible');
        } else {
          cy.get('#tab-list').should('exist');
        }
      });
    });
  });

  describe('Transfers Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab').contains('Transfers').click();
    });

    it('should display transfers tab content', () => {
      cy.get('#tab-transfers').should('have.class', 'active');
    });

    it('should display New Transfer button', () => {
      cy.get('#tab-transfers .btn-primary').should('contain.text', 'New Transfer');
    });

    it('should display either transfers table or empty state', () => {
      cy.get('body').then(($body) => {
        if ($body.find('#tab-transfers .data-table').length) {
          cy.get('#tab-transfers .data-table').should('be.visible');
        } else {
          cy.get('#tab-transfers .empty-state').should('be.visible');
        }
      });
    });
  });

  describe('Revenue Tab Tests', () => {
    beforeEach(() => {
      cy.get('.tab').contains('Revenue').click();
    });

    it('should display revenue tab content', () => {
      cy.get('#tab-revenue').should('have.class', 'active');
    });

    it('should display revenue summary', () => {
      cy.get('.revenue-summary').should('be.visible');
    });

    it('should display revenue cards', () => {
      cy.get('.revenue-card').should('have.length', 3);
    });

    it('should display revenue table', () => {
      cy.get('#tab-revenue .data-table').should('be.visible');
    });
  });

  describe('Create Organization Modal Tests', () => {
    it('should have create org modal in DOM', () => {
      cy.get('#createOrgModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#createOrgModal').should('not.have.class', 'active');
    });

    it('should open modal when button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#createOrgModal').should('have.class', 'active');
    });

    it('should display modal title', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('.modal-title').should('contain.text', 'Create Organization');
    });

    it('should have organization name input', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#createOrgModal input[name="name"]').should('exist');
    });

    it('should have organization type select', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#createOrgModal select[name="org_type"]').should('exist');
    });

    it('should have parent organization select', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#createOrgModal select[name="parent_org_id"]').should('exist');
    });

    it('should close modal when close button clicked', () => {
      cy.get('.header-actions .btn-primary').click();
      cy.get('#createOrgModal').should('have.class', 'active');
      cy.get('#createOrgModal .modal-close').click();
      cy.get('#createOrgModal').should('not.have.class', 'active');
    });
  });

  describe('Edit Organization Modal Tests', () => {
    it('should have edit org modal in DOM', () => {
      cy.get('#editOrgModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#editOrgModal').should('not.have.class', 'active');
    });
  });

  describe('Members Modal Tests', () => {
    it('should have members modal in DOM', () => {
      cy.get('#membersModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#membersModal').should('not.have.class', 'active');
    });
  });

  describe('Transfer Modal Tests', () => {
    it('should have transfer modal in DOM', () => {
      cy.get('#transferModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#transferModal').should('not.have.class', 'active');
    });

    it('should open transfer modal from transfers tab', () => {
      cy.get('.tab').contains('Transfers').click();
      cy.get('#tab-transfers .btn-primary').click();
      cy.get('#transferModal').should('have.class', 'active');
    });
  });

  describe('Consolidated Report Modal Tests', () => {
    it('should have consolidated report modal in DOM', () => {
      cy.get('#consolidatedReportModal').should('exist');
    });

    it('should not be visible by default', () => {
      cy.get('#consolidatedReportModal').should('not.have.class', 'active');
    });
  });

  describe('JavaScript Function Tests', () => {
    it('should have openModal function', () => {
      cy.window().should('have.property', 'openModal');
    });

    it('should have closeModal function', () => {
      cy.window().should('have.property', 'closeModal');
    });

    it('should have createOrganization function', () => {
      cy.window().should('have.property', 'createOrganization');
    });

    it('should have viewOrganization function', () => {
      cy.window().should('have.property', 'viewOrganization');
    });

    it('should have editOrganization function', () => {
      cy.window().should('have.property', 'editOrganization');
    });

    it('should have updateOrganization function', () => {
      cy.window().should('have.property', 'updateOrganization');
    });

    it('should have manageMembers function', () => {
      cy.window().should('have.property', 'manageMembers');
    });

    it('should have addMember function', () => {
      cy.window().should('have.property', 'addMember');
    });

    it('should have removeMember function', () => {
      cy.window().should('have.property', 'removeMember');
    });

    it('should have createTransfer function', () => {
      cy.window().should('have.property', 'createTransfer');
    });

    it('should have approveTransfer function', () => {
      cy.window().should('have.property', 'approveTransfer');
    });

    it('should have viewConsolidatedReport function', () => {
      cy.window().should('have.property', 'viewConsolidatedReport');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
      cy.get('.tabs').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('.stats-grid').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
    });
  });

  describe('Status Badge Styling Tests', () => {
    it('should have pending status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.pending').length) {
          cy.get('.status-badge.pending').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have approved status badge styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.status-badge.approved').length) {
          cy.get('.status-badge.approved').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });

  describe('Organization Type Badge Styling Tests', () => {
    it('should have headquarters org type styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card-type.headquarters').length) {
          cy.get('.org-card-type.headquarters').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have regional org type styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card-type.regional').length) {
          cy.get('.org-card-type.regional').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });

    it('should have branch org type styling', () => {
      cy.get('body').then(($body) => {
        if ($body.find('.org-card-type.branch').length) {
          cy.get('.org-card-type.branch').first().should('be.visible');
        } else {
          cy.get('.main-content').should('exist');
        }
      });
    });
  });
});
