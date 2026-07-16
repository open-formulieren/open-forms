.. _developers_backend_plugins_payment:

=======
Payment
=======

When a form submission requires payment, then the user will initiate the payment module
once the submission is completed. The payment module plugins implement specific payment
provider integrations into Open Forms.

.. contents::
   :local:
   :depth: 2
   :backlinks: none

Python API
==========

Module interface
----------------

The module-level API serves as an abstraction over the various plugins.

.. automodule:: openforms.payments.services
   :members:

Plugin interface
----------------

Payment plugins must inherit from the base plugin.

**Plugin base API**

.. automodule:: openforms.payments.base
   :members:

Available implementations
=========================

Worldline
---------

Developers can setup a local environment to test the Worldline payment plugin. See
:ref:`configuration_payment_worldline` on how to setup a **Worldline merchant** and
configure webhooks with the **Worldine Webhook configuration**.

Testing webhooks with Ngrok
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To locally test webhooks a service like https://ngrok.com can be used. To generate
an **Auth Token** for local usage you will have to signup for an account. The following
steps assume you have access to a local docker setup.

1. After the registration process click on the **Your Authtoken** link
   in the sidebar under the **Getting Started** section.

2. Click the **Copy** button to copy your **Authtoken** which will be used later on.

3. Use a service like Ngrok to expose your local development environment to the internet
   so that webhooks can be delivered.

4. Next, head to Worldline's Merchant Portal and create a webhook endpoint with the URL
   from your service in combination with the path where Open Forms expects webhooks for the
   Worldline payment plugin. The webhook path can seen in the admin overview page
   of the **Worldline merchant** section in Open Forms (whenever atleast one merchant
   is present).

5. After having the webhook endpoint created in the Merchant Portal, create a form
   with the Worldline payment plugin configured and create a form submission.
   After confirming the payment in Open Forms and during the redirect to Worldline
   you should start to see requests showing up in the logging of your django server.
