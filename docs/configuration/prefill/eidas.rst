.. _configuration_prefill_eidas:

=========================
eIDAS for natural persons
=========================

`eIDAS`_ (Electronic Identification and Trust Services) is an European Union regulation,
to allow european citizen to digitally authenticate in any european country using their
national identity. When authenticating with eIDAS, the user supplies some basic personal
information; their first- and lastname, date of birth and their BSN or other national
identification.

The **eIDAS** prefill plugin can be used to access this data in order to prefill personal
information of the authenticated user within a form.

.. note::

   The eIDAS prefill plugin only works if the user logged in using the eIDAS via OIDC
   authentication plugin.


Configuration
=============

#. First ensure the eIDAS OIDC provider and OIDC client are configured (see
   :ref:`configuration guide <configuration_authentication_oidc_eidas>` for details)
#. Then, navigate to: **Configuration** > **General configuration** > **Plugin configuration**.
#. Make sure the **eIDAS** prefill- and authentication plugins are enabled.
#. Click **Save**.
#. The prefill configuration is ready.

How it works
============

As mentioned above, the eIDAS prefill plugin grants access to eIDAS authentication data.

In order to use the plugin you need to complete the configuration above. Next step is
to enable eIDAS authentication on your form, as the eIDAS prefill plugin requires eIDAS
authentication to work. Finally you can add prefill with eIDAS to the components and
variables.

.. _`eIDAS`: https://www.logius.nl/diensten/eidas
