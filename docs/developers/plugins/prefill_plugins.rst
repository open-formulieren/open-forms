.. _developers_prefill_plugins:

===============
Prefill plugins
===============

Open Forms has a plugin system for the prefill module. The prefill module is invoked
when form step (or rather, submission steps) are retrieved from the API to obtain the
FormioJS configuration. In the form builder, it's possible to specify which plugin and
plugin-specific attribute to use to prefill the default value.

Each plugin is responsible for fetching the relevant data from the plugin-specific
backend, which could be StUF-BG, HaalCentraal BRP or Chamber of Commerce for example.

Developing plugins
==================

Every possible backend can be implemented as a plugin, and registered with Open Forms.

Registering the plugin makes it available for content-editors to select as possible
prefill option for a form field.

You can find an example implementation in :mod:`openforms.prefill.contrib.demo`.

Implementation
--------------

Plugins must be added to the ``INSTALLED_APPS`` setting in :mod:`openforms.conf.base`. See the demo 
app (:class:`openforms.prefill.contrib.demo.apps.DemoApp`) as an example.

Plugins must implement the interface from :class:`openforms.prefill.base.BasePlugin`.
It's safe to use this as a base class.

There are two relevant public methods:

``get_available_attributes``
    provide an iterable of ``(identifier, label)`` tuples. This is used to pre-populate/
    display the list of attributes that can be selected by content-editors.
``get_prefill_values``
    the actual implementation of the prefill functionality. This is invoked inside the
    request-response cycle of certain API endpoints.

Context-aware prefill attributes
--------------------------------

Some prefill plugins have attributes that depend on form-level configuration
(e.g. which authentication flow is selected). Instead of returning a static list
from ``get_available_attributes``, these plugins can declare a custom API
endpoint that the form builder calls at design time.

Override :meth:`~openforms.prefill.base.BasePlugin.get_custom_attributes_url` to
return an absolute API path:

.. code-block:: python

    @register("my-plugin")
    class MyPrefill(BasePlugin):
        requires_auth_plugin = ("my-auth",)

        @classmethod
        def get_custom_attributes_url(cls) -> str:
            return "/api/v2/my-plugin/available-claims"

        @staticmethod
        def get_available_attributes():
            # Static fallback (used by non-JS callers and tests)
            return (("claim_a", "Claim A"), ("claim_b", "Claim B"))

The endpoint must return a JSON array of ``{"id": "...", "label": "..."}``
objects.

When ``customAttributesUrl`` is set (exposed in the prefill plugin list API
response), the form builder will ``GET`` this URL instead of the default
``/api/v2/prefill/plugins/<id>/attributes`` endpoint. The options from the
matching authentication backend are forwarded as query parameters, so the
endpoint can scope the attribute list to the selected authentication flow.

For example, if the form has an authentication backend with
``options: {"clientId": "abc-123"}``, the form builder will request::

    GET /api/v2/my-plugin/available-claims?clientId=abc-123

Public Python API
=================

**Plugin base class**

.. autoclass:: openforms.prefill.base.BasePlugin
   :members:

**Module documentation**

.. automodule:: openforms.prefill
   :members:
