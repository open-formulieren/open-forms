from openforms.core.tests.base import BaseFormTestCase


class FormTestCase(BaseFormTestCase):

    def test_login_required(self):
        self.assertTrue(self.form.login_required)
        self.form_def_2.login_required = False
        self.form_def_2.save()
        self.assertFalse(self.form.login_required)
