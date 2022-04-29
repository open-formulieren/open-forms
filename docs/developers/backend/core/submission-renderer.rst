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
