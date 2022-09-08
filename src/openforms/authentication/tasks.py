from openforms.celery import app


@app.task(ignore_result=True)
def hash_identifying_attributes(auth_info_id: int):
    from .models import AuthInfo

    auth_info = AuthInfo.objects.get(id=auth_info_id)
    auth_info.hash_identifying_attributes()
