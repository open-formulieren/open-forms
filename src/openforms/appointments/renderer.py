from collections.abc import Iterator

from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from openforms.formio.rendering.nodes import ComponentNode
from openforms.formio.service import FormioData
from openforms.formio.typing import Component
from openforms.submissions.rendering import Renderer

from .utils import get_appointment, get_plugin


class AppointmentRenderer(Renderer):
    """
    Custom renderer outputting the appointment contact details.
    """

    def get_children(self) -> Iterator[ComponentNode]:
        appointment = get_appointment(self.submission)
        if appointment is None:
            return

        components: list[Component] = appointment.contact_details_meta
        data = FormioData(appointment.contact_details)
        for index, component in enumerate(components):
            child_node = ComponentNode.build_node(
                step_data=data,
                component=component,
                renderer=self,
                configuration_path=f"{index}",
            )
            yield from child_node

    def __str__(self) -> SafeString:
        # Like a Django Form renderer, render to the requested representation

        if (
            not (appointment := get_appointment(self.submission))
            or not appointment.plugin
        ):
            return ""

        template_name = (
            f"appointments/appointment__{self.mode}.{'html' if self.as_html else 'txt'}"
        )
        plugin = get_plugin(plugin=appointment.plugin)

        identifier: str = self.submission.appointment_info.appointment_id
        ctx = {
            "appointment": plugin.get_appointment_details(identifier),
            "contact_details": self.get_children(),  # todo: a bit of a wart
        }
        return render_to_string(template_name, ctx)
