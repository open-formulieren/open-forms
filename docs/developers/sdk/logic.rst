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

1. A user starts filling out the form. We tap into the Formio.js change event to detect
   user changes and update the React state with that. The React state is then again fed
   to the Formio.js component, effectively replacing the Formio.js state with React
   state (declaratively).

2. Data changes are debounced - after 300ms we do the actual logic check with the state at that time.

    - we only perform logic checks (api calls) if the data has changed from the data of
      the previous logic check
    - we only perform logic checks if there is data to check (backend otherwise returns
      HTTP 400)
    - once a logic check is scheduled, we update what the "data of the previous logic
      check" was so we can make the comparison above

3. The logic check returns the update submission state, update form step (configuration
   + data).

    - we update the data in the React state if it is different from the data we had. We
      merge the user-data state with the logic check data (as the user may have started
      filling out other fields while the logic check is in progress)
    - we update the Formio.js configuration by calling the imperative API. Otherwise
      the un/re-mounting in Formio takes too long & triggers React warnings ("can't
      flush discrete state updates")
    - we invoke the callback function from the parent component that a logic check has
      been executed

4. The parent component receives the submission from the logic check, and updates the
   local state, which updates the progress indicator.

Known issues
============

**Logic check callback rebuilds Formio form**

Because of the logic check - even if nothing changed, often the Formio WebForm component
(with all children) is rebuilt. This manifests as:

- `appointment dropdowns flicker`_

.. _appointment dropdowns flicker: https://github.com/open-formulieren/open-forms/issues/698
