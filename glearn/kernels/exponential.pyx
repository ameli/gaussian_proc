# SPDX-FileCopyrightText: Copyright 2021, Siavash Ameli <sameli@berkeley.edu>
# SPDX-License-Identifier: BSD-3-Clause
# SPDX-FileType: SOURCE
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the license found in the LICENSE.txt file in the root
# directory of this source tree.


# =======
# Imports
# =======

from libc.math cimport exp
from .kernel import Kernel
from .kernel cimport Kernel

__all__ = ['Exponential']


# ===========
# Exponential
# ===========

cdef class Exponential(Kernel):
    """
    Exponential kernel.

    The kernel object is used as input argument to the instants of
    :class:`glearn.Covariance` class.

    .. note::

        For the methods of this class, see the base class
        :class:`glearn.kernels.Kernel`.

    See Also
    --------

    glearn.Covariance

    Notes
    -----

    The exponential kernel is defined as

    .. math::

        k(x) = e^{-x}.

    The first derivative of the kernel is

    .. math::

        \\frac{\\mathrm{d} k(x)}{\\mathrm{d}x} = -k(x),

    and its second derivative is

    .. math::

        \\frac{\\mathrm{d} k(x)}{\\mathrm{d}x} = k(x).

    Examples
    --------

    **Create Kernel Object:**

    .. code-block:: python

        >>> from glearn import kernels

        >>> # Create an exponential kernel
        >>> kernel = kernels.Exponential()

        >>> # Evaluate kernel at the point x=0.5
        >>> x = 0.5
        >>> kernel(x)
        0.6065306597126334

        >>> # Evaluate first derivative of kernel at the point x=0.5
        >>> kernel(x, derivative=1)
        -0.6065306597126334

        >>> # Evaluate second derivative of kernel at the point x=0.5
        >>> kernel(x, derivative=2)
        0.6065306597126334

        >>> # Plot kernel and its first and second derivative
        >>> kernel.plot()

    .. image:: ../_static/images/plots/kernel_exponential.png
        :align: center
        :width: 100%
        :class: custom-dark

    **Where to Use Kernel Object:**

    Use the kernel object to define a covariance object:

    .. code-block:: python
        :emphasize-lines: 7

        >>> # Generate a set of sample points
        >>> from glearn.sample_data import generate_points
        >>> points = generate_points(num_points=50)

        >>> # Create covariance object of the points with the above kernel
        >>> from glearn import covariance
        >>> cov = glearn.Covariance(points, kernel=kernel)
    """

    # =========
    # cy kernel
    # =========

    cdef double cy_kernel(self, const double x) noexcept nogil:
        """
        Computes the exponential correlation function for a given Euclidean
        distance of two spatial points.

        The Exponential correlation function defined by

        .. math::

            K(x) = \\exp(-x)

        :param x: The distance that represents the Euclidean distance between
            mutual points.
        :type x: ndarray

        :return: Exponential correlation kernel
        :rtype: double
        """

        return exp(-x)

    # ==========================
    # cy kernel first derivative
    # ==========================

    cdef double cy_kernel_first_derivative(
            self, const double x) noexcept nogil:
        """
        First derivative of kernel.
        """

        return -exp(-x)

    # ===========================
    # cy kernel second derivative
    # ===========================

    cdef double cy_kernel_second_derivative(
            self, const double x) noexcept nogil:
        """
        Second derivative of kernel.
        """

        return exp(-x)
