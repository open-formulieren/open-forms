# Generated by Django 3.2.21 on 2023-11-17 10:40

from django.db import migrations
from django.db.migrations.state import StateApps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from furl import furl


def cleanup_submission_urls(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:

    Submission = apps.get_model("submissions", "Submission")

    for submission in Submission.objects.iterator():
        f = furl(submission.form_url)
        f.remove(fragment=True)
        if f.path.segments[-1:] == ["startpagina"]:
            f.path.segments.remove("startpagina")
        submission.form_url = f.url

        submission.save()


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0002_change_json_encoder"),
    ]

    operations = [
        migrations.RunPython(cleanup_submission_urls, migrations.RunPython.noop)
    ]
