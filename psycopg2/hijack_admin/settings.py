from django.conf import settings

HIJACK_BUTTON_TEMPLATE = getattr(settings, 'HIJACK_BUTTON_TEMPLATE', 'hijack_admin/admin_button.html')

HIJACK_REGISTER_ADMIN = getattr(settings, 'HIJACK_REGISTER_ADMIN', True)
