from openforms.utils.tests.test_migrations import TestMigrations


class ConfirmationEmailTemplatesCosignTest(TestMigrations):
    app = "emails"
    migrate_from = "0009_auto_20230113_1641"
    migrate_to = "0010_add_cosign_templatetag"

    def setUpBeforeMigration(self, apps):
        ConfirmationEmailTemplate = apps.get_model(
            "emails", "ConfirmationEmailTemplate"
        )
        self.email1 = ConfirmationEmailTemplate.objects.create(
            content="""
            Dear Sir, Madam,<br>
            You have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>
            Your reference is: {{ public_reference }}<br>

            {% summary %}<br>
            {% appointment_information %}<br>
            {% payment_information %}<br><br>

            Kind regards,<br>
            <br>
            Open Forms<br>
            """,
            content_en="""
            Dear Sir, Madam,<br>
            You have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>
            Your reference is: {{ public_reference }}<br>

            {% summary %}<br>
            {% appointment_information %}<br>
            {% payment_information %}<br><br>

            Kind regards,<br>
            <br>
            Open Forms<br>
            """,
            content_nl="""
            Bla bla in het Nederlands<br>

            {% summary %}<br>
            {% appointment_information %}<br>
            {% payment_information %}<br><br>

            Met vriendelijke groet,<br>
            <br>
            Open Formulieren<br>
            """,
        )
        self.email2 = ConfirmationEmailTemplate.objects.create(
            content="""
                    Dear Sir, Madam,<br>
                    You have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>
                    Your reference is: {{ public_reference }}<br>

                    {% appointment_information %}<br>
                    {% payment_information %}<br><br>

                    Kind regards,<br>
                    <br>
                    Open Forms<br>
                    """
        )
        self.email3 = ConfirmationEmailTemplate.objects.create(
            content="""
                    Dear Sir, Madam,<br>
                    You have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>
                    Your reference is: {{ public_reference }}<br>

                    {% payment_information %}<br>
                    {% appointment_information %}<br>

                    Kind regards,<br>
                    <br>
                    Open Forms<br>
                    """
        )
        self.email4 = ConfirmationEmailTemplate.objects.create(
            content="""
                    Dear Sir, Madam,<br>
                    You have submitted the form "{{ form_name }}" on {{ submission_date }}.<br>
                    Your reference is: {{ public_reference }}<br>

                    {%payment_information%}<br>
                    {%appointment_information%}<br>

                    Kind regards,<br>
                    <br>
                    Open Forms<br>
                    """
        )

    def test_template_after_migration_contains_cosign_tag(self):
        self.email1.refresh_from_db()

        for field in ["content", "content_nl", "content_en"]:
            with self.subTest(f"Email 1 {field}"):
                self.assertIn("{% cosign_information %}", getattr(self.email1, field))
                self.assertIn("{% summary %}", getattr(self.email1, field))
                self.assertIn("{% payment_information %}", getattr(self.email1, field))
                self.assertIn(
                    "{% appointment_information %}", getattr(self.email1, field)
                )

        self.email2.refresh_from_db()

        self.assertIn("{% cosign_information %}", self.email2.content)
        self.assertIn("{% payment_information %}", self.email2.content)
        self.assertIn("{% appointment_information %}", self.email2.content)

        self.email3.refresh_from_db()

        self.assertIn("{% cosign_information %}", self.email3.content)
        self.assertIn("{% payment_information %}", self.email3.content)
        self.assertIn("{% appointment_information %}", self.email3.content)

        self.email4.refresh_from_db()

        self.assertIn("{% cosign_information %}", self.email4.content)
        self.assertIn("{%payment_information%}", self.email4.content)
        self.assertIn("{%appointment_information%}", self.email4.content)
