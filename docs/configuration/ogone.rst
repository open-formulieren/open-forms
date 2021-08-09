.. _configuration_ogone:

==============
Ingenico Ogone
==============

Open Forms supports the **Ingenico Ogone** legacy payment backend (using a ``PSPID``).

In order to make use of this module, administrators must create an *Ogone merchant* in
the administration interface.

1. Navigate to **Configuration** > **Ogone Merchant**.

2. Click **Add Ogone merchant**.

3. Complete the form fields:

    * **Label**: enter a recognizable name
    * **PSPID**: enter your Ingenico Ogone PSPID
    * **Hash algorithm**: SHA-512

4. In another browser tab or window, open the Ogone backoffice to configure the Ogone
   aspects.

5. In the Ogone backoffice, navigate to **Configuration** > **Technical Configuration**
   > **Global security parameters**

6. Fill out the following values:

    * **Hash algorithm**: SHA-512
    * **Character encoding**: UTF-8

7. Next, nagivate in the Ogone backoffice to: **Configuration** > **Technical Configuration**
   > **Data and origin verification**

8. Copy the *Checks for e-Commerce > SHA-IN pass phrase* to the Ogone merchant
   **SHA-IN passphrase** in the Open Forms administration interface.

9. In the Ogone backoffice, nagivate to: **Configuration** >
   **Technical Configuration** > **Transaction feedback**

10. Under *eCommerce*, tick the checkbox "I would like to receive transaction feedback
    parameters on the redirection URLs."

11. Then, copy *All transaction submission modes > Security for request parameters >
    SHA-OUT pass phrase* to the Ogone merchant **SHA-OUT passphrase** in the Open Forms
    administration interface.

12. Back in the Open Forms administration interface, select a pre-defined
    **Ogone endpoint** or enter a custom proxy URL, and save the configuration.

13. Finally, copy the generated **Feedback url** and finalize the Ogone backoffice
    configuration:

    * Enable *All transaction submission modes > Security for request parameters > HTTP
      request for status changes*
    * Enter the copied **Feedback url** in the field **"URL on which the merchant wishes
      to receive a deferred HTTP request, should the status of a transaction change offline."**

14. Save the changes and verify that all configuration is correct.
