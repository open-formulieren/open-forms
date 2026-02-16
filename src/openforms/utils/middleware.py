from django.conf import settings

from openforms.config.models import CSPSetting


# TODO: this should probably be upgraded to a custom subclass:
# https://django-csp.readthedocs.io/en/v4.0/migration-guide.html#migrating-custom-middleware
class UpdateCSPMiddleware:
    """
    adds database driven CSP directives by simulating the django-csp '@csp_update' decorator

    https://django-csp.readthedocs.io/en/latest/decorators.html#csp-update
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def get_csp_update(self) -> dict[str, list[str]]:
        update = dict()

        # dynamic admin driven
        _append_dict_list_values(update, CSPSetting.objects.as_dict())

        # TODO more contributions can be collected here
        return update

    def __call__(self, request):
        response = self.get_response(request)

        update = self.get_csp_update()
        if not update:
            return response

        # we're basically copying/extending the @csp_update decorator

        # cooperate with possible data from actual decorator
        _is_report_only = bool(settings.CONTENT_SECURITY_POLICY_REPORT_ONLY)
        attrname = "_csp_update_ro" if _is_report_only else "_csp_update"

        have = getattr(response, attrname, None)
        if have:
            _append_dict_list_values(have, update)
        else:
            setattr(response, attrname, update)

        return response


def _merge_list_values(left, right) -> list[str]:
    # combine strings or lists to a list with unique values
    if isinstance(left, str):
        left = [left]
    if isinstance(right, str):
        right = [right]
    return list(set(*left, *right))


def _append_dict_list_values(target, source):
    for k, v in source.items():
        if k in target:
            target[k] = _merge_list_values(target[k], v)
        else:
            if isinstance(v, str):
                target[k] = [v]
            else:
                target[k] = list(set(v))
