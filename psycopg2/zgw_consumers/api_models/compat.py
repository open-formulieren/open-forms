try:
    from relativedeltafield.utils import parse_relativedelta
except ImportError:  # before 1.1.2
    from relativedeltafield import parse_relativedelta  # noqa
