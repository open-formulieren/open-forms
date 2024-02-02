from django_admin_index.utils import (
    should_display_dropdown_menu as default_should_display_dropdown_menu,
)


def should_display_dropdown_menu(request) -> bool:
    default = default_should_display_dropdown_menu(request)

    # never display the dropdown in two-factor admin views
    if request.resolver_match.view_name.startswith("maykin_2fa:"):
        return False

    # do not display the dropdown until the user is verified.
    return default and request.user.is_verified()
