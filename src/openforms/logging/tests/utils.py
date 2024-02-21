from django.test import override_settings


def disable_timelinelog():
    """
    Disable actually creating the audit logs in timeline logger.
    """
    return override_settings(AUDITLOG_DISABLED=True)
