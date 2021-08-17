from django_admin_index.utils import should_display_dropdown_menu as default_should_display_dropdown_menu


def should_display_dropdown_menu(request):
    return default_should_display_dropdown_menu(request) and request.user.is_verified()
