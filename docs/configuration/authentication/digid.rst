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

    Open Forms currently only supports security level (betrouwbaarheidsniveau)
    "Midden".

    ============= =================================================================
    DigiD         SAML2 AuthnContextClassRef element
    ============= =================================================================
    Basis         urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport
    Midden        urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract
    Substantieel  urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard
    Hoog          urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI
    ============= =================================================================

    Source: `Logius <https://www.logius.nl/diensten/digid/documentatie/koppelvlakspecificatie-digid-saml-authenticatie>`__

Obtaining the Service Provider metadata
=======================================

Once access to a DigiD (pre-)production environment has been obtained, Open-Forms has to be configured.
This can be done by navigating to **Configuration** > **DigiD configuration**.

#. **Key pair**: Upload the `PKIoverheid Private Services Server G1`_ and the private key (see point 2 of the next section).
   The certificate will be used in the metadata that will be generated, and the private key will be used to sign the metadata.

#. **Metadata file(XML) URL**: This is the URL where the metadata (XML) for the Identity Provider can be obtained.
   The entity ID (of the identity provider) will automatically be extracted from the XML.

#. **Entity ID**: This is the entity ID of Open-Forms. For DigiD, this can be the URL where Open-Forms is deployed, for
   example ``https://openforms.test.nl``.

#. **Base URL**: This is the URL where Open-Forms is deployed.

#. **Resolve artifact binding content type**: This is the the value of the ``Content-Type`` header for the resolve artifact binding request.
   Modern brokers typically expect ``text/xml`` while ``application/soap+xml`` is considered legacy.

#. **Want assertions signed**: This should be **checked**.

#. **Signature algorithm**: Select ``RSA_SHA1``.

#. **Digest algorithm**: Select ``SHA1``.

#. **Service name**: This is the name of the service for which authentication is needed.

#. **Service description**: A description of the service for which authentication is needed.

#. **Requested attributes**: What attributes are expected to be returned by DigiD after authentication. This should be ``["bsn"]``.

#. **Organisation details**: Telephone/e-mail contacts of the organisation responsible for the service requiring DigiD authentication.

Click then on **Save and continue editing** to persist the configuration changes.

On the top right corner of the configuration page, there is a button **View SAML metadata**. Click on this button and save this metadata.
The metadata needs to be sent to the broker to obtain access to a (pre-)production environment.

.. note::

   Any changes to the configuration in the Admin page cause a change in the metadata. The updated metadata must be then
   sent to the broker again for the changes to be effective.


Steps to request access to a DigiD environment
==============================================

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
   * **URL aansluiting**: *The Open Forms domain, for example: https://forms.organization.com*
   * **Webdienstnaam**: *The same desired service name as given in step 3*
   * **Metadata**: *The XML-file provided to you by your Open Forms supplier (see previous section)*
   * **Publieke deel PKIO-certificaat**: *The public certificate obtained in step 2*

   As technical contact, you should provide your Open Forms supplier contact
   details.

.. _`PKIoverheid Private Services Server G1`: https://cert.pkioverheid.nl/
.. _`PKIO SSL certificate supplier`: https://logius.nl/diensten/pkioverheid/aanvragen
.. _`DigiD`: https://www.digid.nl/
.. _`Logius`: https://www.logius.nl/diensten/digid

Problems? You might want to check out :ref:`installation_issues_form_auth`.
