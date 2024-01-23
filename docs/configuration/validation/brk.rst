.. _configuration_validation_brk:

=========================
BRK - Zakelijk gerechtigd
=========================

The special *AddressNL* component has a specific validator available, that can
check if the currently logged in user is the business owner of the filled-in property.

Configuration
=============

1. Obtain a BRK API key.
2. In Open Forms, navigate to: **Configuration** > **Services**.
3. Click **Add service** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``Basisregistratie Kadaster (BRK)``
   * **Type**: ORC (Overige).
   * **API root URL**: *The API URL provided by KvK but typically:* ``https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/``.
   * **Authorization type**: API key.
   * **Header key**: ``X-Api-Key``.
   * **Header value**: *The KvK API key obtained in step 1*.

4. Click **Save**
5. Navigate to **Configuration** > **Configuration overview**. In the **Validator plugins**
   group, click on **Configuration** for the **Validation plugin config: BRK - Zakelijk gerechtigd** line.
6. Select for the **BRK API**, the **Basisregistratie Kadaster (BRK)** option, that we just created in step 3.
7. Click **Save**
8. When building a form, add an *AddressNL* component from the *Special* group.
9. In the **Validation** tab, select *BRK - Zakelijk gerechtigd*.

.. note::

   This validation plugin is only available if an :ref:`authentication plugin <configuration_authentication_index>`
   that provides a BSN is being used.


Technical
=========

=======  ==================
API      Supported versions
=======  ==================
BRK API  2.0
=======  ==================
