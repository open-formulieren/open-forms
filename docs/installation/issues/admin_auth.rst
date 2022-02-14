.. _installation_issues_admin_auth:

Admin authentication issues
===========================

OpenID Connect login shows errors related to unique email addresses
-------------------------------------------------------------------

If you enabled :ref:`configuration_authentication_oidc` (OIDC) authentication, there are
multiple authentication paths into the admin that may conflict with each other.

If a local user (as opposed to OIDC created user) exists with their email address and
they try to login with their OIDC account having the same email address, you will
likely run into these errors, as email addresses must be unique in Open Forms.

Example error:

.. code-block:: none

    duplicate key value violates unique constraint "filled_email_unique"
    DETAIL:  Key (email)=(collision@example.com) already exists.


On OIDC login, either a user is created or updated with the email address from the
OIDC claims.

Possible solutions:

* Update the local user, change the username into the unique identifier used by the OIDC
  provider. This means the user can no longer login with their old username and password
  combination. They can still login with their email + password combination.

* Update the local user and change the email address. On first OIDC login, a new user
  will be created and you will have to reconfigure all the permissions.

* Delete the local user. On first OIDC login, a new user will be created and you will
  have to set up all the permissions again.

* Exclude ``email`` from the claim mapping. OIDC users will then not have an email
  address set, which prevents them from using the password reset functionality.

* Possibly you can configure the OIDC provider to include matching username claims.
