"""Network-free regression tests for the profile image validator."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("check_profile", Path(__file__).with_name("check_profile.py"))
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class ProfileCheckTests(unittest.TestCase):
    def parse(self, markup):
        parser = checker.ProfileImages("fixture.md")
        parser.feed(markup)
        return parser

    def test_decorative_image_allows_empty_alt(self):
        parser = self.parse('<img src="assets/pro-divider.svg" alt="">')
        self.assertEqual(parser.errors, [])
        self.assertEqual(parser.images, 1)

    def test_missing_alt_is_reported(self):
        parser = self.parse('<img src="assets/pro-divider.svg">')
        self.assertIn("missing alt attribute", " ".join(parser.errors))

    def test_missing_source_is_reported(self):
        self.assertIn("missing source", " ".join(self.parse('<img alt="Example">').errors))

    def test_nonexistent_asset_is_reported(self):
        parser = self.parse('<img src="assets/not-a-real-file.svg" alt="Example">')
        self.assertIn("missing or unsafe local asset", " ".join(parser.errors))

    def test_encoded_path_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            (root.parent / "outside.svg").write_text("fixture", encoding="utf-8")
            with patch.object(checker, "ROOT", root):
                parser = self.parse('<img src="%2e%2e/outside.svg" alt="Example">')
            self.assertIn("unsafe local asset", " ".join(parser.errors))

    def test_current_hero_has_meaningful_alt_in_both_languages(self):
        for alt in ("Build with purpose. Ship with care.", "목적을 갖고 만듭니다."):
            with self.subTest(alt=alt):
                self.assertEqual(self.parse(f'<img src="assets/pro-hero.svg" alt="{alt}">').errors, [])
        self.assertIn("banner alt", " ".join(self.parse('<img src="assets/pro-hero.svg" alt="Banner">').errors))

    def test_obsolete_footer_description_is_reported(self):
        parser = self.parse('<img src="assets/pro-footer.svg" alt="Gradient waving footer">')
        self.assertIn("obsolete artwork", " ".join(parser.errors))

    def test_remote_badges_do_not_need_network(self):
        parser = self.parse('<img src="https://example.invalid/counter.svg" alt="Views">')
        self.assertEqual(parser.errors, [])

    def test_actual_bilingual_readmes_pass(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = checker.main()
        self.assertEqual(result, 0)
        self.assertIn("PASS: 2 locales", output.getvalue())


if __name__ == "__main__":
    unittest.main()
