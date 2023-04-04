from urllib.parse import parse_qs

from zgw_consumers.constants import APITypes, AuthTypes

from openforms.utils.tests.test_migrations import TestMigrations


class ServiceFetchConfigurationQueryParamsForwardMigrationTests(TestMigrations):
    migrate_from = "0003_servicefetchconfiguration__query_params"
    migrate_to = "0004_migrate_query_params"
    app = "variables"

    def setUpBeforeMigration(self, apps):
        ServiceFetchConfiguration = apps.get_model(
            "variables", "ServiceFetchConfiguration"
        )
        Service = apps.get_model("zgw_consumers", "Service")

        service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )

        self.config1 = ServiceFetchConfiguration.objects.create(
            name="GET foo",
            query_params="?foo=bar&bar={{baz}}",
            service=service,
        )
        self.config2 = ServiceFetchConfiguration.objects.create(
            name="GET bar",
            query_params="foo=bar&bar={{baz}}",
            service=service,
        )

    def test_convert_query_params_to_jsonfield(self):
        self.config1.refresh_from_db()
        self.config2.refresh_from_db()

        expected = {
            "foo": ["bar"],
            "bar": ["{{baz}}"],
        }

        self.assertEqual(self.config1._query_params, expected)
        self.assertEqual(self.config2._query_params, expected)


class ServiceFetchConfigurationQueryParamsBackwardMigrationTests(TestMigrations):
    migrate_from = "0004_migrate_query_params"
    migrate_to = "0003_servicefetchconfiguration__query_params"
    app = "variables"

    def setUpBeforeMigration(self, apps):
        ServiceFetchConfiguration = apps.get_model(
            "variables", "ServiceFetchConfiguration"
        )
        Service = apps.get_model("zgw_consumers", "Service")

        service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )

        self.config = ServiceFetchConfiguration.objects.create(
            name="GET foo",
            query_params="",
            _query_params={"foo": ["bar"], "bar": ["{{baz}}"]},
            service=service,
        )

    def test_convert_query_params_to_jsonfield(self):
        self.config.refresh_from_db()

        expected = "?bar=%7B%7Bbaz%7D%7D&foo=bar"

        self.assertEqual(self.config.query_params, expected)
        self.assertEqual(
            parse_qs(self.config.query_params[1:]), {"foo": ["bar"], "bar": ["{{baz}}"]}
        )


class ServiceFetchConfigurationInterpolationFormatForwardMigrationTests(TestMigrations):
    migrate_from = "0010_alter_servicefetchconfiguration_name"
    migrate_to = "0011_migrate_interpolation_format"
    app = "variables"

    def setUpBeforeMigration(self, apps):
        ServiceFetchConfiguration = apps.get_model(
            "variables", "ServiceFetchConfiguration"
        )
        Service = apps.get_model("zgw_consumers", "Service")

        service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )

        self.config = ServiceFetchConfiguration.objects.create(
            name="GET foo",
            query_params={"foo": ["bar"], "bar": ["{baz}", "bar"]},
            headers={"foo": "foo {bar.baz}"},
            body={"foo": ["{bar}"], "bar": {"baz": "{bar}"}},
            service=service,
        )

    def test_migrate_interpolation_syntax(self):
        self.config.refresh_from_db()

        self.assertEqual(
            self.config.query_params, {"foo": ["bar"], "bar": ["{{baz}}", "bar"]}
        )
        self.assertEqual(self.config.headers, {"foo": "foo {{bar.baz}}"})
        self.assertEqual(
            self.config.body, {"foo": ["{{bar}}"], "bar": {"baz": "{{bar}}"}}
        )
