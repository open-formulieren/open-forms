.. _developers_backend_core_formio:

=========================
Core: form.io integration
=========================

Open Forms uses `form.io`_ under the hood to build and render forms, and then adds its
own layers on top of that, such as:

* implementing multi-step forms where every step is a form.io definition
* evaluating backend logic using data from earlier steps
* dynamically adapting form.io definitions as needed

This means that we process the form.io datastructures in the backend, using Python. All
the code for this is organized in the ``openforms.formio`` package.

.. versionchanged:: 2.1.0

    ``openforms.custom_field_types`` was refactored into the ``openforms.formio`` package,
    and all of the separate registries (formatters, normalizers...) were merged into a
    single compoment registry.

Form.io configuration
=====================

A form.io configuration is an object containing a ``"components"`` key mapped to an array of objects
representing the definition of form components for a specific form step.
The following is an example of such a configuration:

.. code-block:: json

    {
        "display": "form",
        "components": [
            {
                "type": "textfield",
                "key": "field_1",
                "label": "Field 1"
            },
            {
                "type": "number",
                "key": "field_2",
                "label": "Field 2"
            }
        ]
    }

Whenever a submission is created, submission data will be attached to it. The layout of this submission
data will depend on the components configuration. For instance, with the example configuration given above,
submission data will look like:

.. code-block:: json

    {
        "field_1": "some_value",
        "field_2": 1
    }


Components can be roughly categorised as layout and data components. Layout components don't have
a matching entry in the submission data.

Every component has two required properties:

* ``"key"``: A unique identifier across the form. The key represents a structured path "into" the submission
  data. A period (``.``) represents a level of nesting in this data.
* ``"type"``: The corresponding component type.

.. note::

    Submission data should be interpreted along with components configuration, as it is impossible
    to determine how data needs to be handled without this context. At times, the submission data
    can also influence the component configuration, e.g. with conditionals expressing when a component
    is visible or not.

The `form.io playground`_ can be used to play with the different components and how the submission data will
look like.

Supported features
==================

.. currentmodule:: openforms.formio.service

Formatting values for display
-----------------------------

Value formatting is done for displaying form submission data summaries, rendering
confirmation PDFs and emails... It is aware if it's in a HTML context or not. It is
heavily used in the :ref:`renderers <developers_backend_core_submission_renderer>`.

Whenever a component plugin is registered, the
:attr:`openforms.formio.registry.BasePlugin.formatter` class attribute **must** be
specified.

.. autofunction:: format_value
    :noindex:


Normalizing input data
----------------------

Data for a component can be sourced from external systems that employ different
formatting rules compared to what form.io expects. Normalizing this data helps to be
able to make proper comparisons at different stages in the submission life-cycle.

You can opt-in to this by configuring :attr:`openforms.formio.registry.BasePlugin.normalizer`.

.. autofunction:: normalize_value_for_component
    :noindex:


Dynamically modifying component configuration
---------------------------------------------

Certain component types require on-the-fly configuration rewriting, such as applying
global configuration options that may change independently from when the form is
actually being designed.

Dynamic rewriting is enabled by implementing
:meth:`openforms.formio.registry.BasePlugin.mutate_config_dynamically`. It receives the
current :class:`openforms.submissions.models.Submission` instance and a mapping of all
the variable names and values at the time.

.. autofunction:: get_dynamic_configuration
    :noindex:

For an example of a custom field type, see :class:`openforms.formio.components.custom.Date`.

Finally, the resulting resolved component definitions are evaluated with the template
engine where variable values are evaluated for compoment labels, descriptions... and
configuration based on the HTTP request is performed (see
:func:`openforms.formio.service.rewrite_formio_components_for_request`).


.. _developers_backend_core_formio_pre_registration:

Pre-registration of components
------------------------------

Some component types have specific logic which should be executed after the form is submitted,
for example updating external service with the submission information.

This logic can be implemented in the :meth:`openforms.formio.registry.BasePlugin.pre_registration_hook`.

This method is called for all components between pre-pregistration and registration steps, so the
submission reference ID is already generated and can be used.

For an example of a custom field type, see :class:`openforms.formio.components.custom.CustomerProfile`.

The complete registration flow is described in the :ref:`developers_backend_core_submissions`.


Reference
=========

Public API - ``openforms.formio.service``
-----------------------------------------

.. automodule:: openforms.formio.service
    :members:

.. autoclass:: openforms.formio.registry.BasePlugin
    :members:
    :exclude-members: verbose_name

Extending
---------

Using our :ref:`usual extension pattern <developers_extending>` you can register your
own types.

Extensions should inherit from :class:`openforms.formio.registry.BasePlugin` or
implement the same protocol(s) and be registered with their form.io type:

.. code-block:: python

    from openforms.formio.formatters.formio import DefaultFormatter
    from openforms.formio.registry import BasePlugin

    @register("myCustomType")
    class MyComponent(BasePlugin):
        formatter = DefaultFormatter


You can find some examples in ``openforms.formio.components.custom``.


Private API
-----------

Module: ``openforms.formio.dynamic_config``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openforms.formio.dynamic_config
    :members:

Module: ``openforms.formio.formatters``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openforms.formio.formatters
    :members:

Module: ``openforms.formio.rendering``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: openforms.formio.rendering
    :members:

.. _form.io: https://www.form.io/
.. _form.io playground: https://formio.github.io/formio.js/app/builder
