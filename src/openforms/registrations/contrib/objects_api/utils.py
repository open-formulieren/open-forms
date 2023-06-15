from .models import ObjectsAPIConfig


def get_registration_json_templates(submission) -> dict:
    config = ObjectsAPIConfig.get_solo()
    form_options = submission.form.registration_backend_options

    content_json = form_options.get("content_json") or config.content_json

    return content_json
