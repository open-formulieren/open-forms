======
Qmatic
======

This plugin is made for the *Qmatic Orchestra Calendar Public Appointment API*.

#. You will need to have a contract with `Qmatic`_ to use this plugin.
#. In Open Forms navigate to: **Configuration** > **Overview**
#. In the **Appointment plugins** group, click on **Configuration** for the **Qmatic configuration** line.
#. Find the **Calendar API field**, click the **Green Plus Button** and fill in the following details:

   * **Label**: Qmatic
   * **Type**: ORC (Overige)
   * **API root URL**: *The API endpoint provided by Qmatic*

     Make sure to *not* include the trailing ``v1`` or ``v2``!
   * **Authorization type**: API key
   * **Header key**: ``X-Api-Key``
   * **Header value**: *The API-key provided by Qmatic*
   * **OAS**: *URL to the Open API-specification provided by Qmatic*

#. Next, verify and check or uncheck the customer contact detail fields that are
   relevant for your environment.

#. Click **Save**

.. _`Qmatic`: https://www.qmatic.com/solutions/online-appointment-booking/
