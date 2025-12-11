# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
from typing import Tuple
import numpy as np
from scipy.integrate import solve_ivp as ode_solver
from scipy.special import fresnel

def spiral_ode(s: float, x0: float, y0: float, theta0: float, curvature_start: float, curvature_end: float, length: float) -> Tuple[float, float, float]:
    r"""
    Compute the spiral as solution of an Initial Value Problem.
    If the formulation of the curve is the following (k is curvature):

     k(s) = k0 + kdot s
                         /s 
     theta(s) = theta0 + | k(z) dz
                         /0
                  /s 
     x(s) = x0 + | cos(theta(z)) dz
                 /0
                  /s 
     y(s) = y0 + | sin(theta(z)) dz
                 /0

    where kdot = (k1 - k0) / L, the associated ODE is something on the line:

     k'(s) = kdot
     theta'(s) = k(s)
     x'(s) = cos(theta(s))
     y'(s) = sin(theta(s))

    the solution of the problem for the set of initial conditions (x0, y0, theta0, k0)
    gives us the position and orientation of the curve for an arbitrary s in the
    range [0, L] (inclusive). For numerical stability reasons, the actual formula used is 
    a scaled version with respect to L.

    Note: the curvilinear abscissa used as input is in the range [0, L]. If the spiral is
          one geometry in a complex plan view, the input s should be offset with respect to 
          the s0 value used to define the geometry

    :param s: curvilinear abscissa (it is internally clamped in [0, L]) [m]
    :param x0: initial x coordinate [m]
    :param y0: initial y coordinate [m]
    :param theta0: initial heading [rad]
    :param curvature_start: initial curvature (k(0)) [1/m^2]
    :param curvature_end: final curvature (k(L)) [1/m^2]
    :param length: length of the curve [m]
    :return: a tuple of final x coordinate, final y coordinate and final heading [m, m, rad]
    :raises ValueError: if length is less or equal than 0.0m
    """           
    if length <= 0.0:
        raise ValueError("length of a geometry cannot be <= 0")
    
    cdot = curvature_end - curvature_start

    def spiral_ode(s_, state):
        return np.array([
            np.cos(state[2]) * length, # x'(s)
            np.sin(state[2]) * length, # y'(s)
            state[3] * length,         # theta'(s)
            cdot])                     # k'(s)
    
    def clamp_s(s_):
        if s_ <= 0.0: return 0.0
        if s >= length: return 1.0
        return s_ / length

    result = ode_solver(spiral_ode, (0.0, clamp_s(s)), np.array([x0, y0, theta0, curvature_start]), rtol=1e-12, atol=1e-9)
    return tuple(result.y[0:3, -1])


def spiral_fresnel(s: float, x0: float, y0: float, theta0: float, curvature_start: float, curvature_end: float, length: float) -> Tuple[float, float, float]:
    r"""
    Evaluate the spiral in closed form. This solution is usually more efficient than
    the Final Value Problem ODE that is in formulated :py:`spiral_ode`, but it is more
    complex to be derived. Bare with ous for some more insight on how it is formulated.

    The equation of the curve still holds true:

     k(s) = k0 + sigma s
                         /s 
     theta(s) = theta0 + | k(z) dz
                         /0
                  /s 
     x(s) = x0 + | cos(theta(z)) dz
                 /0
                  /s 
     y(s) = y0 + | sin(theta(z)) dz
                 /0

    The first part of the function (before sigma calculation) is just bureaucratic stuff:
     * clamp the value of s in [0, L] inclusive
     * do not accept length <= 0
     * evaluate the curve when it has starting curvature and final curvature zero,
       which means the spiral is degenerate in a line (simple integrate the equations
       for curvature(s) = 0)
     * evaluate the curve when it has starting curvature and final curvature are equal,
       but not zero, which means the spiral is degenerate in a line (simple integrate the equations
       for curvature(s) = k0)

    After this initial part, there is the computation of the equation using Fresnel integrals,
    but the complex part is to understand how we obtained this formulation. We are not providing
    the full computation, but the major point to keep in mind to formulate the same equations.
    
     1. The formulation starts with the solution of the heading for the spiral in closed form
        (i.e. solving the integral) that is then manipulated in an alternative form:
    
        theta(s) = theta0 + k0 s + 0.5 sigma s^2 = 
                 = theta0 - 0.5 k0^2/sigma + 0.5 sigma (s + k0/sigma)^2 =
                 = alpha                   + 0.5 sigma (s + k0/sigma)^2
     
        (alpha is a constant value)

     2. The x, y coordinate can be seen as Real and Imaginary coordinates (multiplying the y by sqrt(-1) = i).
        Once this is done, it is simple to reformulate the vector from initial coordinate to final coordinates
        as a complex exponential integral (euler formula)

                                                  /s    i theta(z)
         Delta(s) = (x(s) - x0) + i (y(s) - y0) = |    e            dz
                                                 /0
       
     3. Plugging in the theta(s) in Delta(s) and applying the following coordinate transformation to the 
        integral:

         beta = sqrt(|sigma|/pi)
         t(z) = 1/beta * (z + k0 / sigma)    t(z=0) = t0   t(z=s) = ts
         dt = beta dz

        It emerges a pattern that can be associated to a Fresnel integral! 
        (https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.fresnel.html). Please
        remember that the scipy formula returns: fresnel(u) = sin, cos and it scales the input by pi/2

     4. Plugging all together, we obtain the equations evaluated by this function:

         x(s) = x0 + Re[Delta(s)]
         y(s) = y0 + Im[Delta(s)]

    Note: the curvilinear abscissa used as input is in the range [0, L]. If the spiral is
          one geometry in a complex plan view, the input s should be offset with respect to 
          the s0 value used to define the geometry
    
    :param s: curvilinear abscissa (it is internally clamped in [0, L]) [m]
    :param x0: initial x coordinate [m]
    :param y0: initial y coordinate [m]
    :param theta0: initial heading [rad]
    :param curvature_start: initial curvature (k(0)) [1/m^2]
    :param curvature_end: final curvature (k(L)) [1/m^2]
    :param length: length of the curve [m]
    :return: a tuple of final x coordinate, final y coordinate and final heading [m, m, rad]
    :raises ValueError: if length is less or equal than 0.0m
    """
    def clamp_s(s_):
        if s_ <= 0.0: return 0.0
        if s_ > length: return length
        return s_

    if length <= 0:
        raise ValueError("Length cannot be less or equal than zero")

    s = clamp_s(s)

    delta_curvature = curvature_end - curvature_start
    
    if np.isclose(curvature_start, 0.0) and np.isclose(delta_curvature, 0.0):
        # Degenerate in a line
        return x0 + s * np.cos(theta0), y0 + s * np.sin(theta0), theta0
    
    if np.isclose(delta_curvature, 0.0):
        # Degenerate in a circle
        theta1 = theta0 + curvature_start * s
        x = x0 + (np.sin(theta1) - np.sin(theta0)) / curvature_start
        y = y0 - (np.cos(theta1) - np.cos(theta0)) / curvature_start
        return x, y, theta1

    sigma = delta_curvature / length
    abs_sigma = abs(sigma)
    sign_sigma = 1.0 if sigma >= 0.0 else -1.0

    alpha = theta0 - ((0.5 * curvature_start * curvature_start) / (sigma))
    beta_inv = np.sqrt(abs_sigma) / np.sqrt(np.pi)
    t0 = curvature_start * beta_inv / sigma
    ts = (curvature_start + sigma * s) * beta_inv / sigma
    cos_alpha = np.cos(alpha)
    sin_alpha = np.sin(alpha)

    f_sin_t0, f_cos_t0 = fresnel(t0)
    f_sin_ts, f_cos_ts = fresnel(ts)
    delta_f_sin = f_sin_ts - f_sin_t0
    delta_f_cos = f_cos_ts - f_cos_t0

    theta = theta0 + curvature_start * s + 0.5 * sigma * s * s
    delta_x = (cos_alpha * delta_f_cos - sin_alpha * sign_sigma * delta_f_sin) / beta_inv
    delta_y = (sin_alpha * delta_f_cos + cos_alpha * sign_sigma * delta_f_sin) / beta_inv

    return x0 + delta_x, y0 + delta_y, theta

spiral = spiral_fresnel