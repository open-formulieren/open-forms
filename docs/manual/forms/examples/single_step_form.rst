.. _example_single_step_form:

=============================
Single step form (with logic)
=============================

.. warning::  Logic evaluation for a single step form is performed after submission and
   only in the backend. This means that the user cannot see any data processed by the
   logic rules (in the backend) during the form submission.

Form creation
=============

1. Create a form with the following data:

  * **Name**: Single step form demo
  * **Type**: single step
  
  .. image:: _assets/form-type.png

1. Navigate to the **Steps and fields** tab and add a new (single) step.
2. Add a component (an email for example). It's not so important as this will not play
   a role in our example.
3. Navigate to the **Variables** tab and the **User defined** sub tab.
4. Add one variable with the name *department* (default type of string).
5. Navigate to the **Logic** tab and add the following advanced logic rule:
   
   .. image:: _assets/single_step_logic.png

   .. note:: This is an example of a logic rule where we can populate the variable with
             data based on the form url. In our example if the form url contains */test*
             then we will have *a@example.com* as the value of variable *department*,
             otherwise we will have the fallback which is *b@example.com*.

6. Click **Save** at the bottom to save the form completely.

The above form gives the opportunity to the form admin/builder to populate user defined
variables based on the value of the static variable **form_url** and the logic action.
This can be used in combination with all the available form variables.
