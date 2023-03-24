"""
Utility classes for the submission report rendering.
"""
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form

if TYPE_CHECKING:
    from .models import Submission

logger = logging.getLogger(__name__)


@dataclass
class CoSigner:
    def __init__(self, co_sign_data: dict, auth_attribute: str):
        self.co_sign_data = co_sign_data
        self.auth_attribute = auth_attribute

    @property
    def representation(self) -> str:
        return self.co_sign_data.get("representation", "")

    @property
    def identifier(self) -> str:
        return self.co_sign_data.get("identifier", "")

    def __str__(self):
        if not self.identifier:
            return _(
                "{representation} (missing {auth_attribute} for co-signer)"
            ).format(
                representation=self.representation, auth_attribute=self.auth_attribute
            )
        return f"{self.representation} ({self.auth_attribute}: {self.identifier})"

    def __repr__(self):
        return f"CoSigner(co_sign_data={self.co_sign_data}, auth_attribute={self.auth_attribute})"


@dataclass
class Report:
    submission: "Submission"

    def __post_init__(self):
        from .rendering.renderer import Renderer, RenderModes

        self.renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=True
        )

    @property
    def form(self) -> Form:
        return self.submission.form

    @property
    def show_payment_info(self) -> bool:
        return self.submission.payment_required and self.submission.price

    @property
    def co_signer(self) -> Optional[CoSigner]:
        if not (co_sign_data := self.submission.co_sign_data):
            return None

        co_signer = CoSigner(co_sign_data, self.submission.auth_info.attribute)

        if not co_signer.identifier:
            logger.warning(
                "Incomplete co-sign data for submission %s", self.submission.uuid
            )

        return co_signer

    @property
    def confirmation_page_content(self) -> SafeString:
        # the content is already escaped by Django's rendering engine and mark_safe
        # has been applied by ``Template.render``
        content = self.submission.render_confirmation_page()
        return content
