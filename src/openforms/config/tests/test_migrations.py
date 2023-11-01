from django.test import SimpleTestCase
from django.utils.module_loading import import_string

from openforms.utils.tests.test_migrations import TestMigrations

apply_mapping = import_string(
    "openforms.config.migrations.0059_convert_button_design_tokens.apply_mapping"
)


class MapperTests(SimpleTestCase):
    def test_empty_tokens(self):
        updated = apply_mapping({})

        self.assertEqual(updated, {})

    def test_unrelated_tokens(self):
        source = {"utrecht": {"form-field": {"font-size": {"value": "18px"}}}}

        updated = apply_mapping(source)

        self.assertIsNot(updated, source)
        self.assertEqual(updated, source)

    def test_map_old_token_to_new(self):
        source = {"of": {"button": {"bg": {"value": "blue"}}}}

        updated = apply_mapping(source)

        self.assertEqual(
            updated, {"utrecht": {"button": {"background-color": {"value": "blue"}}}}
        )

    def test_map_and_merge_old_token_to_new(self):
        source = {
            "of": {"button": {"bg": {"value": "blue"}}},
            "utrecht": {"button": {"color": {"value": "pink"}}},
        }

        updated = apply_mapping(source)

        self.assertEqual(
            updated,
            {
                "utrecht": {
                    "button": {
                        "background-color": {"value": "blue"},
                        "color": {"value": "pink"},
                    }
                }
            },
        )

    def test_do_not_overwrite_existing_token(self):
        source = {
            "of": {"button": {"bg": {"value": "red"}}},
            "utrecht": {"button": {"background-color": {"value": "blue"}}},
        }

        updated = apply_mapping(source)

        self.assertEqual(
            updated, {"utrecht": {"button": {"background-color": {"value": "blue"}}}}
        )


class ButtonDesignTokensMigrationTests(TestMigrations):

    app = "config"
    migrate_from = "0058_auto_20231026_1525"
    migrate_to = "0059_convert_button_design_tokens"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        # (Partial) tokens configuration taken from a test instance
        GlobalConfiguration.objects.create(
            design_token_values={
                "of": {
                    "text": {"font-size": {"value": "1rem"}},
                    "color": {
                        "bg": {"value": "#fff"},
                        "fg": {"value": "#000000"},
                        "info": {"value": "#007bc7"},
                        "border": {"value": "#b3b3b3"},
                        "danger": {"value": "#d52b1e"},
                        "primary": {"value": "#07838f"},
                        "success": {"value": "green"},
                        "warning": {"value": "#e17000"},
                    },
                    "button": {
                        "bg": {"value": "#07838f"},
                        "fg": {"value": "#FFFFFF"},
                        "hover": {"bg": {"value": "rgba(0,116,126,255)"}},
                        "primary": {
                            "active": {
                                "bg": {
                                    "value": "green",
                                }
                            }
                        },
                    },
                },
                "utrecht": {
                    "button": {
                        "primary-action": {
                            "active": {
                                "background-color": {"value": "#9d2f66"},
                            },
                        }
                    },
                },
            }
        )

    def test_design_tokens_updated_correctly(self):
        self.maxDiff = None

        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        expected = {
            "of": {
                "text": {"font-size": {"value": "1rem"}},
                "color": {
                    "bg": {"value": "#fff"},
                    "fg": {"value": "#000000"},
                    "info": {"value": "#007bc7"},
                    "border": {"value": "#b3b3b3"},
                    "danger": {"value": "#d52b1e"},
                    "primary": {"value": "#07838f"},
                    "success": {"value": "green"},
                    "warning": {"value": "#e17000"},
                },
            },
            "utrecht": {
                "button": {
                    "background-color": {"value": "#07838f"},
                    "color": {"value": "#FFFFFF"},
                    "hover": {"background-color": {"value": "rgba(0,116,126,255)"}},
                    "primary-action": {
                        "active": {
                            "background-color": {"value": "#9d2f66"},
                        },
                    },
                    "secondary-action": {
                        "background-color": {"value": "#fff"},
                        "border-color": {"value": "#b3b3b3"},
                        "color": {"value": "#000000"},
                        "hover": {"background-color": {"value": "rgba(0,116,126,255)"}},
                    },
                    "subtle": {
                        "danger": {
                            "color": {"value": "#d52b1e"},
                            "active": {
                                "background-color": {"value": "#d52b1e"},
                                "color": {"value": "#fff"},
                            },
                        },
                    },
                },
            },
        }
        self.assertEqual(config.design_token_values, expected)
