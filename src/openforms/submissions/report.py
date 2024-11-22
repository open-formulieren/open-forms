"""
Utility classes for the submission report rendering.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

from openforms.authentication.service import AuthAttribute
from openforms.forms.models import Form

if TYPE_CHECKING:
    from .models import Submission

logger = logging.getLogger(__name__)


@dataclass
class Report:
    submission: Submission

    def __post_init__(self):
        from .rendering.renderer import Renderer, RenderModes

        self.renderer = Renderer(
            submission=self.submission, mode=RenderModes.pdf, as_html=True
        )

    @property
    def form(self) -> Form:
        return self.submission.form

    @property
    def needs_privacy_consent(self) -> bool:
        return self.submission.form.get_statement_checkbox_required(
            "ask_privacy_consent"
        )

    @property
    def needs_statement_of_truth(self) -> bool:
        return self.submission.form.get_statement_checkbox_required(
            "ask_statement_of_truth"
        )

    @property
    def show_payment_info(self) -> bool:
        return self.submission.payment_required and self.submission.price

    @property
    def co_signer(self) -> str:
        """Retrieve and normalize data about the co-signer of a form"""

        if not (co_sign_data := self.submission.co_sign_data):
            return ""

        representation = co_sign_data.get("representation") or ""
        identifier = co_sign_data["identifier"]
        co_sign_auth_attribute = co_sign_data["co_sign_auth_attribute"]
        auth_attribute_label = AuthAttribute[co_sign_auth_attribute].label

        if not representation:
            logger.warning(
                "Incomplete co-sign data for submission %s", self.submission.uuid
            )

        return _("{representation} ({auth_attribute}: {identifier})").format(
            representation=representation,
            auth_attribute=auth_attribute_label,
            identifier=identifier,
        )

    @property
    def confirmation_page_content(self) -> SafeString:
        # a submission that requires cosign is by definition not finished yet, so
        # displaying 'confirmation page content' doesn't make sense. Instead, we
        # render a simple notice describing the cosigning requirement.
        if self.submission.requires_cosign:
            return format_html(
                "<p>{content}</p>",
                content=_(
                    "This PDF was generated before submission processing has started "
                    "because it needs to be cosigned first. The cosign request email "
                    "was sent to {email}."
                ).format(email=self.submission.cosigner_email),
            )

        # the content is already escaped by Django's rendering engine and mark_safe
        # has been applied by ``Template.render``
        content = self.submission.render_confirmation_page()
        return content

    @property
    def appointment(self):
        from openforms.appointments.service import AppointmentRenderer

        return AppointmentRenderer(
            submission=self.renderer.submission,
            mode=self.renderer.mode,
            as_html=self.renderer.as_html,
        )
