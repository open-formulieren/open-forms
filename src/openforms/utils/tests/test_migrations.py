from django.core.management import call_command
from django.db import connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings, tag

unset = object()


@tag("migrations")
class TestMigrations(TransactionTestCase):
    """
    Test the effect of applying a migration

    Adapted from https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
    """

    app = None
    migrate_from = unset
    migrate_to = unset
    setting_overrides = None

    def _go_to_migration(self) -> None:
        overrides = self.setting_overrides or {}
        with override_settings(**overrides):
            executor = MigrationExecutor(connection)
            executor.loader.build_graph()  # reload.
            executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUp(self):
        _checks = (
            self.migrate_from is not unset,
            self.migrate_to is not unset,
            self.app,
        )
        assert all(_checks), (
            f"TestCase '{type(self).__name__}' must define migrate_from, migrate_to and app properties"
        )
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)

        # Reverse to the original migration
        old_migrate_state = executor.migrate(self.migrate_from)
        old_apps = old_migrate_state.apps

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        self._go_to_migration()

    def setUpBeforeMigration(self, apps):
        pass

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # reset to latest migration
        call_command("migrate", verbosity=0, database=connection._alias)


class TruncateCascadeMixin:
    def _fixture_teardown(self):
        """Overwrite the parent so that we can use TRUNCATE ... CASCADE

        Table "mozilla_django_oidc_db_openidconnectconfig_default_groups" references "auth_group".
        But truncating a table referenced in a foreign key constraint gives an error, so we use
        TRUNCATE ... CASCADE to truncate the table at teardown.
        """
        # Allow TRUNCATE ... CASCADE and don't emit the post_migrate signal
        # when flushing only a subset of the apps
        for db_name in self._databases_names(include_mirrors=False):
            # Flush the database
            inhibit_post_migrate = (
                self.available_apps is not None
                or (  # Inhibit the post_migrate signal when using serialized
                    # rollback to avoid trying to recreate the serialized data.
                    self.serialized_rollback
                    and hasattr(connections[db_name], "_test_serialized_contents")
                )
            )
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,  # OVERRIDE FROM PARENT!
                inhibit_post_migrate=inhibit_post_migrate,
            )
