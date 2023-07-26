#!/usr/bin/python
# -*- coding: utf-8 -*-
############################## imports #######################################
import numpy as np
from typing import Callable


######################### module level dunders ###############################
__author__ = "Max Jost, Aleksey Sokolov, Martin Ferdinand Steiner"

############################# functions ######################################
G = 6.67408 * 10 ** (-11)


def funcarray(*funcs):
    """
    A wrapper for code lengh reduction
    lets you input any amount of functions so that a y matrix can be given as input for the functions

    Returns:
        returns a lambda expression as a numpy array
    """
    return lambda t, y: np.array([f(t, y) for f in funcs])


def funcarray_list(funcs: list[Callable]):
    """
    A wrapper for code lengh reduction
    lets you input any amount of functions so that a y matrix can be given as input for the functions

    Returns:
        returns a lambda expression as a numpy array
    """
    return lambda t, y: np.array([f(t, y) for f in funcs])


def Force(ri: list, rj: list, mi: float):
    ri = np.array(ri)
    rj = np.array(rj)
    pot = -G * (mi * ((ri - rj) / (np.sqrt(np.sum((ri - rj) ** 2)) ** 3)))
    return pot


# ri = np.array([1,3,3])
# rj = np.array([2,2,4])
# print((np.sqrt(np.sum((ri - rj) ** 2)) ** 3))
# print(np.sum((ri-rj)**2)**(3/2))
def Potential_space_derivative_x(mi: float, mj: float, ri: list, rj: list):
    pot_x = G * (
        mi
        * mj
        * (
            (ri[0] - rj[0])
            / (
                (
                    (ri[0] - rj[0]) ** 2
                    + (ri[1] - rj[1]) ** 2
                    + (ri[2] - rj[2]) ** 2
                )
                ** (3 / 2)
            )
        )
    )
    return pot_x


def Potential_space_derivative_y(mi: float, mj: float, ri: list, rj: list):
    pot_y = G * (
        mi
        * mj
        * (
            (ri[1] - rj[1])
            / (
                (
                    (ri[0] - rj[0]) ** 2
                    + (ri[1] - rj[1]) ** 2
                    + (ri[2] - rj[2]) ** 2
                )
                ** (3 / 2)
            )
        )
    )
    return pot_y


def Potential_space_derivative_z(mi: float, mj: float, ri: list, rj: list):
    pot_z = G * (
        mi
        * mj
        * (
            (ri[2] - rj[2])
            / (
                (
                    (ri[0] - rj[0]) ** 2
                    + (ri[1] - rj[1]) ** 2
                    + (ri[2] - rj[2]) ** 2
                )
                ** (3 / 2)
            )
        )
    )
    return pot_z


def Hamilton_ODES(m1, m2, m3):
    p_1_x = lambda t, y: (
        Potential_space_derivative_x(
            m1, m2, [y[0], y[1], y[2]], [y[3], y[4], y[5]]
        )
        + Potential_space_derivative_x(
            m1, m3, [y[0], y[1], y[2]], [y[6], y[7], y[8]]
        )
    )
    p_1_y = lambda t, y: (
        Potential_space_derivative_y(
            m1, m2, [y[0], y[1], y[2]], [y[3], y[4], y[5]]
        )
        + Potential_space_derivative_y(
            m1, m3, [y[0], y[1], y[2]], [y[6], y[7], y[8]]
        )
    )
    p_1_z = lambda t, y: (
        Potential_space_derivative_z(
            m1, m2, [y[0], y[1], y[2]], [y[3], y[4], y[5]]
        )
        + Potential_space_derivative_z(
            m1, m3, [y[0], y[1], y[2]], [y[6], y[7], y[8]]
        )
    )

    p_2_x = lambda t, y: (
        Potential_space_derivative_x(
            m1, m2, [y[0], y[1], y[2]], [y[3], y[4], y[5]]
        )
        + Potential_space_derivative_x(
            m2, m3, [y[3], y[4], y[5]], [y[6], y[7], y[8]]
        )
    )
    p_2_y = lambda t, y: (
        Potential_space_derivative_y(
            m1, m2, [y[0], y[1], y[2]], [y[3], y[4], y[5]]
        )
        + Potential_space_derivative_y(
            m2, m3, [y[3], y[4], y[5]], [y[6], y[7], y[8]]
        )
    )
    p_2_z = lambda t, y: (
        Potential_space_derivative_z(
            m1, m2, [y[0], y[1], y[2]], [y[3], y[4], y[5]]
        )
        + Potential_space_derivative_z(
            m2, m3, [y[3], y[4], y[5]], [y[6], y[7], y[8]]
        )
    )

    p_3_x = lambda t, y: (
        Potential_space_derivative_x(
            m1, m3, [y[0], y[1], y[2]], [y[6], y[7], y[8]]
        )
        + Potential_space_derivative_x(
            m2, m3, [y[3], y[4], y[5]], [y[6], y[7], y[8]]
        )
    )
    p_3_y = lambda t, y: (
        Potential_space_derivative_y(
            m1, m3, [y[0], y[1], y[2]], [y[6], y[7], y[8]]
        )
        + Potential_space_derivative_y(
            m2, m3, [y[3], y[4], y[5]], [y[6], y[7], y[8]]
        )
    )
    p_3_z = lambda t, y: (
        Potential_space_derivative_z(
            m1, m3, [y[0], y[1], y[2]], [y[6], y[7], y[8]]
        )
        + Potential_space_derivative_z(
            m2, m3, [y[3], y[4], y[5]], [y[6], y[7], y[8]]
        )
    )

    x_1 = lambda t, y: y[9] / m1
    y_1 = lambda t, y: y[10] / m1
    z_1 = lambda t, y: y[11] / m1

    x_2 = lambda t, y: y[12] / m2
    y_2 = lambda t, y: y[13] / m2
    z_2 = lambda t, y: y[14] / m2

    x_3 = lambda t, y: y[15] / m3
    y_3 = lambda t, y: y[16] / m3
    z_3 = lambda t, y: y[17] / m3
    return funcarray(
        x_1,
        y_1,
        z_1,
        x_2,
        y_2,
        z_2,
        x_3,
        y_3,
        z_3,
        p_1_x,
        p_1_y,
        p_1_z,
        p_2_x,
        p_2_y,
        p_2_z,
        p_3_x,
        p_3_y,
        p_3_z,
    )


# def n_body_ODES_Hamilton(masses:list):
#    positions = []
#    momentum = []
#    number = 3*len(masses)
#    for i, m in enumerate(masses):
#        positions.append(lambda t , y: )


# y[0] bis y[8]  vec(r1) vec(r2) vec(r3)
# y[9] bis y[17]  ableitungen in der gleichen anordnu
def Newton_ODES(m1, m2, m3):
    r_1_1 = lambda t, y: y[9]
    r_1_2 = lambda t, y: y[10]
    r_1_3 = lambda t, y: y[11]
    r_2_1 = lambda t, y: y[12]
    r_2_2 = lambda t, y: y[13]
    r_2_3 = lambda t, y: y[14]
    r_3_1 = lambda t, y: y[15]
    r_3_2 = lambda t, y: y[16]
    r_3_3 = lambda t, y: y[17]

    v_1_1 = lambda t, y: np.dot(
        (
            Force([y[0], y[1], y[2]], [y[3], y[4], y[5]], m2)
            + Force([y[0], y[1], y[2]], [y[6], y[7], y[8]], m3)
        ),
        np.array([1, 0, 0]),
    )
    v_1_2 = lambda t, y: np.dot(
        (
            Force([y[0], y[1], y[2]], [y[3], y[4], y[5]], m2)
            + Force([y[0], y[1], y[2]], [y[6], y[7], y[8]], m3)
        ),
        np.array([0, 1, 0]),
    )
    v_1_3 = lambda t, y: np.dot(
        (
            Force([y[0], y[1], y[2]], [y[3], y[4], y[5]], m2)
            + Force([y[0], y[1], y[2]], [y[6], y[7], y[8]], m3)
        ),
        np.array([0, 0, 1]),
    )

    v_2_1 = lambda t, y: np.dot(
        Force([y[3], y[4], y[5]], [y[0], y[1], y[2]], m1)
        + Force([y[3], y[4], y[5]], [y[6], y[7], y[8]], m3),
        np.array([1, 0, 0]),
    )
    v_2_2 = lambda t, y: np.dot(
        Force([y[3], y[4], y[5]], [y[0], y[1], y[2]], m1)
        + Force([y[3], y[4], y[5]], [y[6], y[7], y[8]], m3),
        np.array([0, 1, 0]),
    )
    v_2_3 = lambda t, y: np.dot(
        Force([y[3], y[4], y[5]], [y[0], y[1], y[2]], m1)
        + Force([y[3], y[4], y[5]], [y[6], y[7], y[8]], m3),
        np.array([0, 0, 1]),
    )

    v_3_1 = lambda t, y: np.dot(
        Force([y[6], y[7], y[8]], [y[0], y[1], y[2]], m1)
        + Force([y[6], y[7], y[8]], [y[3], y[4], y[5]], m2),
        np.array([1, 0, 0]),
    )
    v_3_2 = lambda t, y: np.dot(
        Force([y[6], y[7], y[8]], [y[0], y[1], y[2]], m1)
        + Force([y[6], y[7], y[8]], [y[3], y[4], y[5]], m2),
        np.array([0, 1, 0]),
    )
    v_3_3 = lambda t, y: np.dot(
        Force([y[6], y[7], y[8]], [y[0], y[1], y[2]], m1)
        + Force([y[6], y[7], y[8]], [y[3], y[4], y[5]], m2),
        np.array([0, 0, 1]),
    )

    return funcarray(
        r_1_1,
        r_1_2,
        r_1_3,
        r_2_1,
        r_2_2,
        r_2_3,
        r_3_1,
        r_3_2,
        r_3_3,
        v_1_1,
        v_1_2,
        v_1_3,
        v_2_1,
        v_2_2,
        v_2_3,
        v_3_1,
        v_3_2,
        v_3_3,
    )
