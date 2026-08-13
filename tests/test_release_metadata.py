"""Version and identity must agree across the files a release touches.

The MCP Registry entry drifted six months behind PyPI because nothing checked
it: `pyproject.toml`, `server.json` and the README's `mcp-name` marker are
edited by hand at different times, and only the first one is exercised by any
other test. These assertions make the drift a failing build instead of a stale
listing nobody notices.
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
SERVER_JSON = PROJECT_ROOT / "server.json"
README = PROJECT_ROOT / "README.md"


def _pyproject_version() -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', PYPROJECT.read_text(), re.M)
    assert match, "no version in pyproject.toml"
    return match.group(1)


def _server_json() -> dict:
    return json.loads(SERVER_JSON.read_text(encoding="utf-8"))


class TestVersionAgreement:
    def test_server_json_matches_pyproject(self):
        assert _server_json()["version"] == _pyproject_version(), (
            "server.json version is out of step with pyproject.toml; the MCP "
            "Registry would advertise the wrong release"
        )

    def test_package_version_matches_server_version(self):
        server = _server_json()
        packages = server.get("packages", [])
        assert packages, "server.json declares no packages"
        for package in packages:
            assert package["version"] == server["version"], (
                f"package {package['identifier']} pinned at {package['version']} "
                f"but the server is {server['version']}"
            )

    def test_pypi_package_identifier_matches_project_name(self):
        name = re.search(r'^name\s*=\s*"([^"]+)"', PYPROJECT.read_text(), re.M)
        assert name
        pypi = [p for p in _server_json()["packages"] if p["registryType"] == "pypi"]
        assert pypi, "no PyPI package declared in server.json"
        for package in pypi:
            assert package["identifier"] == name.group(1)


class TestOwnershipMarker:
    def test_readme_carries_the_mcp_name_marker(self):
        # The registry verifies PyPI ownership by finding this string in the
        # package description, which is built from the README. Losing it fails
        # publishing, not the build, so it is worth asserting here.
        marker = re.search(r"mcp-name:\s*([^\s>]+)", README.read_text(encoding="utf-8"))
        assert marker, "README is missing the `mcp-name:` marker"
        assert marker.group(1) == _server_json()["name"], (
            "README mcp-name marker does not match server.json name; PyPI "
            "ownership verification would reject the publish"
        )


class TestServerJsonShape:
    def test_declares_the_hosted_endpoint(self):
        remotes = _server_json().get("remotes", [])
        assert any(r.get("url", "").startswith("https://") for r in remotes), (
            "the hosted endpoint should stay listed so clients can use it "
            "without installing anything"
        )

    def test_repository_points_at_this_project(self):
        repo = _server_json().get("repository", {})
        assert repo.get("url", "").endswith("/deadends.dev")
        assert repo.get("source") == "github"
