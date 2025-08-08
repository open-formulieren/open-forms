from typing import cast

from django.template.backends.django import DjangoTemplates
from django.utils.functional import SimpleLazyObject


class SandboxedDjangoTemplates(DjangoTemplates):
    """
    A 'sandboxed' Django templates backend.

    The sandboxed backend (by default) does not allow:

    * looking up template files from file-system
    * loading or using non-builtin templatetag libraries (except for the ``l10n`` library)
    """

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
                "openforms.utils.templatetags.utils",
            ],
        )
        super().__init__(params)

    def get_templatetag_libraries(self, custom_libraries: dict) -> dict:
        """
        Do not automatically discover template tag libraries.

        This prevents user-content from loading and using the libraries that are
        private API to Open Forms.
        """
        return {}


backend = SandboxedDjangoTemplates({})
"""
An instance of the 'sandboxed' Django templates backend.
"""


def get_registration_custom_libraries() -> list[str]:
    """Get all the custom templatetag libraries defined in the registration backends"""
    from openforms.registrations.registry import register as registry

    # Add any custom templatetags libraries from the registration plugins
    libraries = []
    # Iterate over both enabled/not-enabled plugins, since the backend is initialised once
    for plugin in registry:
        libraries += plugin.get_custom_templatetags_libraries()
    return libraries


def get_openforms_backend():
    return SandboxedDjangoTemplates(
        {
            "OPTIONS": {
                "builtins": [
                    "openforms.emails.templatetags.appointments",
                    "openforms.emails.templatetags.cosign_information",
                    "openforms.emails.templatetags.form_summary",
                    "openforms.emails.templatetags.payment",
                    "openforms.emails.templatetags.products",
                    "openforms.config.templatetags.privacy_policy",
                    "openforms.submissions.templatetags.cosign",
                    "mozilla_django_oidc_db.templatetags.oidc_client",
                ]
                + get_registration_custom_libraries(),
            }
        }
    )


openforms_backend = cast(
    SandboxedDjangoTemplates, SimpleLazyObject(get_openforms_backend)
)
"""
Sandbox instance supporting custom tags for form designers.
"""
