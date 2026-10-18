"""Only published, version-named archives are offered as older releases."""

from release_version import VERSION, LABEL

DOWNLOAD_ROOT = "https://raw.githubusercontent.com/dasamarstar27/Soules"
ARCHIVED_RELEASES = (
    (
        "25.6",
        "38dfc195f332f927d3cac71bed2690056c453fc9",
        "Working tablet purchase Yes/No confirmations.",
    ),
    (
        "25.5",
        "15c43e023187a1ac9f87975897155c32fad05c48",
        "Corner version badge and archived release downloads.",
    ),
    (
        "25.4",
        "be274cc4bd01cfa6351ffd1b620d5826a4fe5a4d",
        "Online tablet hosting setup; Easy and Normal difficulty.",
    ),
    (
        "25.3",
        "4cdcedc701cf462260586ae4c16179649fdcacae",
        "Easy and Normal difficulty; cleaned idea backlog.",
    ),
    (
        "25.2",
        "55ae65bee0a1553785be22901074eb5b10d033c8",
        "Hindi narration and buttons for tablet / Easy reading. Difficulty selection was added later.",
    ),
)


def available_releases():
    entries = [
        dict(
            version=VERSION,
            label=LABEL,
            current=True,
            commit=None,
            url=f"{DOWNLOAD_ROOT}/main/releases/Soules-{LABEL}.zip",
            notes="Current release: one weighted main wander roll with Normal/Easy tables.",
        )
    ]
    for version, commit, notes in ARCHIVED_RELEASES:
        if tuple(map(int, version.split("."))) >= tuple(map(int, VERSION.split("."))):
            continue
        entries.append(
            dict(
                version=version,
                label="V" + version,
                current=False,
                commit=commit,
                url=f"{DOWNLOAD_ROOT}/{commit}/releases/Soules-V{version}.zip",
                notes=notes,
            )
        )
    return entries
