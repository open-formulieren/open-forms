from django.test import TestCase

from ..models import User


class UserManagerTests(TestCase):
    def test_create_superuser(self):
        user = User.objects.create_superuser("god", "god@heaven.com", "praisejebus")
        self.assertIsNotNone(user.pk)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.username, "god")
        self.assertEqual(user.email, "god@heaven.com")
        self.assertTrue(user.check_password("praisejebus"))
        self.assertNotEqual(user.password, "praisejebus")

    def test_create_user(self):
        user = User.objects.create_user("infidel")
        self.assertIsNotNone(user.pk)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.has_usable_password())
