from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("soap", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SuwinetConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "bijstandsregelingen_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/Bijstandsregelingen/v0500}BijstandsregelingenBinding",
                        verbose_name="Bijstandsregelingen Binding Address",
                    ),
                ),
                (
                    "brpdossierpersoongsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/BRPDossierPersoonGSD/v0200}BRPBinding",
                        verbose_name="BRPDossierPersoonGSD Binding Address",
                    ),
                ),
                (
                    "duodossierpersoongsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/DUODossierPersoonGSD/v0300}DUOBinding",
                        verbose_name="DUODossierPersoonGSD Binding Address",
                    ),
                ),
                (
                    "duodossierstudiefinancieringgsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/DUODossierStudiefinancieringGSD/v0200}DUOBinding",
                        verbose_name="DUODossierStudiefinancieringGSD Binding Address",
                    ),
                ),
                (
                    "gsddossierreintegratie_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/GSDDossierReintegratie/v0200}GSDReintegratieBinding",
                        verbose_name="GSDDossierReintegratie Binding Address",
                    ),
                ),
                (
                    "ibverwijsindex_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/IBVerwijsindex/v0300}IBVerwijsindexBinding",
                        verbose_name="IBVerwijsindex Binding Address",
                    ),
                ),
                (
                    "kadasterdossiergsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/KadasterDossierGSD/v0300}KadasterBinding",
                        verbose_name="KadasterDossierGSD Binding Address",
                    ),
                ),
                (
                    "rdwdossierdigitalediensten_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/RDWDossierDigitaleDiensten/v0200}RDWBinding",
                        verbose_name="RDWDossierDigitaleDiensten Binding Address",
                    ),
                ),
                (
                    "rdwdossiergsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/RDWDossierGSD/v0200}RDWBinding",
                        verbose_name="RDWDossierGSD Binding Address",
                    ),
                ),
                (
                    "svbdossierpersoongsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/SVBDossierPersoonGSD/v0200}SVBBinding",
                        verbose_name="SVBDossierPersoonGSD Binding Address",
                    ),
                ),
                (
                    "uwvdossieraanvraaguitkeringstatusgsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierAanvraagUitkeringStatusGSD/v0200}UWVAanvraagUitkeringStatusBinding",
                        verbose_name="UWVDossierAanvraagUitkeringStatusGSD Binding Address",
                    ),
                ),
                (
                    "uwvdossierinkomstengsddigitalediensten_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierInkomstenGSDDigitaleDiensten/v0200}UWVIkvBinding",
                        verbose_name="UWVDossierInkomstenGSDDigitaleDiensten Binding Address",
                    ),
                ),
                (
                    "uwvdossierinkomstengsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierInkomstenGSD/v0200}UWVIkvBinding",
                        verbose_name="UWVDossierInkomstenGSD Binding Address",
                    ),
                ),
                (
                    "uwvdossierquotumarbeidsbeperktengsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierQuotumArbeidsbeperktenGSD/v0300}UWVArbeidsbeperktenBinding",
                        verbose_name="UWVDossierQuotumArbeidsbeperktenGSD Binding Address",
                    ),
                ),
                (
                    "uwvdossierwerknemersverzekeringengsddigitalediensten_binding_address",
                    models.URLField(
                        blank=True,
                        db_column="ba_baracus",
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierWerknemersverzekeringenGSDDigitaleDiensten/v0200}UWVBinding",
                        verbose_name="UWVDossierWerknemersverzekeringenGSDDigitaleDiensten Binding Address",
                    ),
                ),
                (
                    "uwvdossierwerknemersverzekeringengsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVDossierWerknemersverzekeringenGSD/v0200}UWVBinding",
                        verbose_name="UWVDossierWerknemersverzekeringenGSD Binding Address",
                    ),
                ),
                (
                    "uwvwbdossierpersoongsd_binding_address",
                    models.URLField(
                        blank=True,
                        help_text="Binding address for {http://bkwi.nl/SuwiML/Diensten/UWVWbDossierPersoonGSD/v0200}UwvWbBinding",
                        verbose_name="UWVWbDossierPersoonGSD Binding Address",
                    ),
                ),
                (
                    "service",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="soap.soapservice",
                    ),
                ),
            ],
            options={
                "verbose_name": "Suwinet configuration",
            },
        ),
    ]
