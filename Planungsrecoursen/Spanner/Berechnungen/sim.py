from typing import Callable, Sequence
import numpy as np
from numpy.typing import ArrayLike
from tqdm import tqdm
import matplotlib.pyplot as plt

rk4_c_j = [1 / 6, 1 / 3, 1 / 3, 1 / 6]
rk4_b_j = [0, 1 / 2, 1 / 2, 1]
rk4_a_ij = [[0.0] * 4, [1 / 2, 0, 0, 0], [0, 1 / 2, 0, 0], [0, 0, 1, 0]]


def rk4_method(
    F: Callable[[float, ArrayLike], ArrayLike],
    y0: ArrayLike,
    t_vect: Sequence[float] = None,
    t0: float = None,
    t_max: float = None,
    e: float = None,
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

    for n in tqdm(range(1, N_t), desc="rk4-timeloop"):
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

def funcarray(*funcs):
    """
    A wrapper for code lengh reduction
    lets you input any amount of functions so that a y matrix can be given as input for the functions

    Returns:
        returns a lambda expression as a numpy array
    """
    return lambda t, y: np.array([f(t, y) for f in funcs])

def ODES(r1,r2,m,k,dT,T,w):
    theta = lambda t, y: y[1]
    theta_point = lambda t,y: ((2/(m*r2))* (dT*np.sin(w*t)+T) + ((k/m)*((r1)/r2)**2) *np.sin(y[0]))
    return funcarray(theta,theta_point)

def test_odes(m,k,F):
    x = lambda t,y: y[1]
    v = lambda t,y: F/m - (k/m)*y[0]
    return funcarray(x,v)

calc = True
if calc == True:
    t, y = rk4_method(
        F = ODES(0.05,0.1,0.020,0,0,0.100,0.5),
        y0=[0,0],
        t0 = 0 ,
        t_max = 1000,
        e=0.5
    )
#t , y = rk4_method(
#    test_odes(1,1,1),
#    y0 = [0,1],
#    t0 = 0, 
#    t_max=100,
#    e = 1e-4
#)
plt.plot(t,y[0])
plt.show()
plt.cla()
plt.plot(t,y[1])
plt.show()