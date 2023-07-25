#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Cranck-Nicolson Method

**** README: ****
* MathTeX notation is used in comment formula explanations!
"""


############################## imports #######################################
import numpy as np
from tqdm import tqdm
from typing import Callable, Sequence

######################### module level dunders ###############################
__author__ = "Max Jost, Aleksey Sokolov, Martin Ferdinand Steiner"

############################# functions ######################################

m = 1  # mass of particle
hbar = 1  # plancks constant


def crack_nicolson(
    Nx: int, dx: float, Nt: int, dt: float, psi0: list, V: list
):
    """
    Cranck-Nicolson Method for solving timedepending differential Equations

    This function takes psi0 and the Potential V as lists

    Arguments:
        Nx -- Number of Space-Gridpoints
        dx -- spacing between Space-Gridpoints
        Nt -- Number of Time-Gridpoints
        dt -- spacing between Time-Gridpoints
        psi0 -- the wave function at t = 0 as thhe initial condition
        V -- Potential

    Returns:
        psi(x,t) list(list())
    """

    a_k_func = lambda Vk, dx_a, dt_a: 2 * (
        1
        + ((m * dx_a**2) / (hbar**2)) * Vk
        - (1j * 2 * m * dx_a**2) / (hbar * dt_a)
    )

    Omega_func = lambda Vk, dx_a, dt_a: 2 * (
        1
        + ((m * dx_a**2) / (hbar**2)) * Vk
        + (1j * 2 * m * dx_a**2) / (hbar * dt_a)
    )

    a_k = np.squeeze(np.zeros((1, Nx), dtype=np.complex_))

    a_k[1] = a_k_func(V[1], dx, dt)

    for k in tqdm(range(2, Nx - 1), desc="ak-loop"):
        a_k[k] = a_k_func(V[k], dx, dt) - 1 / a_k[k - 1]

    psi = np.zeros((Nt, Nx), dtype=np.complex_)
    psi[0] = psi0
    psi[0][0] = 0 + 0j
    psi[0][Nx - 1] = 0 + 0j
    for n in tqdm(range(0, Nt - 1), desc="time-loop"):
        Omega = np.squeeze(np.zeros((1, Nx), dtype=np.complex_))
        b_n = np.squeeze(np.zeros((1, Nx), dtype=np.complex_))
        for k in range(1, Nx - 1):
            Omega[k] = Omega_func(V[k], dx, dt) * psi[n][k] - (
                psi[n][k - 1] + psi[n][k + 1]
            )
        b_n[1] = Omega[1]
        for k in range(2, Nx - 1):
            b_n[k] = b_n[k - 1] / a_k[k - 1] + Omega[k]

        k_index = np.arange(1, Nx - 1, 1)
        k_index = k_index[::-1]

        psi[n + 1][0] = 0
        psi[n + 1][Nx - 1] = 0
        for k in k_index:
            psi[n + 1][k] = (1 / a_k[k]) * (psi[n + 1][k + 1] - b_n[k])

    return psi


def crack_nicolson_func(
    Nx: int,
    dx: float,
    Nt: int,
    dt: float,
    psi_0: Callable,
    V_0: Callable,
    shift_x: float = 0.0,
):
    """
    Cranck-Nicolson Method for solving timedepending differential Equations

    This function takes psi0 and the Potential V as functions

    Arguments:
        Nx -- Number of Space-Gridpoints
        dx -- spacing between Space-Gridpoints
        Nt -- Number of Time-Gridpoints
        dt -- spacing between Time-Gridpoints
        psi0 -- the wave function at t = 0 as the initial condition
        V -- Potential Function handle

    Returns:
        psi(x,t) list(list())
    """
    x_grid = np.arange((1 - Nx) * dx / 2, Nx * dx / 2, dx) + shift_x
    t_grid = np.arange(0, Nt * dt, dt)
    psi0 = psi_0(x_grid)
    V = V_0(x_grid)

    a_k_func = lambda Vk, dx_a, dt_a: 2 * (
        1
        + ((m * dx_a**2) / (hbar**2)) * Vk
        - (1j * 2 * m * dx_a**2) / (hbar * dt_a)
    )

    Omega_func = lambda Vk, dx_a, dt_a: 2 * (
        1
        + ((m * dx_a**2) / (hbar**2)) * Vk
        + (1j * 2 * m * dx_a**2) / (hbar * dt_a)
    )

    a_k = np.squeeze(np.zeros((1, Nx), dtype=np.complex_))

    a_k[1] = a_k_func(V[1], dx, dt)

    for k in tqdm(range(2, Nx - 1), desc="ak-loop"):
        a_k[k] = a_k_func(V[k], dx, dt) - 1 / a_k[k - 1]

    psi = np.zeros((Nt, Nx), dtype=np.complex_)
    psi[0] = psi0
    psi[0][0] = 0 + 0j
    psi[0][Nx - 1] = 0 + 0j
    for n in tqdm(range(0, Nt - 1), desc="time-loop"):
        Omega = np.squeeze(np.zeros((1, Nx), dtype=np.complex_))
        b_n = np.squeeze(np.zeros((1, Nx), dtype=np.complex_))
        for k in range(1, Nx - 1):
            Omega[k] = Omega_func(V[k], dx, dt) * psi[n][k] - (
                psi[n][k - 1] + psi[n][k + 1]
            )
        b_n[1] = Omega[1]
        for k in range(2, Nx - 1):
            b_n[k] = b_n[k - 1] / a_k[k - 1] + Omega[k]

        k_index = np.arange(1, Nx - 1, 1)
        k_index = k_index[::-1]

        psi[n + 1][0] = 0
        psi[n + 1][Nx - 1] = 0
        for k in k_index:
            psi[n + 1][k] = (1 / a_k[k]) * (psi[n + 1][k + 1] - b_n[k])

    return psi, x_grid, t_grid
