# Contributing

PopulationSim follows the broader
[ActivitySim development guidance](https://activitysim.github.io/activitysim/development.html)
in addition to the repository-specific notes below.

## Development Setup

PopulationSim uses a `uv`-managed development environment.

From the repository root:

```bash
uv sync --dev
```

## Common Checks

Run tests with:

```bash
uv run pytest
```

Build the documentation with:

```bash
cd docs
make html
```

## Pull Requests

Keep changes scoped to a single concern when possible.

Before opening a pull request:

- run the relevant tests
- rebuild the documentation if docs or doc tooling changed
- update documentation when behavior, workflows, or public interfaces change
