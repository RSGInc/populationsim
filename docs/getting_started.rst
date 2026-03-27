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

Alternative workflow
~~~~~~~~~~~~~~~~~~~~

If you prefer not to use ``uv``, you can install the package into a local
virtual environment with ``pip``:

::

  python -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -e .


.. _activitysim :

ActivitySim
~~~~~~~~~~~

.. note::

  PopulationSim is a 64bit Python 3 library that uses a number of packages from the
  scientific Python ecosystem, most notably `pandas <http://pandas.pydata.org>`__
  and `numpy <http://numpy.org>`__. It also relies heavily on the
  `ActivitySim <https://activitysim.github.io>`__ package.

  For local development in this repository, prefer the ``uv`` or ``pip``
  workflows described above. For more information on ActivitySim itself, see
  the ActivitySim `getting started
  <https://activitysim.github.io/activitysim/gettingstarted.html>`__ guide.


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

  * Review the outputs in the *output* folder

Example_calm_repop
~~~~~~~~~~~~~~~~~~

The repop configuration requires outputs from a base run. Therefore, the base configuration must be run before running the repop configuration. Follow the steps below to run **example_calm_repop** set up:

  * Run ``example_calm`` first so that ``example_calm/output/pipeline.h5`` exists
  * Open a command prompt in the example_calm_repop folder
  * Run the following commands:

  ::

   cd examples/example_calm_repop
   uv run python run_populationsim.py

  * Review the outputs in the *output* folder

Example_oceanside_repop
~~~~~~~~~~~~~~~~~~~~~~~

Follow the steps below to run **example_oceanside_repop**:

  * Open a command prompt in the example_oceanside_repop folder
  * Run the following commands:

  ::

   cd examples/example_oceanside_repop
   uv run python run_populationsim.py

  * Review the outputs in the *output* folder

Example_survey_weighting
~~~~~~~~~~~~~~~~~~~~~~~~

Follow the steps below to run **example_survey_weighting** set up:

  * Open a command prompt in the example_survey_weighting folder
  * Run the following commands:

  ::

   cd examples/example_survey_weighting
   uv run python run_populationsim.py

  * Review the outputs in the *output* folder

Example_test
~~~~~~~~~~~~

Follow the steps below to run **example_test** through the command-line
interface:

  * Open a command prompt in the repository root
  * Run the following commands:

  ::

   uv run python -m populationsim -c examples/example_test/configs -d examples/example_test/data -o examples/example_test/output

  * Review the outputs in the *output* folder
