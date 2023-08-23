from typing import Iterator

from openforms.formio.rendering.nodes import ComponentNode
from openforms.formio.typing import Component
from openforms.submissions.rendering import Renderer

from .service import get_appointment


class AppointmentRenderer(Renderer):
    """
    Custom renderer outputting the appointment contact details.
    """

    def get_children(self) -> Iterator[ComponentNode]:
        appointment = get_appointment(self.submission)
        if appointment is None:
            return

        components: list[Component] = appointment.contact_details_meta
        data = appointment.contact_details
        for index, component in enumerate(components):
            child_node = ComponentNode.build_node(
                step_data=data,
                component=component,
                renderer=self,
                configuration_path=f"{index}",
            )
            yield child_node
            yield from child_node
