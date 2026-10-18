"""Published downgrade entries refer to real versioned builds, not invented history."""

from pathlib import Path
from unittest import TestCase
from zipfile import ZipFile
from release_catalog import available_releases
from release_version import VERSION


class ReleaseCatalogTests(TestCase):
    def test_current_and_archives_match_available_builds(self):
        entries = available_releases()
        self.assertEqual(entries[0]["version"], VERSION)
        self.assertTrue(entries[0]["current"])
        self.assertEqual(len({entry["version"] for entry in entries}), len(entries))
        root = Path(__file__).resolve().parents[1]
        for entry in entries[1:]:
            with self.subTest(version=entry["version"]):
                self.assertFalse(entry["current"])
                self.assertEqual(len(entry["commit"]), 40)
                self.assertIn("/" + entry["commit"] + "/", entry["url"])
                with ZipFile(
                    root / "releases" / ("Soules-" + entry["label"] + ".zip")
                ) as archive:
                    self.assertEqual(
                        archive.read(entry["label"] + "/VERSION").decode().strip(),
                        entry["version"],
                    )
                    self.assertIn(
                        entry["label"] + "/Play Soules.bat", archive.namelist()
                    )

    def test_reading_versions_has_no_game_or_cookie_side_effects(self):
        from app import app

        with app.test_client() as client:
            response = client.get("/api/releases")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["current"], VERSION)
            self.assertNotIn("Set-Cookie", response.headers)
            html = client.get("/").text
            self.assertIn('id="release-version"', html)
            self.assertIn('id="versions-dialog"', html)
            self.assertIn(
                "Tablet players cannot switch the shared server themselves", html
            )
            self.assertIn("Newer saves may contain items or systems", html)
