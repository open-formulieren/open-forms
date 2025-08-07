.. _configuration_payment_worldline:

=========
Worldline
=========

Open Forms supports the **Worldline** payment backend (using a ``PSPID``).

In order to make use of this module, administrators must create a *Worldline merchant* and
a *Worldline Webhook entry* in the admin interface.

1. Navigate to **Configuration** > **Configuration Overview**. In the **Payment Provider Plugin** group, click on **Configuration** for the **Worldline: Test merchant** line.

2. Click **Add Worldline merchant**.

3. Complete the form fields:

    * **Label**: *Fill in a human readable label*, for example: ``My Worldline``
    * **PSPID**: *Your Worldline PSPID*
    * **Hash algorithm**: SHA-512

4. In another browser tab or window, open the Worldline backoffice to configure the Worldline
   aspects.

5. In the Worldline backoffice, navigate to **Configuration** > **Technical Configuration**
   > **Global security parameters**

6. Fill out the following values:

    * **Hash algorithm**: SHA-512
    * **Character encoding**: UTF-8

7. Next, head to Worldline's merchant portal and click on **Developers** in the sidebar
   on the left.

8. Generate the following values:

    * **API Key**
    * **API Secret**

9. Copy the **API Key** and **API Secret** into the corresponding fields in
   the **Worldline Merchant** that was created in step 3.

10. Save the changes and verify that all configuration is correct.

11. Previous steps were done to setup the redirection between Open Forms and Worldline,
    the following steps will configure the webhook integration. Nagivate in the
    Worldline backoffice to: **Configuration** > **Technical information** > **API settings**

12. Generate a **WebhooksKey** and a **WebhooksKeySecret** and save these values somewhere safe.

13. Head back to the Open Forms admin and navigate to **Miscellaneous** > **Worldline webhook entries**.

14. Click **Add Worldline Webhook Entry**.

15. Copy the **WebhooksKey** from step 12 into the **Webhook Key ID** form field and the **WebhooksKeySecret**
    into the **Webhook Key Secret** form field.

16. Save the changes.

17. Navigate in the Open Forms admin to the **Worldline merchant** list overview and copy
    the **Feedback url** value.

18. Copy the **Feedback url** into the **Endpoint Urls** text area in the Worldline backoffice
    and save the configuration. The **Endpoint Urls** field is on the same page
    the **WebhooksKey** and **WebhooksKeySecret** were generated (in step 12).

19. Save the changes and verify that all configuration is correct.
