.. highlight:: shell

============
Installation
============


Stable release
--------------

To install OpenQTSim, run this command in your terminal:

.. code-block:: bash

    # Use pip to install OpenQTSim
    pip install openqtsim

This is the preferred method to install OpenQTSim, as it will always install the most recent stable release.

If you do not have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for OpenQTSim can be downloaded from the `Github repo`_:

.. code-block:: bash

    # Use git to clone OpenQTSim
    git clone https://github.com/TUDelft-CITG/OpenQTSim.git
    cd OpenQTSim

It is recommended to install OpenQTSim in a separate (conda) environment. Install it in developer
(editable) mode, so that changes to the source code are used directly:

.. code-block:: bash

    # Create and activate an environment (only needed once)
    conda create -n OpenQTSim python
    conda activate OpenQTSim

    # Install OpenQTSim in developer mode
    pip install -e .

Optional dependencies
---------------------

The parallel simulations of ``openqtsim.mt_engine`` (the 2000-series example notebooks) use `Dask`_.
Install Dask together with OpenQTSim with:

.. code-block:: bash

    pip install -e ".[dask]"

To run the tests and the example notebooks, also install pytest and Jupyter:

.. code-block:: bash

    pip install pytest pytest-cov jupyter
    pytest

.. _Github repo: https://github.com/TUDelft-CITG/OpenQTSim
.. _Dask: https://www.dask.org
