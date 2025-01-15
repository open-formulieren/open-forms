.. _configuration_authentication_eherkenning_eidas:

====================================
eHerkenning and eIDAS authentication
====================================

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

    Authentication via eIDAS uses the same supplier and generated files as
    eHerkenning. If you plan on adding eIDAS support to Open Forms, it's best
    to do these 2 at the same time.

Limitations
===========

Some limitations apply.

**KVKNr identifier required**

Open Forms only supports the ``KVKNr`` identifier. Other identification numbers exist,
but we don't support these (yet). Ensure that your supplier specifies the relevant
identifying attribute, since this can not be specified in Open Forms.

Additional identifying attributes may be specified - these will be ignored.

**Security level**

Open Forms currently only supports the same security level for all forms. You can not
override this, and the security level is recorded in the service catalog so it is
outside of our control. We're aware of this feature request though.

.. note::

    The available security levels are:

    =========== =============== ===========================================
    eHerkenning eIDAS           SAML2 AuthnContextClassRef element
    =========== =============== ===========================================
    EH2         basis/low       urn:etoegang:core:assurance-class:loa2
    EH2+        basis/low       urn:etoegang:core:assurance-class:loa2plus
    EH3         substantieel    urn:etoegang:core:assurance-class:loa3
    EH4         hoog/high       urn:etoegang:core:assurance-class:loa4
    =========== =============== ===========================================

    Source: `Afsprakenstelsel eToegang <https://afsprakenstelsel.etoegang.nl/Startpagina/as/level-of-assurance>`_

Step by step overview
=====================

The high-level overview of steps you need to perform are described here. The following
sections provide more details.

1. Contact an `approved eHerkenning supplier`_ to get started. Sometimes, your
   Open Forms supplier can communicate directly with the eHerkenning supplier.
   Make sure you indicate if you want to connect using eHerkenning, eIDAS or
   both and what type of environment (test or production).

2. Request a `PKIoverheid Private Services Server G1`_ certificate at your
   `PKIO SSL certificate supplier`_. This is required for backchannel
   communication with your eHerkenning supplier (if you already have one for
   Open Forms, it can be re-used).

   You can :ref:`prepare the certificates <configuration_authentication_eh_prepare_certificates>`
   from the admin interface.

3. Send the following information to your Open Forms supplier:

   * Public and private certificate (obtained in step 2, private certificate is already
     present if you generated the Signing Request (CSR) via the admin)
   * Name of the approved eHerkenning supplier
   * The desired consuming service indexes (or Service IDs)
   * Desired service name(s) in Dutch and English (for example: "Digitaal Loket")
   * Privacy policy URL of your main website
   * The `OIN`_ of your organization.

   Your Open Forms supplier will install the certificates in Open Forms,
   generate some XML metadata files and sends these back to you, or your
   eHerkenning supplier directly.

4. Your eHerkenning supplier will inform you when everything is set up.

.. _configuration_authentication_eh_prepare_certificates:

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

You can now proceed to :ref:`configuration_authentication_eh_metadata`.


.. _configuration_authentication_eh_metadata:

Generating the Service Provider metadata
========================================

In the admin environment we can configure the DigiD identity provider and select our
required certificate pair(s). Once this is done, we can generate our service provider
metadata.

#. Navigate to the **Admin**.
#. In the menu, navigate to **Configuration** > **EHerkenning/eIDAS configuration**.
#. Under the *X.509 Certificate* section, click the **Manage (number)** link.
#. Click the **Add Digid/eHerkenning certificate** button in the top right of the page.
#. For **Config type**, select "eHerkenning".
#. For **Certificate**, click the search icon and select the certificate pair that was
   created earlier (in the :ref:`configuration_authentication_eh_prepare_certificates`
   section).
#. **Save** the configuration and close the window/tab.
#. Continue on the *EHerkenning/eIDAS configuration* page.
#. In the section *Identity provider*, enter the identity provider
   **metadata file (XML) URL**. This URL should be provided by your broker/supplier. The
   metadata will be retrieved and processed.
#. Next, in the section *SAML configuration*, enter the fields:

   * **Entity ID**: This is the entity ID of Open-Forms.
   * **Base URL**: Enter the URL where Open-Forms is deployed (and publicly accessible).
   * **Resolve artifact binding content type**: select ``text/xml`` unless you're using
     old/legacy brokers or are instructed to pick ``application/soap+xml``.
   * **Want assertions signed**: This should be **checked**.
   * **Want assertions encrypted**: This should be **unchecked**.
   * **Signature algorithm**: Select ``RSA_SHA256``.
   * **Digest algorithm**: Select ``SHA256``.

#. Continue to the section *Service details* and fill out the fields:

   * **Service name**: This is the name of the service for which authentication is needed.
   * **Service description**: A description of the service for which authentication is needed.
   * **OIN**: Enter your OIN_.
   * **Broker ID**: Specify the OIN_ of your broker.
   * **Privacy policy**: Enter the link to the webpage where your privacy policy is
     hosted.
   * **Service language**: Enter ``nl``.

#. Next, in the section *eHerkenning* you can configurare parameters for eHerkenning:

    * **Requested attributes**: leave empty. Definitely do *not* include
      ``urn:etoegang:1.9:EntityConcernedID:KvKnr`` as this is managed elsewhere.
    * **EHerkenning LOA**: "Low (2+)" is the minimum required level.

#. Optionally, configure the same parameters for *eIDAS* or check the **No eIDAS**
   checkbox to omit it.

#. Finally, you should provide some *organization details* - provide the telephone/e-mail
   contacts of the organisation responsible for the service requiring eHerkenning/eIDAS
   authentication.

Click on **Save and continue editing** to persist the configuration changes.

On the top right corner of the configuration page, there is a button
**View SAML metadata (XML)**. Click this button to download the metadata. The metadata
needs to be sent to the broker to obtain access to a (pre-)production environment.

.. note::

   Any changes to the configuration in the Admin page cause a change in the metadata.
   The updated metadata must be then sent to the broker again for the changes to be effective.

.. _`PKIoverheid Private Services Server G1`: https://cert.pkioverheid.nl/
.. _`PKIO SSL certificate supplier`: https://www.logius.nl/domeinen/toegang/pkioverheidcertificaat-aanvragen
.. _`eHerkenning`: https://www.logius.nl/diensten/eherkenning
.. _`eIDAS`: https://www.logius.nl/diensten/eidas
.. _`approved eHerkenning supplier`: https://eherkenning.nl/nl/eherkenning-gebruiken/leveranciersoverzicht
.. _`OIN`: https://www.logius.nl/diensten/oin


Problems? You might want to check out :ref:`installation_issues_form_auth`.
