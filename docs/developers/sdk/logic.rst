.. _developers_sdk_logic:

=====
Logic
=====

Open Forms supports complex logic evaluated in the backend. Form designers can set up
logical rules which consist of:

* a trigger - a condition that must evaluate to be "true"
* one or more actions that are performed if the trigger evaluates to "true"

The SDK makes the necessary calls to ask for logic evaluation.

Algorithm
=========

1. A user starts filling out the form. This triggers the FormIO WebForm component ``onChange`` function.
   At this point any logic rules specified on the components are checked and the form is re-rendered if anything has
   changed (for example, a component has become visible). The Formio.js 'change' event is emitted, which we use
   to detect user changes and update the React state, as well as schedule the logic checks in the backend.

2. Data changes are debounced - after 1000ms we do the actual logic check with the state at that time.

    - we only perform logic checks (api calls) if the data has changed from the data of
      the previous logic check
    - we only perform logic checks if there is data to check (backend otherwise returns
      HTTP 400)
    - once a logic check is scheduled, we update what the "data of the previous logic
      check" was so we can make the comparison above
    - the logic check is performed on the default form configuration with the data received from the frontend

3. The logic check returns the updated submission state, updated form step (configuration
   + data).

    - we update the data in the React state if it is different from the data we had. We
      merge the user-data state with the logic check data (as the user may have started
      filling out other fields while the logic check is in progress)
    - if the configuration has changed, we update the Formio.js configuration by calling the imperative API
      (``setForm``). Otherwise the un/re-mounting in Formio.js takes too long & triggers React warnings ("can't
      flush discrete state updates").
    - the call to ``setForm`` re-renders the form. While re-rendering, any logic rules on the components are
      re-evaluated. This means that rules on the components will override any changes of the backend logic if they are
      in conflict.
    - we invoke the callback function from the parent component that a logic check has
      been executed

4. The parent component receives the submission from the logic check, and updates the
   local state, which updates the progress indicator.

Frontend rules vs Backend rules
===============================

When building a form, it is possible to attach logic rules to each component (in the modal used to define the component).
These are referred to as 'frontend rules', while the rules defined in the logic tab of the form builder are referred
to as 'backend rules'. The key differences between the two are:

**Frontend rules**

- Are evaluated quicker, because they are evaluated in the frontend
- Override the results of backend rules
- Cannot check conditions over multiple steps
- Cannot change the state of form steps between applicable/not-applicable

**Backend rules**

- Can check conditions over multiple steps
- Can change the state of form steps between applicable/not-applicable

.. note::

   It has been reported that using both frontend rules and backend rules can cause the focus of the form to jump
   in unexpected ways.

Known issues
============

**Logic check callback rebuilds Formio form**

Because of the logic check - even if nothing changed, often the Formio WebForm component
(with all children) is rebuilt. This manifests as:

- `appointment dropdowns flicker`_

.. _appointment dropdowns flicker: https://github.com/open-formulieren/open-forms/issues/698
