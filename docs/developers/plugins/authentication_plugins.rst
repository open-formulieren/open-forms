.. _developers_authentication_plugins:

======================
Authentication plugins
======================

Open Forms has a plugin system for the authentication module. The authentication module
is invoked when users login using one of the possible authentication methods. In the form
builder, it's possible to specify which authentication methods are available for users.
Some authentication methods allow further plugin-specific configuration to specify
additional authentication requirements.

Each plugin is responsible for specific authentication flows and serves different form
and user needs.

Yivi plugins
============

Most authentication plugins require users to authenticate using a certain identity
provider (i.e. DigiD or eHerkenning), after which we expect certain claims to be
available, like claims for the bsn or kvk-numbers.

Yivi is a bit strange in that regard, as it provides/allows authentication using multiple
identity providers. This means that we cannot expect any specific claims to been met
after authentication.

Yivi configuration
------------------

When configuring the Yivi plugin, in the form builder, you can specify which
authentication options are available during login with Yivi and which additional
attributes should be requested.

Basic auth flow
---------------

When the end-user uses a form with Yivi authentication, they can login using the Yivi
mobile app. Using the app, users can choose which authentication option to use and which
attributes to provide. This results in specific claims being returned.

Because the end-user chooses which authentication option to use, we cannot know
beforehand which identifying values (kvk, bsn, pseudo) will be available after
authentication. We need to check the returned claims to determine which authentication
option was used and what we should do with the authentication data.

Additional attributes using condiscon
-------------------------------------

Due to the flexibility of available authentication options and additional attributes, we
cannot specify the scope in the global Yivi configuration; instead, we need to specify
the scopes on the fly. For this, we need a custom AuthenticationInitView.

From the plugin options we can determine which scopes to use (using the
``authentication_options`` and ``additional_attributes_groups``). In the
``start_login()`` we pass the plugin options to the Yivi AuthenticationInitView. From
here, we used in the ``get_extra_params()`` function to add the scopes to the
authentication request.

By passing the scopes as `condiscon <https://irma.app/docs/condiscon/>`_ we can give
users the ability to choose which attributes to accept (otherwise, all attributes would
be required). In ``_yivi_condiscon_scope()`` we create the condiscon scope and return the
scopes in the `Signicat condiscon scope shape <https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request>`_.

After authentication
--------------------

After authentication we look at the resulting authentication claims, these decide how the
authentication data is saved and used. In the Yivi plugin
``_get_user_chosen_authentication_attribute()`` function we determine the used
authentication option, which is then used in ``transform_claims()`` to map the auth
claims to a ``FormAuth`` shape.

All other claims (that are not authentication identification specific) that are returned
we check against the plugin options specified ``additional_attributes_groups``. If the claim is
derived from one of the additional attributes, then we add it to the ``FormAuth`` under
the collective name ``additional_claims``.
