inline_registry = {}


def register_inline(*args, **kwargs):
    def inner(admin_inline):
        name = kwargs["backend_name"]
        inline_registry[name] = admin_inline
        return admin_inline

    return inner
