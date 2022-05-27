from typing import Dict, List

from openforms.config.models import GlobalConfiguration


class UpdateCSPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def get_csp_update(self) -> Dict[str, List[str]]:
        update = dict()
        config = GlobalConfiguration.get_solo()
        _append_dict_list_values(update, config.get_csp_updates())
        return update

    def __call__(self, request):
        response = self.get_response(request)

        update = self.get_csp_update()
        if not update:
            return response

        # we're basically copying/extending the @csp_update decorator
        update = dict((k.lower().replace("_", "-"), v) for k, v in update.items())

        # cooperate with possible data from actual decorator
        have = getattr(response, "_csp_update", None)
        if have:
            _append_dict_list_values(have, update)
        else:
            response._csp_update = update

        return response


def _merge_list_values(left, right) -> List[str]:
    if isinstance(left, str):
        left = [left]
    if isinstance(right, str):
        right = [right]
    return list(set(*left, *right))


def _append_dict_list_values(target, source):
    for k in source:
        if k in target:
            target[k] = _merge_list_values(target[k], source[k])
        else:
            if isinstance(source[k], str):
                target[k] = [source[k]]
            else:
                target[k] = source[k]
