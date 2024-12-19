.. _configuration_authentication_digid:

====================
DigiD authentication
====================

Some forms can require authentication. Open Forms supports authentication
using `DigiD`_. Access to DigiD can typically be obtained via `Logius`_.

Using DigiD for authentication will provide the BSN (social security number) of
the authenticated person to the form context. Using the BSN, certain fields can
be :ref:`prefilled <configuration_prefill_index>` with relevant personal data.

Steps to request access to a DigiD environment
==============================================

The high-level overview of steps you need to perform are described here. The following
sections provide more details.

1. Read the requirements for getting access to DigiD on the `Logius`_ website.
   There are several steps that need to be taken on your end that are not
   covered here.

2. Request a `PKIoverheid Private Services Server G1`_ certificate at your
   `PKIO SSL certificate supplier`_. This is required for backchannel
   communication with Logius (if you already have one for Open Forms, it can be
   re-used).

   You can :ref:`prepare the certificates <configuration_authentication_digid_prepare_certificates>`
   from the admin interface.

3. Send the following information to your Open Forms supplier in a secure way:

   * Public and private certificate (obtained in step 2, private certificate is already
     present if you generated the Signing Request (CSR) via the admin)
   * Desired service name (for example: "Digitaal Loket") shown in DigiD
   * Privacy policy URL of your main website

   Your Open Forms supplier will install the certificates in Open Forms,
   generate some XML metadata files and send these back to you.

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

.. tip::

    You can specify a different security level (betrouwbaarheidsniveau) on a per-form
    basis.

    ============= =================================================================
    DigiD         SAML2 AuthnContextClassRef element
    ============= =================================================================
    Basis         urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport
    Midden        urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract
    Substantieel  urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard
    Hoog          urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI
    ============= =================================================================

    Source: `Logius <https://www.logius.nl/diensten/digid/documentatie/koppelvlakspecificatie-digid-saml-authenticatie>`__


.. _configuration_authentication_digid_prepare_certificates:

Preparing the certificates
==========================

To request a *PKIoverheid certificate*, you need a private key and a certificate signing
request. You can generate these using ``openssl`` or other utilities, or use the built-in
signing requests in the admin interface.

.. tip:: Creating the signing requests from the admin ensures the private key never
   leaves the server, lessening the chances that it is accidentally leaked.

**Using the admin interface**

#. Navigate to the **Admin**.
#. In the menu, navigate to **Configuration** > **Signing requests**.
#. In the top right of the page, click the **Add signing request** button.
#. Enter the desired fields - the information will be included in the signing request.
   Consult with your certificate supplier which data is required and what values are
   expected.
#. Click **Save** to persist the changes. The page is reloaded.
#. Under the section *Signing request (CSR)*, click the **Download CSR** link.

Now, send the downloaded CSR to your certificate supplier and wait for them to verify
it and provide you with the matching certificate. This can take some time (hours to
days), as verification is often a manual process.

Once you have received the certificate, navigate back to the admin and locate your
signing request.

#. Edit the original signing request record in the admin.
#. Navigate to the *Upload signed certificate* section.
#. Upload the certificate provided by the certificate supplier.
#. Save the changes.

If everything is valid, the private key + public cerificate pair is now available and
almost ready for use. You can verify it in the admin via **Configuration** >
**Certificates**.

You can now proceed to :ref:`configuration_authentication_digid_metadata`.

.. _configuration_authentication_digid_metadata:

Generating the Service Provider metadata
========================================

In the admin environment we can configure the DigiD identity provider and select our
required certificate pair(s). Once this is done, we can generate our service provider
metadata.

#. Navigate to the **Admin**.
#. In the menu, navigate to **Configuration** > **DigiD configuration**.
#. Under the *X.509 Certificate* section, click the **Manage (number)** link.
#. Click the **Add Digid/eHerkenning certificate** button in the top right of the page.
#. For **Config type**, select "DigiD".
#. For **Certificate**, click the search icon and select the certificate pair that was
   created earlier (in the :ref:`configuration_authentication_digid_prepare_certificates`
   section).
#. **Save** the configuration and close the window/tab.
#. Continue on the *DigiD configuration* page.
#. In the section *Identity provider*, enter the identity provider **metadata file (XML) URL**.
   E.g. for pre-production: ``https://was-preprod1.digid.nl/saml/idp/metadata``. The
   metadata will be retrieved and processed.
#. Next, in the section *SAML configuration*, enter the fields:

   * **Entity ID**: This is the entity ID of Open-Forms. For DigiD, this can be the URL
     where Open-Forms is deployed, for example ``https://openforms.test.nl``.
   * **Base URL**: Enter the URL where Open-Forms is deployed (and publicly accessible).
   * **Resolve artifact binding content type**: select ``text/xml`` unless you're using
     old/legacy brokers or are instructed to pick ``application/soap+xml``.
   * **Want assertions signed**: This should be **checked**.
   * **Signature algorithm**: Select ``RSA_SHA1``.
   * **Digest algorithm**: Select ``SHA1``.

#. Continue to the section *Service details* and fill out the fields:

   * **Service name**: This is the name of the service for which authentication is needed.
   * **Service description**: A description of the service for which authentication is needed.
   * **Requested attributes**: What attributes are expected to be returned by DigiD
     after authentication. This should be ``["bsn"]``.
   * Leave **Single logout** unchecked, as we currently don't support this.

#. Finally, you should provide some *organization details* - provide the telephone/e-mail
   contacts of the organisation responsible for the service requiring DigiD authentication.

Click on **Save and continue editing** to persist the configuration changes.

On the top right corner of the configuration page, there is a button
**View SAML metadata (XML)**. Click this button to download the metadata. The metadata
needs to be sent to the broker to obtain access to a (pre-)production environment.

.. note::

   Any changes to the configuration in the Admin page cause a change in the metadata.
   The updated metadata must be then sent to the broker again for the changes to be effective.

.. _`PKIoverheid Private Services Server G1`: https://cert.pkioverheid.nl/
.. _`PKIO SSL certificate supplier`: https://www.logius.nl/domeinen/toegang/pkioverheidcertificaat-aanvragen
.. _`DigiD`: https://www.digid.nl/
.. _`Logius`: https://www.logius.nl/diensten/digid

Problems? You might want to check out :ref:`installation_issues_form_auth`.
