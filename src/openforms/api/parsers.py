from django.conf import settings

from rest_framework import parsers

from .exceptions import RequestEntityTooLarge


class MaxFilesizeMultiPartParser(parsers.MultiPartParser):
    """
    A multipart parser that limits the request body size with file uploads.

    Django has ``DATA_UPLOAD_MAX_MEMORY_SIZE``, but this excludes file uploads, posing
    no limit on the maximum allowed file size.

    Every Formio upload (even with file multiple) is sent to the upload endpoint -
    multiple files are not combined into a single request (body) for upload.
    Effectively, the file upload size is restricted by using this parser.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        # the superclass also fails on missing request in the parser context, we can
        # safely assume the request is present
        request = parser_context["request"]

        # Content-Length should contain the length of the body we are about
        # to parse.
        try:
            content_length = int(request.headers.get("content-length", 0))
        except (ValueError, TypeError):
            content_length = 0

        # check that content length is not greater than what is allowed
        if content_length > settings.MAX_FILE_UPLOAD_SIZE:
            raise RequestEntityTooLarge()

        # ok - we can send this body to the actual parser.
        # Validating the result of this (the files) doesn't make sense, as the request body
        # contains metadata about the file (name, content-length...) with a non-zero size.
        # If the file itself would be larger than ``MAX_FILE_UPLOAD_SIZE``, then the
        # validation of the entire body would have tripped already (at the nginx level even!).
        return super().parse(
            stream, media_type=media_type, parser_context=parser_context
        )


class PlainTextParser(parsers.BaseParser):
    """
    Plain text parser.
    """

    media_type = "text/plain"

    def parse(
        self, stream, media_type: str | None = None, parser_context: dict | None = None
    ) -> str:
        """
        Simply return a string representing the body of the request.
        """
        return stream.read()
