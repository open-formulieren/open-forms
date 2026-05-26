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

Custom auth context for third-party plugins
===========================================

The built-in authentication plugins (DigiD, eHerkenning, Yivi, etc.) each have a
dedicated ``TypedDict`` in :mod:`openforms.authentication.types` that describes
the shape of their auth context. These types are collected in the ``AnyAuthContext``
union.

Third-party plugins that manage their own auth context do not need to add a
plugin-specific type to this union. Instead, set ``manage_auth_context = True``
on the plugin class and implement
:meth:`~openforms.authentication.base.BasePlugin.auth_info_to_auth_context`
to return a dict matching :class:`~openforms.authentication.types.PluginAuthContext`:

.. code-block:: python

    from openforms.authentication.base import BasePlugin
    from openforms.authentication.types import PluginAuthContext

    class MyPlugin(BasePlugin):
        manage_auth_context = True

        def auth_info_to_auth_context(self, auth_info) -> PluginAuthContext:
            return {
                "source": "my-provider",
                "levelOfAssurance": auth_info.loa,
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "bsn",
                        "identifier": auth_info.value,
                    }
                },
            }

``PluginAuthContext`` uses ``str`` for ``source`` and ``levelOfAssurance`` and
``dict`` for ``authorizee``, so the plugin is free to structure the authorizee
payload however it needs.

**Reference**

.. autoclass:: openforms.authentication.types.PluginAuthContext
