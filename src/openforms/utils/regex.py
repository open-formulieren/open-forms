import re


def add_cosign_info_templatetag(template: str) -> str:
    pattern = re.compile(
        r"(\{% summary %\}|\{% appointment_information %\}|\{% payment_information %\})"
    )
    replacement = r"{% cosign_information %}\n\1"
    return pattern.sub(replacement, template, count=1)
