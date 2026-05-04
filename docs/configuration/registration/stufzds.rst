.. _configuration_registration_stufzds:

========
StUF-ZDS
========

The `StUF-ZDS`_ (StUF Zaak- en Documentservices) is a SOAP based Zaak and
Documents service. Open Forms can be configured to access this SOAP-service to
register form submissions.

.. _`StUF-ZDS`: https://vng-realisatie.github.io/Zaak-en-Documentservices/

.. note::

   This service contains sensitive data and requires a connection to an
   external system, offered or maintained by a service provider.

.. contents:: Jump to
   :depth: 2
   :local:
   :backlinks: none

What does the Open Forms administator need?
===========================================

The values for these parameters should be provided to the Open Forms
administrator by the service provider.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Security**
Public certificate            The certificate, used by the service, to identify itself for 2-way TLS.
**SOAP services**
BeantwoordVraag endpoint      URL for the ``BeantwoordVraag`` SOAP-endpoint that Open Forms can access.
VrijeBerichten endpoint       URL for the ``VrijeBerichten`` SOAP-endpoint that Open Forms can access.
OntvangAsynchroon endpoint    URL for the ``OntvangAsynchroon`` SOAP-endpoint that Open Forms can access.
**Stuurgegevens**
Ontvanger Organisatie         Name of the organization submissions are sent to.
Ontvanger Applicatie          Name of the application submissions are sent to.
**ZDS**
Gemeentecode                  4 digit code of the municipality.
Zaaktype code                 Code of the (default) zaaktype.
Zaaktype omschrijving         Description of the (default) zaaktype. Used as identifier if code does not match.
Status code                   Code of the (default) initial status.
Status omschrijving           Description of the (default) initial status. Used as identifier if code does not match.
Documenttype omschrijving     Description of documenttype, used for the submission PDF.
============================  =======================================================================================


What does the service provider need?
====================================

The values for these parameters should be provided to the service provider by
the Open Forms administrator.

============================  =======================================================================================
Parameter                     Description
============================  =======================================================================================
**Security**
Public certificate            The certificate, used by Open Forms, to identify itself for 2-way TLS.
IP address                    The IP address of the Open Forms server (optional, for whitelisting).
**Stuurgegevens**
Zender Organisatie            Typically the organization name but can be whatever the service provider configured.
Zender Applicatie             Typically ``Open Forms`` but can be whatever the service provider configured.
============================  =======================================================================================


Configuration
=============

1. Obtain credentials and endpoint for StUF-ZDS from the client.
2. In Open Forms, navigate to: **Configuration** > **SOAP Services**
3. Click **Add SOAP Services** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``My StUF-ZDS service``
   * **URL**: *Fill in the full URL to the SOAP service endpoint*
   * **SOAP Version**: *Select the SOAP version of your backend provider*

4. In the **Authentication** section enter the authentication details provided by
   the service provider:

   * **Security**: *select the security level required by your backend provider*

      * **Basic authentication**: use HTTP Basic authentication, requires to also fill in **Username** and **Password**
      * **SOAP extension: WS-Security**: use WS-Security, requires to also fill in **Username** and **Password**
      * **Both**: use both HTTP Basic authentication and WS-Security, requires to also fill in a shared **Username** and **Password**
      * **None**: no username/password based security (default)

    * **Certificate** and **Certificate key**: optionally provide a certificate and key file for client identification. If empty mutual TLS is disabled

5. Click **Save**

6. Navigate to: **Miscellaneous** > **StUF-services**

7. Click **Add StUF-service** and fill in the following details:

   * **Soap service**: *Select the SOAP service we created above*

8. In the **StUF parameters** section enter the receiving details provided by
   the service provider. For the sending organization details, you can fill in:

   * **Versturende applicatie**: Open Forms

9. In the **Connection** section:

   * **Endpoint BeantwoordVraag**: *Fill in the full URL to the endpoint for the SOAP 'BeantwoordVraag' action*
   * **Endpoint VrijeBerichten**: *Fill in the full URL to the endpoint for the SOAP 'VrijeBerichten' action*
   * **Endpoint OntvangAsynchroon**: *Fill in the full URL to the endpoint for the SOAP 'OntvangAsynchroon' action*

10. Click **Save**

11. Navigate to **Configuration** > **Overview**. In the **Registration plugin** group, click on **Configuration** for the **StUF-ZDS** line.
12. Select for the **Service**, the StUF Service we created above
13. Additionally, you can provide values for the ``<ZKN:omschrijving>`` element for some
    "zaakbetrokkenen" that may get created (like cosigner, registrator, partners...).
    The values here depend on your downstream StUF-ZDS service provider.
14. Click **Save**

The StUF-ZDS configuration is now complete and can be selected as registration
backend in the form builder.


Technical
=========

================  ===================
Service           Supported versions
================  ===================
StUF-ZDS          1.0 - 1.2
================  ===================


Messages
--------

These SOAP-operations are used by this plugin:

* ``genereerZaakIdentificatie_Di02``
* ``creeerZaak_Lk01``

   * ``heeftAlsInitiator`` (the initiator can be excluded if needed)

       * ``extraElementen``, explicitely mapped variables through the configuration

   * ``heeftAlsOverigBetrokkene`` (set if: an employee logs in on behalf of
     a client, the submission has been cosigned or there are family member relations)
   * ``heeft`` (the status can be excluded if needed)
   * ``extraElementen``, all remaining unmapped submission data elements + explicitly
     mapped (registration) variables through the configuration

* ``updateZaak_Lk01`` (only used when delayed payments are enabled)
* ``genereerDocumentIdentificatie_Di02``
* ``voegZaakdocumentToe_Lk01`` (for both the submission document and each attachment)


.. note:: We provide support of ``extraElementen`` for  ``creeerZaak_Lk01`` on two levels:

    * ``ZKN:object/StUF:extraElementen``
    * ``ZKN:object/ZKN:heeftAlsInitiator/StUF:extraElementen``

   Both mappings can be added on the "Extra elements" tab of the plugin configuration options,
   and any form variable that's not mapped explicitly will be included in the object level extra elements.

Vendor-specific notes
=====================

Some vendors of StUF-ZDS-compatible systems require some extra attention.

.. tip:: Missing some vendors here? Let us know in a
   `Github issue <https://github.com/open-formulieren/open-forms/issues>`_.

Onegov 365 zaaksysteem
----------------------

``<ZKN:startdatum>`` support
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Onegov expects a datetime here rather than a date. However, the StUF-ZDS standard
prescribes a date without any time information.

As a workaround, you should update the form registration configuration with an
``extraElement`` mapping. In the registration plugin configuration options, ensure that
there's a mapping entry from the form variable "Submission completion timestamp"
(``completed_on``) to the name ``zaak.pv_startdatum``.

Payment details information
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open Forms uses the StUF-ZDS elements ``<ZKN:betalingsIndicatie>`` and
``<ZKN:laatsteBetaaldatum>`` to report the payment status. Onegov expects additional
information that's not readily available in the StUF-ZDS standard, through
``extraElementen``:

* ``zaak.pv_orderid``: the registration variable "Payment public order IDs"
  (``payment_public_order_ids``) exists, however emitting it will result in a ``.0``,
  ``.1``, ... suffix being added to the name of the extra element, as multiple order
  IDs may exist. This will effectively produce XML looking like:

  .. code-block:: xml

    <StUF:extraElement naam="zaak.pv_orderid.0">12334</StUF:extraElement>

  .. warning:: It's currently unknown if Onegov can handle this or not.

  .. note:: Administrators can control the template of these order IDs. Take into
     account that Onegov has a 100-character limit on the value of this element.

* ``zaak.pv_bedrag``: the registration variable "Payment amount" (``payment_amount``)
  can be mapped to this name. It uses a period (``.``) character as decimal separator,
  as expected by Onegov.

* ``zaak.pv_betaalmethode``: this should be omitted - Open Forms uses payment providers
  that manage this and for us the payment method is unknown anyway.

* ``zaak.pv_transactieid``: the information is available in the registration variable
  "Provider payment IDs" (``provider_payment_ids``), but it has the same limitation like
  ``zaak.pv_orderid`` with regard to the suffixes. An element value may not exceed 100
  characters here either.

* ``zaak.pv_betaalstatus``: this cannot be mapped, but the StUF-ZDS element
  ``<ZKN:betalingsIndicatie>`` is the right place and we manage that automatically
  already.

Contact information
^^^^^^^^^^^^^^^^^^^

Open Forms uses the StUF-ZDS element ``heeftAlsAanspreekpunt`` to send contact details of the initiator.
Onegov doesn't support it, therefore we added a workaround with ``extraElement`` mapping on the initiator level.

In the registration plugin configuration options, go to the "Extra elements" tab and add mapping entries
on the **initiator** level. The expected StUF names are:

* ``pv_afwijkendtelefoon``: use the form variable that contains the phone number
* ``pv_emailafwijkend``: use the form variable that contains the email address
