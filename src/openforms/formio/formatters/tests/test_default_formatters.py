from django.test import TestCase

from ..registry import register


class DefaultFormatterTestCase(TestCase):
    def test_formatters(self):
        data = {
            "textField": (
                {
                    "key": "textField",
                    "type": "textfield",
                    "label": "Text Field",
                },
                "Some Text",
            ),
            "emailField": (
                {
                    "key": "emailField",
                    "type": "email",
                    "label": "Email Field",
                },
                "foo@bar.com",
            ),
            "dateField": (
                {
                    "key": "dateField",
                    "type": "date",
                    "label": "Date Field",
                },
                "2022-01-02",
            ),
            "timeField": (
                {
                    "key": "timeField",
                    "type": "time",
                    "label": "Time Field",
                },
                "17:30:00",
            ),
            "phoneNumberField": (
                {
                    "key": "phoneNumberField",
                    "type": "phoneNumber",
                    "label": "Phone Number Field",
                },
                "0612345678",
            ),
            "fileField": (
                {
                    "key": "fileField",
                    "type": "file",
                    "label": "File Field",
                },
                [
                    {
                        "url": "http://server/api/v1/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                        "data": {
                            "url": "http://server/api/v1/submissions/files/62f2ec22-da7d-4385-b719-b8637c1cd483",
                            "form": "",
                            "name": "my-image.jpg",
                            "size": 46114,
                            "baseUrl": "http://server/form",
                            "project": "",
                        },
                        "name": "my-image-12305610-2da4-4694-a341-ccb919c3d543.jpg",
                        "size": 46114,
                        "type": "image/jpg",
                        "storage": "url",
                        "originalName": "my-image.jpg",
                    }
                ],
            ),
            "textArea": (
                {
                    "key": "textArea",
                    "type": "textarea",
                    "label": "Text Area",
                },
                "Some Text area",
            ),
            "numberField": (
                {
                    "key": "numberField",
                    "type": "number",
                    "label": "Number Field",
                },
                "42",
            ),
            "passwordField": (
                {
                    "key": "passwordField",
                    "type": "password",
                    "label": "Password",
                },
                "some_pwd",
            ),
            "checkBox": (
                {
                    "key": "checkBox",
                    "type": "checkbox",
                    "label": "Checkbox",
                },
                True,
            ),
            "selectBoxes": (
                {
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "label": "Selectboxes",
                    "values": [
                        {"label": "Option 1", "value": "option1"},
                        {"label": "Option 2", "value": "option2"},
                        {"label": "Option 3", "value": "option3"},
                    ],
                },
                {"option1": True, "option2": False, "option3": True},
            ),
            "selectField": (
                {
                    "key": "selectField",
                    "type": "select",
                    "label": "Select Field",
                    "data": {
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ]
                    },
                },
                "option2",
            ),
            "currencyField": (
                {
                    "key": "currencyField",
                    "type": "currency",
                    "label": "Currency Field",
                },
                "$50",
            ),
            "radioButtons": (
                {
                    "key": "radioButtons",
                    "type": "radio",
                    "label": "Radio buttons",
                    "values": [
                        {"label": "Option 1", "value": "option1"},
                        {"label": "Option 2", "value": "option2"},
                    ],
                },
                "option1",
            ),
        }

        expected = {
            "textField": "Some Text",
            "emailField": "foo@bar.com",
            "dateField": "2 januari 2022",
            "timeField": "17:30",
            "phoneNumberField": "0612345678",
            "fileField": "my-image.jpg",
            "textArea": "Some Text area",
            "numberField": "42",
            "passwordField": "\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF",
            "checkBox": "ja",
            "selectBoxes": "Option 1, Option 3",
            "selectField": "Option 2",
            "currencyField": "$50",
            "radioButtons": "Option 1",
        }
        for field_name, (component, value) in data.items():
            with self.subTest(type=component["type"]):
                formatter = register[component["type"]]
                self.assertEqual(formatter(component, value), expected[field_name])
