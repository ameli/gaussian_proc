# SPDX-FileCopyrightText: Copyright 2021, Siavash Ameli <sameli@berkeley.edu>
# SPDX-License-Identifier: BSD-3-Clause
# SPDX-FileType: SOURCE
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the license found in the LICENSE.txt file in the root directory
# of this source tree.


# ============
# check import
# ============

def _check_import():
    """
    The following two issues (see if conditions below) only happen in a cython
    package and if the package is build without --inplace option. This is
    because without the --inplace option, the *.so files will be built inside
    the /build directory (not in the same directory of the source code where
    *.pyx files are). On the other hand, when the user's directory is in the
    parent directory of the package, this path will be the first path on the
    sys.path. Thus, it looks for the package in the source-code directory, not
    where it was built or installed. But, because the built is outside of the
    source (recall no --inplace), it cannot find the *.so files.

    To resolve this issue:
    1. Either build the package with --inplace option.
    2. Change the current directory, or the directory of the script that you
       are running out of the source code.
    """

    import sys
    import os

    # Find the current directory of user (where the user calls an executable)
    _user_current_dir = os.getcwd()

    # Find executable directory (this is where the *.py executable is)
    _executable_file = os.path.abspath(sys.argv[0])
    _executable_dir = os.path.dirname(_executable_file)

    # Find the project directory (second parent directory of this script)
    _package_dir = os.path.dirname(os.path.realpath(__file__))  # It is: ../
    _project_dir = os.path.dirname(_package_dir)                # It is: ../../

    if (_user_current_dir == _project_dir):
        raise RuntimeError('You are in the source-code directory of this ' +
                           'package. Importing the package will fail. To ' +
                           'resolve this issue, consider changing the ' +
                           'current directory outside of the directory of ' +
                           'the source-code of this package. Your current ' +
                           'directory is: %s.' % _user_current_dir)

    if (_executable_dir == _project_dir):
        raise RuntimeError('You are running a script in the source-code ' +
                           'directory of this package. Importing the ' +
                           'package will fail. To resolve this issue, ' +
                           'consider changing the script directory outside ' +
                           'of the directory of the source-code of this ' +
                           'package. Your current directory is: %s.'
                           % _executable_dir)


# =======
# Imports
# =======

# Load OpenMP before all other modules to avoid segmentation fault in MacOS
# caused by duplicate loading of libomp by this package and the libomp lib that
# is shipped with detkit package (detkit is imported in _mean/linear_model.py)
import sys as _sys                                                 # noqa: E402
if _sys.platform.lower() == "darwin":
    from ._load_omp import load_omp
    load_omp()

try:
    from ._mean import LinearModel                                 # noqa: E402
    from ._covariance import Covariance                            # noqa: E402
    from ._gaussian_process import GaussianProcess                 # noqa: E402
    from .device import Timer, Memory, info
    from ._definitions import get_config                           # noqa: E402

except Exception as e:
    # Before printing the exception, check if the exception is raised due to
    # being on the wrong directory.
    _check_import()

    # If the error was not due to being in the source directory, raise previous
    # error.
    raise e

__all__ = ['LinearModel', 'Covariance', 'GaussianProcess', 'Timer', 'Memory',
           'info', 'get_config']

from .__version__ import __version__                          # noqa: F401 E402
