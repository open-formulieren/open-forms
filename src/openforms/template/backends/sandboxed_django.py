from django.template.backends.django import DjangoTemplates


class SandboxedDjangoTemplates(DjangoTemplates):
    def __init__(self, params):
        params = params.copy()
        params.setdefault("NAME", "django_sandboxed")
        # no file system paths to look up files (also blocks {% include %} etc)
        params.setdefault("DIRS", [])
        params.setdefault("APP_DIRS", False)

        params.setdefault("OPTIONS", {})
        params["OPTIONS"].setdefault(
            "autoescape", True
        )  # assume HTML context and auto-escape
        params["OPTIONS"].setdefault(
            "libraries", {}
        )  # no access to our custom template tags by default
        params["OPTIONS"].setdefault(
            "builtins",
            [
                "django.templatetags.l10n",  # allow usage of localize/unlocalize
            ],
        )
        super().__init__(params)

    def get_templatetag_libraries(self, custom_libraries):
        """
        Do not automatically discover template tag libraries.

        This prevents user-content from loading and using the libraries that are
        private API to Open Forms.
        """
        return {}


backend = SandboxedDjangoTemplates({})
"""
An instance of the 'sandboxed' Django templates backend.

The sandboxed backend (by default) does not allow:

* looking up template files from file-system
* loading or using non-builtin templatetag libraries (except for the ``l10n`` library)
"""
