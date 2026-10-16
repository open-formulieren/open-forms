.. _developers_initial_data:

===============================
Seeding initial submission data
===============================

Open Forms has a feature where organization employees (given the appropriate
permissions) can fill out and submit forms on behalf of a customer (citizen or company).

The authentication details (BSN, KvK-number) for this can be pre-loaded in Open Forms
to optimize this flow and reduce the chances of mistakes (e.g. a typo when copying over
the identifier value).

.. versionadded:: 4.1.0

Overview of the flow
====================

#. External application prepares the authentication details.
#. Open Forms responds with a ``redirectUrl``.
#. User in the external application navigates to the provided ``redirectUrl``.
#. User of the external application is presented with the start page of the form.
#. User of the external application starts the employee-login authentication.
#. In the intermediate screen, citizen or company is pre-selected and the relevant
   details are already filled out.
#. User of the external application confirms and fills out the form, as usual.
#. The employee is registered on the submission as the registrator.

Integration steps for the external application
==============================================

The external application must make a server-to-server API call to seed the initial
submission data.

Prerequisites
-------------

* An API token must be configured, see :ref:`developers_public_api`.
* The user account must have the "Initial data | initial submission data | Can add
  initial submission data" permission.

API call(s)
-----------

.. note:: You can find the technical specification in the API docs under
   "Create initial submission data".

In the API call, you must specify the UUID of the form that will be started. All
available forms can be listed through the ``/api/v2/public/forms`` endpoint.

You must provide the representee details to be used in the form submission, either BSN
of the citizen or KvK number (and possible branch number) of the company.

Finally, the time-to-live (``ttl``) is a number that specifies how long this seed data
is kept, in hours. The expiry date is calculated from the creation timestamp plus the
specified TTL.

Example call:

.. code-block:: http

    POST /api/v2/public/initial-data HTTP/1.0
    Authorization: Token <token>
    Content-Type: application/json

    {
      "form": "f094a464-00e0-431a-8e77-07d5b409133d",
      "representee": {
        "authAttribute": "bsn",
        "value": "000000000"
      },
      "ttl": 2
    }

Will prepare the submission data for the BSN ``000000000`` that will expiry after two
hours.

The response data contains:

* ``uuid``: unique database ID of the initial data record, can be used to look it up
  again via ``GET /api/v2/public/initial-data/:uuid``.
* ``redirectUrl``: fully qualified URL to the form that will start the submission with
  the seeded data. You should not modify this in any way.
* ``expiresAt``: ISO-8601 datetime that specifies the latest moment this seed data is
  considered valid. After this time it will not be used anymore and will get
  automatically deleted from the database.

Interaction with embedding
--------------------------

When you use embedding, you'll typically want to start the form on your own domain/page
instead of the default form page of Open Forms. Pass the ``formUrl`` property in the
create request of the exact form location, and the ``redirectUrl`` will make use of it.

E.g. if the form will be filled out at ``https://example.com/my-cms-page/the-form``:

.. code-block:: http

    POST /api/v2/public/initial-data HTTP/1.0
    Authorization: Token <token>
    Content-Type: application/json

    {
      "form": "f094a464-00e0-431a-8e77-07d5b409133d",
      "formUrl": "https://example.com/my-cms-page/the-form",
      "representee": {
        "authAttribute": "bsn",
        "value": "000000000"
      },
      "ttl": 2
    }

Security and privacy considerations
===================================

* Only the original creator of the initial data can retrieve it again from the API.
* The representation never returns the ``representee`` or other potentially sensitive
  information, when reading it. This includes the response to the create call. Only
  essential metadata is returned.
* Once the ``ttl`` is expired, a periodic task will permanently delete the seed data
  from the database. The TTL has an upper limit of 7 days.
* When seed data is used, this is logged to the audit log, together with the
  organization employee identifier.
* Initial data is one-time use - once it's related to a submission (i.e. the form was
  started after logging in), it cannot be used again.
* Guessing the UUID of seed data is not part of the threat model:

  - it's extremely unlikely that a correct UUID is guessed that is also still valid
    within the TTL window.
  - *using* the seed data requires a user account with the appropriate permissions.
