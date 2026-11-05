import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "prepare_english_localization.py"
SPEC = importlib.util.spec_from_file_location("prepare_english_localization", MODULE_PATH)
assert SPEC and SPEC.loader
localization = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(localization)


class PrepareEnglishLocalizationTest(unittest.TestCase):
    def test_group_contiguous_sorts_and_deduplicates(self):
        self.assertEqual(
            localization.group_contiguous([9, 3, 4, 4, 7, 8]),
            [(3, 4), (7, 9)],
        )

    def test_manifest_is_default_on_and_guarded(self):
        manifest = localization.build_manifest(
            [
                {
                    "offset": 1234,
                    "file": "assets/example.bin",
                    "sha256": "a" * 64,
                    "expected_sha256": "b" * 64,
                }
            ]
        )
        self.assertIn('id = "macross.localization.english"', manifest)
        self.assertIn("default_enabled = true", manifest)
        self.assertIn('target = "disc_user"', manifest)
        self.assertIn(f'disc_sha256 = "{localization.SOURCE_SHA256}"', manifest)
        self.assertIn(f'sha256 = "{"a" * 64}"', manifest)
        self.assertIn(f'expected_sha256 = "{"b" * 64}"', manifest)
        self.assertIn(
            '[[author_link]]\nname = "NXP1000"\n'
            'url = "https://github.com/NXP1000"',
            manifest,
        )
        self.assertNotIn('author_link = "https://github.com/NXP1000"', manifest)

    def test_clean_removes_only_generated_package(self):
        with tempfile.TemporaryDirectory() as temp:
            packages = Path(temp)
            generated = packages / localization.PACKAGE_ID / localization.PACKAGE_VERSION
            unrelated = packages / "example.other" / "1.0.0"
            generated.mkdir(parents=True)
            unrelated.mkdir(parents=True)
            localization.clean_package(packages)
            self.assertFalse((packages / localization.PACKAGE_ID).exists())
            self.assertTrue(unrelated.is_dir())

    def test_archive_target_cannot_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(localization.PreparationError):
                localization.safe_archive_target(Path(temp), "../escape")


if __name__ == "__main__":
    unittest.main()
