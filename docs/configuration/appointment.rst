.. _configuration_appointment:

=========================
Appointment configuration
=========================

Appointments can be made using two separate services.  JCC and Qmatic.
Open Forms can be configured to make use of one of these services.

JCC
---

1. In Open Forms navigate to: **Configuration** > **JCC configuration**
2. Click the **Green Plus Button** and fill in the following details:

   * **Label**: JCC
   * **Ontvangende organisatie**: Open Forms
   * **Ontvangende applicatie**: Open Forms
   * **Versturende organisatie**: Horstaandemaas
   * **Versturende applicatie**: Afspraak Acceptatie
   * **URL**: https://example.com/jcc/GenericGuidanceSystem2.asmx?wsdl

3. Click **Save**

Qmatic
------

This plugin is made for the *Qmatic Orchestra Calendar Public Appointment API* and is currently untested.

1. You will need to have a contract with `Qmatic`_ to use this plugin.
2. In Open Forms navigate to: **Configuration** > **Qmatic configuration**
3. Click the **Green Plus Button** and fill in the following details:

   * **Label**: Qmatic
   * **Type**: ORC (Overige)
   * **API root URL**: *The API endpoint provided by Qmatic*
   * **Authorization type**: API key
   * **Header key**: X-Api-Key
   * **Header value**: *The API-key provided by Qmatic*
   * **OAS**: *URL to the Open API-specification provided by Qmatic*

4. Click **Save**

Appointments config
-------------------

Regardless of which service you decide to use navigate
to **Configuration** > **Appointments config** and select which service you set up
from the dropdown.

The Appointments configuration is now completed.

.. _`Qmatic`: https://www.qmatic.com/solutions/online-appointment-booking/
