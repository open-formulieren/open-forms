# -*- coding: utf-8 -*-
from hijack.tests.test_hijack import BaseHijackTests

from hijack_admin import settings as hijack_admin_settings
from hijack_admin.tests.test_app.models import RelatedModel


class HijackAdminTests(BaseHijackTests):

    def setUp(self):
        super(HijackAdminTests, self).setUp()

    def tearDown(self):
        super(HijackAdminTests, self).tearDown()

    def test_hijack_button(self):
        response = self.client.get('/admin/auth/user/')
        self.assertTrue('<a href="/hijack/{}/" class="button">'.format(self.user.id) in str(response.content))

    def test_hijack_button_related(self):
        RelatedModel.objects.create(user=self.user)
        response = self.client.get('/admin/test_app/relatedmodel/')
        self.assertTrue('<a href="/hijack/{}/" class="button">'.format(self.user.id) in str(response.content))

    def test_settings(self):
        self.assertTrue(hasattr(hijack_admin_settings, 'HIJACK_BUTTON_TEMPLATE'))
        self.assertEqual(hijack_admin_settings.HIJACK_BUTTON_TEMPLATE, 'hijack_admin/admin_button.html')
        self.assertTrue(hasattr(hijack_admin_settings, 'HIJACK_REGISTER_ADMIN'))
        self.assertEqual(hijack_admin_settings.HIJACK_REGISTER_ADMIN, True)
