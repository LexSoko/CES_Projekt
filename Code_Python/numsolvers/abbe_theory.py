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


def optical_mask():
    