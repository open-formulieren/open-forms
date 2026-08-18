.. _developers_backend_core_logic_engine:

==================
Core: logic engine
==================

Open Forms has a "logic engine" that powers the dynamic behaviour of a form with its
given input data. Below you find an attempt to document its behaviour.

Backend vs. frontend logic
==========================

Historically, there have been two kinds of form logic:

* frontend logic, which you typically find on the "Advanced" tab of a form component.
  This logic is limited to the visibility of a component based on the value(s) of another
  component.
* backend logic, which you find on the "Logic" tab of a form.

Frontend logic is relatively simple in concept, as it only controls the visibility of a
component in the same form step. Backend logic allows defining logic rules that span
one or more form steps and may also control other aspects, such as:

* modifying component properties (required, hidden/visible, read-only)
* calculating and updating values of any variable, including user defined variables
* triggering DMN evaluation
* triggering service fetch calls
* marking a form step as applicable or not
* blocking form submission
* ...

The distinction used to clear because one was evaluated in the frontend and the other
in the backend, but as of Open Forms 3.5.x (some) backend logic can also be evaluated
in the browser (frontend).

.. tip:: Whatever kind of logic is used, it is *always* executed in the backend for
   security reasons - client-side evaluation and results cannot be trusted. So even the
   "frontend logic" has an implementation in the backend.

Policy for where/when the logic is evaluated
============================================

Logic rules are usually "functions" that take form field values as input and produce
a certain output or side-effect. Form field values are dynamic user input, so in essence,
every user interaction that leads to a value change of *a* form field should trigger
a logic evaluation run.

That is effectively what happens in the SDK, with some debouncing set up to avoid
spamming backend systems.

The SDK has two options:

* evaluate the logic rules client-side and apply the results/side-effects immediately
* call the backend logic evaluation endpoint with the form field values as input data

The former is fast as it completely avoids an entire HTTP roundtrip, but it cannot be
used all situations because server-side data cannot safely be exposed to the browser,
as there's a risk of sensitive data leaking from the server. This concerns
(non-exhaustive):

* values of user defined variables that only exist on the server
* service fetch calls, typically they use internal API endpoints and require credentials
* DMN evaluation, which requires internal API endpoints

The backend relays metadata to the frontend whether logic rules can be evaluated in the
frontend or not. Whatever the conclusion is, during submission (of a step and the form
as a whole), all logic rules are evaluated on the server as well to be able to perform
input validation.

Logic engine details
====================

Given a form in Open Forms with:

* one or more form steps
* dynamic form field label evaluation (e.g. usage of ``{{ otherField }}`` expressions)
* components that require dynamic settings (e.g. file upload with
  "use global configuration" option enabled, the ``npFamilyMembers`` component,
  ``radio``/``select``/``selectboxes`` components that use reference lists values...)
* conditionals expressed between components (e.g. component X is visible when component
  Y has value Z)
* and backend logic rules (e.g. mark step 3 applicable if condition X)

then the logic engine will perform the following steps in the described order:

1. Load the form submission and the particular step that may require logic evaluation.
2. Take the current submission data as input for evaluation.
3. If unsaved user input is being evaluated, update the current submission data (in
   memory) with the unsaved input data.
4. If unsaved user input is being evaluated, reset potentially persisted step data if
   the field is hidden with clear-on-hide in the frontend.
5. Evaluate the "frontend logic" conditionals - every component is checked if it's
   conditionally hidden or visible. If it's hidden and clear-on-hide is enabled, the
   evaluation data is immediately updated. If it was hidden and becomes visible, a value
   for the component is immediately populated in the evaluation data. This is done for
   every component - top to bottom in the component tree, depth first.
6. Collect the backend logic rules to evaluate (depending on the step currently being
   evaluated). The relevant rules and steps are set when the form is saved by a form
   designer in the admin.
7. Evaluate each logic rule. Value updates in the evaluation data are immediately
   applied, and side-effects are collected. Hidden/visible updates are processed the
   same way as the frontend logic rules. Service fetch, DMN... are evaluated at this
   stage.
8. Now the final evaluation data state is reached, and this input is used for further
   engine operations.
9. Evaluate the dynamic formio configuration:

    - rewrite formio components/configuration, e.g. convert the ``npFamilyMembers`` to a
      ``selectboxes`` component and/or fetch the component options from the configured
      reference lists
    - set the translated component validation error messages
    - set the translated component properties (like label, description...)
    - inject the values obtained from prefill

10. Apply the logic side effects, e.g. marking fields as required, read-only, marking
    steps as applicable/not-applicable...
11. Interpolate the template expressions used in component definitions, as this required
    the properly translated text to be set and the evaluation data to be resolved.
12. Calculate the difference in variables state vs. the input data, and report back what
    needs to be updated on the client side.

**Client-side variant**

When logic is evaluated client side, the same order of steps is applied, but not
everything is available client side. In those situations, the logic rules will be marked
to run on the server.

Currently unsupported client side:

* anything that requires server-side user defined variables
* (Django) template evaluation/interpolation
* prefill injection
* dynamic component rewriting
* selecting the right translations

**Logic rule serialization and partial logic evaluation**

The limitations of the client side logic are mitigated considerably by
*partial json logic evaluation*. When the form step definition and its logic rules are
retrieved from the backend, the backend already evaluates things as much as possible
and sort of "pre-compiles" the backend logic rules when it's safe to do so. This can
effectively make certain user-defined variables "dissapear" and enable client-side logic
after all.
