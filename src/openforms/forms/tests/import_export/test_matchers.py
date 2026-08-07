from django.test import TestCase

from openforms.forms.import_export.matchers.form_definition import FormDefinitionMatcher
from openforms.forms.tests.factories import FormDefinitionFactory


class FormDefinitionMatcherTests(TestCase):
    def test_find_similar_form_definition(self):
        fd = FormDefinitionFactory.create(
            uuid="0a1c2ac4-b5fb-429b-899d-2f4813d53bfa",
            configuration={
                "components": [
                    {
                        "id": "e0bdve",
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ]
            },
            is_reusable=True,
        )

        # Search for a form definition with a similar component, but different id
        matcher = FormDefinitionMatcher()
        found_instance = matcher.find(
            {
                "components": [
                    {
                        "id": "123abc",
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ]
            }
        )

        self.assertIsNotNone(found_instance)
        self.assertEqual(fd.pk, found_instance.pk)

    def test_find_similar_form_definition_with_nested_components(self):
        fd = FormDefinitionFactory.create(
            uuid="0a1c2ac4-b5fb-429b-899d-2f4813d53bfa",
            configuration={
                "components": [
                    {
                        "id": "c2sac1",
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Editgrid",
                        "groupLabel": "item",
                        "components": [
                            {
                                "id": "e0bdve",
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Textfield",
                            }
                        ],
                    },
                ]
            },
            is_reusable=True,
        )

        # Search for a form definition with similar components, but different id's
        matcher = FormDefinitionMatcher()
        found_instance = matcher.find(
            {
                "components": [
                    {
                        "id": "456def",
                        "type": "editgrid",
                        "key": "editgrid",
                        "label": "Editgrid",
                        "groupLabel": "item",
                        "components": [
                            {
                                "id": "123abc",
                                "key": "textfield",
                                "type": "textfield",
                                "label": "Textfield",
                            }
                        ],
                    },
                ]
            }
        )

        self.assertIsNotNone(found_instance)
        self.assertEqual(fd.pk, found_instance.pk)

    def test_return_none_when_no_similar_form_definition_is_found(self):
        FormDefinitionFactory.create(
            uuid="0a1c2ac4-b5fb-429b-899d-2f4813d53bfa",
            configuration={
                "components": [
                    {
                        "id": "e0bdve",
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    }
                ]
            },
            is_reusable=True,
        )

        matcher = FormDefinitionMatcher()
        found_instance = matcher.find(
            {
                "components": [
                    {
                        "id": "123abc",
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield met een andere titel",
                    },
                ]
            }
        )

        self.assertIsNone(found_instance)

    def test_return_none_when_similar_form_definition_is_not_reusable(self):
        FormDefinitionFactory.create(
            uuid="0a1c2ac4-b5fb-429b-899d-2f4813d53bfa",
            configuration={
                "components": [
                    {
                        "id": "e0bdve",
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    }
                ]
            },
            is_reusable=False,
        )

        matcher = FormDefinitionMatcher()
        found_instance = matcher.find(
            {
                "components": [
                    {
                        "id": "123abc",
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ]
            }
        )

        self.assertIsNone(found_instance)
