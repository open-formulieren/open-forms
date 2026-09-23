import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils import timezone

import time_machine
from furl import furl
from privates.test import temp_private_root
from structlog.testing import capture_logs

from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.authentication.contrib.digid.tests.test_auth_procedure import (
    DigiDConfigMixin,
)
from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import ThemeFactory
from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.formio.service import FormioData
from openforms.formio.typing.custom import SupportedChannels
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.frontend.tests import FrontendRedirectMixin
from openforms.prefill.contrib.customer_interactions.constants import PLUGIN_IDENTIFIER
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ..constants import SUBMISSIONS_SESSION_KEY
from ..exceptions import FormMaximumSubmissions
from ..tokens import submission_resume_token_generator
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


class SubmissionResumeViewTests(FrontendRedirectMixin, TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
        submission = SubmissionFactory.from_components(
            form__formstep__form_definition__login_required=False,
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            form_url="http://maykinmedia.nl/myform",
            submitted_data={"email": "test@test.nl"},
        )
        # add a second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            data={"foo": "bar"},
        )
        submission.load_execution_state(refresh=True)

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url=submission.form_url,
            action="resume",
            action_params={
                "step_slug": submission.get_last_completed_step().form_step.slug,
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

        # Assert submission is stored in session
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_403_response_with_unfound_submission(self):
        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": "irrelevant",
                "submission_uuid": uuid.uuid4(),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_403_response_with_bad_token(self):
        submission = SubmissionFactory.create()

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": "bad",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_invalid_after_submission_incomplete_invalid_time(self):
        config = GlobalConfiguration.get_solo()
        config.sdk_url = "http://maykinmedia-sdk.nl/"
        config.save()

        submission = SubmissionFactory.create()

        with time_machine.travel(
            submission.created_on
            - timedelta(
                days=(
                    submission_resume_token_generator.get_token_timeout_days(submission)
                    + 1
                )
            ),
            tick=False,
        ):
            token = submission_resume_token_generator.make_token(submission)

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_valid_on_same_day(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
        )
        # add a second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)

    def test_redirects_to_auth_if_form_requires_login(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="digid",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        expected_redirect_url = furl(
            f"http://testserver/auth/{submission.form.slug}/digid/start"
        )
        expected_redirect_url.args["next"] = f"http://testserver{endpoint}"

        response = self.client.get(endpoint)

        self.assertRedirects(
            response, expected_redirect_url.url, fetch_redirect_response=False
        )
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_after_successful_auth_redirects_to_form(self):
        submission = SubmissionFactory.from_components(
            components_list=[{"key": "foo", "type": "textfield"}],
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            auth_info__plugin="digid",
            form_url="http://testserver/myform/",
            auth_info__value="123456782",
        )
        form_step = submission.form.formstep_set.first()
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url=submission.form_url,
            action="resume",
            action_params={
                "step_slug": form_step.slug,
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

        self.assertIn(SUBMISSIONS_SESSION_KEY, self.client.session)
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    @tag("gh-2301")
    def test_identifying_attribute_not_hashed_after_resume(self):
        # create
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://testserver/myform/",
            auth_info__plugin="digid",
            auth_info__value="123456782",
            suspended=True,
        )
        form_step = submission.form.formstep_set.first()
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"foo": "bar"},
        )
        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()
        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        # resumed
        self.assertEqual(response.status_code, 302)
        self.assertIn(SUBMISSIONS_SESSION_KEY, self.client.session)
        submission.refresh_from_db()
        self.assertEqual(submission.auth_info.value, "123456782")

    def test_invalid_auth_plugin_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="wrong-plugin",
            form_url="http://testserver/myform/",
            auth_info__value="123456782",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_invalid_auth_attribute_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="digid",
            form_url="http://testserver/myform/",
            auth_info__attribute=AuthAttribute.kvk,
            auth_info__value="123456782",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_invalid_auth_value_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="digid",
            form_url="http://testserver/myform/",
            auth_info__value="wrong-bsn",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_resume_creates_valid_url(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[],
            form_url="http://maykinmedia.nl/some-form/startpagina",
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url="http://maykinmedia.nl/some-form",
            action="resume",
            action_params={
                "step_slug": submission.get_last_completed_step().form_step.slug,
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

    @tag("gh-3613")
    def test_redirects_to_auth_if_form_does_not_require_login_but_user_logged_in_the_first_time(
        self,
    ):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=False,
            auth_info__plugin="digid",
            auth_info__value="some-hashed-value",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        expected_redirect_url = furl(
            f"http://testserver/auth/{submission.form.slug}/digid/start"
        )
        expected_redirect_url.args["next"] = f"http://testserver{endpoint}"

        response = self.client.get(endpoint)

        self.assertRedirects(
            response, expected_redirect_url.url, fetch_redirect_response=False
        )
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_resume_with_form_max_submissions_limit_reached(self):
        theme = ThemeFactory.create(
            design_token_values={"of": {"page-footer": {"bg": {"value": "#facade"}}}}
        )
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[],
            form_url="http://maykinmedia.nl/some-form/startpagina",
            form__theme=theme,
            form__submission_limit=1,
            form__submission_counter=1,
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context_data["error"], FormMaximumSubmissions)
        self.assertIn("#facade", response.content.decode())

    def test_resume_with_form_max_submissions_limit_not_reached(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[],
            form_url="http://maykinmedia.nl/some-form/startpagina",
            form__submission_limit=2,
            form__submission_counter=1,
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)

    def test_prefill_rerun_when_plugin_not_supported(self):
        submission = SubmissionFactory.from_components(
            suspended_on=timezone.now(),
            completed=False,
            components_list=[
                {
                    "key": "hc_prefill_partners_mutable",
                    "type": "partners",
                    "label": "Partners",
                },
            ],
        )
        FormVariableFactory.create(
            key="hc_prefill_partners_immutable",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "hc_prefill_partners_mutable",
                "min_age": None,
                "max_age": None,
            },
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "999970124",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        submission.refresh_from_db()

        resume_endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with (
            patch(
                "openforms.prefill.contrib.family_members.plugin.FamilyMembersPrefill.get_prefill_values_from_options"
            ) as mocked_get_prefill_values_from_options,
            capture_logs() as logs,
        ):
            self.client.get(resume_endpoint)

            mocked_get_prefill_values_from_options.assert_not_called()

            self.assertTrue(
                any(log["event"] == "plugin_not_supported_in_resume" for log in logs)
            )


@temp_private_root(reset_storage=False)
@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class SubmissionResumeViewVCRTests(
    OFVCRMixin,
    FrontendRedirectMixin,
    SubmissionsMixin,
    DigiDConfigMixin,
    TestCase,
):
    def test_prefill_rerun_complete_flow_when_plugin_supported(self):
        config = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        profile_channels: list[SupportedChannels] = ["email", "phoneNumber"]

        form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            formstep__form_definition__login_required=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "profile",
                        "type": "customerProfile",
                        "label": "Profile",
                        "digitalAddressTypes": profile_channels,
                        "shouldUpdateCustomerData": False,
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="communication-preferences",
            form=form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "customer_interactions_api_group": config.identifier,
                "profile_form_variable": "profile",
            },
        )

        # 1. start submission with prefill configured
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        body = {
            "form": f"http://testserver.com{
                reverse('api:form-detail', kwargs={'uuid_or_slug': form.uuid})
            }",
            "formUrl": "http://testserver.com/my-form",
        }

        # we mock the data from the prefill plugin in order to test that they are going
        # to be correctly updated (after a re-run of the prefill plugin)
        mocked_prefill_data = {
            "communication-preferences": [
                {
                    "type": "email",
                    "options": ["john.smith@gmail.com"],
                    "preferred": "john.smith@gmail.com",
                },
                {
                    "type": "phoneNumber",
                    "options": [
                        "0612345678",
                    ],
                    "preferred": "0612345678",
                },
            ]
        }

        create_submission_response = self.client.post(
            reverse("api:submission-list"), body, HTTP_HOST="testserver.com"
        )

        self.assertEqual(create_submission_response.status_code, 201)

        submission = form.submission_set.get()

        self.assertEqual(submission.auth_info.value, "123456782")

        # override the prefill data with the mocked
        submission.variables_state.save_prefill_data(FormioData(mocked_prefill_data))

        variables_initial_state_data = submission.variables_state.get_data()

        self.assertEqual(
            variables_initial_state_data["communication-preferences"],
            [
                {
                    "type": "email",
                    "options": ["john.smith@gmail.com"],
                    "preferred": "john.smith@gmail.com",
                },
                {
                    "type": "phoneNumber",
                    "options": ["0612345678"],
                    "preferred": "0612345678",
                },
            ],
        )

        # 2. suspend submission
        suspend_endpoint = reverse(
            "api:submission-suspend", kwargs={"uuid": submission.uuid}
        )
        self.client.post(suspend_endpoint, {"email": "test@example.com"})

        submission.refresh_from_db()

        self.assertNotEqual(submission.auth_info.value, "123456782")

        # 3. resume submission

        # update the session again since the user at this point should be authenticated
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        submission.refresh_from_db()

        resume_endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        self.assertNotEqual(submission.auth_info.value, "123456782")

        response = self.client.get(resume_endpoint)

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url="http://testserver.com/my-form",
            action="resume",
            action_params={
                "step_slug": form.formstep_set.get().slug,
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

        submission.refresh_from_db()
        variables_updated_state_data = submission.variables_state.get_data()

        self.assertEqual(submission.auth_info.value, "123456782")
        self.assertEqual(
            variables_updated_state_data["communication-preferences"],
            [
                {
                    "type": "email",
                    "options": [
                        {"address": "john.smith@gmail.com", "verification_date": None},
                        {
                            "address": "john.smith@gmail.com",
                            "verification_date": "2026-09-09",
                        },
                        {"address": "someemail@example.org", "verification_date": None},
                        {
                            "address": "devilkiller@example.org",
                            "verification_date": None,
                        },
                        {"address": "john.smith@gmail.com", "verification_date": None},
                    ],
                    "preferred": "john.smith@gmail.com",
                },
                {
                    "type": "phoneNumber",
                    "options": [
                        {"address": "0612345678", "verification_date": None},
                        {"address": "0687654321", "verification_date": None},
                        {"address": "0612345678", "verification_date": None},
                    ],
                    "preferred": "0612345678",
                },
            ],
        )
