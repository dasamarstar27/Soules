"""Build a repeatable, version-named game ZIP from tracked source files only."""

from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
EXCLUDED = {
    ".git",
    ".venv",
    "instance",
    "__pycache__",
    "releases",
    "downloads",
    "build",
    "dist",
}
PRIVATE = {
    "soulcrypt_save.json",
    "saves.json",
    "leaderboard.json",
    ".env",
    "secrets.toml",
}


def build(root, output, version, paths):
    import re

    if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version):
        raise ValueError("Use a version such as 25.2.")
    root = root.resolve()
    prefix = "V" + version + "/"
    manifest = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(set(paths)):
            relative = PurePosixPath(name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or any(part in EXCLUDED for part in relative.parts)
                or relative.name in PRIVATE
                or relative.suffix in (".pyc", ".log")
            ):
                continue
            path = root.joinpath(*relative.parts)
            if not path.is_file():
                continue
            if not path.resolve().is_relative_to(root):
                raise ValueError("Tracked file points outside this checkout: " + name)
            payload = path.read_bytes()
            entry = ZipInfo(
                prefix + relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0)
            )
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = (
                0o755 if path.stat().st_mode & 0o111 else 0o644
            ) << 16
            archive.writestr(entry, payload)
            manifest[relative.as_posix()] = hashlib.sha256(payload).hexdigest()
        entry = ZipInfo(
            prefix + "SOURCE_MANIFEST.json", date_time=(1980, 1, 1, 0, 0, 0)
        )
        entry.compress_type = ZIP_DEFLATED
        archive.writestr(
            entry,
            json.dumps(
                dict(version=version, sha256=manifest), indent=2, sort_keys=True
            ).encode(),
        )
    return len(manifest)


def main():
    version = (ROOT / "VERSION").read_text().strip()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "releases" / f"Soules-V{version}.zip"
    )
    args = parser.parse_args()
    paths = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    print(
        f"{build(ROOT,args.output,version,paths)} source files packaged in {args.output} under V{version}/"
    )


if __name__ == "__main__":
    main()
