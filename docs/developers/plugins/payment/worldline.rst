.. _developers_plugins_payment_worldline:

========================
Worldline payment plugin
========================

Developers can setup a local environment to test the Worldline payment plugin. See
:ref:`_configuration_payment_worldline` on how to setup a **Worldline merchant** and
configure webhooks with the **Worldine Webhook configuration**.

Testing webhooks with Ngrok
===========================

To locally test webhooks a service like https://ngrok.com can be used. To generate
an **Auth Token** for local usage you will have to signup for an account. The following
steps assume you have access to a local docker setup.

1. After the registration process follow the  click on the **Your Authtoken** link
   in the sidebar on the leftunder the **Getting Started** section.

2. Click the **Copy** button to copy your **Authtoken** which will be used later on.

3. Run the following command to start the Ngrok container which will redirect requests
   from Worldline to your local setup:

    .. code-block:: bash

       docker run --net=host -it -e NGROK_AUTHTOKEN=<your-authtoken> ngrok/ngrok:latest http <django-server-listen-port>

4. Copy the first value shown in the Ngrok CLI interface under **Forwarding**. It's
   value will look similiar to the following value:

    .. code-block:: bash

       https://eb6b18ae86e5.ngrok-free.app

5. Next head to Worldline's Merchant Portal and create a webhook endpoint with the URL
   from step 4 in combination with the path where Open Forms expects webhooks for the
   Worldline payment plugin. The webhook path can seen in the admin overview page
   of the **Worldline merchant** section in Open Forms (whenever atleast one merchant
   is present).

6. After having the webhook endpoint created in the Merchant Portal create a form
   with the Worldline payment plugin configured and create a form submission.
   After confirming the payment in Open Forms and during the redirect to Worldline
   you should start to see requests showing up in both the logging of your django server
   and in the Ngrok CLI interface.
