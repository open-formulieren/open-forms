from zgw_consumers.constants import APITypes

from openforms.utils.tests.test_migrations import TestMigrations


class ServiceURLVersionSuffixTestsMixin:
    app = "qmatic"

    # parametrize tests
    api_root_before = ""
    api_root_after = ""

    def setUpBeforeMigration(self, apps):
        QmaticConfig = apps.get_model("qmatic", "QmaticConfig")
        Service = apps.get_model("zgw_consumers", "Service")
        service = Service.objects.create(
            api_root=self.api_root_before, label="Qmatic", api_type=APITypes.orc
        )
        QmaticConfig.objects.create(service=service)

    def test_migration_effect(self):
        QmaticConfig = self.apps.get_model("qmatic", "QmaticConfig")
        config = QmaticConfig.objects.get()

        self.assertEqual(config.service.api_root, self.api_root_after)


class RemoveV1ForwardTests(ServiceURLVersionSuffixTestsMixin, TestMigrations):
    migrate_from = "0002_qmaticconfig_required_customer_fields"
    migrate_to = "0003_strip_qmatic_service_v1"

    api_root_before = "https://example.com/qmatic/v1/"
    api_root_after = "https://example.com/qmatic/"


class NoopForwardTests(ServiceURLVersionSuffixTestsMixin, TestMigrations):
    migrate_from = "0002_qmaticconfig_required_customer_fields"
    migrate_to = "0003_strip_qmatic_service_v1"

    api_root_before = "https://example.com/qmatic/"
    api_root_after = "https://example.com/qmatic/"


class AddV1BackwardTests(ServiceURLVersionSuffixTestsMixin, TestMigrations):
    migrate_from = "0003_strip_qmatic_service_v1"
    migrate_to = "0002_qmaticconfig_required_customer_fields"

    api_root_before = "https://example.com/qmatic/"
    api_root_after = "https://example.com/qmatic/v1/"


class NoopBackwardTests(ServiceURLVersionSuffixTestsMixin, TestMigrations):
    migrate_from = "0003_strip_qmatic_service_v1"
    migrate_to = "0002_qmaticconfig_required_customer_fields"

    api_root_before = "https://example.com/qmatic/v1/"
    api_root_after = "https://example.com/qmatic/v1/"
