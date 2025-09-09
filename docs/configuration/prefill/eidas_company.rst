.. _configuration_prefill_eidas_company:

===================
eIDAS for companies
===================

`eIDAS`_ (Electronic Identification and Trust Services) is an European Union regulation,
to allow european citizen and companies to digitally authenticate in any european country
using their national identity. When authenticating with eIDAS, the user supplies some
basic personal information; their first- and lastname, date of birth and their BSN or
other national identification. When authenticating as a company, the legal name of the
company will also be made available.

The **eIDAS** prefill plugin can be used to access this data in order to prefill personal
and company information of the authenticated company and acting person within a form.

.. note::

   The eIDAS for companies prefill plugin only works if the user logged in using the
   eIDAS for companies via OIDC authentication plugin.


Configuration
=============

#. First ensure the eIDAS for companies OIDC provider and OIDC client are configured
   (see :ref:`configuration guide <configuration_authentication_oidc_eidas_company>`
   for details)
#. Then, navigate to: **Configuration** > **General configuration** > **Plugin configuration**.
#. Make sure the **eIDAS for companies** prefill- and authentication plugins are enabled.
#. Click **Save**.
#. The prefill configuration is ready.

How it works
============

As mentioned above, the eIDAS for companies prefill plugin grants access to eIDAS
authentication data.

In order to use the plugin you need to complete the configuration above. Next step is
to enable eIDAS for companies authentication on your form, as the eIDAS for companies
prefill plugin requires eIDAS for companies authentication to work. Finally you can add
prefill with eIDAS for companies to the components and variables.

.. _`eIDAS`: https://www.logius.nl/diensten/eidas
