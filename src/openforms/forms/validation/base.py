from django.utils.translation import gettext_lazy as _

from openforms.plugins.plugin import AbstractBasePlugin
from openforms.typing import JSONObject


class BaseValidator(AbstractBasePlugin):
    @property
    def verbose_name(self):
        return _("FormIO '{type}' component validator").format(type=self.identifier)

    def __call__(self, component: JSONObject) -> None:
        raise NotImplementedError("You must implement the __call__ method")  # noqa
