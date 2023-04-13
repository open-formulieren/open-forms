.. _configuration_registration_email:

=====
Email
=====

Open Forms can be configured to register form submissions by email.

Sending the registrations uses the global :ref:`email-settings` and does not
require additional configuration. The receiving address as well as the email subject can be configured when
building the form.

.. note::

    Email should be configured by the Open Forms supplier and also requires
    proper setup of SPF and/or DMARC-records.

Templates
---------

By default, Open Forms uses the templates configured in the admin, under
**Configuratie** > **Algemene configuratie** > **Registratie email**. Here it is possible to specify:

* The subject of the registration email
* The subject of the email sent once there is an update to the payment status
* The HTML template for the body of the email
* The text template for the body of the email

.. note::

   The text template is needed in case the email client used to read the registration email does not support rendering
   HTML. Therefore, it should contain the same information of the HTML template.

Both in the templates for the subject and the body, one can use the Django template syntax. For more information on how
to use this syntax and which variables/expressions are available, see the section :ref:`manual_templates`.

It is also possible to specify a template for each form. This can be configured in the form editor, under the tab
**Registratie** and then selecting **E-mail registratie** in the drop down menu.

File uploads/attachments
------------------------

By default, any files uploaded as part of the submission are not added as email attachments.
Instead, the e-mail contains download links to the individual files. These links require
users to be authenticated and have the correct permissions:

* users must be staff users
* users must have permission to read file attachments. The standard group "Behandelaars"
  offers this permission.

However, you can override this on a global *and* per-form level. It is the
responsibility of the form designer to ensure that the upload file size limits are
configured appropriately to ensure that emails will not be rejected because of too-large
sizes. This depends largely on the mail/SMTP service you are using, see also
:ref:`email-settings`.

.. note::

    Email attachments are typically restricted in size, making it impossible to actually
    deliver the emails for further processing.
