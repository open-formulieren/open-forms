.. _developers_backend_service_fetch:

=============
Service fetch
=============

With 'service fetch' we refer to the ability to perform HTTP requests during
the form logic evaluation.

Flow
----

From the admin, the form designer configures a logic rule with the action ``fetch-from-service``.
In the JSON definition of the action, there is a ``variable`` parameter which points to a user-defined variable.
The corresponding variable contains an attribute ``service_fetch_configuration`` which contains a reference to
a :class:`openforms.variables.models.ServiceFetchConfiguration`. This configuration specifies:

- the :class:`zgw_consumers.models.Service` that will be used to perform the request
- the endpoint that will be queried
- any query parameters
- any expression to apply to the response

While the form is being filled in by a user, the :func:`openforms.submissions.form_logic.evaluate_form_logic` method
performs the request specified in the logic rule action if the trigger evaluates to ``True``.

The data in the response from the external service is processed with any expression (``jq`` or JsonLogic) specified in the
configuration. The result is set as the value field of the
:class:`openforms.submissions.models.SubmissionValueVariable` referenced in the logic rule action.

.. note::

   Before Open Forms version 2.2.0, the reference to the
   :class:`openforms.variables.models.ServiceFetchConfiguration` was stored in the logic rule
   action and not on the variable itself. Forms exported from older version may still have this reference in the JSON
   of the logic rule action, but this parameter is ignored from version 2.3.x.
