from hijack.permissions import superusers_only


def verified_superusers_only(*, hijacker, hijacked):
    return (
        superusers_only(hijacker=hijacker, hijacked=hijacked) and hijacker.is_verified()
    )
