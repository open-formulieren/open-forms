.. _configuration_authentication_digid:

====================
DigiD authentication
====================

.. warning::
    
    This plugin cannot be configured via the admin interface and requires an 
    update of the Open Forms installation.

Some forms can require authentication. Open Forms supports authentication 
using `DigiD`_. Access to DigiD can typically be obtained via `Logius`_.

Using DigiD for authentication will provide the BSN (social security number) of
the authenticated person to the form context. Using the BSN, certain fields can
be :ref:`prefilled <configuration_prefill_index>` with relevant personal data.

.. note::
    
    Open Forms currently only supports security level 25 
    (zekerheidsniveau = Substantieel).


Step by step overview
=====================

1. Read the requirements for getting access to DigiD on the `Logius`_ website.
   There are several steps that need to be taken on your end that are not 
   covered here.

2. Request a `PKIoverheid Private Services Server G1`_ certificate at your 
   `PKIO SSL certificate supplier`_. This is required for backchannel 
   communication with Logius (if you already have one for Open Forms, it can be
   re-used).

3. Send the following information to your Open Forms supplier in a secure way:

   * Public and private certificate (obtained in step 2)
   * Desired service name (for example: "Digitaal Loket") shown in DigiD
   * Privacy policy URL of your main website
   
   Your Open Forms supplier will install the certificates in Open Forms, 
   generate some XML metadata files and sends these back to you.

4. Request access to the pre-production environment on the `Logius`_ website 
   and follow the steps there. To request access, you will need the following
   information:

   * **Zekerheidsniveau**: ``Midden``
   * **DigiD eenmalig inloggen**: ``Nee``
   * **URL aansluiting**: *The Open Forms domain, for example: https://forms.organisation.com*
   * **Webdienstnaam**: *The same desired service name as given in step 3*
   * **Metadata**: *The XML-file provided to you by your Open Forms supplier*
   * **Publieke deel PKIO-certificaat**: *The public certificate obtained in step 2*

   As technical contact, you should provide your Open Forms supplier contact
   details.

.. _`PKIoverheid Private Services Server G1`: https://www.pkioverheid.nl/
.. _`PKIO SSL certificate supplier`: https://logius.nl/diensten/pkioverheid/aanvragen
.. _`DigiD`: https://www.digid.nl/
.. _`Logius`: https://www.logius.nl/diensten/digid

Problems? You might want to check out :ref:`installation_issues_form_auth`.
