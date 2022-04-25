"""
High-level submission renderer capable of outputting to different modes.
"""
from dataclasses import dataclass
from typing import List, Optional

from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

from openforms.forms.models import Form

from ..models import Submission


class RenderModes(DjangoChoices):
    cli = ChoiceItem("cli", _("CLI"))
    pdf = ChoiceItem("pdf", _("PDF"))
    confirmation_email = ChoiceItem("confirmation_email", _("Confirmation email"))
    export = ChoiceItem("export", _("Submission export"))
    # registration_email = ChoiceItem('registration_email', _("Registration email"))


@dataclass
class Renderer:
    # render context
    submission: Submission
    mode: str
    as_html: bool
    limit_value_keys: Optional[List[str]] = None

    @property
    def form(self) -> Form:
        return self.submission.form
