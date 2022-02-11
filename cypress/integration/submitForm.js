// sample_spec.js created with Cypress
//
// Start writing your Cypress tests below!
// If you're unfamiliar with how Cypress works,
// check out the link below and learn how to write your first test:
// https://on.cypress.io/writing-first-test

describe('Basic integration test', () => {
  it('Fill in a basic form with multiple steps', () => {
    cy.visit('test-form')

    cy.formStartButton().click()

    // Step 1
    cy.formField("field1").should("be.visible").type("foo");
    cy.continueButton().should(($button) => {
      expect($button).not.to.have.attr("aria-disabled");
      $button.click();
    });

    // Step 2
    cy.formField("field2").should("be.visible").type("bar");
    cy.continueButton().should(($button) => {
      expect($button).not.to.have.attr("aria-disabled");
      $button.click();
    });

    cy.privacyCheckbox().click();
    cy.confirmationButton().click();

    cy.contains("Download uw inzending als PDF document", {timeout: 20000}).should("be.visible");
  })
})
