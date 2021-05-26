====================
Registration plugins
====================

Open Forms has a plugin system for the registrations module. The registrations module
is invoked when a form submission is completed, and is responsible for persisting the
form data to the configured backend.

Developing plugins
==================

Every possible backend can be implemented as a plugin, and registered with Open Forms.

Registering the plugin makes it available for content-editors to select as a registration
backend for a form.

Registration
------------

Plugins are implemented as Django apps / Python packages. The
``openforms.registrations.contrib.demo`` plugin acts as an example.

1. Create the python package in ``openforms.registrations.contrib.<vendor>``
2. Ensure you have an AppConfig_ defined in this package, e.g.:

   .. code-block:: python

       class MyPlugin(AppConfig):
           name = "openforms.registrations.contrib.<vendor>"
           verbose_name = "My <vendor> plugin"

           def ready(self):
               from . import plugin  # noqa

   It's important to import the plugin as part of the ``ready`` hook of the ``AppConfig``,
   as this ensures that the plugin is added to the registry.

3. Add the application to ``settings.INSTALLED_APPS``, this will cause the ``AppConfig``
   to be loaded.

Implementation
--------------

A plugin is nothing more than a callable, most often a plain Python function. It must
adhere to the following function signature:

.. code-block:: python

    from typing import Optional

    from openforms.submissions.models import Submission


    def plugin(submission: Submission, options: dict) -> Optional[dict]:
        # do stuff


The function body is of course up to you to interact with the registration backend.

Each backend can require additional configuration/options that is required for the
implementation. This is specified as a ``rest_framework.serializers.Serializer``:

.. code-block:: python

    from zgw_consumers.models import Service, APITypes


    class PluginOptions(serializers.Serializer):
        zaaktype = serializers.URLField()
        zaken_api = serializers.PrimaryKeyRelatedField(
            queryset=Service.objects.filter(api_type=APITypes.zrc)
        )

Plugin developers have full control over these serializers.

The serializer is specified during plugin registration, using the ``@register``
decorator syntax:

.. code-block:: python

    from ...registry import register


    @register("unique-key", "Human readable name", configuration_options=PluginOptions)
    def plugin(submission: Submission, options: dict) -> dict:
        ...


The return value of the callback is saved on the submission as backend result/log. If
this is not JSON-serializable, you can specify a serializer for this as well:

.. code-block:: python

    from ...registry import register


    @register(
        "unique-key",
        "Human readable name",
        configuration_options=PluginOptions,
        backend_feedback_serializer=BackendFeedbackSerializer,
    )
    def plugin(submission: Submission, options: dict) -> dict:
        ...


Registration failure
--------------------

If the registration fails for whatever reason, then your plugin should raise
:class:`openforms.registrations.exceptions.RegistrationFailed`. This will mark the
submission with a failed state, making it possible to handle these failures.

The submission handler extracts the traceback, so you should ideally raise this exception
from the root exception to include the full traceback:

.. code-block:: python

    try:
        ...  # do plugin stuff
    except Exception as exc:
        raise RegistrationFailed from exc

.. _AppConfig: https://docs.djangoproject.com/en/2.2/ref/applications/
