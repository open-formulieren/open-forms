import rest_framework_nested
from rest_framework_nested.viewsets import (
    NestedViewSetMixin as _NestedViewSetMixin,
    _force_mutable,
)

assert rest_framework_nested.__version__ == "0.95.0"


class NestedViewSetMixin(_NestedViewSetMixin):
    def initialize_request(self, request, *args, **kwargs):
        """
        Adds the parent params from URL inside the children data available
        """
        # PATCHED: Call the super super
        # - request = super().initialize_request(request, *args, **kwargs)
        # + request = super(_NestedViewSetMixin, self).initialize_request(request, *args, **kwargs)
        request = super(_NestedViewSetMixin, self).initialize_request(
            request, *args, **kwargs
        )

        for url_kwarg, fk_filter in self._get_parent_lookup_kwargs().items():
            # fk_filter is alike 'grandparent__parent__pk'
            parent_arg = fk_filter.partition("__")[0]
            for querydict in [request.data, request.query_params]:
                with _force_mutable(querydict):
                    # PATCHED: manage.py spectacular crashed due to a KeyError
                    # - querydict[parent_arg] = kwargs[url_kwarg]
                    # + querydict[parent_arg] = kwargs.get(url_kwarg)
                    querydict[parent_arg] = kwargs.get(url_kwarg)
        return request
