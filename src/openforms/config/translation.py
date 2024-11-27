from modeltranslation.translator import TranslationOptions, register

from .models import GlobalConfiguration


@register(GlobalConfiguration)
class GlobalConfigurationTranslationOptions(TranslationOptions):
    fields = (
        "submission_confirmation_title",
        "submission_confirmation_template",
        "cosign_submission_confirmation_title",
        "cosign_submission_confirmation_template",
        "submission_report_download_link_title",
        "confirmation_email_subject",
        "confirmation_email_content",
        "cosign_request_template",
        "cosign_confirmation_email_subject",
        "cosign_confirmation_email_content",
        "email_verification_request_subject",
        "email_verification_request_content",
        "save_form_email_subject",
        "save_form_email_content",
        "form_previous_text",
        "form_change_text",
        "form_confirm_text",
        "form_begin_text",
        "form_step_previous_text",
        "form_step_save_text",
        "form_step_next_text",
        "privacy_policy_label",
        "statement_of_truth_label",
    )
    fallback_undefined = {
        "submission_confirmation_title": "",
        "submission_confirmation_template": "",
        "cosign_submission_confirmation_title": "",
        "cosign_submission_confirmation_template": "",
        "submission_report_download_link_title": "",
        "confirmation_email_subject": "",
        "confirmation_email_content": "",
        "cosign_request_template": "",
        "cosign_confirmation_email_subject": "",
        "cosign_confirmation_email_content": "",
        "email_verification_request_subject": "",
        "email_verification_request_content": "",
        "save_form_email_subject": "",
        "save_form_email_content": "",
        "form_previous_text": "",
        "form_change_text": "",
        "form_confirm_text": "",
        "form_begin_text": "",
        "form_step_previous_text": "",
        "form_step_save_text": "",
        "form_step_next_text": "",
        "privacy_policy_label": "",
        "statement_of_truth_label": "",
    }
