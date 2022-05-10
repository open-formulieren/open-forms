// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })


// Find the button to start the form
Cypress.Commands.add("formStartButton", () => {
    return cy.get('.openforms-button--primary');
})

// Find a form field by its key
Cypress.Commands.add("formField", (fieldKey, timeout=10000) => {
    cy.wait(500)
    return cy.get(`.openforms-form-control--${fieldKey}`, {timeout: timeout}).should("be.visible");
})

// Find the continue button
Cypress.Commands.add("continueButton", (timeout=10000) => {
    return cy.get('button[name="next"][type="submit"]', {timeout: timeout});
})

// Continue to the next form step
Cypress.Commands.add("nextStep", () => {
    cy.continueButton().should(($button) => {
        expect($button).not.to.have.attr("aria-disabled");
        $button.click();
    });
})

// Find the privacyCheckbox
Cypress.Commands.add("privacyCheckbox", (timeout=20000) => {
    return cy.get('input[name="privacy"]', {timeout: timeout});
})

// Find the confirmationButton
Cypress.Commands.add("confirmationButton", (timeout=20000) => {
    return cy.get('button[name="confirm"]', {timeout: timeout});
})
