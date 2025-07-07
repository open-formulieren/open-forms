.. _developers_backend_modules_authentication:

==============
Authentication
==============

The authentication plugins allow end-users/citizen to identify themselves when
interacting with official municipality forms. This makes users more trustful and
identifiable.

.. contents:: :local:
   :depth: 3

Python API
==========

The public API serves as an abstraction over the various engines.

**Reference**

.. automodule:: openforms.authentication.service
   :members:


Plugin developer reference
--------------------------

See the :ref:`Python API <developers_authentication_plugins_python_api>`.


Available implementations
=========================

The following plugins are available in Open Forms core.

Yivi (OIDC)
-----------

Yivi allows authentication based on attributes (which *could* be a bsn or kvk-number).
This means that we cannot know beforehand which specific claims will be received after
authentication.

Configuration is done in the admin via **Configuratie** > **Yivi (OIDC)**.

.. automodule:: openforms.authentication.contrib.yivi_oidc
   :members:

.. note:: For end-users to authenticate with Yivi they need access to a mobile phone with
   the Yivi app installed.

.. note:: Technical note: Yivi usage is currently limited to Signicat.

Form specific configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When configuring the Yivi plugin, in the form builder, you can specify which
authentication options are available during login (bsn, kvk and/or pseudo) and which
additional attributes should be requested from the user.

.. autoclass:: openforms.authentication.contrib.yivi_oidc.config.YiviOptionsSerializer
   :members:

Requesting attributes using the condiscon system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`Condiscon <https://docs.yivi.app/condiscon/>`_ is a Yivi-specific way of defining the
authentication attributes to request from users. With condiscon you define a multi-layer
conditional data structure, which provides users more control over which attributes they
do and don't provide.

Which attributes to use is derived from the
:mod:`openforms.authentication.contrib.yivi_oidc.config.YiviOptionsSerializer`
:attr:`authentication_options` and :attr:`additional_attributes_groups`. In the
:func:`start_login()` we pass the plugin options to the Yivi
:class:`openforms.authentication.contrib.yivi_oidc.views.OIDCAuthenticationInitView`.
From here, we used in the :func:`get_extra_params()` function to add the attributes to
the authentication request.

As the condiscon scope is form-specific, we need to modify the authentication request
scopes dynamically. The scope is shaped following the
`Signicat parameters <https://developer.signicat.com/broker/signicat-identity-broker/authentication-providers/yivi.html#example-of-adding-condiscon-parameter-in-your-oidc-request>`_
scope standard.

.. autoclass:: openforms.authentication.contrib.yivi_oidc.views.OIDCAuthenticationInitView
   :members:

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
