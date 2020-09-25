registry = {}


def register(func):
    dotted_path = f"{func.__module__}.{func.__qualname__}"
    registry[dotted_path] = func
    return func


@register
def console_backend(submission):
    print(submission.data)


@register
def create_zaak_backend(submission):
    print(submission.data)
