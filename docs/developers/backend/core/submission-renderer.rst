.. _developers_backend_core_submission_renderer:

.. currentmodule:: openforms.submissions.rendering

====================
Submission rendering
====================

Submission rendering is the concept of outputting the submitted data for a given form
in a particular format. A couple of examples:

* An overview of the information and submitted data in a confirmation PDF
* A summary of the submitted data in an e-mail confirmation
* Overview of the submitted data in a registration e-mail
* Exporting the submission data to a particular format (CSV, JSON...)

Rendering submissions is dependent on implementation details. E.g., for the e-mails
and PDF you typically output to HTML (the HTML gets converted to a PDF), but for e-mail
you *also* want a plain text variant for e-mail clients that can't render rich text.

Additionally, the markup for the e-mail and PDF is different due to the difference in
CSS and layout-capabilities. And, for exports you want the raw values with their proper
data-types, while for other render modes you need the human-readable presentation of the
data.

All these challenges are solved by leveraging a :class:`Renderer` class. You specify the
desired render mode and whether HTML is desired or not, and the underlying
data-structures can format themselves in a suitable fashion.

Command-line interface
======================

The management command ``render_report`` allows you do debug render mode specific
implementations. By default it outputs in the CLI render mode, but you can override this.

.. note::
   This command always groups the formio component labels and values in a table,
   independent from the selected render mode. The visibility rules of components
   depending on the render mode are respected though.

To get full command documentation, run:

.. code-block:: bash

    python src/manage.py render_report --help

Example command and output:

.. code-block:: bash

    LOG_LEVEL=WARNING src/manage.py render_report 563

.. code-block:: none

    Submission 563 - Development
        Stap 1
            ----------------------  --------------------------
            Eenvoudig tekstveld     Veld 1 ingevuld
            Toon veldengroep?       Ja
            Veldengroep met logica
            Nested 1                Nested veld in veldengroep
            Toon stap 2?            ja
            ----------------------  --------------------------
        Stap 2
            -------------------  -----------------------
            Vrije tekst, stap 2  Stap 2 ingevuld
            WYSIWYG              WYSIWYG content
            Bijlage              bijlage: sample.pdf
            Ondertekening        handtekening toegevoegd
            -------------------  -----------------------

Reference
=========

Renderer class
--------------

Example usage:

.. code-block:: python

    renderer = Renderer(submission, mode=RenderModes.pdf, as_html=False)
    for node in renderer:
        print(node.render())


.. autoclass:: Renderer
   :members:

   .. automethod:: __iter__

Node types
----------

.. autoclass:: openforms.submissions.rendering.nodes.FormNode
   :members:


.. autoclass:: openforms.submissions.rendering.nodes.SubmissionStepNode
   :members:


Formio integration
------------------

The renderers extend to the FormIO component types.

You can :ref:`extend <developers_extending>` your custom FormIO types by using the
register hook, the mechanism is identical to the usual :ref:`plugin system <plugins_index>`.

**Example**

.. code-block:: python

    from openforms.formio.rendering.nodes import ComponentNode
    from openforms.formio.rendering.registry import register


    @register("my-custom-component-type")
    class MyCustomComponentType(ComponentNode):
        ...

.. automodule:: openforms.formio.rendering.nodes
   :members:

**Vanilla FormIO components**

The following component types are automatically picked up by Open Forms

.. automodule:: openforms.formio.rendering.default
   :members:
