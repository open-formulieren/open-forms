.. _developers_extensions:

==========
Extensions
==========

Keycloak token exchange extension
=================================

The municipality of Den Haag started a proof of concept for the addition of Attribute Based Access Control (ABAC) to the
ZGW APIs. This means that an authenticated user should only be able to retrieve data from the ZGW APIs which they are
entitled to see. In the proof of concept, the Keycloak preview feature called "`token exchange`_" is leveraged to get a
OAUTH2 access token that is then sent to the downstream APIs to determine what the user is allowed to retrieve.

Open Forms makes requests to APIs like, for example, Haal Centraal when retrieving user data for the prefill at the
start of a submission. To work with Den Haag's proof of concept, we need to obtain the access token from Keycloak
to send it to Haal Centraal. Because the token exchange is not a Keycloak core feature (disabled by default), this
process was implemented in Open Forms as an extension: `open-forms-ext-token-exchange`_.

The flow works as follows:

#. A user logs in with DigiD/eHerkenning/eIDAS/DigiD Machtigen/eHerkenning Bewindvoering through Keycloak (OpenID
   connect). Keycloak returns a token in the payload along with the BSN/KvK/Pseudo ID.

   * The authentication plugins in Open Forms extract the user information from the payload and add it to the session
     under the :class:`openforms.authentication.constants.FORM_AUTH_SESSION_KEY` key.
   * The :class:`AuthenticationReturnView` of the authentication plugins fires a signal to notify that the authentication
     was successful if the :class:`openforms.authentication.constants.FORM_AUTH_SESSION_KEY` key is present in the session.
   * The ``open-forms-ext-token-exchange`` extension receives the signal and extracts the Keycloak token from the request.
     This token is saved in thread local memory.

#. The submission is started and Open Forms requests prefill data from Haal Centraal:

   * The client that makes the request to the ZGW API is :class:`openforms.pre_requests.clients.PreRequestZGWClient`.
     This client is a subclass of :class:`zgw_consumers.client.ZGWClient` which overrides the ``pre_request`` method so
     that any pre-request hooks registered in Open Forms are run before performing the request.
   * The ``open-forms-ext-token-exchange`` extension registers a pre-request hook which adds a
     `custom authentication class`_ to the request.
   * The custom authentication class :class:`token_exchange.auth.TokenAccessAuth` checks if the URL to which the
     request is being made has a service with an associated :class:`token_exchange.models.TokenExchangeConfiguration`.
     If it's NOT the case, it doesn't do anything. If it's the case, it makes the token exchange request to Keycloak
     and adds the obtained access token to the headers of the request to the downstream API.

#. The token exchange extension hooks into the ``request_finished`` Django signal. Once a request has been handled, the token
   stored in the thread local memory is clear to prevent mixing up tokens between requests.

.. _token exchange: https://www.keycloak.org/docs/latest/securing_apps/#_token-exchange
.. _open-forms-ext-token-exchange: https://github.com/open-formulieren/open-forms-ext-token-exchange
.. _custom authentication class: https://requests.readthedocs.io/en/latest/user/advanced/#custom-authentication
