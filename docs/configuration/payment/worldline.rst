.. _configuration_payment_worldline:

=========
Worldline
=========

Open Forms supports the **Worldline** payment backend (using a ``PSPID``).

In order to make use of this module, administrators must create a *Worldline merchant* and
a *Worldline Webhook configuration* in the admin interface.

1. Navigate to **Configuration** > **Configuration Overview**. In the **Payment Provider Plugin** group, click on **Configuration** for the **Worldline: Test merchant** line.

2. Click **Add Worldline merchant**.

3. Complete the form fields:

    * **Label**: *Fill in a human readable label*, for example: ``My Worldline``
    * **PSPID**: *Your Worldline PSPID*

4. Next, in another browser tab or window, head to Worldline's Merchant Portal
   and click on **Developers** > **Payment API** in the sidebar on the left.

5. Generate the following values:

    * **API Key ID**
    * **Secret API Key**

6. Copy the **API Key** and **Secret API Key** into the corresponding fields in
   the **Worldline Merchant** that was accessed in the Open Forms admin in step 3.

7. Save the changes and verify that all configuration is correct.

8. The previous steps configured the redirect flow between Open Forms and Worldline,
    the following steps will configure the webhook integration. Nagivate in the
    Worldline Merchant Portal sidebar to: **Developer** > **Webhooks**

9. Generate webhook credentials by clicking on the **Generate webhook keys**
   and save the **Webhook ID** and **Secret webhook key** values somewhere safe.

10. Head back to the Open Forms admin and navigate to **Configuration** > **Worldline webhook configuration**.

11. Copy the **Webhook ID** from step 12 into the **Webhook Key ID** form field and the **Secret webhook key**
    into the **Webhook Key Secret** form field.

12. Copy the **Feedback url** from the webhook configuration page.

13. Save the changes.

14. Head back to Worldline's Merchant Portal and navigate to the **Webhooks** section
    (see step 8). Click on the **Add webhook endpoint button** and fill in the
    **Feedback url** that was copied in step 12 and click **Confirm**.
