"""Custom themes appear once in the picker and require saved variants."""

import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mangomod import config_parser, theme


class ThemeVariantTests(unittest.TestCase):
    def test_created_variants_and_legacy_css(self):
        with TemporaryDirectory() as directory, patch.object(config_parser, "APP_SETTINGS_DIR", Path(directory)):
            theme_id, error = theme.create_custom_theme("Forest", "dark", "#20252b", "#323942", "#77bbaa")
            assert error is None and theme_id == "user:Forest"
            assert theme.available_themes()[-1] == (theme_id, "Forest")
            assert theme.load_theme_css(theme_id, mode="dark")[1] is None
            assert theme.load_theme_css(theme_id, mode="light")[1] == "This theme has no Light variant. Create it first."

            second_id, error = theme.create_custom_theme("Forest", "light", "#edf0ed", "#faf9f4", "#336655")
            assert error is None and second_id == theme_id
            assert [item for item in theme.available_themes() if item[0] == theme_id] == [(theme_id, "Forest")]
            assert theme.load_theme_css(theme_id, mode="light")[1] is None
            assert theme.create_custom_theme("Forest", "light", "#edf0ed", "#faf9f4", "#336655")[1] == "This theme already has a Light variant."

            legacy = theme.user_themes_dir() / "Legacy.css"
            legacy.write_text("@define-color mm_accent #445566;\n", encoding="utf-8")
            assert ("user:Legacy", "Legacy") in theme.available_themes()
            assert theme.load_theme_css("user:Legacy", mode="dark")[1] is None
            assert theme.load_theme_css("user:Legacy", mode="light")[1] == "This theme has no Light variant. Create it first."
            assert theme.delete_custom_theme("mango-dark") == (False, "Built-in themes cannot be deleted.")
            assert theme.delete_custom_theme("user:Legacy") == (True, None)
            assert not legacy.exists()
            assert theme.delete_custom_theme(theme_id) == (True, None)
            assert not (theme.user_themes_dir() / "Forest.dark.css").exists()
            assert not (theme.user_themes_dir() / "Forest.light.css").exists()
            assert all(item[0] != theme_id for item in theme.available_themes())


if __name__ == "__main__":
    unittest.main()
