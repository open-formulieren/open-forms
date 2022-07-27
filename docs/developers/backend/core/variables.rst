.. _developers_backend_core_variables:

=========
Variables
=========

Submission Variables
====================

TODO: In #1705 will reorganise the info below

Static submission variables
---------------------------

Static variables are not persisted to the database and are not sent to the frontend.
They are evaluated in the backend and can be injected into the configuration or used
during logic evaluation.

The flow of how static variables are used in the backend is:

#. During the start of a submission:

   #. ``POST /submissions``: prefill data is retrieved and ``SubmissionValueVariables`` of component / user defined type
      with prefill data are saved to the backend. Any user defined variables unrelated to a step are also persisted to
      the database. Static variables are NOT persisted to the database.

   #. ``GET to /submissions/<submission_uuid>/steps/<submission_step_uuid>``: function ``get_dynamic_configuration``
      loads any data specified by ``FormVariable`` of type ``static`` and uses is to inject it in the configuration.

#. During logic evaluation:
   Class ``DataForLogic`` keeps track of the data used for the logic. It keeps track of the initial_data
   (default values + values entered by the user which are sent to the ``logic_check`` endpoint), ``static_data`` and the
   updated data (``initial_data`` with any changes made by the logic).
   The static data is used to evaluate the logic, but it is not sent back to the frontend.

#. When the step is persisted to the database:
   All the data corresponding to variables of type component / user defined is saved in a ``SubmissionValueVariable``.
