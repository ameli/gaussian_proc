# SPDX-FileCopyrightText: Copyright 2021, Siavash Ameli <sameli@berkeley.edu>
# SPDX-License-Identifier: BSD-3-Clause
# SPDX-FileType: SOURCE
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the license found in the LICENSE.txt file in the root
# directory of this source tree.


# ======
# Kernel
# ======

cdef class Kernel(object):

    cdef double cy_kernel(self, const double x) noexcept nogil
    cdef double cy_kernel_first_derivative(self, const double x) noexcept nogil
    cdef double cy_kernel_second_derivative(
        self, const double x) noexcept nogil
