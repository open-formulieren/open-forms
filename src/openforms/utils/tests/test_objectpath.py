from django.test import TestCase

from openforms.utils.objectpath import PathResolveError, resolve_object_path


class ObjectPathTest(TestCase):
    def test_resolve(self):
        obj = {"foo": 1, "bar": {"a": {"b": {"c": 3}}}}

        self.assertEqual(resolve_object_path(obj, "foo"), 1)
        self.assertEqual(resolve_object_path(obj, "bar__a__b__c"), 3)

        with self.assertRaises(PathResolveError):
            resolve_object_path(obj, "bazz")

        with self.assertRaises(PathResolveError):
            resolve_object_path(obj, "nest__a__bazz")

        with self.assertRaises(PathResolveError):
            resolve_object_path(obj, "")

        with self.assertRaises(PathResolveError):
            resolve_object_path(obj, "__")

        with self.assertRaises(PathResolveError):
            resolve_object_path(obj, "foo__")

        with self.assertRaises(PathResolveError):
            resolve_object_path(obj, "__foo")

    def test_resolve_prefixed_fragments(self):
        obj = {"_embed": {"foo": {"_embed": {"bar": 1}}}}

        self.assertEqual(resolve_object_path(obj, "_embed__foo___embed__bar"), 1)
