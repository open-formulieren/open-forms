.. _configuration_authentication_oidc_org:

=======================================
OpenID Connect for organization members
=======================================

.. note::

  This page documents how to set up Single Sign on (SSO) for organization 
  members, to access and fill in forms. If you are looking to authenticate 
  admins for the management interface, please go 
  :ref:`here <configuration_authentication_oidc>`.

Open Forms supports login on forms by *organization members* through Single Sign On
(SSO) via the OpenID Connect protocol (OIDC).

Members of the organization can login to forms for internal use by the organization
using the same OpenID Connect configuration that is used for the management interface.
In this flow:

1. The organization member clicks *Inloggen met OpenID Connect* on the (internal) form.
2. The member gets redirected to the login flow of the OpenID Connect provider where
   the member logs in.
3. After completion of the OpenID Connect provider login the member is redirected back
   to the form in Open Forms.
4. The member is now logged into Open Forms and can proceed to complete the form.
5. Open Forms optionally stores the employee ID (from the OIDC claims) on the user
   record *and* the form submission.

.. _configuration_authentication_oidc_org_appgroup:

Configuring OIDC for login of organization members
==================================================

The OpenID Connect configuration is shared with
:ref:`the configuration of the management interface <configuration_authentication_oidc>`
and follows the same steps with a few addtional notes:

- It is not recommended to use the *Default groups* configuration option when using
  OpenID Connect for organization members to authenticate on forms.

- To store user information from OpenID and track an "Employee ID" it is required to
  configure the ``claim mapping``. This is JSON object where the claims from the OIDC
  user-info gets mapped to attributes on the user in Open Forms. For more info and
  options on configuring the mapping see
  `mozilla-django-oidc-db <https://github.com/maykinmedia/mozilla-django-oidc-db>`_
  (Section 4.1, User profile) and the documentation of your OpenID Connect provider for
  the structure of the returned user-info.

  Example:

  .. code-block:: json

    {
        "email": "email",
        "last_name": "family_name",
        "first_name": "given_name",
        "employee_id": "name_of_claim_with_employee_id"
    }

  Note we set the ``employee_id`` to track the member on both the submission and the
  created user.

- We recommend configuring the roles on the OIDC provider side together with the
  ``Groups glob pattern`` to automatically assign the correct groups when an employee
  authenticates via OIDC. More information about permissions and groups is available
  in the :ref:`manual <manual_accounts>` (in Dutch).

After completing these steps a form can be created with the authentication backend
``Organization via OpenID Connect``, see :ref:`manual_forms_basics`.
