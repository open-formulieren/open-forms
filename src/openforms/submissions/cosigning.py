"""
Expose utilities for submissions that require cosigning.

Cosigning is the practice where a second actor "approves" the submission. The original
submitter specifies who needs to cosign, e.g. a partner.

Currently there are two versions of cosigning, with a third in the making:

* v1: a cosign component directly in the form, which starts an additional authentication
  flow. When the submission is completed, it is already cosigned. This flow causes
  problems if the DigiD session is remembered and the original submitter is
  automatically logged in again.
* v2: still a component in the form, but cosigning is now out-of-band. The original
  submitter provides the email address of the cosigner who will receive the request
  via email. When the submission is completed, it is not yet cosigned.
* v3: will probably be similar to v2, but more rigid and without Formio components.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Literal, NotRequired, TypedDict

import structlog

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.typing import FormAuth
from openforms.formio.typing import Component
from openforms.typing import JSONObject

if TYPE_CHECKING:
    from .models import Submission

logger = structlog.stdlib.get_logger(__name__)

type CosignData = CosignV1Data | CosignV2Data


class CosignV1Data(TypedDict):
    """
    The shape of data stored in
    :attr:`openforms.submissions.models.Submission.co_sign_data`.
    """

    version: Literal["v1"]
    plugin: str
    identifier: str
    representation: NotRequired[str]
    co_sign_auth_attribute: AuthAttribute
    fields: JSONObject


class CosignV2Data(FormAuth):
    """
    The shape of data stored in
    :attr:`openforms.submissions.models.Submission.co_sign_data`.

    In cosign v2, the data inherits from the standard :class:`FormAuth` data, so it
    contains the auth plugin, attribute and identifier value.
    """

    version: Literal["v2"]
    cosign_date: NotRequired[str]
    """
    ISO-8601 formatted datetime indicating when the cosigner confirmed the submission.

    The key may be absent in legacy submissions, which is why it's marked as
    ``NotRequired``. It was added in Open Forms 2.7.0

    .. todo:: DeprecationWarning -> remove NotRequired in Open Forms 4.0.
    """


class CosignState:
    """
    Encapsulate all the cosign state of a submission.
    """

    def __init__(self, submission: Submission):
        self.submission = submission

    def __repr__(self):
        reference = (
            self.submission.public_registration_reference or self.submission.uuid
        )
        return f"<CosignState submission=<Submission reference={reference}>>"

    def _find_component(self) -> Component | None:
        """
        Discover the Formio cosign component in the submission/form.
        """
        from .form_logic import check_submission_logic

        check_submission_logic(self.submission)

        # use the complete view on the Formio component tree(s)
        configuration_wrapper = self.submission.total_configuration_wrapper

        # there should only be one cosign component, so we check our flatmap to find the
        # component.
        for component in configuration_wrapper.component_map.values():
            if component["type"] == "cosign":
                # we can't just blindly return the component, as it may be conditionally
                # displayed, which is equivalent to "cosign not relevant". See
                # https://github.com/open-formulieren/open-forms/issues/3901
                state = self.submission.load_submission_value_variables_state()
                visible = configuration_wrapper.is_visible_in_frontend(
                    component["key"], values=state.get_data(include_unsaved=True)
                )
                if not visible:
                    return None
                return component
        return None

    @property
    def is_required(self) -> bool:
        """
        Determine if cosigning is required for the submission or not.

        Cosign is considered required in either of the following conditions:

        * the cosign component in the form is required (even after evaluating form logic)
        * the cosign component in the form is optional and an email address has been
          provided - this indicates the submitter wanted someone to cosign it given the
          choice.

        .. note:: This does not consider cosign v1, as the cosigning is required to be
           able to complete the submission.
        """
        cosign_component = self._find_component()
        if cosign_component is None:
            return False

        # if the component itself is marked as required, we know for sure cosigning is
        # required
        required = cosign_component.get("validate", {}).get("required", False)
        if required:
            return True

        # otherwise, we check if there's a cosigner email specified
        return bool(self.email)

    @property
    def is_waiting(self) -> bool:
        """
        Indicate if the submission is still waiting to be cosigned.
        """
        if self.is_signed:
            return False

        # Cosign not complete, but required or the component was filled in the form
        if self.is_required:
            return True

        # Cosign optional or possibly not relevant at all.
        return False

    @property
    def is_signed(self) -> bool:
        """
        Indicate if the submission has been cosigned.
        """
        return self.submission.cosign_complete

    @cached_property
    def email(self) -> str:
        """
        Get the email address of the cosigner.
        """
        cosign_component = self._find_component()
        assert cosign_component is not None, (
            "You can only look up the email in forms that have a cosign component"
        )

        variables_state = self.submission.load_submission_value_variables_state()
        values = variables_state.get_data()
        # detect inconsistent state - the component may be added after the submission
        # was completed
        if (key := cosign_component["key"]) not in values:
            logger.info(
                "cosign_component_key_missing_from_values",
                submission_uuid=str(self.submission.uuid),
                component_key=key,
            )
            return ""
        cosigner_email = values[key]
        assert isinstance(cosigner_email, str)
        return cosigner_email

    @property
    def legacy_signing_details(self) -> CosignData:
        """
        Expose the legacy cosign data.

        In the legacy format, we don't know (at the type level) whether cosign v1 or
        v2 was used.
        """
        return self.submission.co_sign_data

    @property
    def signing_details(self) -> CosignV2Data:
        """
        Expose the cosign details.

        Legacy (cosign v1) cosign details are unsupported, use
        :attr:`legacy_signing_details` for those instead.
        """
        assert self.is_signed, (
            "You may only access the signing details after validating the 'is_signed' state."
        )
        return self.submission.co_sign_data
