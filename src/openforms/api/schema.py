from drf_spectacular.openapi import AutoSchema as _AutoSchema


class AutoSchema(_AutoSchema):
    # Subclassed because we often end up hooking into the schema generator. This
    # provides the plumbing.
    pass
