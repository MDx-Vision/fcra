// Exhaustive test for /dashboard/calendar
describe('Calendar Page - /dashboard/calendar', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'testpass123');
    cy.visit('/dashboard/calendar');
  });

  describe('Page Load Tests', () => {
    it('should load the page without errors', () => {
      cy.url().should('include', '/dashboard/calendar');
      cy.get('.main-content').should('be.visible');
    });

    it('should have correct page title', () => {
      cy.title().should('contain', 'Calendar');
    });

    it('should not return server errors', () => {
      cy.request('/dashboard/calendar').its('status').should('be.oneOf', [200, 302]);
    });
  });

  describe('Header Tests', () => {
    it('should display the page header', () => {
      cy.get('h1').should('contain.text', 'Deadline Calendar');
    });

    it('should display header section', () => {
      cy.get('.header').should('be.visible');
    });
  });

  describe('Calendar Container Tests', () => {
    it('should display calendar container', () => {
      cy.get('.calendar-container').should('be.visible');
    });

    it('should display calendar element', () => {
      cy.get('#calendar').should('exist');
    });

    it('should initialize FullCalendar', () => {
      // Wait for calendar to initialize
      cy.get('#calendar').should('be.visible');
      cy.get('.fc').should('exist');
    });
  });

  describe('Calendar Navigation Tests', () => {
    it('should display calendar toolbar', () => {
      cy.get('.fc-toolbar').should('exist');
    });

    it('should have navigation buttons', () => {
      cy.get('.fc-button').should('have.length.at.least', 1);
    });

    it('should display current month/view title', () => {
      cy.get('.fc-toolbar-title').should('exist');
    });
  });

  describe('Filter Tests', () => {
    it('should display Apply Filters button', () => {
      cy.get('.btn-primary').contains('Apply Filters').should('be.visible');
    });

    it('should display Clear Filters button', () => {
      cy.get('.btn-secondary').contains('Clear Filters').should('be.visible');
    });

    it('should have clickable filter buttons', () => {
      cy.get('.btn-primary').contains('Apply Filters').should('not.be.disabled');
    });
  });

  describe('Modal Tests', () => {
    it('should have deadline modal element', () => {
      cy.get('#deadlineModal').should('exist');
    });

    it('should have modal hidden by default', () => {
      cy.get('.modal-overlay.active').should('not.exist');
    });

    it('should have modal close button', () => {
      cy.get('.modal-close').should('exist');
    });

    it('should have modal body with detail fields', () => {
      cy.get('#modalClient').should('exist');
      cy.get('#modalType').should('exist');
      cy.get('#modalDeadlineDate').should('exist');
    });
  });

  describe('Responsive Tests', () => {
    it('should display correctly on desktop (1280px)', () => {
      cy.viewport(1280, 720);
      cy.get('.main-content').should('be.visible');
      cy.get('.calendar-container').should('be.visible');
    });

    it('should display correctly on tablet (768px)', () => {
      cy.viewport(768, 1024);
      cy.get('.main-content').should('be.visible');
      cy.get('#calendar').should('be.visible');
    });

    it('should display correctly on mobile (375px)', () => {
      cy.viewport(375, 667);
      cy.get('.main-content').should('be.visible');
      cy.get('h1').should('be.visible');
    });
  });

  describe('Button Functionality Tests', () => {
    it('should have primary button styling', () => {
      cy.get('.btn-primary').should('exist');
    });

    it('should have secondary button styling', () => {
      cy.get('.btn-secondary').should('exist');
    });
  });

  describe('Accessibility Tests', () => {
    it('should have proper heading hierarchy', () => {
      cy.get('h1').should('have.length.at.least', 1);
    });

    it('should have accessible calendar element', () => {
      cy.get('#calendar').should('be.visible');
    });
  });

  describe('Calendar View Tests', () => {
    it('should display calendar grid', () => {
      cy.get('.fc-view').should('exist');
    });

    it('should display day cells', () => {
      cy.get('.fc-daygrid-day, .fc-day').should('have.length.at.least', 1);
    });
  });
});
