.. _developers_authentication_plugins:

======================
Authentication plugins
======================

Open Forms has a plugin system for the
:ref:`authentication module <developers_backend_modules_authentication>`, which is
invoked when a user wants to login on a form. In the form builder, it's possible to
specify which plugins are available for authentication. Some plugins allow additional
form-specific configuration.

.. _developers_authentication_plugins_python_api:

Public Python API
=================

Authentication plugins must inherit from the base plugin.

Plugins that use the OpenID Connect (OIDC) protocol should inherit from the OIDC plugin
base :class:`openforms.contrib.auth_oidc.plugin.OIDCAuthentication`.

**Plugin base API**

.. automodule:: openforms.authentication.base
   :members:

**Plugin Generic OIDC class**

.. autoclass:: openforms.contrib.auth_oidc.plugin.OIDCAuthentication
   :members:
