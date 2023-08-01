from dataclasses import dataclass
from typing import Any, Iterator

from openforms.formio.rendering.nodes import ComponentNodeBase
from openforms.formio.service import FormioData, format_value
from openforms.submissions.rendering import Renderer

from .service import get_appointment


@dataclass
class ContactDetailNode(ComponentNodeBase):
    """
    Rendering of a contact detail formio component.

    Ideally we'd be able to share more logic with the
    :class:`openforms.formio.rendering.nodes.ComponentNode`, but that is too tighly
    coupled with ``FormStep`` and ``SubmissionStep`` Django models at the moment.

    Therefore, this implementation is extremely minimal.
    """

    data: FormioData

    @property
    def value(self) -> Any:
        assert "key" in self.component
        return self.data[self.component["key"]]

    @property
    def display_value(self) -> Any:
        return format_value(self.component, self.value, as_html=self.renderer.as_html)

    def get_children(self):
        return []

    def render(self) -> str:
        """
        Output a simple key-value pair of label and value.
        """
        return f"{self.label}: {self.display_value}"


class AppointmentRenderer(Renderer):
    """
    Custom renderer outputting the appointment contact details.
    """

    def get_children(self) -> Iterator[ContactDetailNode]:
        appointment = get_appointment(self.submission)
        if appointment is None:
            return

        data = FormioData(appointment.contact_details)
        for component in appointment.contact_details_meta:
            yield ContactDetailNode(renderer=self, component=component, data=data)
