.. _configuration_payment_worldline:

=========
Worldline
=========

Open Forms supports the **Worldline** payment backend (using a ``PSPID``).

In order to make use of this module, administrators must create a *Worldline merchant* in
the admin interface.

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
