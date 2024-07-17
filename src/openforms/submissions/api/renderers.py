from rest_framework import renderers


class FileRenderer(renderers.BaseRenderer):
    media_type = "application/octet-stream"
    format = "octet"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class PlainTextErrorRenderer(renderers.BaseRenderer):
    media_type = "text/plain"
    format = "txt"

    def render(
        self, serializer_errors, accepted_media_type=None, renderer_context=None
    ):
        messages = []
        for sub_errors in serializer_errors.values():
            messages.extend(sub_errors)
        message = " ".join(messages)
        return message.encode(self.charset)
