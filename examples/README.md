# PopulationSim Examples

This directory contains runnable example projects for PopulationSim. Each
example is structured as a small project with its own `configs`, `data`, and
`output` directories.

## Environment

From the repository root, the preferred setup is:

```bash
uv sync --dev
```

Then run commands with `uv run ...`.

## Command-Line Interface

PopulationSim provides a CLI that can be run either through the installed
`populationsim` entry point or with `python -m populationsim`:

```bash
populationsim -c /path/to/configs -d /path/to/data -o /path/to/output
```

### CLI Options

- `-c, --config`: Path to config directory (can be specified multiple times)
- `-d, --data`: Path to data directory (can be specified multiple times)
- `-o, --output`: Path to output directory
- `-w, --working_dir`: Path to example/project directory (default: current directory)
- `-r, --resume`: Resume after step
- `-p, --pipeline`: Pipeline file name
- `-s, --settings_file`: Settings file name
- `--households_sample_size`: Households sample size
- `-m, --multiprocess`: Run multiprocess (optionally specify number of processes)
- `-e, --ext`: Package of extension modules to load
- `--fast`: Do not limit process to one thread

## Example Projects

- `example_calm`: Base synthetic population run using CALM data
- `example_calm_repop`: Repopulation example that depends on the base CALM run
- `example_oceanside_repop`: Oceanside repopulation example with a pipeline setup helper
- `example_survey_weighting`: Survey-weighting workflow
- `example_test`: Small test fixture with standard, flex, and multiprocess configs

## Common Run Patterns

### Run an example wrapper script

Each example with a `run_populationsim.py` wrapper can be run from its example
directory:

```bash
cd examples/example_calm
uv run python run_populationsim.py
```

Available wrapper-script examples:

- `example_calm`
- `example_calm_repop`
- `example_oceanside_repop`
- `example_survey_weighting`
- `example_test`

### Run through the CLI from the repo root

```bash
uv run python -m populationsim \
  -c ./examples/example_test/configs \
  -d ./examples/example_test/data \
  -o ./examples/example_test/output
```

### Use a working directory

```bash
uv run python -m populationsim -w ./examples/example_test
```

### Use multiple config directories

```bash
uv run python -m populationsim \
  -c ./examples/example_test/configs_mp \
  -c ./examples/example_test/configs \
  -d ./examples/example_test/data \
  -o ./examples/example_test/output \
  -m 2
```

### Resume from a checkpoint

```bash
uv run python -m populationsim \
  -c ./examples/example_test/configs \
  -d ./examples/example_test/data \
  -o ./examples/example_test/output \
  -r expand_households
```

## Example Notes

### `example_calm_repop`

This example expects outputs from `example_calm`. Run the base CALM example
first so `example_calm/output/pipeline.h5` exists.

### `example_oceanside_repop`

This example uses `construct_pipe.py` to prepare the pipeline before running
PopulationSim.

## CLI Example Script

The `cli_example.py` script demonstrates how to invoke the CLI from Python
code. You can run it with:

```bash
uv run python examples/cli_example.py
```

It runs the `example_test` configuration through `python -m populationsim`.
