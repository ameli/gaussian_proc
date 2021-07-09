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

# Python
import numpy
import multiprocessing

# Cython
from cython.parallel cimport parallel, prange
from ._kernels cimport matern_kernel, euclidean_distance
from libc.stdlib cimport exit, malloc, free
cimport cython
cimport openmp

__all__ = ['generate_dense_correlation']


# ===========================
# generate correlation matrix
# ===========================

@cython.boundscheck(False)
@cython.wraparound(False)
cdef void _generate_correlation_matrix(
        const double[:, ::1] points,
        const int matrix_size,
        const int dimension,
        const double[:] correlation_scale,
        const double nu,
        const int num_threads,
        double[:, ::1] correlation_matrix) nogil:
    """
    Generates a dense correlation matrix.

    :param points: A 2D array containing the coordinates of the spatial set of
        points in the unit hypercube. The first index of this array is the
        point ids and the second index is the dimension of the coordinates.
    :type points: cython memoryview (double)

    :param matrix_size: The shape of the first index of ``points``, which is
        also the size of the generated output matrix.
    :type matrix_size: int

    :param dimension: The shape of the second index of ``points`` array, which
        is the dimension of the spatial points.
    :type dimension: int

    :param correlation_scale: A parameter of the correlation function that
        scales distances.
    :type correlation_scale: double

    :param nu: The parameter :math:`\\nu` of Matern correlation kernel.
    :type nu: float

    :param num_threads: Number of parallel threads in openmp.
    :type num_threads: int

    :param correlation_matrix: Output array. Correlation matrix of the size
        ``matrix_size``.
    :type correlation_matrix: cython memoryview (double)
    """

    cdef int i, j
    cdef int dim

    # Set number of parallel threads
    openmp.omp_set_num_threads(num_threads)

    # Using max possible chunk size for parallel threads
    cdef int chunk_size = int((<double> matrix_size) / num_threads)
    if chunk_size < 1:
        chunk_size = 1

    # Iterate over rows of correlation matrix
    with nogil, parallel():
        for i in prange(matrix_size, schedule='static', chunksize=chunk_size):
            for j in range(i, matrix_size):

                # Compute correlation
                correlation_matrix[i][j] = matern_kernel(
                        euclidean_distance(
                            points[i][:],
                            points[j][:],
                            correlation_scale,
                            dimension),
                        nu)

                # Use symmetry of the correlation matrix
                if i != j:
                    correlation_matrix[j][i] = correlation_matrix[i][j]


# ==========================
# generate dense correlation
# ==========================

def generate_dense_correlation(
        points,
        correlation_scale,
        nu,
        verbose):
    """
    Generates a dense correlation matrix.

    .. note::

        If the ``kernel_threshold`` is large, it causes:

            * The correlation matrix :math:`\\mathbf{K}` will not be
              positive-definite.
            * The function :math:`\\mathrm{trace}\\left((\\mathbf{K}+t
              \\mathbf{I})^{-1}\\right)` produces unwanted oscillations.

    :param points: 2D array of the coordinates of the set of points. The first
        index of the array is the point Ids and its size determines the size of
        the correlation matrix. The second index of the array corresponds to
        the dimension of the spatial points.
    :type points: numpy.ndarray

    :param correlation_scale: A parameter of correlation function that scales
        distance.
    :type correlation_scale: float

    :param verbose: If ``True``, prints some information during the process.
    :type verbose: bool

    :return: Correlation matrix. If ``points`` is ``n*m`` array, the
        correlation matrix has ``n*n`` shape.
    :rtype: numpy.ndarray

    :param nu: The parameter :math:`\\nu` of Matern correlation kernel.
    :type nu: float
    """

    # size of data and the correlation matrix
    matrix_size = points.shape[0]
    dimension = points.shape[1]

    # Get number of CPU threads
    num_threads = multiprocessing.cpu_count()

    # Initialize matrix
    correlation_matrix = numpy.zeros(
            (matrix_size, matrix_size),
            dtype=float)

    # Dense correlation matrix
    _generate_correlation_matrix(
            points,
            matrix_size,
            dimension,
            correlation_scale,
            nu,
            num_threads,
            correlation_matrix)

    if verbose:
        print('Generated dense correlation matirx of size: %d.'
              % (matrix_size))

    return correlation_matrix
