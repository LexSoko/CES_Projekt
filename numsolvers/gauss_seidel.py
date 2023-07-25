#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Gauss-Seidel metod

**** README: ****
* MathTeX notation is used in comment formula explanations!
"""


############################## imports #######################################
import numpy as np
import copy
from tqdm import tqdm

######################### module level dunders ###############################
__author__ = "Max Jost, Aleksey Sokolov, Martin Ferdinand Steiner"

############################# functions ######################################


def gauss_seidel_method(
    A,
    b,
    conv_crit=10e-10,
    abort_crit=10e5,
    caldiff=False,
    div_crit=10e100,
    disable_ldb=False,
    disable_gs_errorbar=False,
):
    """
    Gauss-Seidel method

    Gauss-Seidel method for solving symetric linear equation systems.
    Convergates if A is positiv definit

    Arguments:
        A(array) -- Symetrical (n x n) 2D-Array, with no zeros on the diagonal
        b(array) -- 1D-Array of size n

    Keyword Arguments:
        conv_crit(float) -- absolut error between x**(p) and x**(p-1) below which convergenz is asumed (default: {10e-10})
        abort_crit(float) -- max. number of iterations until function is stopped (default: {10e5})
        caldiff(bool) -- If True, function will also calculate the L2-norm of the differenc between b and b**(p) (default: {False})
        div_crit(float) -- maximal value for |x^p-x^(p-1)|, afterwards the calculation is considerd divergent
        disable_ldb(bool) -- If True, no loadingbars whil be displayed while calculating

    Returns:
        x(array) -- solution vector
        a(bool) -- status parameter; when False, function did not convergate, or function stopped due to itteration max.
        b_diff_norm(array) -- L2-norm of the differenc between b and b**(p) for each iteration; only given if calldiff == True
    """
    rows, cols = np.shape(A)

    # check if array is symetrical
    if rows != cols:
        print("Error gauss_seidel_method: Given matrix A is not symetrical")
        return

    n = rows

    # get the diagonal of A as an numpy array
    A_dia = []
    for i in range(0, n):
        A_dia.append(A[i][i])
    A_dia = np.array(A_dia)

    # check if any of the diagonal values is 0
    if np.any(A_dia == 0):
        print("Error: Given Matrix A has 0 as its value on the diagonal")
        return

    x = [1.0] * n  # created starting vektor
    x = np.array(x, dtype=np.complex_)

    err = np.array(
        conv_crit + 1
    )  # create starting error, which is bigger than the convergenc criteria

    b_diff_norm = []
    p = 0  # p is the iteration count
    # main progress bar
    pbar = tqdm(
        desc="gs-error-bar",
        disable=disable_gs_errorbar,
        total=(1.0 - conv_crit),
        miniters=10,
    )

    while (
        np.any(err > conv_crit) and np.any(err < div_crit) and p < abort_crit
    ):
        x_p_1 = copy.deepcopy(x)
        sum1 = 0
        sum2 = 0
        for i in tqdm(
            range(0, n), desc="gauss_seidel row-loop", disable=disable_ldb
        ):
            # calculate the two summs of the gauss seidl formula
            sum1, sum2 = summs2(A, n, i, x, sum1, sum2)

            x[i] = (b[i] - sum1 - sum2) / A[i][i]

            sum1 = 0
            sum2 = 0

        # absolut error
        dx = np.abs(x - x_p_1)
        err = dx

        # rel error
        dx_r = np.real(dx)
        x_r = np.real(x)
        r_err = np.abs(
            np.divide(dx_r, x_r, out=np.zeros_like(dx_r), where=x_r != 0)
        )
        r_err_max = r_err.max()
        pbar.n = 1.0 - r_err_max
        pbar.refresh()

        # calculate differenz between current b and real b
        if caldiff:
            b_diff_norm.append(np.linalg.norm(np.dot(A, x) - b))
        if any(ele == np.inf for ele in b_diff_norm) or any(
            ele == np.nan for ele in b_diff_norm
        ):
            p = abort_crit

        p += 1

    if p < abort_crit:
        a = True  # the algorithm calculated the result within the given iteration max
    else:
        a = False  # the algorithm did not calculated the result within the given iteration max

    if caldiff:
        b_diff_norm = np.array(b_diff_norm)
        b_diff_norm = np.nan_to_num(b_diff_norm, posinf=1.7e155)
        return x, a, b_diff_norm

    return x, a


def gauss_seidel_method_nonzero(
    A,
    b,
    nonzero_indizes_list,
    conv_crit=10e-10,
    abort_crit=10e5,
    caldiff=False,
    div_crit=10e100,
    disable_ldb=False,
    disable_gs_errorbar=False,
    binding_x=None,
    binding_mask=None,
):
    """
    Improved Gauss-Seidel method

    Gauss-Seidel method for solving symetric linear equation systems.
    Convergates if A is positiv definit.

    Improvements:
        nonzero optimization -- the two summs of the gauss seidl formula only
        summ over indices, where the corresponting matrix element is not zero.
        This feature requires passing of the nonzero_indizes_list.
        solution vector constraints -- gives the posibility to bind certain
        elements of the solution vector to certain values.
        This feature requires passing the binding_x and binding_mask.

    Arguments:
        A(array) -- Symetrical (n x n) 2D-Array, with no zeros on the diagonal
        b(array) -- 1D-Array of size n
        k_nb_list -- list of all neibouring indices for given k

    Keyword Arguments:
        conv_crit(float) -- absolut error between x**(p) and x**(p-1) below which convergenz is asumed (default: {10e-10})
        abort_crit(float) -- max. number of iterations until function is stopped (default: {10e5})
        caldiff(bool) -- If True, function will also calculate the L2-norm of the differenc between b and b**(p) (default: {False})
        div_crit(float) -- maximal value for |x^p-x^(p-1)|, afterwards the calculation is considerd divergent
        disable_ldb(bool) -- If True, no solution element index driven loadingbars will be displayed while calculating
        disable_gs_errorbar(bool) -- If True, no iteration error driven loadingbars will be displayed while calculating
        binding_x(1D array,float) -- the solution vector with the bound solution values
        binding_mask(1D array,bool) -- boolean mask for the solution vector, true where value is bound, false where it's not bound

    Returns:
        x(array) -- solution vector
        a(bool) -- status parameter; when False, function did not convergate, or function stopped due to itteration max.
        b_diff_norm(array) -- L2-norm of the differenc between b and b**(p) for each iteration; only given if calldiff == True
    """

    # binding flag
    bound_system = True
    if binding_mask is None or binding_x is None:
        bound_system = False

    rows, cols = np.shape(A)

    # check if array is symetrical
    if rows != cols:
        print("Error gauss_seidel_method: Given matrix A is not symetrical")
        return

    n = rows

    # get the diagonal of A as an numpy array
    A_dia = []
    for i in range(0, n):
        A_dia.append(A[i][i])
    A_dia = np.array(A_dia)

    # check if any of the diagonal values is 0
    if np.any(A_dia == 0):
        print("Error: Given Matrix A has 0 as its value on the diagonal")
        return

    x = [1.0] * n  # created starting vektor
    x = np.array(x, dtype=np.complex_)
    if bound_system:
        x = np.where(binding_mask, binding_x, x)

    err = np.array(
        conv_crit + 1
    )  # create starting error, which is bigger than the convergenc criteria

    b_diff_norm = []
    p = 0  # p is the iteration count
    # main progress bar
    pbar = tqdm(
        desc="gs-error-bar",
        disable=disable_gs_errorbar,
        total=(1.0 - conv_crit),
        miniters=10,
    )

    # prepare nonzero indices lists for the two sums of the gauss seidl formula
    sum1_nonzero_indices_lists = []
    sum2_nonzero_indices_lists = []
    for j, nonzeros in enumerate(nonzero_indizes_list):
        nz_arr = np.array(nonzeros)
        sum1_indices = np.array(np.where(nz_arr < j))
        sum2_indices = np.array(np.where(nz_arr > j))

        sum1_nonzero_indices_lists.append(
            np.array(nonzero_indizes_list[j])[sum1_indices]
        )
        sum2_nonzero_indices_lists.append(
            np.array(nonzero_indizes_list[j])[sum2_indices]
        )

    # prepare index list only containing non bound solution vector indices
    if bound_system:
        k_unbound = [k for k in range(0, n) if binding_mask[k] == False]
    else:
        k_unbound = [k for k in range(0, n)]

    while (
        np.any(err > conv_crit) and np.any(err < div_crit) and p < abort_crit
    ):
        x_p_1 = copy.deepcopy(x)
        sum1 = 0
        sum2 = 0
        for i in k_unbound:

            # calculate the two summs of the gauss seidl formula
            sum1, sum2 = summs2_nonzero(
                A,
                sum1_nonzero_indices_lists[i],
                sum2_nonzero_indices_lists[i],
                n,
                i,
                x,
                sum1,
                sum2,
            )

            x[i] = (b[i] - sum1 - sum2) / A[i][i]

            sum1 = 0
            sum2 = 0

        # absolut error
        dx = np.abs(x - x_p_1)
        err = dx

        # rel error
        dx_r = np.real(dx)
        x_r = np.real(x)
        r_err = np.abs(
            np.divide(dx_r, x_r, out=np.zeros_like(dx_r), where=x_r != 0)
        )
        r_err_max = r_err.max()
        pbar.n = 1.0 - r_err_max
        pbar.refresh()

        # calculate differenz between current b and real b
        if caldiff:
            b_diff_norm.append(np.linalg.norm(np.dot(A, x) - b))
        if any(ele == np.inf for ele in b_diff_norm) or any(
            ele == np.nan for ele in b_diff_norm
        ):
            p = abort_crit

        p += 1

    if p < abort_crit:
        a = True  # the algorithm calculated the result within the given iteration max
    else:
        a = False  # the algorithm did not calculated the result within the given iteration max

    if caldiff:
        b_diff_norm = np.array(b_diff_norm)
        b_diff_norm = np.nan_to_num(b_diff_norm, posinf=1.7e155)
        return x, a, b_diff_norm

    return x, a


def summs(A, n, i, x, sum1, sum2):
    """
    old summation which was slow
    """
    for j in range(0, i):
        sum1 += A[i][j] * x[j]
    for j in range(i + 1, n):
        sum2 += A[i][j] * x[j]
    return sum1, sum2


def summs2(A, n, i, x, sum1, sum2):
    """
    new summation which is way less slow especially for large matrices
    """
    sum1 = np.sum(A[i][:i] * x[:i])
    sum2 = np.sum(A[i][(i + 1) :] * x[(i + 1) :])
    return sum1, sum2


def summs2_nonzero(A, sum1_indices, sum2_indices, n, i, x, sum1, sum2):
    """
    new summation which is way less slow especially for large matrices and also
    supports predetermined summation indices lists
    """
    sum1 = np.sum(A[i][sum1_indices] * x[sum1_indices])
    sum2 = np.sum(A[i][sum2_indices] * x[sum2_indices])
    return sum1, sum2
