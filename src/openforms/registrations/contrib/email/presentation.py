from dataclasses import dataclass
from typing import Any

from django.urls import reverse
from django.utils.html import format_html_join

from furl import furl

from openforms.utils.urls import build_absolute_uri


@dataclass
class SubmittedDataWrapper:
    value: Any
    is_file: bool = False

    def __str__(self):
        return self.as_html()

    def as_html(self):
        if self.is_file:
            return self.display_files(html=True)

        # bit of duplication from display_value... recurse!
        elif isinstance(self.value, (list, tuple)):
            return ", ".join(
                [SubmittedDataWrapper(value=v).as_html() for v in self.value]
            )

        return str(self.value)

    def as_plain_text(self):
        if self.is_file:
            return self.display_files(html=False)
        # bit of duplication from display_value... recurse!
        elif isinstance(self.value, (list, tuple)):
            return ", ".join(
                [SubmittedDataWrapper(value=v).as_plain_text() for v in self.value]
            )
        return str(self.value)

    def display_files(self, html=True) -> str:
        files = []
        for submission_file_attachment in self.value:
            display_name = submission_file_attachment.get_display_name()
            download_link = build_absolute_uri(
                reverse(
                    "submissions:attachment-download",
                    kwargs={"uuid": submission_file_attachment.uuid},
                )
            )
            url = furl(download_link)
            url.args["hash"] = submission_file_attachment.content_hash
            files.append((url, display_name))

        if html:
            return format_html_join(
                ", ",
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                files,
            )

        else:
            return ", ".join(f"{link} ({display})" for link, display in files)
