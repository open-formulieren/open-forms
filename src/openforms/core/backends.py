registry = {}


def register(func):
    dotted_path = f"{func.__module__}.{func.__qualname__}"
    registry[dotted_path] = func
    return func


@register
def console_backend(submission_step) -> None:
    print(submission_step.data)
