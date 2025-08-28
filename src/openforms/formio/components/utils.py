import html

from django.utils.crypto import salted_hmac


def _normalize_pattern(pattern: str) -> str:
    """
    Normalize a regex pattern so that it matches from beginning to the end of the value.
    """
    if not pattern.startswith("^"):
        pattern = f"^{pattern}"
    if not pattern.endswith("$"):
        pattern = f"{pattern}$"
    return pattern


def salt_location_message(message_bits: dict[str, str]) -> str:
    """
    Put an extra layer of protection and make sure that the value is not tampered with.
    """
    computed_message = f"{message_bits['postcode']}/{message_bits['number']}/{message_bits['city']}/{message_bits['street_name']}"
    computed_hmac = salted_hmac("location_check", value=computed_message).hexdigest()
    return computed_hmac


def sanitize_file_name(file_name: str) -> str:
    """
    copy of MultiPartParser.sanitize_file_name method
    """
    file_name = html.unescape(file_name)
    file_name = file_name.rsplit("/")[-1]
    file_name = file_name.rsplit("\\")[-1]
    # Remove non-printable characters.
    file_name = "".join([char for char in file_name if char.isprintable()])

    return file_name
