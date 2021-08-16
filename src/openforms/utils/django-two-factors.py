from django.utils.module_loading import import_string


def should_display_dropdown_menu(request):
    return import_string("django_admin_index.utils.should_display_dropdown_menu")(request) and request.user.is_verified()
