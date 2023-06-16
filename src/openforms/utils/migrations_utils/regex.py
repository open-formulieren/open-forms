import re


def add_cosign_info_templatetag(template: str) -> str:
    pattern = re.compile(
        r"(\{%\s?summary\s?%\}|\{%\s?appointment_information\s?%\}|\{%\s?payment_information\s?%\})"
    )
    replacement = r"{% cosign_information %}\n\1"
    return pattern.sub(replacement, template, count=1)
