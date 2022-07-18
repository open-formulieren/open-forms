.. _developers_backend_dev_rendering:

========================
Rendering in development
========================

During development, you can visualize how some non-web target renders of submission
data look like through the use of some development-only views.

For the low level renderer API, see :ref:`developers_backend_core_submission_renderer`.
Typically the development views make use of this low-level renderer API.

All the relevant URL routes are listed in :mod:`openforms.urls` behind the
``settings.DEBUG`` setting.

E-mails
=======

The e-mail debug views allow you to (roughly) visualize the styling of the e-mails that
are sent out, both in HTML or plain text mode.

There are two types of e-mails:

* confirmation e-mail sent to the person filling out the form
* registration e-mail sent as part of the backend registration process

You can access these at ``http://localhost:8000/dev/email/confirmation/:submission_id``
and ``http://localhost:8000/dev/email/registration/:submission_id`` respectively.

Both views support a query string parameter ``?mode=text`` to toggle between plain text
or HTML templates. HTML is the default.

Summary PDF
===========

The summary PDF is rendered using a HTML-to-PDF library, so most of the styling can be
developed and tweaked using the browser. Page-specific styling cannot be tested this
way though, for that it's better to use the ``render_confirmation_pdf`` management
command.

You can access the PDF preview at ``http://localhost:8000/dev/submissions/:id/pdf``.
