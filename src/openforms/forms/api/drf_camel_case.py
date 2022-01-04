from djangorestframework_camel_case.settings import api_settings

from openforms.registrations.registry import register


class FormCamelCaseMixin:
    @property
    def json_underscoreize(self):
        """
        Get the keys to ignore from all registration plugins.

        .. todo:: this would greatly benefit from a more advanced drf-camel-case, where
           keys are now global without any context. it would benefit greatly from being
           able to namespace this, but that's currently not possible in the library.

        .. warning:: this also puts _all_ the plugin-specific keys into the same parser,
           while we'd rather be able to just validate this depending on the applicable
           registration backend. Future improvement!
        """
        ignore_fields = []
        for plugin in register:
            if not plugin.camel_case_ignore_fields:
                continue
            ignore_fields += list(plugin.camel_case_ignore_fields)

        return {
            **api_settings.JSON_UNDERSCOREIZE,
            "ignore_fields": ignore_fields,
        }
