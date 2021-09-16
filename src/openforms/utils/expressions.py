from django.db.models import F, Value
from django.db.models.functions import Coalesce, NullIf


def FirstNotBlank(*fields):
    # note: we could support any expression but lets assume F() field names for now
    assert len(fields) >= 2, "pass at least two field names"
    fields = list(fields)
    last = fields.pop()
    args = [NullIf(F(f), Value("")) for f in fields] + [F(last)]
    return Coalesce(*args)
