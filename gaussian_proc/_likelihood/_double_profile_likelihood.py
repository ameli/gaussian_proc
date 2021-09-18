# SPDX-FileCopyrightText: Copyright 2021, Siavash Ameli <sameli@berkeley.edu>
# SPDX-License-Identifier: BSD-3-Clause
# SPDX-FileType: SOURCE
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the license found in the LICENSE.txt file in the root directory
# of this source tree.


# =======
# Imports
# =======

import time
import numpy
import scipy
import scipy.linalg
import scipy.sparse
import scipy.sparse.linalg
import scipy.optimize
from functools import partial

from .._utilities.plot_utilities import *                    # noqa: F401, F403
from .._utilities.plot_utilities import load_plot_settings, save_plot, plt, \
        mark_inset, InsetPosition, matplotlib
from ._profile_likelihood import ProfileLikelihood


# =========================
# Double Profile Likelihood
# =========================

class DoubleProfileLikelihood(object):

    # ==========
    # likelihood
    # ==========

    def likelihood(
            z,
            X,
            cov,
            sign_switch,
            log_eta_guess,
            hyperparam):
        """
        Variable eta is profiled out, meaning that optimal value of eta is
        used in log-likelihood function.
        """

        # Here, hyperparam consists of only distance_scale, but not eta.
        if isinstance(hyperparam, list):
            hyperparam = numpy.array(hyperparam)
        distance_scale = numpy.abs(hyperparam)
        cov.set_distance_scale(distance_scale)

        # Find optimal eta
        eta = DoubleProfileLikelihood._find_optimal_eta(
                z, X, cov, distance_scale, log_eta_guess)
        log_eta = numpy.log(eta)

        # Construct new hyperparam that consists of both eta and distance_scale
        hyperparam_full = numpy.r_[log_eta, distance_scale]

        # Finding the maxima.
        lp = ProfileLikelihood.likelihood(
                z, X, cov.mixed_cor, sign_switch, hyperparam_full)

        return lp

    # ===================
    # likelihood jacobian
    # ===================

    @staticmethod
    def likelihood_jacobian(
            z,
            X,
            cov,
            sign_switch,
            log_eta_guess,
            hyperparam):
        """
        Computes Jacobian w.r.t eta, and if given, distance_scale.
        """

        # When profiling eta is enabled, derivative w.r.t eta is not needed.
        # Compute only Jacobian w.r.t distance_scale. Also, here, the input
        # hyperparam consists of only distance_scale (and not eta).
        if isinstance(hyperparam, list):
            hyperparam = numpy.array(hyperparam)
        distance_scale = numpy.abs(hyperparam)
        cov.set_distance_scale(distance_scale)

        # Find optimal eta
        eta = DoubleProfileLikelihood._find_optimal_eta(
                z, X, cov, distance_scale, log_eta_guess)
        log_eta = numpy.log(eta)

        # Construct new hyperparam that consists of both eta and distance_scale
        hyperparam_full = numpy.r_[log_eta, distance_scale]

        # Compute first derivative w.r.t distance_scale
        der1_distance_scale = \
            ProfileLikelihood.likelihood_der1_distance_scale(
                    z, X, cov, hyperparam_full)

        # Jacobian only consists of the derivative w.r.t distance_scale
        jacobian = der1_distance_scale

        # print('scale: %f, eta: %f, jac: %f'
        #       % (distance_scale[0], eta, jacobian[0]))
        print(jacobian)

        if sign_switch:
            jacobian = -jacobian

        return jacobian

    # ==================
    # likelihood hessian
    # ==================

    @staticmethod
    def likelihood_hessian(z, X, cov, sign_switch, hyperparam):
        """
        Computes Hessian w.r.t eta, and if given, distance_scale.
        """

        # When profiling eta is enabled, derivative w.r.t eta is not needed.
        # Compute only Jacobian w.r.t distance_scale. Also, here, the input
        # hyperparam consists of only distance_scale (and not eta).
        if isinstance(hyperparam, list):
            hyperparam = numpy.array(hyperparam)
        distance_scale = numpy.abs(hyperparam)
        cov.set_distance_scale(distance_scale)

        # Find optimal eta
        eta = DoubleProfileLikelihood._find_optimal_eta(
                z, X, cov, distance_scale, log_eta_guess)
        log_eta = numpy.log(eta)

        # Construct new hyperparam that consists of both eta and distance_scale
        hyperparam_full = numpy.r_[log_eta, distance_scale]

        # Compute second derivative w.r.t distance_scale
        der2_distance_scale = \
                ProfileLikelihood.likelihood_der2_distance_scale(
                        z, X, cov, hyperparam)

        # Concatenate derivatives to form Hessian of all variables
        hessian = der2_distance_scale

        # if sign_switch:
        #     hessian = -hessian

        return hessian

    # ================
    # find optimal eta
    # ================

    def _find_optimal_eta(
            z,
            X,
            cov,
            distance_scale,
            log_eta_guess=0.0,
            optimization_method='Nelder-Mead'):
        """
        Finds optimal eta to profile it out of the log-likelihood.
        """

        # # Note: When using interpolation, make sure the interval below is
        # # exactly the end points of eta_i, not less or more.
        # min_eta_guess = numpy.min([1e-4, 10.0**log_eta_guess * 1e-2])
        # max_eta_guess = numpy.max([1e+3, 10.0**log_eta_guess * 1e+2])
        # interval_eta = [min_eta_guess, max_eta_guess]
        #
        # # Using root finding method on the first derivative w.r.t eta
        # result = ProfileLikelihood.find_likelihood_der1_zeros(
        #         z, X, cov.mixed_cor, interval_eta)
        # eta = result['hyperparam']['eta']

        cov.set_distance_scale(distance_scale)
       
        # optimization_method = 'Newton-CG'
        result = ProfileLikelihood.maximize_likelihood(
                z, X, cov,
                tol=1e-3,
                hyperparam_guess=[log_eta_guess],
                optimization_method=optimization_method)

        eta = result['hyperparam']['eta']
        return eta

    # ===================
    # maximize likelihood
    # ===================

    @staticmethod
    def maximize_likelihood(
            z,
            X,
            cov,
            tol=1e-3,
            hyperparam_guess=[0.1, 0.1],
            optimization_method='Nelder-Mead',
            verbose=False):
        """
        Maximizing the log-likelihood function over the space of parameters
        sigma and sigma0

        In this function, hyperparam = [sigma, sigma0].
        """

        # Keeping times
        initial_wall_time = time.time()
        initial_proc_time = time.process_time()

        # When profile eta is used, hyperparam only contains distance_scale
        log_eta_guess = 1.0

        # Partial function of likelihood with profiled eta. The input
        # hyperparam is only distance_scale, not eta.
        sign_switch = True
        likelihood_partial_func = partial(
                DoubleProfileLikelihood.likelihood, z, X,
                cov, sign_switch, log_eta_guess)

        # Partial function of Jacobian of likelihood (with minus sign)
        jacobian_partial_func = partial(
                DoubleProfileLikelihood.likelihood_jacobian, z,
                X, cov, sign_switch, log_eta_guess)

        # Partial function of Hessian of likelihood (with minus sign)
        # hessian_partial_func = partial(
        #         DoubleProfileLikelihood.likelihood_hessian, z
        #         X, cov, sign_switch, log_eta_guess)

        # Minimize
        res = scipy.optimize.minimize(
                likelihood_partial_func, hyperparam_guess,
                method=optimization_method, tol=tol, jac=jacobian_partial_func)
                # hess=hessian_partial_func)

        # Get the optimal distance_scale
        distance_scale = numpy.abs(res.x)

        # Find optimal eta with the given distance_scale
        eta = DoubleProfileLikelihood._find_optimal_eta(
                z, X, cov, distance_scale, log_eta_guess)

        # Find optimal sigma and sigma0 with the optimal eta
        sigma, sigma0 = ProfileLikelihood.find_optimal_sigma_sigma0(
                z, X, cov.mixed_cor, eta)
        max_lp = -res.fun

        # Adding time to the results
        wall_time = time.time() - initial_wall_time
        proc_time = time.process_time() - initial_proc_time

        # Output dictionary
        result = {
            'hyperparam':
            {
                'sigma': sigma,
                'sigma0': sigma0,
                'eta': eta,
                'distance_scale': distance_scale,
            },
            'optimization':
            {
                'max_likelihood': max_lp,
                'iter': res.nit,
            },
            'time':
            {
                'wall_time': wall_time,
                'proc_time': proc_time
            }
        }

        return result

    # ===============
    # plot likelihood
    # ===============

    @staticmethod
    def plot_likelihood(
            z,
            X,
            cov,
            result):
        """
        Plots log likelihood for distance_scale parameters.
        """

        dimension = cov.mixed_cor.cor.dimension

        if dimension == 1:
            DoubleProfileLikelihood.plot_likelihood_1d(z, X, cov, result)
        elif dimension == 2:
            DoubleProfileLikelihood.plot_likelihood_2d(z, X, cov, result)
        else:
            raise ValueError('Likelihood of only 1 and 2 dimensional cases ' +
                             'can be plotted.')

    # ==================
    # plot likelihood 1d
    # ==================

    @staticmethod
    def plot_likelihood_1d(
            z,
            X,
            cov,
            result=None):
        """
        Plots log likelihood versus sigma, eta hyperparam
        """

        load_plot_settings()

        # Generate lp for various distance scales
        distance_scale = numpy.logspace(-3, 2, 200)
        eta = numpy.zeros((distance_scale.size, ), dtype=float)
        lp = numpy.zeros((distance_scale.size, ), dtype=float)
        der1_lp = numpy.zeros((distance_scale.size, ), dtype=float)
        der1_lp_numerical = numpy.zeros((distance_scale.size-2, ), dtype=float)
        log_eta_guess = 1.0
        sign_switch = False

        fig, ax = plt.subplots(ncols=2, figsize=(11, 5))
        ax2 = ax[0].twinx()

        for j in range(distance_scale.size):
            cov.set_distance_scale(distance_scale[j])
            lp[j] = DoubleProfileLikelihood.likelihood(
                    z, X, cov, sign_switch, log_eta_guess,
                    distance_scale[j])
            der1_lp[j] = DoubleProfileLikelihood.likelihood_jacobian(
                    z, X, cov, sign_switch, log_eta_guess,
                    distance_scale[j])[0]
            eta[j] = DoubleProfileLikelihood._find_optimal_eta(
                    z, X, cov, distance_scale[j], log_eta_guess)

        # Numerical derivative of likelihood
        der1_lp_numerical = (lp[2:] - lp[:-2]) / \
                (distance_scale[2:] - distance_scale[:-2])

        # Exclude large eta
        eta[eta > 1e+16] = numpy.nan

        # Find maximum of lp
        max_index = numpy.argmax(lp)
        optimal_distance_scale = distance_scale[max_index]
        optimal_lp = lp[max_index]

        # Plot
        ax[0].plot(distance_scale, lp, color='black',
                label=r'$\ell(\hat{\eta}, \theta)$')
        ax[1].plot(
            distance_scale, der1_lp, color='black',
            label=
            r'$\frac{\mathrm{d} \ell(\hat{\eta}, \theta)}{\mathrm{d} \theta}$')
        ax[1].plot(
                distance_scale[1:-1], der1_lp_numerical, '--', color='black')
        ax2.plot(distance_scale, eta, '--', color='black',
                 label=r'$\hat{\eta}(\theta)$')
        ax[0].plot(optimal_distance_scale, optimal_lp, 'o', color='black',
                markersize=4, label=r'$\hat{\theta}$ (brute force)')

        if result is not None:
            opt_distance_scale = result['hyperparam']['distance_scale']
            opt_lp = result['optimization']['max_likelihood']
            ax[0].plot(opt_distance_scale, opt_lp, 'o', color='maroon',
                    markersize=4, label=r'$\hat{\theta}$ (optimized)')

        # Plot annotations
        ax[0].legend(loc='lower right')
        ax[1].legend(loc='lower right')
        ax2.legend(loc='upper right')
        ax[0].set_xscale('log')
        ax[1].set_xscale('log')
        ax[0].set_xlim([distance_scale[0], distance_scale[-1]])
        ax[1].set_xlim([distance_scale[0], distance_scale[-1]])
        ax2.set_xlim([distance_scale[0], distance_scale[-1]])
        ax2.set_ylim(bottom=0.0, top=None)
        ax[0].set_xlabel(r'$\theta$')
        ax[1].set_xlabel(r'$\theta$')
        ax[0].set_ylabel(r'$\ell(\hat{\eta}(\theta), \theta)$')
        ax[1].set_ylabel(
            r'$\frac{\mathrm{d}\ell(\hat{\eta}(\theta),' +
            r' \theta)}{\mathrm{d} \theta}$')
        ax2.set_ylabel(r'$\hat{\eta}(\theta)$')
        ax[0].set_title(r'Log likelihood function profiled for $\eta$')
        ax[1].set_title(r'Derivative of log likelihood function')
        ax[0].grid(True)
        ax[1].grid(True)

        plt.tight_layout()
        plt.show()

    # ==================
    # plot likelihood 2D
    # ==================

    @staticmethod
    def plot_likelihood_2d(
            z,
            X,
            cov,
            result=None):
        """
        Plots log likelihood versus sigma, eta hyperparam
        """

        load_plot_settings()

        eta = numpy.logspace(-3, 3, 100)
        distance_scale = numpy.logspace(-3, 2, 100)
        lp = numpy.zeros((distance_scale.size, eta.size), dtype=float)

        # Compute lp
        for i in range(distance_scale.size):
            mixed_cor.set_distance_scale(distance_scale[i])
            for j in range(eta.size):
                lp[i, j] = DoubleProfileLikelihood.likelihood(
                        z, X, cov, False, numpy.log10(eta[j]))

        # Convert inf to nan
        lp = numpy.where(numpy.isinf(lp), numpy.nan, lp)

        [distance_scale_mesh, eta_mesh] = numpy.meshgrid(distance_scale, eta)

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(numpy.log10(eta_mesh),
                               numpy.log10(distance_scale_mesh), lp.T,
                               linewidth=0, antialiased=True, alpha=0.9,
                               label=r'$\ell(\eta, \theta)$')
        fig.colorbar(surf, ax=ax)

        surf._facecolors2d = surf._facecolor3d
        surf._edgecolors2d = surf._edgecolor3d

        # Find max for each fixed eta
        opt_distance_scale1 = numpy.zeros((eta.size, ), dtype=float)
        opt_lp1 = numpy.zeros((eta.size, ), dtype=float)
        opt_lp1[:] = numpy.nan
        for j in range(eta.size):
            if numpy.all(numpy.isnan(lp[:, j])):
                continue
            max_index = numpy.nanargmax(lp[:, j])
            opt_distance_scale1[j] = distance_scale[max_index]
            opt_lp1[j] = lp[max_index, j]
        ax.plot3D(numpy.log10(eta), numpy.log10(opt_distance_scale1), opt_lp1,
                  color='red', label=r'$\max_{\theta} \ell_{\eta}(\theta)$')

        # Find max for each fixed distance_scale
        opt_eta2 = numpy.zeros((distance_scale.size, ), dtype=float)
        opt_lp2 = numpy.zeros((distance_scale.size, ), dtype=float)
        opt_lp2[:] = numpy.nan
        for i in range(distance_scale.size):
            if numpy.all(numpy.isnan(lp[i, :])):
                continue
            max_index = numpy.nanargmax(lp[i, :])
            opt_eta2[i] = eta[max_index]
            opt_lp2[i] = lp[i, max_index]
        ax.plot3D(numpy.log10(opt_eta2), numpy.log10(distance_scale), opt_lp2,
                  color='goldenrod',
                  label=r'$\max_{\eta} \ell_{\theta}(\eta)$')

        # Plot max of the whole 2D array
        max_indices = numpy.unravel_index(numpy.nanargmax(lp), lp.shape)
        opt_distance_scale = distance_scale[max_indices[0]]
        opt_eta = eta[max_indices[1]]
        opt_lp = lp[max_indices[0], max_indices[1]]
        ax.plot3D(numpy.log10(opt_eta), numpy.log10(opt_distance_scale),
                  opt_lp, 'o', color='red', markersize=6,
                  label=r'$\max_{\eta, \theta} \ell$ (by brute force on grid)')

        # Plot optimal point as found by the profile likelihood method
        if result is not None:
            opt_distance_scale = result['hyperparam']['distance_scale']
            opt_lp = result['optimization']['max_likelihood']

            ax.plot3D(numpy.log10(optimal_eta),
                      numpy.log10(optimal_distance_scale),
                      optimal_lp, 'o', color='magenta', markersize=6,
                      label=r'$\max_{\eta, \theta} \ell$ (by optimization)')

        # Plot annotations
        ax.legend()
        ax.set_xlim([numpy.log10(eta[0]), numpy.log10(eta[-1])])
        ax.set_ylim([numpy.log10(distance_scale[0]),
                    numpy.log10(distance_scale[-1])])
        ax.set_xlabel(r'$\log_{10}(\eta)$')
        ax.set_ylabel(r'$\log_{10}(\theta)$')
        ax.set_zlabel(r'$\ell(\eta, \theta)$')
        ax.set_title('Log Likelihood function')
        plt.show()
