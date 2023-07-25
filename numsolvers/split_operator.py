#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Assignment 3 Task 3 Split Operator Method
"""


############################## imports #########################################
import numpy as np
from numpy.fft import fft, ifft as inv_fft
import numpy.typing as nptyp
from tqdm import tqdm
from typing import Callable, List, Tuple

######################### module level dunders #################################
__author__ = "Max Jost, Aleksey Sokolov, Martin Ferdinand Steiner"

# natural unit and other constants
h = c = 1.0
m = 1.0


def op_dt(op, dt):
    """Time Evolution Operator"""
    return np.exp(-(1j / h) * op * dt)


def op_split_psi(V, T, Psi, dt=1.0):
    """Split Operator Method"""
    # act on psi with "half" potential time dev operator in REAL SPACE
    psi_x_1 = op_dt(V / 2, dt) * Psi
    # transform REAL SPACE -> MOMENTUM SPACE
    psi_q_1 = fft(psi_x_1)
    # act on psi with kinetic time dev operator in MOMENTUM SPACE
    psi_q_fin = op_dt(T, dt) * psi_q_1
    # transform MOMENTUM SPACE -> REAL SPACE
    psi_x_2 = inv_fft(psi_q_fin)
    # act on psi with second "half" potential time dev operator in REAL SPACE
    psi_x_fin = op_dt(V / 2, dt) * psi_x_2

    return psi_x_fin


def exec_split_operator_method(
    N_x: int,
    d_x: float,
    N_t: int,
    d_t: float,
    psi_0: Callable[[nptyp.NDArray], nptyp.NDArray],
    V: Callable[[nptyp.NDArray], nptyp.NDArray],
    T: Callable[[nptyp.NDArray], nptyp.NDArray] = (
        lambda q_grid, m=1: q_grid**2 / (2 * (m))
    ),
    shift_x: float = 0.0,
) -> Tuple[nptyp.NDArray, List, List[nptyp.NDArray]]:
    """
    Executes the calculations of the wave function time development on a (x,t) grid with given specifications.
    Only for time independend potential and kinetic operators

    Arguments:
        N_x -- number of datapoints on x-grid
        d_x -- x-grid intervall
        N_t -- number of datapoints on t-grid
        d_t -- t-grid intervall
        psi_0 -- function handle for wafefunction on x-grid
        V -- function handle for potential operator on x-grid (real space)

    Keyword Arguments:
        T -- Kinetic Operator in Momentum space (default: {q_grid=calculated fromx_grid specs, m=1, T = q_grid**2/(2 * m)})

    Returns:
        Tuple[NDArray, List, List[NDArray]] -- [x_grid,t_grid,psi_time_dev]
        x_grid -- the x_grid (real space grid) as NDArray
        t_grid -- the time grid
        psi_time_dev -- the time developed wafefunction as a list of NDArrays
    """
    # real space, momentum space and time space setup
    # q space needs to be shifted weirdly, so that the np.fft works correctly
    x_grid = np.arange((1 - N_x) * d_x / 2, N_x * d_x / 2, d_x) + shift_x

    d_q = 2 * np.pi / (d_x * N_x)
    q_grid = d_q * np.concatenate(
        (np.arange(0.0, N_x / 2), np.arange(-N_x / 2, 0.0))
    )

    t_grid = np.arange(0, N_t + 1) * d_t

    # calculate operators and wave function
    V_x = V(x_grid)
    T_q = T(q_grid)
    psi_t0 = psi_0(x_grid)

    # calculation of the psi time evolution
    psi = []
    psi_t = psi_t0
    psi.append(psi_t)
    for t in tqdm(t_grid):
        psi_t = op_split_psi(V_x, T_q, psi_t, dt=d_t)
        psi.append(psi_t)

    return x_grid, t_grid, psi
