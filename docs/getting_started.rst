.. PopulationSim documentation master file
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _getting_started:

Getting Started
===============

This page describes how to install and run PopulationSim with the provided example.

Installation
------------

PopulationSim is distributed as a standard Python package with
``pyproject.toml``. The repository currently supports Python 3.9 through 3.12.

Preferred workflow
~~~~~~~~~~~~~~~~~~

The repository includes a ``uv.lock`` file. If you use
`uv <https://docs.astral.sh/uv/>`__, the recommended setup is:

::

  uv sync --dev

This creates the project environment and installs PopulationSim in editable
mode for local development.


.. _activitysim :

ActivitySim
~~~~~~~~~~~

.. note::

  PopulationSim is a 64bit Python 3 library that uses a number of packages from the
  scientific Python ecosystem, most notably `pandas <http://pandas.pydata.org>`__
  and `numpy <http://numpy.org>`__. It also relies heavily on the
  `ActivitySim <https://activitysim.github.io>`__ package.

  For local development in this repository, use the ``uv`` workflow described
  above. For more information on ActivitySim itself, see
  the ActivitySim `getting started
  <https://activitysim.github.io/activitysim/gettingstarted.html>`__ guide.


Running PopulationSim
---------------------

PopulationSim can be run in two ways.

**Using the** ``populationsim`` **entry point:**

The installed package provides a ``populationsim`` command that accepts paths to
the config, data, and output directories directly:

::

  uv run populationsim -c <config_dir> -d <data_dir> -o <output_dir>

Common CLI arguments are:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Argument
     - Description
   * - ``-c`` / ``--config``
     - Path to config directory (may be specified multiple times)
   * - ``-d`` / ``--data``
     - Path to data directory (may be specified multiple times)
   * - ``-o`` / ``--output``
     - Path to output directory
   * - ``-w`` / ``--working_dir``
     - Path to project directory (default: current directory)
   * - ``-r`` / ``--resume``
     - Resume after a specific model step
   * - ``-p`` / ``--pipeline``
     - Pipeline file name
   * - ``-s`` / ``--settings_file``
     - Settings file name
   * - ``-m`` / ``--multiprocess``
     - Run multiprocess (optionally specify number of processes)
   * - ``-e`` / ``--ext``
     - Package of extension modules to load
   * - ``--households_sample_size``
     - Households sample size
   * - ``--fast``
     - Do not limit each process to one thread

**Using a** ``run_populationsim.py`` **script:**

Each example includes a ``run_populationsim.py`` convenience script that
hard-codes the project directory and any example-specific setup (such as
building a pipeline file before the run). This is the recommended pattern for
your own projects. Run it with:

::

  uv run python run_populationsim.py


Run Examples
------------

There are five runnable examples in the repository:

1. The ``example_calm`` set-up runs a base synthetic population for the CALM region.

2. The ``example_calm_repop`` set-up updates the CALM synthetic population for a smaller geography using outputs from the base run.

3. The ``example_oceanside_repop`` set-up runs a repop workflow for the Oceanside example.

4. The ``example_survey_weighting`` set-up runs PopulationSim for the case of developing final weights for a household travel survey.

5. The ``example_test`` set-up is a smaller example used by the automated tests and is useful for quick CLI validation.

More information on configuration can be found in the **Application & Configuration** section.

Example_calm
~~~~~~~~~~~~

Follow the steps below to run **example_calm** set up:

  * Open a command prompt in the example_calm folder
  * Run the following commands:

  ::

   cd examples/example_calm
   uv run python run_populationsim.py

  * Review the outputs in the ``output`` folder

Example_calm_repop
~~~~~~~~~~~~~~~~~~

The repop configuration requires outputs from a base run. Therefore, the base configuration must be run before running the repop configuration. Follow the steps below to run **example_calm_repop** set up:

  * Run ``example_calm`` first so that ``example_calm/output/pipeline.h5`` exists
  * Open a command prompt in the example_calm_repop folder
  * Run the following commands:

  ::

   cd examples/example_calm_repop
   uv run python run_populationsim.py

  * Review the outputs in the ``output`` folder

Example_oceanside_repop
~~~~~~~~~~~~~~~~~~~~~~~

Follow the steps below to run **example_oceanside_repop**:

  * Open a command prompt in the example_oceanside_repop folder
  * Run the following commands:

  .. note::

    Unlike the other examples, the ``output`` directory is not included in the
    repository and must be created manually before running the script.

  ::

   cd examples/example_oceanside_repop
   mkdir output
   uv run python run_populationsim.py

  * Review the outputs in the ``output`` folder

Example_survey_weighting
~~~~~~~~~~~~~~~~~~~~~~~~

Follow the steps below to run **example_survey_weighting** set up:

  * Open a command prompt in the example_survey_weighting folder
  * Run the following commands:

  ::

   cd examples/example_survey_weighting
   uv run python run_populationsim.py

  * Review the outputs in the ``output`` folder

Example_test
~~~~~~~~~~~~

Follow the steps below to run **example_test** set up:

  * Open a command prompt in the example_test folder
  * Run the following commands:

  ::

   cd examples/example_test
   uv run python run_populationsim.py

  * Review the outputs in the ``output`` folder

  Alternatively, run from the repository root using the CLI entry point:

  ::

   uv run populationsim -c examples/example_test/configs -d examples/example_test/data -o examples/example_test/output
