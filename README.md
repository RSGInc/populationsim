PopulationSim
=============

PopulationSim is an open platform for population synthesis.  It emerged
from Oregon DOT's desire to build a shared, open, platform that could be
easily adapted for statewide, regional, and urban transportation planning
needs.  PopulationSim is implemented in the
[ActivitySim](https://github.com/activitysim/activitysim) framework.

## Requirements

- Python 3.9 through 3.12
- A local clone of this repository

This repository is configured as a modern Python package with
[`pyproject.toml`](pyproject.toml) and a `uv.lock` file. If you use
[`uv`](https://docs.astral.sh/uv/), it is the preferred way to create the
environment and run commands in this repo.

## Installation

### Preferred: `uv`

```bash
uv sync --dev
```

This creates the project environment and installs the package in editable mode.

### Alternative: `pip`

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Command-Line Interface

PopulationSim can be run directly from the command line:

```bash
populationsim -c /path/to/configs -d /path/to/data -o /path/to/output
```

You can also run the package as a module:

```bash
python -m populationsim -c /path/to/configs -d /path/to/data -o /path/to/output
```

The CLI supports the current repo entry point defined in `pyproject.toml`,
including:

- `-w, --working_dir` for project-style runs with `configs`, `data`, and
  `output` subdirectories
- repeated `-c/--config` and `-d/--data` arguments
- `-m, --multiprocess` for multiprocess configurations
- `-r, --resume` to resume after a step
- `-e, --ext` to load extension packages

## Running Examples

The [`examples/`](examples/) directory contains runnable projects that match the
current repository layout:

- `example_calm`
- `example_calm_repop`
- `example_oceanside_repop`
- `example_survey_weighting`
- `example_test`

Most examples can be run from their own directory with:

```bash
uv run python run_populationsim.py
```

For a direct CLI run, `example_test` is the smallest self-contained example:

```bash
uv run python -m populationsim \
  -c examples/example_test/configs \
  -d examples/example_test/data \
  -o examples/example_test/output
```

See [examples/README.md](examples/README.md) for example-specific notes.

## Documentation

https://activitysim.github.io/populationsim/
