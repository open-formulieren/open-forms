.. _developers_backend_modules_authentication:

==============
Authentication
==============

The authentication module provides plugins to establish the identity of end-users
filling out a form. Identifying attributes can then be used by
:ref:`developers_prefill_plugins` to retrieve additional details of the citizen or
company. Depending on the authentication plugin used, a certain level of assurance
regarding the authentication strength can be obtained as well, increasing trust for
higher levels.

.. contents:: :local:
   :depth: 2

Python API
==========

The public API serves as an abstraction over the various plugins.

**Reference**

.. automodule:: openforms.authentication.service
   :members:


Plugin developer reference
--------------------------

See the :ref:`Python API <developers_authentication_plugins_python_api>`.


Available implementations
=========================

The following plugins are available in Open Forms core.

Demo, DigiD Mock, Outage
------------------------

Demo plugins, available only to admin users and when demo plugins are enabled in the
configuration. They allow simulating various login mechanisms without requiring a real
integration.

DigiD
-----

Provides DigiD integration via the SAMLv2 standards. Implemented throught the library
django-digid-eherkenning.

eHerkenning and eIDAS
---------------------

Provides eHerkenning and eIDAS integration via the SAMLv2 standards. Implemented
through the library django-digid-eherkenning.

DigiD and eHerkenning/eIDAS via OpenID Connect
----------------------------------------------

DigiD, eHerkenning and eIDAS support through the OIDC protocol rather than SAML. Depends
on an OpenID Connect provider that implements the SAML flows under the hood. Implemented
throught the ``oidc`` flavour of the django-digid-eherkenning library.

Organisation (OIDC)
-------------------

Provides authentication for staff users through their organisation single-sign on.
Shares the OpenID Connect configuration for the admin login option, but is exposed to
form authentication as well.

Yivi (OIDC)
-----------

Yivi authenticates based on attributes (which *could* be a bsn or kvk-number) disclosed
by the end users. As a consequence, we cannot know beforehand which specific claims will
be received after authentication.

Configuration is done in the admin via **Configuratie** > **Yivi (OIDC)**.

.. note:: End-users must have the Yivi app installed on their phone.

.. warning:: Due to technical reasons, Yivi support is currently only available through
   Signicat.

Form specific configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When configuring the Yivi plugin, in the form builder, you can specify which
authentication options are available during login (bsn, kvk and/or pseudo) and which
additional attributes should be requested from the user. See
:class:`openforms.authentication.contrib.yivi_oidc.config.YiviOptionsSerializer` for
details.

Requesting attributes using the condiscon system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Condiscon <https://docs.yivi.app/condiscon/>`_ is a Yivi-specific way of defining the
authentication attributes to request from users. With condiscon you define a multi-layer
conditional data structure, which provides users more control over which attributes they
do and don't provide.

:attr:`openforms.authentication.contrib.yivi_oidc.config.YiviOptionsSerializer.authentication_options`
and :attr:`openforms.authentication.contrib.yivi_oidc.config.YiviOptionsSerializer.additional_attributes_groups`
determine which attributes to include in the condiscon parameter.

:meth:`openforms.authentication.contrib.yivi_oidc.plugin.YiviOIDCAuthentication.start_login`
passes the plugin options to
:class:`openforms.authentication.contrib.yivi_oidc.views.OIDCAuthenticationInitView`,
after which :meth:`openforms.authentication.contrib.yivi_oidc.views.OIDCAuthenticationInitView.get_extra_params`
adds the attributes to the authentication request.

As the condiscon scope is form-specific, we need to modify the authentication request
scopes dynamically. The scope is shaped following the
`Signicat parameters <https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request>`_
scope standard.

.. note:: Important notes about the Yivi attributes and condiscon!

   - For the Yivi authentication to be successful, at least *one* attribute needs to be
     disclosed.
   - The order of `optional disjunction <https://docs.yivi.app/condiscon/#other-features>`_
     matters. Make sure that the "empty" option is the last item in the disjunction list.

     Example of a valid optional disjunction:

     .. code:: json

       [
         [
           ["pbdf.pbdf.diploma.degree"],
           [],
         ]
       ]

Authentication result
^^^^^^^^^^^^^^^^^^^^^

Which authentication value (bsn, kvk or pseudo) is returned by the plugin depends on the
form-specific configuration, and the data provided by the user.

To determine which authentication option was used you have to check the returned claims.
This is done by the :func:`_get_user_chosen_authentication_attribute()` function; it
checks the returned claims against the global configuration for bsn and kvk claims. If
they match, then we know if the user logged in using bsn, kvk or anonymous/pseudo.

Generic OIDC support
^^^^^^^^^^^^^^^^^^^^

The current Yivi setup is limited to Signicat condiscon. For generic OIDC support we need
to investigate how other identity providers work with Yivi.

In this context, "generic OIDC" means the normal way of working with OIDC, similar to how
DigiD and eHerkenning via OIDC work. Instead of one gigantic bundled scope, you provide
individual scopes for the claims you want to be fulfilled.

(This way of working *might* result into losing the major strength of Yivi; that the user
can choose what data they provide.)

Generic OIDC authentication with Signicat
"""""""""""""""""""""""""""""""""""""""""

One piece of the puzzle: generic OIDC authentication via Signicat.

Besides the condiscon scope, Signicat also supports generic OIDC authentication. With the
generic OIDC authentication you don't provide a single scope that results in multiple
claims; rather, you pass each Yivi attribute as an individual scope item.

For example, the following scope will request the bsn and fullname of a user:

.. code-block:: bash

    scope: "openid irma-demo.gemeente.personalData.bsn irma-demo.gemeente.personalData.fullname"

Whether other identity providers work similarly is yet to determine.

Reference
^^^^^^^^^

.. automodule:: openforms.authentication.contrib.yivi_oidc
   :members:

.. autoclass:: openforms.authentication.contrib.yivi_oidc.config.YiviOptionsSerializer

.. autoclass:: openforms.authentication.contrib.yivi_oidc.plugin.YiviOIDCAuthentication
   :members:

.. autoclass:: openforms.authentication.contrib.yivi_oidc.views.OIDCAuthenticationInitView
   :members:
