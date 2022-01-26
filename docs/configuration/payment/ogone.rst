.. _configuration_payment_ogone:

==============
Ingenico Ogone
==============

Open Forms supports the **Ingenico Ogone** legacy payment backend (using a ``PSPID``).

In order to make use of this module, administrators must create an *Ogone merchant* in
the admin interface.

1. Navigate to **Configuration** > **Overview**. In the **Payment Provider Plugin** group, click on **Configuration** for the **Ogone legacy: Test merchant** line.

2. Click **Add Ogone merchant**.

3. Complete the form fields:

    * **Label**: *Fill in a human readable label*, for example: ``My Ogone``
    * **PSPID**: *Your Ingenico Ogone PSPID*
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
   **SHA-IN passphrase** in the Open Forms admin interface.

9. In the Ogone backoffice, nagivate to: **Configuration** >
   **Technical Configuration** > **Transaction feedback**

10. Under *eCommerce*, tick the checkbox "I would like to receive transaction feedback
    parameters on the redirection URLs."

11. Under *Direct HTTP server-to-server request*

   * Select the radio button *Online but switch to a deferred request when the online requests fail.*
   * Switch back to the Open Forms admin to copy the value of **Feedback url**, return to the Ogone backoffice and paste it
     into each of the two Ogone fields labelled "If the payment's status is.. "
   * In the **Request method** radio group select the option *POST*

12. Under *Dynamic e-Commerce parameters* clear everything from the select box except ``NCERROR``, ``PAYID``, ``ORDERID`` and ``STATUS``

13. Then copy the value of *All transaction submission modes > Security for request parameters >
    SHA-OUT pass phrase* to the Ogone merchant **SHA-OUT passphrase** in the Open Forms
    admin interface.

14. Back in the Open Forms admin interface, select a pre-defined
    **Ogone endpoint** or enter a custom proxy URL, and save the configuration.

15. Finally, copy the generated **Feedback url** and finalize the Ogone backoffice
    configuration:

    * For the radio buttons *All transaction submission modes > Security for request parameters > HTTP
      request for status changes* select the options *For each offline status change (payment, cancellation, etc.)*
    * Enter the copied **Feedback url** in the field **"URL on which the merchant wishes
      to receive a deferred HTTP request, should the status of a transaction change offline."**


16. Save the changes and verify that all configuration is correct.
