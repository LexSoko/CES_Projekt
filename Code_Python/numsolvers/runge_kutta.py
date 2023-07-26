from typing import Callable, Sequence
import numpy as np
from numpy.typing import ArrayLike
from tqdm import tqdm

rk4_c_j = [1 / 6, 1 / 3, 1 / 3, 1 / 6]
rk4_b_j = [0, 1 / 2, 1 / 2, 1]
rk4_a_ij = [[0.0] * 4, [1 / 2, 0, 0, 0], [0, 1 / 2, 0, 0], [0, 0, 1, 0]]

# koefficients for the adaptive Runge-kutta-Fehlberg method
rk45_ad_c_j = [0, 1 / 4, 3 / 8, 12 / 13, 1, 1 / 2]
rk45_ad_b_j = [16 / 135, 0, 6656 / 12825, 28561 / 56430, -9 / 50, 2 / 55]
rk45_ad_bs_j = [25 / 216, 0, 1408 / 2565, 2197 / 4104, -1 / 5, 0]
rk45_ad_a_ij = [
    [0.0] * 6,
    [1 / 4, 0, 0, 0, 0, 0],
    [3 / 32, 9 / 32, 0, 0, 0, 0],
    [1932 / 2197, -7200 / 2197, 7296 / 2197, 0, 0, 0],
    [439 / 216, -8, 3680 / 513, -845 / 4104, 0, 0],
    [-8 / 27, 2, -3544 / 2565, 1859 / 4104, -11 / 40, 0],
]


def rk4_method(
    F: Callable[[float, ArrayLike], ArrayLike],
    y0: ArrayLike,
    t_vect: Sequence[float] = None,
    t0: float = None,
    t_max: float = None,
    e: float = None,
    disable=True,
):
    """
    Runge Kutta 4th Order

    calculates RungeKutta 4th order with fixed timesteps.
    Either accepts a prepared time point list t_vec or otherwise
    a starttime t0 endtime t_max and a time intervall

    Arguments:
        F -- Functional F(t,y(t)) for Equation y`(t) = F(t,y(t))
        y0 -- start condition vector

    Keyword Arguments:
        t_vect -- time points (default: {None}) should be in form array([t0, t1, t2,...,tn])
        t0 -- start time (default: {None})
        t_max -- end time (default: {None})
        e -- time intervall (default: {None})

    Returns:
        tuple (t_vect, y(t) as numpy array)
    """
    # time checking
    if t_vect is not None:
        # func is with t_vect
        tarr = t_vect
        t0 = t_vect[0]
        e = tarr[1] - tarr[0]
        t_max = t_vect[-1]
    elif t0 is not None and t_max is not None and e is not None:
        # we have to create t_vect
        tarr = np.arange(t0, t_max + e, e)
    else:
        # time params missing
        return None

    # basic dimensionalities
    N_t = np.size(tarr, 0)
    N_dim = len(y0)

    # prepeation
    y = np.zeros((N_t, N_dim))
    y[0] = y0

    for n in tqdm(range(1, N_t), desc="rk4-timeloop", disable=False):
        cur_t = tarr[n - 1]
        cur_y = y[n - 1]
        # for j in range(len(c)):
        #    k.append(F(cur_t + c[i]*e,))
        k1 = F(cur_t, cur_y)
        k2 = F(cur_t + rk4_c_j[1] * e, cur_y + e * (rk4_a_ij[1][0] * k1))
        k3 = F(
            cur_t + rk4_c_j[2] * e,
            cur_y + e * (rk4_a_ij[2][0] * k1 + rk4_a_ij[2][1] * k2),
        )
        k4 = F(
            cur_t + rk4_c_j[3] * e,
            cur_y
            + e
            * (
                rk4_a_ij[3][0] * k1 + rk4_a_ij[3][1] * k2 + rk4_a_ij[3][2] * k3
            ),
        )

        y[n] = cur_y + (1 / 6) * (k1 + 2 * k2 + 2 * k3 + k4) * e

        tarr[n] = cur_t + e

    return tarr, y.T


def rk4_method_asg3(
    F: Callable[[float, ArrayLike], ArrayLike],
    y0: ArrayLike,
    t_vect: Sequence[float] = None,
    t0: float = None,
    t_max: float = None,
    e: float = None,
    epsilon: float = None,
    v: Callable[[float, ArrayLike], ArrayLike] = None,
):
    """
    Runge Kutta 4th Order

    calculates RungeKutta 4th order with fixed timesteps.
    Either accepts a prepared time point list t_vec or otherwise
    a starttime t0 endtime t_max and a time intervall

    Arguments:
        F -- Functional F(t,y(t)) for Equation y`(t) = F(t,y(t))
        y0 -- start condition vector

    Keyword Arguments:
        t_vect -- time points (default: {None}) should be in form array([t0, t1, t2,...,tn])
        t0 -- start time (default: {None})
        t_max -- end time (default: {None})
        e -- time intervall (default: {None})

    Returns:
        tuple (t_vect, y(t) as numpy array)
    """
    # time checking
    if t_vect is not None:
        # func is with t_vect
        tarr = t_vect
        t0 = t_vect[0]
        e = tarr[1] - tarr[0]
        t_max = t_vect[-1]
    elif t0 is not None and t_max is not None and e is not None:
        # we have to create t_vect
        tarr = np.arange(t0, t_max + e, e)
    else:
        # time params missing
        return None

    # basic dimensionalities
    N_t = np.size(tarr, 0)
    N_dim = np.size(y0)

    # prepeation
    y = np.zeros((N_t, N_dim))
    y[0] = y0

    for n in tqdm(range(1, N_t), desc="rk4-timeloop", disable=True):
        cur_t = tarr[n - 1]
        cur_y = y[n - 1]
        # for j in range(len(c)):
        #    k.append(F(cur_t + c[i]*e,))
        k1 = F(cur_t, cur_y, epsilon, v)
        k2 = F(
            cur_t + rk4_c_j[1] * e,
            cur_y + e * (rk4_a_ij[1][0] * k1),
            epsilon,
            v,
        )
        k3 = F(
            cur_t + rk4_c_j[2] * e,
            cur_y + e * (rk4_a_ij[2][0] * k1 + rk4_a_ij[2][1] * k2),
            epsilon,
            v,
        )
        k4 = F(
            cur_t + rk4_c_j[3] * e,
            cur_y
            + e
            * (
                rk4_a_ij[3][0] * k1 + rk4_a_ij[3][1] * k2 + rk4_a_ij[3][2] * k3
            ),
            epsilon,
            v,
        )

        y[n] = cur_y + (1 / 6) * (k1 + 2 * k2 + 2 * k3 + k4) * e

        tarr[n] = cur_t + e

    return tarr, y.T


def expl_rk_method(
    F: Callable[[float, ArrayLike], ArrayLike],
    y0: ArrayLike,
    a_ij: ArrayLike,
    bj: ArrayLike,
    cj: ArrayLike,
    t_vect: Sequence[float] = None,
    t0: float = None,
    t_max: float = None,
    e: float = None,
):
    """
    Runke Kutta n-th order

    Calculates Runge-Kutta n-th order with fixed timesteps.
    Either accepts a prepared time point list t_vec or otherwise
    a starttime t0, endtime t_max and a time intervall.
    Determination of order n happens through the coefficients
    a_ij, bj and cj, so they have to be provided.

    Arguments:
        F -- Functional F(t,y(t)) for Equation y`(t) = F(t,y(t))
        y0 -- start condition vector
        a_ij -- coefficient matrix
        bj -- coeff. vector
        cj -- coeff. vector

    Keyword Arguments:
        t_vect -- time points should be in form array([t0, t1, t2,...,tn]) (default: {None})
        t0 -- start time (default: {None})
        t_max -- end time (default: {None})
        e -- time intervall (default: {None})

    Returns:
        tuple (t_vect, y(t) as numpy array)
    """

    # time checking
    if t_vect is not None:
        # func is called with t_vect
        tarr = t_vect
        t0 = t_vect[0]
        e = tarr[1] - tarr[0]
        t_max = t_vect[-1]
    elif t0 is not None and t_max is not None and e is not None:
        # create t_vect
        tarr = np.arange(t0, t_max + e, e)
    else:
        # time parameters missing
        print("from expl_rk_method(): given time not ok")
        return None

    # coefficient checking
    if (
        len(cj) != len(bj)
        or len(bj) != len(a_ij[0])
        or len(cj) != len(a_ij[0])
    ):
        print("from expl_rk_method(): given coefficients not ok")
        return None

    # basic dimensionalities
    N_t = len(tarr)
    N_dim = np.size(y0)
    N_coef_elements = len(bj)

    # preperation
    y = np.zeros((N_t, N_dim))
    y[0] = y0
    k = np.zeros((N_coef_elements, N_dim))

    for n in tqdm(range(0, N_t - 1), desc="rk4-timeloop"):
        current_t = tarr[n]
        current_y = y[n]
        for s in range(N_coef_elements):
            k[s] = F(
                current_t + cj[s],
                current_y
                + e * np.sum([a_ij[s][l] * k[l] for l in range(s)], axis=0),
            )
        #############################################################
        # k_end = np.zeros(N_dim)
        # for i in range(N_coef_elements):
        #    k_end += bj[i] * k[i]
        k_end = np.sum([bj[i] * k[i] for i in range(N_coef_elements)], axis=0)
        ##############################################################
        y[n + 1] = current_y + e * k_end
        tarr[n + 1] = current_t + e

    return tarr, y.T


def adpt_rk4_method(
    F: Callable[[float, ArrayLike], ArrayLike],
    y0: ArrayLike,
    t0: float,
    t_max: float,
    e0: float,
    err_max=10e-5,
    dt_min=10e-8,
    p_dt=4.0,
):
    """
    Adaptive Runke Kutta 4-th Order

    Calculates Runge-Kutta 4-th in paralell with RK-5 for a timepoint by using
    the Runge-kutta-Fehlberg method Butcher Table (see https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods#Adaptive_Runge%E2%80%93Kutta_methods).
    Now we have two results, the y(t_n) 4-th order and the y(t_n) 5-th of which
    The Difference is an aproximation of the error, which lies in the same base
    10 order like the real error. If this error is bigger than err_max, the
    timestep h will be decreased by dividing through the control parameter p_dt
    and the calculation of the current timepoint is recalculated until the error
    is low enough. If the error is to low, the timestep h will be increased by
    multiplying with p_dt, so that the algorithm speeds up.\n
    Only accepts a starttime t0 endtime t_max and a staring time intervall e0.
    To debug issues this method also gives back the estimated error on all
    elements of y(t) and the number of recalculations for one timepoint.


    Arguments:
        F -- Functional F(t,y(t)) for Equation y`(t) = F(t,y(t))\n
        y0 -- start condition vector

    Keyword Arguments:
        t0 -- start time (default: {None})\n
        t_max -- end time (default: {None})\n
        e0 -- starting time intervall (default: {None})\n
        err_max -- maximal allowed error (default: {10e-5})\n
        dt_min -- minimal allowed timestep (default: {10e-8})\n
        p_dt -- control parameter for time-step change (default: {4.0})\n

    Returns:
        tuple:\n
        t_vect -- time series for time variable as np array
            with shape (number_t)\n
        y(t) -- calculated datapoints as timeseries and as np array
            with shape (dim_y,number_t)\n
        it_per_t_n -- counter how often rk had to be repeated per datapoint as
            timeseries as np array with shape (number_t)\n
        err_per_t_n -- erstimated error vector values as timeseries and as np
            array with shape (dim_y,number_t)
    """
    # lets you evaluate alle Funcs in FuncaArray for same input

    # time checking
    if t0 is None or t_max is None or e0 is None:
        # time params missing
        print("from expl_rk_method(): given time not ok")
        return None

    # basic dimensionalities
    N_dim = np.size(y0)

    # preperation
    y = [y0]
    t = [t0]
    k = [y0] * 6

    # control value for error checking
    p_err = 0.25

    # running variables
    h = e0  # current timestep
    err = 1.0  # estimated error vector
    t_n = t0  # current time
    y_n = y0  # current phasespace vector values
    k1 = 0
    k2 = 0
    k3 = 0
    k4 = 0
    k5 = 0
    k6 = 0

    # debug variables
    # how much iteration the adaptive algorithm needs to calculate one
    # single datapoint as timeseries
    it_per_t_n = [0]
    # the estimated error time series
    err_per_t_n = [np.array([0.0, 0.0, 0.0, 0.0])]

    # we have to preperate the progress bar in a different way here, bc we use
    # a while loop
    pbar = tqdm(desc="adpt-rk-loop", total=int(t_max))
    while t_n < t_max:
        iter = 0
        while True:
            iter = iter + 1
            # calc k vectors
            k1 = F(t_n, y_n)
            k2 = F(
                t_n + rk45_ad_c_j[1] * h, y_n + h * (rk45_ad_a_ij[1][0] * k1)
            )
            k3 = F(
                t_n + rk45_ad_c_j[2] * h,
                y_n + h * (rk4_a_ij[2][0] * k1 + rk45_ad_a_ij[2][1] * k2),
            )
            k4 = F(
                t_n + rk45_ad_c_j[3] * h,
                y_n
                + h
                * (
                    rk45_ad_a_ij[3][0] * k1
                    + rk45_ad_a_ij[3][1] * k2
                    + rk45_ad_a_ij[3][2] * k3
                ),
            )
            k5 = F(
                t_n + rk45_ad_c_j[4] * h,
                y_n
                + h
                * (
                    rk45_ad_a_ij[4][0] * k1
                    + rk45_ad_a_ij[4][1] * k2
                    + rk45_ad_a_ij[4][2] * k3
                    + rk45_ad_a_ij[4][3] * k4
                ),
            )
            k6 = F(
                t_n + rk45_ad_c_j[5] * h,
                y_n
                + h
                * (
                    rk45_ad_a_ij[5][0] * k1
                    + rk45_ad_a_ij[5][1] * k2
                    + rk45_ad_a_ij[5][2] * k3
                    + rk45_ad_a_ij[5][3] * k4
                    + rk45_ad_a_ij[5][4] * k5
                ),
            )
            # calculate estimated error vector
            err = np.abs(
                h
                * (
                    (rk45_ad_b_j[0] - rk45_ad_bs_j[0]) * k1
                    + (rk45_ad_b_j[1] - rk45_ad_bs_j[1]) * k2
                    + (rk45_ad_b_j[2] - rk45_ad_bs_j[2]) * k3
                    + (rk45_ad_b_j[3] - rk45_ad_bs_j[3]) * k4
                    + (rk45_ad_b_j[4] - rk45_ad_bs_j[4]) * k5
                    + (rk45_ad_b_j[5] - rk45_ad_bs_j[5]) * k6
                )
            )

            # exit conditions for error loop
            if np.all(err <= err_max) or h <= dt_min:
                break
            else:
                h = h / p_dt

        t_np1 = t_n + h

        y_np1 = y_n + h * (
            rk45_ad_bs_j[0] * k1
            + rk45_ad_bs_j[1] * k2
            + rk45_ad_bs_j[2] * k3
            + rk45_ad_bs_j[3] * k4
            + rk45_ad_bs_j[4] * k5
            + rk45_ad_bs_j[5] * k6
        )

        t.append(t_np1)
        y.append(y_np1)
        it_per_t_n.append(iter)
        err_per_t_n.append(err)
        t_n = t_np1
        y_n = y_np1

        pbar.update(h)
        # condition to increment h when accuracy is to good
        if np.all(err < (err_max * p_err)):
            h = h * p_dt

    return (
        np.asarray(t),
        np.stack(y, axis=0).T,
        np.asarray(it_per_t_n),
        np.stack(err_per_t_n, axis=0).T,
    )
