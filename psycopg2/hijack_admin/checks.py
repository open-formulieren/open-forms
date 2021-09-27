# -*- coding: utf-8 -*-
from django.core.checks import Error, Warning, register
from django.conf.global_settings import AUTH_USER_MODEL as DEFAULT_AUTH_USER_MODEL
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model

from hijack import settings as hijack_settings


def _using_hijack_admin_mixin():
    from hijack_admin.admin import HijackUserAdminMixin

    user_admin_class_name = getattr(
        settings, 'HIJACK_USER_ADMIN_CLASS_NAME', None)
    user_admin_class = user_admin_class_name \
        if user_admin_class_name else type(
            admin.site._registry.get(get_user_model(), None))

    return issubclass(user_admin_class, HijackUserAdminMixin)


def check_get_requests_allowed(app_configs, **kwargs):
    errors = []
    if not hijack_settings.HIJACK_ALLOW_GET_REQUESTS:
        errors.append(
            Error(
                'Hijack GET requests must be allowed for django-hijack-admin to work.',
                hint='Set HIJACK_ALLOW_GET_REQUESTS to True.',
                obj=None,
                id='hijack_admin.E001',
            )
        )
    return errors


def check_custom_user_model(app_configs, **kwargs):
    warnings = []
    if (settings.AUTH_USER_MODEL != DEFAULT_AUTH_USER_MODEL and
            not _using_hijack_admin_mixin()):
        warnings.append(
            Warning(
                'django-hijack-admin does not work out the box with a custom user model.',
                hint='Please mix HijackUserAdminMixin into your custom UserAdmin.',
                obj=settings.AUTH_USER_MODEL,
                id='hijack_admin.W001',
            )
        )
    return warnings


def register_checks():
    for check in [
        check_get_requests_allowed,
        check_custom_user_model,
    ]:
        register(check)
