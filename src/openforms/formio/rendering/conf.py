from openforms.submissions.rendering.constants import RenderModes

from .constants import RenderConfigurationOptions
from .nodes import RenderConfiguration

RENDER_CONFIGURATION = {
    # RenderModes.cli: RenderConfiguration(key=None, default=True),
    RenderModes.pdf: RenderConfiguration(
        RenderConfigurationOptions.show_in_pdf, default=True
    ),
    RenderModes.confirmation_email: RenderConfiguration(
        RenderConfigurationOptions.show_in_confirmation_email, default=False
    ),
    RenderModes.export: RenderConfiguration(key=None, default=True),
}
"""
Map render modes to the component configuration key to check, with their defaults.
"""
