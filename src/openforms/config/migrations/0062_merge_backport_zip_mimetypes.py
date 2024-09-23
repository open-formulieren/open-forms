# Manually created since django can't figure it out with `makemigrations --merge`
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0059_alter_globalconfiguration_form_upload_default_file_types"),
        ("config", "0054_v250_to_v270"),
    ]

    operations = []
