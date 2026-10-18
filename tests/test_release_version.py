from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from zipfile import ZipFile
import json
import hashlib
from build_release import build
from release_version import VERSION, LABEL


class VersionedReleaseTests(TestCase):
    def test_release_label_in_browser_and_api(self):
        from app import app

        self.assertEqual(VERSION, "25.6")
        self.assertEqual(LABEL, "V25.6")
        client = app.test_client()
        self.assertEqual(client.get("/api/version").json["release"], LABEL)
        self.assertIn("Soules " + LABEL, client.get("/").text)
        self.assertIn("/static/hindi.js", client.get("/").text)

    def test_package_uses_version_folder_and_excludes_private_or_nested_archives(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                "VERSION": b"25.2\n",
                "Play Soules.bat": b"python play.py",
                "static/hindi.js": b"hindi",
                "instance/private.json": b"secret",
                "soulcrypt_save.json": b"private",
                ".venv/a": b"env",
                "releases/old.zip": b"old",
            }
            for name, payload in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            first = root / "one.zip"
            second = root / "two.zip"
            self.assertEqual(build(root, first, "25.2", list(files)), 3)
            build(root, second, "25.2", list(files))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with ZipFile(first) as archive:
                self.assertTrue(
                    all(name.startswith("V25.2/") for name in archive.namelist())
                )
                self.assertNotIn("V25.2/soulcrypt_save.json", archive.namelist())
                manifest = json.loads(archive.read("V25.2/SOURCE_MANIFEST.json"))
                self.assertEqual(
                    manifest["sha256"]["static/hindi.js"],
                    hashlib.sha256(b"hindi").hexdigest(),
                )

    def test_version_cannot_escape_package_folder(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                build(Path(directory), Path(directory) / "a.zip", "../private", [])
