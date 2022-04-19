from typing import List

from django.conf import settings

from openforms.forms.models.form import FormsExport
from openforms.tokens import BaseTokenGenerator


class ExportedFormsTokenGenerator(BaseTokenGenerator):
    """
    Strategy object used to generate and check tokens for downloading a zip file of exported forms.
    """

    key_salt = "openforms.forms.admin.tokens.ExportedFormsTokenGenerator"
    token_timeout_days = settings.FORMS_EXPORT_DOWNLOAD_LINK_EXPIRES_AFTER_DAYS

    def get_hash_value_parts(self, exported_forms: FormsExport) -> List[str]:
        exported_forms_attributes = (
            "id",
            "datetime_downloaded",
        )
        exported_forms_bits = [
            str(getattr(exported_forms, attribute) or "")
            for attribute in exported_forms_attributes
        ]
        return exported_forms_bits


exported_forms_token_generator = ExportedFormsTokenGenerator()
