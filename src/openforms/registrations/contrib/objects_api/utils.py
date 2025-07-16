from django.utils.html import escape

from openforms.typing import VariableValue


def recursively_escape_html_strings[T: VariableValue](value: T) -> T:
    """
    Recursively apply HTML escaping to string value nodes.
    """
    match value:
        case list():
            return [recursively_escape_html_strings(item) for item in value]  # pyright: ignore[reportReturnType]
        case dict():
            return {
                key: recursively_escape_html_strings(value)
                for key, value in value.items()
            }  # pyright: ignore[reportReturnType]
        case str():
            return escape(value)
        case _:
            # nothing to do, return unmodified
            return value


def apply_defaults_to(config_group, options) -> None:
    options.setdefault("version", 1)
    options.setdefault(
        "informatieobjecttype_submission_report",
        config_group.informatieobjecttype_submission_report,
    )
    options.setdefault(
        "informatieobjecttype_submission_csv",
        config_group.informatieobjecttype_submission_csv,
    )
    options.setdefault(
        "informatieobjecttype_attachment", config_group.informatieobjecttype_attachment
    )
    options.setdefault("organisatie_rsin", config_group.organisatie_rsin)

    # now, normalize the catalogue information and associated document types
    has_catalogue_override = (catalogue := options.get("catalogue")) is not None
    if not has_catalogue_override and config_group.catalogue_domain:
        # domain implies RSIN is set
        catalogue = {
            "domain": config_group.catalogue_domain,
            "rsin": config_group.catalogue_rsin,
        }
    options.setdefault("catalogue", catalogue)

    # if we don't have a catalogue override, we can just pick the first non-empty
    # document reference
    for opt in (
        "iot_submission_report",
        "iot_submission_csv",
        "iot_attachment",
    ):
        default_value = getattr(config_group, opt)
        match options.get(opt):
            # if there's a catalogue override, do not use fallback document
            # description
            case "" | None if has_catalogue_override:
                pass
            # if there's no catalogue override, use the fallback value, which *may*
            # be an empty string too (in this case, the missing key is normalized)
            case "" | None if not has_catalogue_override:
                options[opt] = default_value
            # if there's a non-empty override, leave it untouched
            case str(some_val) if len(some_val) > 0:
                pass
