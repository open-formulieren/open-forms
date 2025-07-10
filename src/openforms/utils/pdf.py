from django.conf import settings

import structlog

logger = structlog.stdlib.get_logger(__name__)


def get_base_url():
    return settings.BASE_URL


def render_to_pdf(template_name: str, context: dict[str, object]) -> tuple[str, bytes]:
    """
    Render a (HTML) template to PDF with the given context.
    """
    # local import to avoid importing weasyprint at startup time
    from maykin_common.pdf import render_template_to_pdf as _render_template_to_pdf

    return _render_template_to_pdf(template_name, context, variant="pdf/ua-1")


def convert_html_to_pdf(html: str) -> bytes:
    """Convert a string with HTML to a PDF."""
    # local import to avoid importing weasyprint at startup time
    from maykin_common.pdf import render_to_pdf as _render_to_pdf

    _, pdf = _render_to_pdf(html, variant="pdf/ua-1")
    return pdf
