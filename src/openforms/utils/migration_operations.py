import os

from django.conf import settings
from django.db import migrations, router


def _get_reset_sql() -> str:
    INFILE = os.path.join(settings.BASE_DIR, "bin", "reset_sequences.sql")

    with open(INFILE, "r") as infile:
        SQL = infile.read()

    return SQL


class ResetSequences(migrations.RunSQL):
    """
    Run the reset_sequences SQL.

    Resetting the Postgres sequences makes sure you don't get Integrity Errors
    when creating objects because of failing unique constraints. This happens
    when you create records explicitly with PKs, bypassing the database PK
    generation. Resetting the sequences makes sure the sequences are aware of
    the used PKs.

    .. note:: PostgreSQL only, or make sure to provide valid sql in
      bin/reset_sequences

    Usage:

        >>> from openforms.utils.migrations.operations import ResetSequences
        >>> class Migration(migrations.Migration):
        ...     dependencies = (...)
        ...     operations = [
        ...         ResetSequences(),
        ...     ]
    """

    reversible = True

    def __init__(self, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

    def database_forwards(self, app_label, schema_editor, from_state, to_state) -> None:
        if router.allow_migrate(
            schema_editor.connection.alias, app_label, **self.hints
        ):

            base_sql = _get_reset_sql()

            with schema_editor.connection.cursor() as cursor:
                cursor.execute(base_sql)
                rows = cursor.fetchall()

            sql = "\n".join(x[0] for x in rows)

            self._run_sql(schema_editor, sql)

    def database_backwards(self, *args, **kwargs) -> None:
        pass
