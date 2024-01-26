from django.test import SimpleTestCase

from openforms.utils.tests.test_migrations import TestMigrations

from ..migrations._design_tokens import apply_button_mapping, apply_layout_mapping


class ButtonMapperTests(SimpleTestCase):
    def test_empty_tokens(self):
        updated = apply_button_mapping({})

        self.assertEqual(updated, {})

    def test_unrelated_tokens(self):
        source = {"utrecht": {"form-field": {"font-size": {"value": "18px"}}}}

        updated = apply_button_mapping(source)

        self.assertIsNot(updated, source)
        self.assertEqual(updated, source)

    def test_map_old_token_to_new(self):
        source = {"of": {"button": {"bg": {"value": "blue"}}}}

        updated = apply_button_mapping(source)

        self.assertEqual(
            updated, {"utrecht": {"button": {"background-color": {"value": "blue"}}}}
        )

    def test_map_and_merge_old_token_to_new(self):
        source = {
            "of": {"button": {"bg": {"value": "blue"}}},
            "utrecht": {"button": {"color": {"value": "pink"}}},
        }

        updated = apply_button_mapping(source)

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

        updated = apply_button_mapping(source)

        self.assertEqual(
            updated, {"utrecht": {"button": {"background-color": {"value": "blue"}}}}
        )


class LayoutMapperTests(SimpleTestCase):
    def test_empty_tokens(self):
        updated = apply_layout_mapping({})

        self.assertEqual(updated, {})

    def test_unrelated_tokens(self):
        source = {"utrecht": {"form-field": {"font-size": {"value": "18px"}}}}

        updated = apply_layout_mapping(source)

        self.assertIsNot(updated, source)
        self.assertEqual(updated, source)

    def test_map_old_token_to_new(self):
        source = {"of": {"page-footer": {"bg": {"value": "blue"}}}}

        updated = apply_layout_mapping(source)

        self.assertEqual(
            updated,
            {
                "of": {"page-footer": {"bg": {"value": "blue"}}},
                "utrecht": {"page-footer": {"background-color": {"value": "blue"}}},
            },
        )

    def test_map_and_merge_old_token_to_new(self):
        source = {
            "of": {"page-header": {"bg": {"value": "blue"}}},
            "utrecht": {"page-header": {"color": {"value": "pink"}}},
        }

        updated = apply_layout_mapping(source)

        self.assertEqual(
            updated,
            {
                "of": {"page-header": {"bg": {"value": "blue"}}},
                "utrecht": {
                    "page-header": {
                        "background-color": {"value": "blue"},
                        "color": {"value": "pink"},
                    }
                },
            },
        )

    def test_do_not_overwrite_existing_token(self):
        source = {
            "of": {"page-header": {"bg": {"value": "red"}}},
            "utrecht": {"page-header": {"background-color": {"value": "blue"}}},
        }

        updated = apply_layout_mapping(source)

        self.assertEqual(
            updated,
            {
                "of": {"page-header": {"bg": {"value": "red"}}},
                "utrecht": {"page-header": {"background-color": {"value": "blue"}}},
            },
        )


class ButtonDesignTokensMigrationTests(TestMigrations):

    app = "config"
    migrate_from = "0002_squashed_to_of_v230"
    migrate_to = "0053_v230_to_v250"

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

        Theme = self.apps.get_model("config", "Theme")
        theme = Theme.objects.get()

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
        self.assertEqual(theme.design_token_values, expected)


class LayoutDesignTokensMigrationTests(TestMigrations):

    app = "config"
    migrate_from = "0002_squashed_to_of_v230"
    migrate_to = "0053_v230_to_v250"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        # (Partial) tokens configuration taken from a test instance
        GlobalConfiguration.objects.create(
            design_token_values={
                "of": {
                    "text": {"font-size": {"value": "1rem"}},
                    "page-header": {
                        "bg": {"value": "#07838f"},
                        "fg": {"value": "#FFFFFF"},
                    },
                },
                "utrecht": {
                    "page-footer": {
                        "background-color": {"value": "green"},
                    },
                },
            }
        )

    def test_design_tokens_updated_correctly(self):
        self.maxDiff = None

        Theme = self.apps.get_model("config", "Theme")
        theme = Theme.objects.get()

        expected = {
            "of": {
                "text": {"font-size": {"value": "1rem"}},
                "page-header": {
                    "bg": {"value": "#07838f"},
                    "fg": {"value": "#FFFFFF"},
                },
            },
            "utrecht": {
                "page-footer": {
                    "background-color": {"value": "green"},
                },
                "page-header": {
                    "background-color": {"value": "#07838f"},
                    "color": {"value": "#FFFFFF"},
                },
            },
        }
        self.assertEqual(theme.design_token_values, expected)


class EnableNewBuilderMigrationTests(TestMigrations):
    app = "config"
    migrate_from = "0053_v230_to_v250"
    migrate_to = "0054_enable_new_builder"

    def setUpBeforeMigration(self, apps):
        GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
        GlobalConfiguration.objects.create(enable_react_formio_builder=False)

    def test_builder_enabled(self):
        GlobalConfiguration = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfiguration.objects.get()

        self.assertTrue(config.enable_react_formio_builder)
