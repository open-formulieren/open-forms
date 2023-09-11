from openforms.utils.tests.test_migrations import TestMigrations


class TestRefactorSoapServices(TestMigrations):
    migrate_from = "0001_initial_pre_openforms_v230"
    migrate_to = "0013_auto_20230718_1036"
    app = "stuf"

    def setUpBeforeMigration(self, apps):
        SoapService = apps.get_model("stuf", "SoapService")
        StufService = apps.get_model("stuf", "StufService")

        soap_service = SoapService.objects.create(
            label="Soap service",
            url="http://soap.nl",
        )

        StufService.objects.create(
            soap_service=soap_service,
            ontvanger_applicatie="Openforms",
            zender_applicatie="Openforms",
        )

    def test_data_is_not_lost(self):
        SoapService = self.apps.get_model("soap", "SoapService")
        StufService = self.apps.get_model("stuf", "StufService")

        soap_service = SoapService.objects.get(label="Soap service")
        stuf_service = StufService.objects.get(soap_service=soap_service)

        self.assertEqual(soap_service.url, "http://soap.nl")
        self.assertEqual(stuf_service.ontvanger_applicatie, "Openforms")
        self.assertEqual(stuf_service.zender_applicatie, "Openforms")
