.. _configuration_prefill_communication_preferences:

=========================
Communication preferences
=========================

The **Communication preferences** prefill plugin stores data records for digital addresses based
on a person's BSN, retrieved from a `Customer Interactions API`_. These records can be used to
populate the "customerProfile" form component.

.. note::

   The `Customer Interactions API`_ stores data related to the contacts between clients and the
   municipality. The API specifications aren't standardized, therefore Open Forms follows the
   `Customer Interactions API`_ specifications of `Open Klant`_.

   Information about the architecture and the vision of the API can be also found on the
   `VNG github`_.


What does the Open Forms administrator need?
============================================

* An instance of the `Open Klant`_ with:

    - an API token to access the API from Open Forms


Configuration
=============

To use the Communication Preferences prefill plugin you need to configure the access to
`Customer Interactions API`_.

#. In Open Forms, navigate to: **Configuration** > **Services**
#. Create a service for the Customer Interactions API.

   a. Click **Add service**.
   b. Fill out the form:

      * **Label**: *Fill in a human readable label*, for example: ``My Customer Interactions API``
      * **Type**: Select the type: ``Klanten API``
      * **API root url**: The root of this API, *for example* ``https://example.com/klantinteracties/api/v1/``

      * **Authorization type**: Select the option: ``API Key``
      * **Header key**: Fill in ``Authorization``
      * **Header value**: Fill in ``Token <tokenValue>`` where ``<tokenValue>`` is replaced
        by the token provided by the Open Klant

   c. Click **Save**.

#. Navigate to **Configuration** > **Configuration overview**. In the
   **Prefill plugins** group, click on **Manage API groups** for the **Communication preferences**
   line.

#. Create a new API group for the `Customer Interactions API`_:

   a. Click **Add customer interactions API group**.
   b. Enter the following details:

      * **Name**: Enter a recognizable name, it will be displayed in various dropdowns.
      * **Customer Interactions API**: Select the service created above.

   c. Click **Save**


How it works
============

In order to enable the plugin you need to complete the configuration above. Next step is
to add the relevant component and a **user defined** form variable:

  * The component you need to add to the form is "Profile" from the special fields.
    This will automatically create a form variable of data type ``array``.
    This form variable will hold the data which the user submits.

  * Next step is to add a user defined variable that we call ``profilePrefill``.
    This variable is used for configuring the plugin and holding the pre-filled data from
    the `Customer Interactions API`_. In the Configuration popup select the API group
    created in the "Configuration" section and the profile form variable.


Technical
=========

========================= ==================
Service                   Supported versions
========================= ==================
Open Klant                2.14
========================= ==================


.. _`Customer Interactions API`: https://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/maykinmedia/open-klant/master/src/openklant/components/klantinteracties/openapi.yaml
.. _`Open Klant`: https://open-klant.readthedocs.io/en/latest/
.. _`VNG github`: https://vng-realisatie.github.io/klantinteracties/
