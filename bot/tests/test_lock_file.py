"""
Tests for uv.lock dependency lock file integrity.

This PR (dependency upgrades) only modifies uv.lock. These tests validate that
the lock file has correct structure, expected package versions, and that key
changes from the PR are present.
"""

import tomllib
from pathlib import Path

import pytest

LOCK_FILE_PATH = Path(__file__).parent.parent.parent / "uv.lock"


@pytest.fixture(scope="module")
def lock_data():
    """Parse uv.lock TOML and return the data as a dict."""
    with LOCK_FILE_PATH.open("rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="module")
def packages_by_name(lock_data):
    """Return a dict mapping package name -> package dict for quick lookups."""
    return {pkg["name"]: pkg for pkg in lock_data["package"]}


# ---------------------------------------------------------------------------
# Lock file header / metadata
# ---------------------------------------------------------------------------


def test_lock_file_exists():
    assert LOCK_FILE_PATH.exists(), f"uv.lock not found at {LOCK_FILE_PATH}"


def test_lock_file_is_valid_toml():
    """Lock file must be parseable as TOML without error."""
    with LOCK_FILE_PATH.open("rb") as f:
        data = tomllib.load(f)
    assert isinstance(data, dict)


def test_lock_file_version(lock_data):
    assert lock_data["version"] == 1


def test_lock_file_revision(lock_data):
    assert lock_data["revision"] == 3


def test_lock_file_requires_python(lock_data):
    assert lock_data["requires-python"] == ">=3.14"


def test_resolution_markers_present(lock_data):
    """resolution-markers field was added in this PR."""
    assert "resolution-markers" in lock_data, "resolution-markers key missing from lock file"


def test_resolution_markers_count(lock_data):
    """Exactly two resolution markers (split at Python 3.15 boundary)."""
    markers = lock_data["resolution-markers"]
    assert len(markers) == 2


def test_resolution_markers_python_315_split(lock_data):
    """Markers must represent the Python 3.15 version split added in this PR."""
    markers = lock_data["resolution-markers"]
    assert any("3.15" in m and ">=" in m for m in markers), (
        "Expected a marker for python_full_version >= '3.15'"
    )
    assert any("3.15" in m and "<" in m for m in markers), (
        "Expected a marker for python_full_version < '3.15'"
    )


def test_packages_list_is_non_empty(lock_data):
    assert len(lock_data["package"]) > 0


# ---------------------------------------------------------------------------
# New package: ast-serialize (added as mypy 2.x dependency)
# ---------------------------------------------------------------------------


def test_ast_serialize_present(packages_by_name):
    assert "ast-serialize" in packages_by_name, "ast-serialize package missing from lock file"


def test_ast_serialize_version(packages_by_name):
    assert packages_by_name["ast-serialize"]["version"] == "0.5.0"


def test_ast_serialize_source_is_pypi(packages_by_name):
    source = packages_by_name["ast-serialize"]["source"]
    assert "registry" in source
    assert "pypi.org" in source["registry"]


def test_ast_serialize_has_wheels(packages_by_name):
    pkg = packages_by_name["ast-serialize"]
    assert "wheels" in pkg, "ast-serialize must have wheel entries"
    assert len(pkg["wheels"]) > 0, "ast-serialize wheels list must not be empty"


def test_ast_serialize_wheels_have_required_fields(packages_by_name):
    wheels = packages_by_name["ast-serialize"]["wheels"]
    for wheel in wheels:
        assert "url" in wheel, f"Wheel missing 'url': {wheel}"
        assert "hash" in wheel, f"Wheel missing 'hash': {wheel}"
        assert "size" in wheel, f"Wheel missing 'size': {wheel}"


def test_ast_serialize_wheel_hashes_are_sha256(packages_by_name):
    wheels = packages_by_name["ast-serialize"]["wheels"]
    for wheel in wheels:
        assert wheel["hash"].startswith("sha256:"), (
            f"Expected sha256 hash, got: {wheel['hash']}"
        )


def test_ast_serialize_has_sdist(packages_by_name):
    pkg = packages_by_name["ast-serialize"]
    assert "sdist" in pkg, "ast-serialize must have an sdist entry"
    assert "url" in pkg["sdist"]
    assert "hash" in pkg["sdist"]


def test_ast_serialize_covers_multiple_platforms(packages_by_name):
    """ast-serialize ships wheels for multiple OS/arch combos."""
    wheels = packages_by_name["ast-serialize"]["wheels"]
    urls = [w["url"] for w in wheels]
    has_macos = any("macosx" in u for u in urls)
    has_linux = any("linux" in u for u in urls)
    has_windows = any("win" in u for u in urls)
    assert has_macos, "ast-serialize missing macOS wheels"
    assert has_linux, "ast-serialize missing Linux wheels"
    assert has_windows, "ast-serialize missing Windows wheels"


# ---------------------------------------------------------------------------
# mypy: upgraded from 1.19.1 → 2.1.0 and now depends on ast-serialize
# ---------------------------------------------------------------------------


def test_mypy_version(packages_by_name):
    assert packages_by_name["mypy"]["version"] == "2.1.0"


def test_mypy_depends_on_ast_serialize(packages_by_name):
    deps = packages_by_name["mypy"].get("dependencies", [])
    dep_names = [d["name"] for d in deps]
    assert "ast-serialize" in dep_names, (
        f"mypy 2.1.0 must depend on ast-serialize; got deps: {dep_names}"
    )


def test_mypy_still_depends_on_mypy_extensions(packages_by_name):
    deps = packages_by_name["mypy"].get("dependencies", [])
    dep_names = [d["name"] for d in deps]
    assert "mypy-extensions" in dep_names


def test_mypy_still_depends_on_pathspec(packages_by_name):
    deps = packages_by_name["mypy"].get("dependencies", [])
    dep_names = [d["name"] for d in deps]
    assert "pathspec" in dep_names


def test_mypy_old_version_not_present(lock_data):
    """Regression: mypy 1.19.1 must not appear in the lock file."""
    for pkg in lock_data["package"]:
        if pkg["name"] == "mypy":
            assert pkg["version"] != "1.19.1", "Old mypy 1.19.1 still present in lock file"


# ---------------------------------------------------------------------------
# Updated packages — version assertions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pkg_name, expected_version",
    [
        ("certifi", "2026.5.20"),
        ("django", "6.0.5"),
        ("gunicorn", "26.0.0"),
        ("librt", "0.11.0"),
        ("packaging", "26.2"),
        ("pathspec", "1.1.1"),
        ("psycopg", "3.3.4"),
        ("psycopg-binary", "3.3.4"),
        ("pygments", "2.20.0"),
        ("pytest", "9.0.3"),
        ("ruff", "0.15.15"),
        ("sentry-sdk", "2.61.1"),
        ("slack-bolt", "1.28.0"),
        ("slack-sdk", "3.42.0"),
        ("tzdata", "2026.2"),
        ("urllib3", "2.7.0"),
    ],
)
def test_package_version(packages_by_name, pkg_name, expected_version):
    assert pkg_name in packages_by_name, f"Package '{pkg_name}' missing from lock file"
    actual = packages_by_name[pkg_name]["version"]
    assert actual == expected_version, (
        f"{pkg_name}: expected {expected_version}, got {actual}"
    )


# ---------------------------------------------------------------------------
# Regression: old versions must not be present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pkg_name, old_version",
    [
        ("certifi", "2026.2.25"),
        ("django", "6.0.2"),
        ("gunicorn", "25.1.0"),
        ("librt", "0.8.1"),
        ("mypy", "1.19.1"),
        ("packaging", "26.0"),
        ("pathspec", "1.0.4"),
        ("psycopg", "3.3.3"),
        ("psycopg-binary", "3.3.3"),
        ("pygments", "2.19.2"),
        ("pytest", "9.0.2"),
        ("ruff", "0.15.4"),
        ("sentry-sdk", "2.54.0"),
        ("slack-bolt", "1.27.0"),
        ("slack-sdk", "3.40.1"),
        ("tzdata", "2025.3"),
        ("urllib3", "2.6.3"),
    ],
)
def test_old_package_version_not_present(lock_data, pkg_name, old_version):
    """Ensure pre-PR versions are no longer in the lock file."""
    for pkg in lock_data["package"]:
        if pkg["name"] == pkg_name:
            assert pkg["version"] != old_version, (
                f"{pkg_name} still has old version {old_version} in lock file"
            )


# ---------------------------------------------------------------------------
# Structural integrity of all packages
# ---------------------------------------------------------------------------


def test_all_packages_have_name(lock_data):
    for pkg in lock_data["package"]:
        assert "name" in pkg, f"Package entry missing 'name': {pkg}"
        assert pkg["name"], "Package name must not be empty"


def test_all_packages_have_version(lock_data):
    for pkg in lock_data["package"]:
        assert "version" in pkg, f"Package '{pkg.get('name')}' missing 'version'"
        assert pkg["version"], f"Package '{pkg.get('name')}' has empty version"


def test_all_packages_have_source(lock_data):
    for pkg in lock_data["package"]:
        assert "source" in pkg, f"Package '{pkg.get('name')}' missing 'source'"


def test_all_package_sources_reference_pypi(lock_data):
    """All packages must be sourced from PyPI (no private/git sources)."""
    for pkg in lock_data["package"]:
        source = pkg["source"]
        if "registry" in source:
            assert "pypi.org" in source["registry"], (
                f"Package '{pkg['name']}' references unexpected registry: {source['registry']}"
            )


def test_all_wheel_hashes_are_sha256(lock_data):
    for pkg in lock_data["package"]:
        for wheel in pkg.get("wheels", []):
            assert wheel["hash"].startswith("sha256:"), (
                f"Non-sha256 hash for {pkg['name']} wheel: {wheel['hash']}"
            )


def test_all_sdist_hashes_are_sha256(lock_data):
    for pkg in lock_data["package"]:
        sdist = pkg.get("sdist")
        if sdist:
            assert sdist["hash"].startswith("sha256:"), (
                f"Non-sha256 hash for {pkg['name']} sdist: {sdist['hash']}"
            )


def test_no_duplicate_package_names(lock_data):
    """Each package name must appear at most once."""
    names = [pkg["name"] for pkg in lock_data["package"]]
    seen = set()
    duplicates = []
    for name in names:
        if name in seen:
            duplicates.append(name)
        seen.add(name)
    assert not duplicates, f"Duplicate package entries found: {duplicates}"


def test_all_wheel_urls_are_https(lock_data):
    for pkg in lock_data["package"]:
        for wheel in pkg.get("wheels", []):
            assert wheel["url"].startswith("https://"), (
                f"Non-HTTPS wheel URL for {pkg['name']}: {wheel['url']}"
            )


def test_all_sdist_urls_are_https(lock_data):
    for pkg in lock_data["package"]:
        sdist = pkg.get("sdist")
        if sdist:
            assert sdist["url"].startswith("https://"), (
                f"Non-HTTPS sdist URL for {pkg['name']}: {sdist['url']}"
            )
