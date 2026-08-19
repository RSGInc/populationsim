.. PopulationSim documentation master file
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation Build
===================

This page describes how to build the PopulationSim documentation during local
development.

Building HTML docs
------------------

The Sphinx documentation lives in the ``docs`` directory and is typically built
through the wrapper Makefile from inside that directory:

::

  cd docs
  make html

This writes the generated site to ``docs/_build/html``.

Useful Makefile targets
-----------------------

The most useful Makefile targets are:

* ``make html`` to build the HTML site
* ``make clean`` to remove files under ``docs/_build``
* ``make linkcheck`` to check external links referenced by the docs
* ``make help`` to list the available Sphinx wrapper targets

Lower-level Sphinx command
--------------------------

The Makefile is a convenience wrapper around the local Sphinx executable in the
repository virtual environment. If needed, the equivalent lower-level command
can be run from the repository root:

::

  uv run sphinx-build -n -W -b html docs docs/_build/html
