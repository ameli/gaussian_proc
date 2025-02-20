.. _test-package:

Test Package
************

You can test the package using either `pytest <https://docs.pytest.org/>`__ or `tox <https://tox.wiki/en/4.7.0/>`__.

Test with ``pytest``
====================

|codecov-devel|

The package can be tested by running several `test scripts <https://github.com/ameli/glearn/tree/main/tests>`_, which test all `sub-packages <https://github.com/ameli/glearn/tree/main/glearn>`_ and `examples <https://github.com/ameli/glearn/tree/main/examples>`_.

Clone the source code from the repository and install the required test packages by

.. prompt:: bash

    git clone https://github.com/ameli/glearn.git
    cd glearn
    python -m pip install -r tests/requirements.txt
    python -m pip install .

To automatically run all tests, use ``pytest`` which is installed by the above commands.

.. prompt:: bash

    mv glearn glearn-do-not-import
    pytest

.. attention::

    To properly run ``pytest``, rename ``/glearn/glearn`` directory as shown in the above code. This makes ``pytest`` to properly import |project| from the installed location, not from the source code directory.

Test with ``tox``
=================

To run a test in a virtual environment, use ``tox`` as follows:

1. Clone the source code from the repository:
   
   .. prompt:: bash
       
       git clone https://github.com/ameli/glearn.git

2. Install `tox <https://tox.wiki/en/latest/>`_:
   
   .. prompt:: bash
       
       python -m pip install tox

3. Run tests by
   
   .. prompt:: bash
       
       cd glearn
       tox

.. |codecov-devel| image:: https://img.shields.io/codecov/c/github/ameli/glearn
   :target: https://codecov.io/gh/ameli/glearn
