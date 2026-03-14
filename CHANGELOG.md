# CHANGELOG


## v0.1.0 (2026-03-14)

### Features

- Add automated release and publish workflow
  ([`6890ad4`](https://github.com/vincenzo-gasparo/pytest-pw-config-gen/commit/6890ad4a40439e99c2f95ff46d531d94c17e04ae))

On every push to main, python-semantic-release reads conventional commit messages to determine the
  version bump, updates pyproject.toml, creates a git tag and GitHub release, then builds and
  publishes to PyPI via OIDC trusted publishing (no API token needed).

Commit convention: fix: → patch (0.1.0 → 0.1.1)

feat: → minor (0.1.0 → 0.2.0)

feat!: → major (0.1.0 → 1.0.0)
