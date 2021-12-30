.. _installation_issues_auth:

Authentication issues
=====================

If you enabled :ref:`DigiD <configuration_authentication_digid>`, 
:ref:`eHerkenning or eIDAS <configuration_authentication_eherkenning_eidas>` 
for your form and it doesn't work, we show some common problems and how to 
resolve them.


The login screen is not shown at all
------------------------------------

After clicking on the form authentication login button, the login process does 
not start. This can be caused for a number of reasons. Please check the logs
for a more detailed error message and see below.


ImproperlyConfigured: The file: XXX could not be found. Please specify an existing metadata in the conf['metadata_file'] setting.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The metadata file was not correctly deployed when installing Open Forms.


OneLogin_Saml2_Error: Invalid dict settings: idp_sso_not_found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure the metadata ``IDPSSODescriptor`` element contains at least the 
following child elements. The exact ``Location`` URLs can differ:

.. code: xml

    <md:ArtifactResolutionService Binding="urn:oasis:names:tc:SAML:2.0:bindings:SOAP" Location="[...]/saml/idp/resolve_artifact" index="0"/>
    <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="[...]/saml/idp/request_logout"/>
    <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="[...]/idp/request_authentication"/>
    <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="[...]/saml/idp/request_authentication"/>
