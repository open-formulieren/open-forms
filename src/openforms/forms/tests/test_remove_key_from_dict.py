from django.test import TestCase

from openforms.forms.utils import remove_key_from_dict


class RemoveKeyFromDictTests(TestCase):
    def test_remove_key_from_dict_removes_expected_key(self):
        dictionary = {
            "remove_me": False,
            "dont_remove_me": True,
            "inner_dict": {"remove_me": False, "dont_remove_me": True},
            "a_list": [
                {
                    "remove_me": False,
                    "dont_remove_me": True,
                    "inner_dict": {"remove_me": False, "dont_remove_me": True},
                }
            ],
        }

        remove_key_from_dict(dictionary, "remove_me")

        expected_result = {
            "dont_remove_me": True,
            "inner_dict": {"dont_remove_me": True},
            "a_list": [
                {"dont_remove_me": True, "inner_dict": {"dont_remove_me": True}}
            ],
        }
        self.assertEqual(dictionary, expected_result)
