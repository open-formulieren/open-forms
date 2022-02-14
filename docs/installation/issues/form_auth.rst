.. _installation_issues_form_auth:

Form authentication issues
==========================

If you enabled :ref:`DigiD <configuration_authentication_digid>`, 
:ref:`eHerkenning or eIDAS <configuration_authentication_eherkenning_eidas>` 
for your form and it doesn't work, we show some common problems and how to 
resolve them.


The login screen is not shown at all
------------------------------------

After clicking on the form authentication login button, the login process does 
not start. This can be caused for a number of reasons. Please check the logs
for a more detailed error message and see below.

**Error**

.. code::

    ImproperlyConfigured: The file: XXX could not be found. Please specify an existing metadata in the conf['metadata_file'] setting.

**Solution**

The metadata file was not correctly deployed when installing Open Forms. Please configure and deploy Open Forms properly.


**Error**

.. code::

    OneLogin_Saml2_Error: Invalid dict settings: idp_sso_not_found

**Solution**

Make sure the metadata ``IDPSSODescriptor`` element contains at least the 
following child elements. The exact ``Location`` URLs can differ:

.. code:: xml

    <md:ArtifactResolutionService Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP" Location="[...]/saml/idp/resolve_artifact" index="0"/>
    <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="[...]/saml/idp/request_logout"/>
    <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="[...]/idp/request_authentication"/>
    <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="[...]/saml/idp/request_authentication"/>


The DigiD login succeeds but Open Forms shows that login failed
---------------------------------------------------------------

After clicking the form authentication login button, the login process starts
but after completing it, Open Forms shows an error message. Please check the 
logs for a more detailed error message and see below.

**Error**

.. code::

   The ArtifactResponse could not be validated due to the following error:
   The status code of the ArtifactResponse was not Success, was RequestDenied

**Solution**

   The DigiD broker probably returns an invalid response. This can be caused by 
   many things and should debugged with the DigiD broker and the Open Forms 
   supplier.

**Error**

.. code::

   The sha1 hash of the entityId returned in the SAML Artifact (...) does not 
   match the sha1 hash of the configured entityId 
   (https://example.com/saml/metadata)

**Solution**

The configured metadata does not match the entityID configured. The Open Forms 
provider should configure the proper metadata file or the DigiD broker should 
provide the proper metadata.

.. code::

   The Response could not be validated due to the following error:
   https://example.com is not a valid audience for this Response

**Solution**

The DigiD broker should make sure the configured audience matches the exact URL 
as shown in the error. Make sure there is no trailing slash (``/``) or 
``http`` instead of ``https``.

**Error**

.. code::

   The Response could not be validated due to the following error:
   The Assertion of the Response is not signed and the SP require it

.. code::

    The Response could not be validated due to the following error:
    No Signature found. SAML Response rejected

**Solution**

The DigiD broker should either sign the assertion in the XML or the entire 
response. The Open Forms supplier should set ``DIGID_WANT_ASSERTIONS_SIGNED`` to 
either ``True`` if the assertion is signed and to ``False`` if the response is 
signed.
