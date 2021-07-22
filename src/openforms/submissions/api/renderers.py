from rest_framework import renderers


class PDFRenderer(renderers.BaseRenderer):
    # this is a bit of a lie, since we're using it for a send-file response that returns
    # generated PDFs. So it's actually nginx doing the actual response.
    # Example in DRF docs: https://www.django-rest-framework.org/api-guide/renderers/#setting-the-character-set
    media_type = "application/pdf"
    format = "pdf"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class FileRenderer(renderers.BaseRenderer):
    media_type = "application/octet-stream"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data
