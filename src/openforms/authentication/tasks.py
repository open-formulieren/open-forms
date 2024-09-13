from io import StringIO

from django.core.management import call_command

from openforms.celery import app


@app.task(ignore_result=True)
def hash_identifying_attributes(auth_info_id: int):
    from .models import AuthInfo

    auth_info = AuthInfo.objects.get(id=auth_info_id)
    auth_info.hash_identifying_attributes()


@app.task(ignore_result=True)
def update_saml_metadata() -> None:
    """
    A weekly task for updating the SAML metadata concerning DigiD/Eherkenning

    Calling the command update_stored_metadata which is part of the
    `digid_eherkenning.management.commands` module of django-digid-eherkenning library.
    Updates the stored metadata file and prepopulates the db fields.
    """
    stdout = StringIO()
    call_command("update_stored_metadata", "digid", stdout=stdout)
    call_command("update_stored_metadata", "eherkenning", stdout=stdout)
