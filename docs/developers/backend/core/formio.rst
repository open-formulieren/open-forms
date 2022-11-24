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
:func:`openforms.formmio.service.rewrite_formio_components_for_request`).

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
