import itertools


def peek(sequence):
    """
    Returns the value of the top of the sequence without removing the value
    from the data.
    """
    iterable = iter(sequence)
    try:
        first = next(iterable)
        return first, itertools.chain([first], iterable)
    except StopIteration:
        return None, []
