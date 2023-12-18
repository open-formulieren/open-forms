.. _developers_extensions:

==========
Extensions
==========

Keycloak token exchange extension
=================================

The municipality of Den Haag started a proof of concept for the addition of Attribute Based Access Control (ABAC) to the
ZGW APIs. This means that an authenticated user should only be able to retrieve data from external services (such as
Haal Centraal BRP bevragen or retrieving case data from the ZGW APIs) which they are entitled to see.
In the proof of concept, the Keycloak preview feature called "`token exchange`_" is leveraged to get a
(OAUTH2) access token that is then sent to the downstream APIs to determine what the user is allowed to retrieve.

Open Forms makes requests to APIs like, for example, Haal Centraal when retrieving user data for the prefill at the
start of a submission. To work with Den Haag's proof of concept, we need to obtain the access token from Keycloak
to send it to Haal Centraal. Because the token exchange is not a Keycloak core feature (disabled by default), this
process was implemented in Open Forms as an extension: `open-forms-ext-token-exchange`_.

The flow works as follows:

#. A user logs in with DigiD/eHerkenning/eIDAS/DigiD Machtigen/eHerkenning Bewindvoering through Keycloak (OpenID
   connect). Keycloak returns a token in the payload along with the BSN/KvK/Pseudo ID.

   * The authentication plugins in Open Forms extract the user information from the payload and add it to the session
     under the :const:`openforms.authentication.constants.FORM_AUTH_SESSION_KEY` key.
   * The `mozilla-django-oidc`_ saves the access token to the session, under the key ``oidc_access_token``. See the
     method ``store_tokens``.
   * The :class:`AuthenticationReturnView` of the authentication plugins fires a signal to notify that the authentication
     was successful if the :const:`openforms.authentication.constants.FORM_AUTH_SESSION_KEY` key is present in the session.

#. The submission is started:

   * The ``perform_create`` of the :class:`openforms.submissions.api.viewsets.SubmissionViewSet` fires the
     ``submission_start`` signal.
   * The ``open-forms-ext-token-exchange`` extension receives the signal and extracts the Keycloak token from the session.
     This token is cached with key ``accesstoken:<submission uuid>``.

#. Open Forms requests prefill data from Haal Centraal:

   * The client that makes the request to the ZGW API is :class:`openforms.pre_requests.clients.PreRequestZGWClient`.
     This client is a subclass of :class:`zgw_consumers.client.ZGWClient` which overrides the ``pre_request`` method so
     that any pre-request hooks registered in Open Forms are run before performing the request.
   * The ``open-forms-ext-token-exchange`` extension registers a pre-request hook which adds a
     `custom authentication class`_ to the request.
   * The custom authentication class ``token_exchange.auth.TokenAccessAuth`` checks if the URL to which the
     request is being made has a service with an associated ``token_exchange.models.TokenExchangeConfiguration``.
     If it's NOT the case, it doesn't do anything. If it's the case, it makes the token exchange request to Keycloak
     and adds the obtained access token to the headers of the request to the downstream API.

.. _token exchange: https://www.keycloak.org/docs/latest/securing_apps/#_token-exchange
.. _open-forms-ext-token-exchange: https://github.com/open-formulieren/open-forms-ext-token-exchange
.. _custom authentication class: https://requests.readthedocs.io/en/latest/user/advanced.html#custom-authentication
.. _mozilla-django-oidc: https://github.com/mozilla/mozilla-django-oidc/blob/2.0.0/mozilla_django_oidc/auth.py
