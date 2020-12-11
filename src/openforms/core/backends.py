registry = {}


def register(func):
    dotted_path = f"{func.__module__}.{func.__qualname__}"
    registry[dotted_path] = func
    return func


@register
def console_backend(submission) -> None:
    for step in submission.submissionstep_set.all():
        print(step.data)
