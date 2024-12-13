from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory

from ..factories import FormFactory
from .mixins import FormListAjaxMixin


@disable_admin_mfa()
class FormReachedSubmissionLimitListFilterTests(FormListAjaxMixin, WebTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = SuperUserFactory.create()

    def test_visible_forms_when_submission_limit_available(self):
        self.app.set_user(user=self.user)

        visible_form = FormFactory.create()
        visible_form2 = FormFactory.create(submission_limit=2, submission_counter=1)
        not_visible_form = FormFactory.create(submission_limit=2, submission_counter=2)
        not_visible_form2 = FormFactory.create(submission_limit=2, submission_counter=3)

        response = self._get_form_changelist(
            user=self.user, query={"submission_limit": "available"}
        )

        self.assertContains(response, visible_form.name)
        self.assertContains(response, visible_form2.name)
        self.assertNotContains(response, not_visible_form.name)
        self.assertNotContains(response, not_visible_form2.name)

    def test_visible_forms_when_submission_limit_unavailable(self):
        self.app.set_user(user=self.user)

        not_visible_form = FormFactory.create()
        not_visible_form2 = FormFactory.create(submission_limit=2, submission_counter=1)
        visible_form = FormFactory.create(submission_limit=2, submission_counter=2)
        visible_form2 = FormFactory.create(submission_limit=2, submission_counter=3)

        response = self._get_form_changelist(
            user=self.user, query={"submission_limit": "unavailable"}
        )

        self.assertContains(response, visible_form.name)
        self.assertContains(response, visible_form2.name)
        self.assertNotContains(response, not_visible_form.name)
        self.assertNotContains(response, not_visible_form2.name)
