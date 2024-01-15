.. _configuration_validation_brk:

=========================
BRK - Zakelijk gerechtigd
=========================

The special *AddressNL* component has a specific validator available, that can
check if the currently logged in user is the business owner of the filled-in property.

Configuration
=============

1. Obtain a BRK API key.
2. In Open Forms, navigate to: **Miscellaneous** > **KvK configuration**.
3. Click **Add** next to the **KvK API Basisprofiel** field and fill in the following
   details:

   * **Label**: *Fill in a human readable label*, for example: ``My BRK API``
   * **Type**: ORC (Overige).
   * **API root URL**: *The API URL provided by KvK but typically:* ``https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/``.
   * **Authorization type**: API key.
   * **Header key**: ``X-Api-Key``.
   * **Header value**: *The KvK API key obtained in step 1*.
   * **OAS file**: ``https://raw.githubusercontent.com/VNG-Realisatie/Haal-Centraal-BRK-bevragen/master/specificatie/genereervariant/openapi.yaml``.

4. Click **Save** in the popup to save and close it.
5. When building a form, add a *AddressNL* component from the *Special* dropdown.
6. In the **Validation** tab, select *BRK - Zakelijk gerechtigd*.

.. warning::

   This validation plugin is only available if an :ref:`authentication plugin <configuration_authentication_index>`
   that provides a BSN is being used.


Technical
=========

=======  ==================
API      Supported versions
=======  ==================
BRK API  2.0
=======  ==================
