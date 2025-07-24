.. _developers_backend_core_variables:

===============
Core: variables
===============

There are two models for variables, :class:`openforms.forms.models.FormVariable` and
:class:`openforms.submissions.models.SubmissionValueVariable`. ``FormVariable`` objects
are related to a form while ``SubmissionValueVariable`` objects are related to a
submission (and a form variable).

Form Variables
==============

A ``FormVariable`` can have one of two sources:

* **Component**: the variable corresponds to a component in the form.
* **User defined**:
  the variable is added by the person designing the form and doesn't explicitly appear in the form. It
  can however be used for calculations or in form fields. They can also be prefilled in the same way as form components.

The API for the ``FormVariables`` has a bulk create / update endpoint. This means that a ``PUT`` call to this endpoint
will delete all existing ``FormVariables`` related to a form and replace them with the data sent in the PUT call.
If there are any existing completed submissions, the ``SubmissionValueVariables`` will not be deleted, but they will no
longer be related to a ``FormVariable``. Any in progress submission will also have ``SubmissionValueVariables`` without
a related ``FormVariable``. The result of this situation is that any data input by the user will not be saved.

.. note::

   In Open Forms versions < 2.0, form components could have the same key across different steps. Now, there is a unique
   together constraint on the ``form`` and ``key`` attributes of the ``FormVariable``. So all components must have
   different keys *across the form*. Before upgrading to 2.0, it is important to fix any duplicate keys.

   Use the management command ``check_duplicate_component_keys`` to check for duplicate keys on an environment.

.. note::

   When updating to Open Forms 2.0, all form components should have keys containing only alphanumeric characters,
   underscores, dots and dashes and should not be ended by dash or dot (and should not contain spaces).

   The management command ``check_invalid_field_keys`` can be used to check for form definitions with invalid keys
   on an environment.


Static variables
----------------

Static variables are a third type of ``FormVariable``. These are not saved in the database and only live in memory.
The endpoint ``/api/v1/variables/static`` gives a list of the static variables to which every form will have access to.

Adding new static variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Static variables can be defined by each app with the same mechanism used for plugins (see :ref:`adding_your_plugin`
for more details).

The steps to add a static variable to an app are:

#. Within the app, create a python package ``static_variables``.
#. Add an ``apps.py`` file with an ``AppConfig``. The static variables need to be imported in the ``ready`` method to be
   added to the register:

   .. code-block:: python

        from django.apps import AppConfig

        class StaticVariables(AppConfig):
            name = "openforms.<app_name>.static_variables"
            label = "<app_name>_static_variables"
            verbose_name = "<App name> static variables"

            def ready(self):
                from . import static_variables  # noqa

#. Add ``openforms.<app_name>.static_variable.apps.StaticVariables`` to the ``settings.INSTALLED_APPS``.
#. Create a ``static_apps.py`` in the ``static_variables`` package of the app which you just created.
#. Define any new static variable here using the ``BaseStaticVariable`` base class and the ``register_static_variable``
   decorator (which adds the variable to the register).

   .. code-block:: python

        @register_static_variable("<variable key>")
        class NewStaticVariable(BaseStaticVariable):
            name = _("<variable name>")
            data_type = "<variable type>"

            def get_initial_value(self, *args, **kwargs):
                ...


Submission Value Variables
==========================

Each ``SubmissionValueVariable`` is related to a ``FormVariable`` and contains the data filled in by the
user/prefill plugins/logic rules for that variable.

Flow during form filling
------------------------

#. During the start of a submission:

   * ``POST /submissions``:

     #. The prefill data is retrieved and saved in the corresponding ``SubmissionValueVariable`` (these are
        persisted to the database).
     #. The ``SubmissionValueVariable`` corresponding to a user defined ``FormVariable`` that have not been saved yet
        are initialised with the specified initial value and persisted to the database.

   * ``GET to /submissions/<submission_uuid>/steps/<submission_step_uuid>``:
     The ``SubmissionStepSerializer`` evaluates the form logic to dynamically update the form configuration. This loads
     the ``SubmissionValueVariablesState`` which contains the value of the variables and of the static data. When the
     logic updates this state, the changes are kept in memory and are not persisted to the database.

#. During logic evaluation:

   * ``POST /submissions/<submission_uuid>/steps/<submission_step_uuid>/_check_logic``:
     The endpoint receives any data input by the user in a particular step. This data is merged with data already
     present for any other step of the form and it is used to evaluate the form logic and update dynamically the form
     configuration.

#. Going to the next step (persisting a step to the database):

   * ``PUT /submissions/<submission_uuid>/steps/<submission_step_uuid>``:
     When the ``SubmissionStepSerializer`` is saved during this request, any ``SubmissionValueVariable`` related to it
     is persisted to the database.
     After the serializer is saved, any ``SubmissionValueVariable`` unrelated to a particular step is persisted if its
     data was changed in this submission step.

Rendering
---------

User defined ``SubmissionValueVariables`` are rendered when the renderer is in mode ``cli`` (command line) and
``registration`` (for the data sent to the registration backends). They are **NOT** included in the summary page of the
form, the confirmation email or the PDF of the submission report.


Working with submission data
============================

Accessing the values stored in the ``SubmissionValueVariables`` should be done through the
``SubmissionValueVariablesState``. There is a single method (``SubmissionValueVariablesState.get_data()``, see below)
which collects all submission value variables of the corresponding submission, and converts them to native Python types.
This means that submitted data for date, time, and datetime components will be converted to ``date``, ``time``, and
``datetime`` objects respectively. It allows us to easily perform operations (comparison, relative deltas, etc.) on the
values of these components, without having to deal with on-the-fly conversions from (ISO) strings to time-related
objects.

Note that the data is still stored as JSON in the database, and also exits our Python-type domain once we serialize
back for API responses.

.. autoclass:: openforms.submissions.models.submission_value_variable.SubmissionValueVariablesState
   :members:

