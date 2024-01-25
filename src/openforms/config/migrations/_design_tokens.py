from copy import deepcopy
from typing import Callable, TypeAlias, TypedDict

from glom import assign, delete, glom

# mapping from new, NL DS token to the source (old custom token)
BUTTON_MAPPING = {
    "utrecht.button.background-color": "of.button.bg",
    "utrecht.button.border-color": "of.button.color-border",
    "utrecht.button.color": "of.button.fg",
    "utrecht.button.font-family": "of.typography.sans-serif.font-family",
    "utrecht.button.hover.background-color": "of.button.hover.bg",
    "utrecht.button.hover.border-color": "of.button.hover.color-border",
    "utrecht.button.active.background-color": "of.button.active.bg",
    "utrecht.button.active.border-color": "of.button.active.color-border",
    "utrecht.button.active.color": "of.button.active.fg",
    "utrecht.button.focus.border-color": "of.button.focus.color-border",
    "utrecht.button.primary-action.background-color": "of.button.primary.bg",
    "utrecht.button.primary-action.border-color": "of.button.primary.color-border",
    "utrecht.button.primary-action.color": "of.button.primary.fg",
    "utrecht.button.primary-action.hover.background-color": "of.button.primary.hover.bg",
    "utrecht.button.primary-action.hover.border-color": "of.button.primary.hover.color-border",
    "utrecht.button.primary-action.active.background-color": "of.button.primary.active.bg",
    "utrecht.button.primary-action.active.border-color": "of.button.primary.active.color-border",
    "utrecht.button.primary-action.active.color": "of.button.primary.active.fg",
    "utrecht.button.primary-action.focus.border-color": "of.button.primary.focus.color-border",
    "utrecht.button.primary-action.danger.background-color": "of.button.danger.bg",
    "utrecht.button.primary-action.danger.border-color": "of.button.danger.color-border",
    "utrecht.button.primary-action.danger.color": "of.button.danger.fg",
    "utrecht.button.primary-action.danger.hover.background-color": "of.button.danger.hover.bg",
    "utrecht.button.primary-action.danger.hover.border-color": "of.button.danger.hover.color-border ",
    "utrecht.button.primary-action.danger.active.background-color": "of.button.danger.active.bg",
    "utrecht.button.primary-action.danger.active.border-color": "of.button.danger.active.color-border ",
    "utrecht.button.primary-action.danger.active.color": "of.button.danger.active.fg",
    "utrecht.button.primary-action.danger.focus.border-color": "of.button.danger.focus.color-border ",
    "utrecht.button.secondary-action.background-color": "of.color.bg",
    "utrecht.button.secondary-action.border-color": "of.color.border",
    "utrecht.button.secondary-action.color": "of.color.fg",
    "utrecht.button.secondary-action.hover.background-color": "of.button.hover.bg",
    "utrecht.button.secondary-action.hover.border-color": "of.button.hover.color-border",
    "utrecht.button.secondary-action.active.background-color": "of.button.active.bg",
    "utrecht.button.secondary-action.active.border-color": "of.button.active.color-border",
    "utrecht.button.secondary-action.active.color": "of.button.active.fg",
    "utrecht.button.secondary-action.focus.border-color": "of.color.focus-border",
    "utrecht.button.secondary-action.danger.background-color": "of.button.danger.bg",
    "utrecht.button.secondary-action.danger.border-color": "of.button.danger.color-border",
    "utrecht.button.secondary-action.danger.color": "of.button.danger.fg",
    "utrecht.button.secondary-action.danger.hover.background-color": "of.button.danger.hover.bg",
    "utrecht.button.secondary-action.danger.hover.border-color": "of.button.danger.hover.color-border",
    "utrecht.button.secondary-action.danger.active.background-color": "of.button.danger.active.bg ",
    "utrecht.button.secondary-action.danger.active.border-color": "of.button.danger.active.color-border ",
    "utrecht.button.secondary-action.danger.active.color": "of.button.danger.active.fg",
    "utrecht.button.secondary-action.danger.focus.border-color": "of.button.danger.focus.color-border ",
    "utrecht.button.subtle.danger.background-color": "of.button.danger.bg",
    "utrecht.button.subtle.danger.border-color": "of.button.danger.color-border",
    "utrecht.button.subtle.danger.color": "of.color.danger",
    "utrecht.button.subtle.danger.active.background-color": "of.color.danger",
    "utrecht.button.subtle.danger.active.color": "of.color.bg",
}


# mapping from new, NL DS token to the source (old custom token)
LAYOUT_MAPPING = {
    # footer
    "utrecht.page-footer.background-color": "of.page-footer.bg",
    "utrecht.page-footer.color": "of.page-footer.fg",
    # header
    "utrecht.page-header.background-color": "of.page-header.bg",
    "utrecht.page-header.color": "of.page-header.fg",
    # use logical properties instead of absolute positions
    "of.page-header.logo-return-url.min-block-size": "of.page-header.logo-return-url.min-height",
    "of.page-header.logo-return-url.min-inline-size": "of.page-header.logo-return-url.min-width",
    "of.page-header.logo-return-url.mobile.min-block-size": "of.page-header.logo-return-url.mobile.min-height",
    "of.page-header.logo-return-url.mobile.min-inline-size": "of.page-header.logo-return-url.mobile.min-width",
}

OBSOLETE_PREFIXES = (
    "of.page-footer.",
    "of.page-header.",
)


class TokenValue(TypedDict):
    value: str


TokenContainer: TypeAlias = dict[str, "TokenValue | TokenContainer"]


unset = object()


def apply_button_mapping(design_tokens: TokenContainer) -> TokenContainer:
    result = deepcopy(design_tokens)

    tokens_to_unset = set()

    for new, old in BUTTON_MAPPING.items():
        old_value = glom(design_tokens, old, default=unset)
        if old_value is unset:
            continue

        existing_value = glom(result, new, default=unset)
        if existing_value is not unset:
            tokens_to_unset.add(old)
            continue

        assign(result, new, old_value, missing=dict)
        tokens_to_unset.add(old)

    for token in tokens_to_unset:
        # don't delete utility tokens!
        if not token.startswith("of.button."):
            continue
        delete(result, token)

    return remove_empty_design_tokens(result)


def apply_layout_mapping(design_tokens: TokenContainer) -> TokenContainer:
    result = deepcopy(design_tokens)

    tokens_to_unset = set()

    for new, old in LAYOUT_MAPPING.items():
        old_value = glom(design_tokens, old, default=unset)
        if old_value is unset:
            continue

        existing_value = glom(result, new, default=unset)
        if existing_value is not unset:
            tokens_to_unset.add(old)
            continue

        assign(result, new, old_value, missing=dict)
        tokens_to_unset.add(old)

    # TODO: re-enable this when #3593 is properly resolved.
    # for token in tokens_to_unset:
    #     # don't delete utility tokens!
    #     if not any(token.startswith(prefix) for prefix in OBSOLETE_PREFIXES):
    #         continue
    #     delete(result, token)

    return remove_empty_design_tokens(result)


def remove_empty_design_tokens(obj: dict) -> dict:
    if "value" in obj:
        return obj

    result = {}
    for key, value in obj.items():
        if not isinstance(value, dict):
            continue
        updated_value = remove_empty_design_tokens(value)
        # empty object -> remove it by not including it anymore
        if not updated_value:
            continue

        result[key] = updated_value

    return result


def _update_factory(mapper: Callable[[TokenContainer], TokenContainer]):
    def inner(apps, _):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.first()
        if config is None:
            return

        updated = mapper(config.design_token_values)
        if updated != config.design_token_values:
            config.design_token_values = updated
            config.save(update_fields=["design_token_values"])

    return inner


update_button_design_token_values = _update_factory(apply_button_mapping)
update_layout_design_token_values = _update_factory(apply_layout_mapping)
