============
roman_photoz
============

The ``roman_photoz`` package provides tools for processing catalogs
produced by the Roman Space Telescope Calibration Pipeline (``romancal``)
to estimate photometric redshift.

Overview
--------

The Roman Space Telescope will produce large catalogs of astronomical objects.
This package provides tools for processing these catalogs to estimate photometric
redshifts. Key features include:

* Processing Roman catalog data in ASDF format
* Creating filter definitions based on Roman Space Telescope specifications
* Generating simulated catalogs for development and testing
* Estimating photometric redshifts using LePhare

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage

.. toctree::
   :maxdepth: 2
   :caption: Modules

   create_roman_filters
   roman_catalog_process
   roman_catalog_handler
   create_simulated_catalog

API Reference
-------------

.. automodule:: roman_photoz
   :members:
   :undoc-members:
   :show-inheritance:

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
