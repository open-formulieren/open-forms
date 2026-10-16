.. _developers_public_api:

====================
Public API endpoints
====================

Open Forms uses API endpoints for its functionality - some of these are considered
"public" and intended to be called by external parties. The endpoints are of the form
``/api/v2/public/...``.

Public here does not mean that anonymous access is allowed. You must authenticate (typically
with token authentication) to be able to use the endpoints.

.. tip::

    If you're developing a client for Open Forms, please take a look at the OpenAPI 3
    specification in the root of the project or spin up an instance and visit the
    interactive documentation at ``http://localhost:8000/api/docs/``.

.. warning::

    Any API endpoint that's not explicitly labeled as public (in the URL), is private
    and not subject to our semantic versioning :ref:`policy <developers_versioning>`.
    Making use of those endpoints is at own risk, since changes may be introduced
    without notice.

Authentication
==============

Token authentication is the preferred authentication schema. To obtain a token, an
administrator must first (in the admin interface):

#. Create an API user account with appropriate permissions.
#. Create an API token for the user account.
#. Communicate the token to the party that will make the API calls.

Given an example token ``ac51ff9b963a1909295356efa4aee62f88c336b2``, as a client you
authenticate by including the ``Authorization`` header in your requests:

.. code-block:: http

    GET /api/v2/public/forms HTTP/1.0
    Authorization: Token ac51ff9b963a1909295356efa4aee62f88c336b2
