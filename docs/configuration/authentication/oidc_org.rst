.. _configuration_authentication_oidc_org:

=======================================
OpenID Connect for organisation members
=======================================

Open Forms support login on forms by *organisation members* through Single Sign On (SSO) via the OpenID Connect protocol (OIDC).

Members of the organisation can login to forms for internal use by the organisation using the same OpenID Connect configuration that is used for the management interface.
In this flow:

1. The organisation member clicks *Inloggen met OpenID Connect* on the internal form.
2. The member gets redirected to the login flow of the OpenID Connect provider where the member logs in.
3. After completion of the OpenID Connect provider login the member is redirected back to the form in Open Forms.
4. The member is now logged into Open Forms and can proceed to complete the form.
5. Open Forms optionally stores a configurable "Employee ID" claim from the OIDC user-info on both the submission as the created user.

.. _configuration_authentication_oidc_org_appgroup:

Configuring OICD for login of organisation members
==================================================

The OpenID Connect configuration is shared with :ref:`the configuration of the management interface <configuration_authentication_oidc>` and follows the same steps with a few addtional notes:

- The plugin callback URL needs to be registered at the OpenID Connect provider. Contact the organisations IAM and ask them add to the whitelist ``https://open-formulieren.gemeente.nl/org-oidc/callback/`` (replace ``open-formulieren.gemeente.nl`` with the domain of your Open Forms installation).

- It is not recommended to use the *Default groups* configuration option when using OpenID Connect for organisation members to authenticate on forms.

- To store user information from OpenID and track an "Employee ID" it is required to configure the `claim mapping`. This is JSON object where the claims from the OIDC user-info gets mapped to attributes on the user in Open Forms. For more info and options on configuring the mapping see `mozilla-django-oidc-db <https://github.com/maykinmedia/mozilla-django-oidc-db#user-content-user-profile>`_ and the documentation of your OpenID Connect provider for the structure of the returned user-info.

  Example:

  .. code-block:: javascript

    {
        "email": "email",
        "last_name": "family_name",
        "first_name": "given_name",
        "employee_id": "name_of_claim_with_employee_id"
    }

  Note we set the ``employee_id`` to track the member on both the submission and the created user.


After completing these steps a form can be created with the authentication backend ``Organisation via OpenID Connect``, see :ref:`manual_forms_basics`.



