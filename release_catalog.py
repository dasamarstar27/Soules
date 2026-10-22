"""Only published, version-named archives are offered as older releases."""

from release_version import VERSION, LABEL

DOWNLOAD_ROOT = "https://raw.githubusercontent.com/dasamarstar27/Soules"
ARCHIVED_RELEASES = (
    (
        "25.10",
        "7630fc8ce5e1829553056f59007f9feb7bdf6561",
        "Regional work-site supplies and an offline Simple laptop edition.",
    ),
    (
        "25.9",
        "3a4dcd952d769a77ecbc4ca1e5f3dddb9e698769",
        "Four monster forms at levels 1, 5, 10 and 15.",
    ),
    (
        "25.8",
        "c766285680e8107dd5c0c50e445a28c6244736db",
        "Camp stories, worker orders and stable sidebar choices.",
    ),
    (
        "25.7",
        "d2ad6e4e789c30499eba14c971b7c8dae9c5774d",
        "One weighted wander outcome with Normal and Easy tables.",
    ),
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
            notes="Current release: gathering keeps its reward and adds a monster or structure; fewer quiet wanders.",
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
