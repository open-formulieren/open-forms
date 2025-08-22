.. _configuration_prefill_yivi:

====
Yivi
====

`Yivi`_ is a identity wallet, allowing greater control for users about which personal
data they share with a website. The information available after Yivi authentication
depends on the Yivi authentication plugin configuration, and the decisions of the
authenticated user.

The **Yivi** prefill plugin can be used to access this data in order to prefill personal
or professional information of the authenticated user within a form.

.. note::

   The Yivi prefill plugin only works if the user logged in using the Yivi via OIDC
   authentication plugin.


Configuration
=============

#. First thing you need is to configure the Yivi OIDC provider and OIDC client
   (see :ref:`configuration guide <configuration_authentication_oidc_yivi>` for details)
#. Next step is to navigate to: **Configuration** > **General configuration** > **Plugin configuration**.
#. Make sure the **Yivi** prefill- and authentication plugins are enabled.
#. Click **Save**.
#. The prefill configuration is ready.

How it works
============

As mentioned above, the Yivi prefill plugin grants access to Yivi authentication data.

In order to use the plugin you need to complete the configuration above. Next step is
to enable Yivi authentication on your form, as the Yivi prefill plugin requires Yivi
authentication to work. Finally you can add prefill with Yivi to the variables.

.. _`Yivi`: https://yivi.app/
