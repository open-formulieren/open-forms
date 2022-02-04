from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from cookie_consent.admin import LogItemAdmin as CookieLogAdmin
from cookie_consent.models import LogItem as CookieLog
from cspreports.admin import CSPReportAdmin
from cspreports.models import CSPReport
from djchoices import ChoiceItem, DjangoChoices


class SubmitActions(DjangoChoices):
    save = ChoiceItem("_save", _("Save"))
    add_another = ChoiceItem("_addanother", _("Save and add another"))
    edit_again = ChoiceItem("_continue", _("Save and continue editing"))


def replace_cookie_log_admin():
    # defaults to True
    if getattr(settings, "COOKIE_CONSENT_LOG_ENABLED", True):

        class LogAdmin(CookieLogAdmin):
            def has_add_permission(self, request):
                return False

            def has_delete_permission(self, request, obj=None):
                return False

            def has_change_permission(self, request, obj=None):
                return False

        admin.site.unregister(CookieLog)
        admin.site.register(CookieLog, LogAdmin)


class CSPReportOverrideAdmin(CSPReportAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.unregister(CSPReport)
admin.site.register(CSPReport, CSPReportOverrideAdmin)
