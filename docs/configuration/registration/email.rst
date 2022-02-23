.. _configuration_registration_email:

=====
Email
=====

Open Forms can be configured to register form submissions by email.

Sending the registrations uses the global :ref:`email-settings` and does not 
require additional configuration. The receiving address can be configured when 
building the form.

.. note::
    
    Email should be configured by the Open Forms supplier and also requires
    proper setup of SPF and/or DMARC-records.

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

    Email attachments are typicall restricted in size, making it impossible to actually
    deliver the emails for further processing.
