from typing import TYPE_CHECKING, Optional

from django.utils.translation import gettext_lazy as _

from openforms.variables.base import BaseStaticVariable
from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.registry import register_static_variable

if TYPE_CHECKING:  # pragma: nocover
    from openforms.submissions.models import Submission


@register_static_variable("product")
class Product(BaseStaticVariable):
    name = _("Product")
    data_type = FormVariableDataTypes.object

    def get_initial_value(self, submission: Optional["Submission"]) -> Optional[dict]:
        if not submission or not submission.form.product:
            return None

        product = submission.form.product
        data = {
            "uuid": product.uuid,
            "name": product.name,
            "price": product.price,
            "information": product.information,
        }
        return data
