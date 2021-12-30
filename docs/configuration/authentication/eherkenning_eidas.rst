.. _configuration_authentication_eherkenning_eidas:

====================================
eHerkenning and eIDAS authentication
====================================

.. warning::
    
    This plugin cannot be configured via the admin interface and requires an 
    update of the Open Forms installation.

Some forms can require authentication. Open Forms supports authentication 
using `eHerkenning`_ and `eIDAS`_. To use eHerkenning and/or eIDAS, you must 
have a contract with an `approved eHerkenning supplier`_.

Using eHerkenning for authentication will provide the KvK-number (chamber of 
commerce number) of the authenticated company to the form context. Using the 
KvK-number, certain fields can be 
:ref:`prefilled <configuration_prefill_index>` with relevant personal data.

When using eIDAS, only a pseudoID is provided along with certain attributes
that describes the authenticated entity (person or company).

.. note::
    
    Open Forms currently only supports the same security level for all forms.


.. note::

    Authentication via eIDAS uses the same supplier and generated files as
    eHerkenning. If you plan on adding eIDAS support to Open Forms, it's best
    to do these 2 at the same time.


Step by step overview
=====================

1. Contact an `approved eHerkenning supplier`_ to get started. Sometimes, your
   Open Forms supplier can communicate directly with the eHerkenning supplier.
   Make sure you indicate if you want to connect using eHerkenning, eIDAS or 
   both and what type of environment (test or production).

2. Request a `PKIoverheid Private Services Server G1`_ certificate at your 
   `PKIO SSL certificate supplier`_. This is required for backchannel 
   communication with your eHerkenning supplier (if you already have one for 
   Open Forms, it can be re-used).

3. Send the following information to your Open Forms supplier:

   * Public and private certificate (obtained in step 2)
   * Name of the approved eHerkenning supplier
   * The desired consuming service indexes (or Service IDs)
   * Desired service name(s) in Dutch and English (for example: "Digitaal Loket")
   * Privacy policy URL of your main website
   * The `OIN`_ of your organisation.
   
   Your Open Forms supplier will install the certificates in Open Forms, 
   generate some XML metadata files and sends these back to you, or your
   eHerkenning supplier directly.

4. Your eHerkenning supplier will inform you when everything is set up.

.. _`PKIoverheid Private Services Server G1`: https://www.pkioverheid.nl/
.. _`PKIO SSL certificate supplier`: https://logius.nl/diensten/pkioverheid/aanvragen
.. _`eHerkenning`: https://www.logius.nl/diensten/eherkenning
.. _`eIDAS`: https://www.logius.nl/diensten/eidas
.. _`approved eHerkenning supplier`: https://eherkenning.nl/nl/eherkenning-gebruiken/leveranciersoverzicht
.. _`OIN`: https://www.logius.nl/diensten/oin


Problems? You might want to check out :ref:`installation_issues_auth`.
