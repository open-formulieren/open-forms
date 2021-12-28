.. _installation_form_hosting:

============
Form hosting
============

Forms designed with Open Forms would typically be included on some CMS via the
:ref:`Javascript snippet <developers_sdk_embedding>`. However, if this is not possible,
forms can also be accessed through the UI portion of Open Forms.

This section of the documentation documents the various configuration aspects available
to tweak this to your organization needs. It is assumed that open forms is deployed on
a subdomain such as ``open-forms.gemeente.nl``, but other approaches are also possible.


Organization configuration
==========================

Published forms are available via the URL ``https://open-forms.gemeente.nl/<form-slug>``,
which renders the form in a minimal skeleton. The look and feel of this skeleton can be
modified by administrators, to some extent. See :ref:`configuration_general_styling`.

Deployment configuration
------------------------

The privacy policy URL in the footer is taken from the ``EHERKENNING_PRIVACY_POLICY``
environment variable, which is configured at deployment time. See
:ref:`installation_config_eherkenning` for more information.


Configuration with CNAME DNS records
====================================

It's possible to deploy Open Forms as a "SaaS" service - the service provider manages
the installations of Open Forms on their own (internal) domain and organizations can
use this.

Organizations can use CNAME DNS records to point ``https://open-forms.gemeente.nl`` to
the internal host ``open-forms.gemeente.service-provider.nl``, for example. However,
some special care is needed for this.

* The CNAME record(s) MUST be included in the ``ALLOWED_HOSTS``
  :ref:`configuration parameter<installation_environment_config>`.

* The TLS certificate used must include the CNAME domain name.
