.. _configuration_payment_worldline:

=========
Worldline
=========

Open Forms supports the **Worldline** payment backend (using a ``PSPID``).

In order to make use of this module, administrators must create a *Worldline merchant* and
a *Worldline Webhook configuration* in the admin interface.

#. Navigate to **Configuration** > **Configuration Overview**. In the **Payment Provider Plugin**
   group, click on **Add merchant** for the **Worldline merchant** line (or configure an existing merchant).

#. Complete the form fields to _`generate a merchant`:

   * **Label**: *Fill in a human readable label*, for example: ``My Worldline``
   * **PSPID**: *Your Worldline PSPID*

#. Next, in another browser tab or window, head to Worldline's Merchant Portal
   and click on **Developers** > **Payment API** in the sidebar on the left.

#. Generate the following values:

   * **API Key ID**
   * **Secret API Key**

#. Copy the **API Key** and **Secret API Key** into the corresponding fields in
   the **Worldline Merchant** that was accessed in the Open Forms admin, `see previous step <generate a merchant_>`_.

#. Save the changes and verify that all configuration is correct.

#. The previous steps configured the redirect flow between Open Forms and Worldline,
   the following steps will configure the _`webhook integration`.
   Navigate in the Worldline Merchant Portal sidebar to: **Developer** > **Webhooks**

#. Generate webhook credentials by clicking on the **Generate webhook keys**
   and save the **Webhook ID** and **Secret webhook key** values somewhere safe.

#. Head back to the Open Forms admin and navigate to **Configuration** > **Worldline webhook configuration**.

#. Copy the **Webhook ID** from the `previous step <webhook integration_>`_ into
   the **Webhook Key ID** form field and the **Secret webhook key** into the
   **Webhook Key Secret** form field.

#. Copy the **Feedback url** from the _`webhook configuration page`.

#. Save the changes.

#. Head back to Worldline's Merchant Portal and navigate to the **Webhooks** section
   (see `previous step <webhook integration_>`_). Click on the
   **Add webhook endpoint button** and fill in the **Feedback url** that was copied
   in the `previous step <webhook configuration page_>`_ and click **Confirm**.

Now that a **Worldline Merchant** is configured and the **Worldline webhook configuration** is set up,
it is possible to select the Worldline payment backend under the **Payment provider** subsection in the
**Product & payment** tab. In addition to selecting the merchant, there are also fields to configure the
payments description (only shown in the Backoffice) and the template that should be used during the payment
process, which is what the **variant** field is for.
