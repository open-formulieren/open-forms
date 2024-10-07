.. _developers_extensions:

==========
Extensions
==========

Official extensions maintained by the Open Forms core developers.

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

   * Prefill data is retrieved using the client
     :class:`openforms.contrib.haal_centraal.clients.brp.BRPClient`, which makes use of
     the pre-request hooks through :class:`openforms.pre_requests.clients.PreRequestMixin`.
     It intercepts the :mod:`requests` request preparation to modify the request before
     it's actually sent out over the network.
   * The ``open-forms-ext-token-exchange`` extension registers a pre-request hook which adds a
     `custom authentication class`_ to the request.
   * The custom authentication class ``token_exchange.auth.TokenAccessAuth`` checks if the URL to which the
     request is being made has a service with an associated ``token_exchange.models.TokenExchangeConfiguration``.
     If it's NOT the case, it doesn't do anything. If it's the case, it makes the token exchange request to Keycloak
     and adds the obtained access token to the headers of the request to the downstream API.

.. _token exchange: https://www.keycloak.org/securing-apps/token-exchange
.. _open-forms-ext-token-exchange: https://github.com/open-formulieren/open-forms-ext-token-exchange
.. _custom authentication class: https://requests.readthedocs.io/en/latest/user/advanced.html#custom-authentication
.. _mozilla-django-oidc: https://github.com/mozilla/mozilla-django-oidc/blob/2.0.0/mozilla_django_oidc/auth.py

Haal Centraal HR prefill extension
==================================

This is an extension to add a prefill plugin to retrieve data from the `Haal Centraal HR API`_ using KVK numbers.
The Haal Centraal HR API is a Den Haag specific API and not a national Dutch standard. For this reason, this prefill
plugin was added as an extension rather than a Open-Forms core prefill plugin: `open-forms-ext-haalcentraal-hr`_.

This prefill plugin supports the Keycloak token exchange if used alongside the Keycloak token exchange extension.

.. _Haal Centraal HR API: https://app.swaggerhub.com/apis/DH-Sandbox/handelsregister/1.3.0
.. _open-forms-ext-haalcentraal-hr: https://github.com/open-formulieren/open-forms-ext-haalcentraal-hr

Configuration
-------------

* Go to **Configuration** > **Services** and create a service for Haal Centraal HR.
* Go to **Configuration** > **Application groups** > **Configuration**.
  Move the model ``prefill_haalcentraalhr.Haalcentraalhrconfig`` from the left to the right panel. Then click on **Save**.
* Go to **Configuration** > **Haal Centraal HR Configuration**. Select the service for Haal Centraal HR and save the configuration.

If the token exchange should be performed:

* Go to **Miscellaneous** > **Token exchange plugin configurations**.
  Click on **Add Token exchange plugin configuration** and fill in the details:

  * Select the Haal Centraal HR service.
  * Add the Keycloak audience.

  Save the configuration.

The prefill will be available in the form designer in the same way as other prefill plugins.


