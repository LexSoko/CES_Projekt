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


class Diffraction:
    def __init__(self, Lx: float, Ly: float, Nx: int, Ny: int, ʎ: float):
        self.Lx = Lx
        self.Ly = Ly
        self.Nx = Nx
        self.Ny = Ny
        self.ʎ = ʎ

        self.dx = Lx / Nx
        self.dy = Ly / Ny

        self.dphi = ʎ / (2 * Lx)
        self.dtheta = ʎ / (2 * Ly)

        self.__ix__ = 0
        self.__iy__ = 1

        self.space_grid_app = np.meshgrid(
            self.dx * (np.arange(Nx) - (Nx // 2)),
            self.dy * (np.arange(Ny) - (Ny // 2)),
        )

        self.__iphi__ = 0
        self.__itheta__ = 1

        self.space_grid_diff = np.fft.fftshift(
            np.meshgrid(
                self.dphi * (np.arange(Nx) - (Nx // 2)),
                self.dtheta * (np.arange(Ny) - (Ny // 2)),
            )
        )

        self.apperture = np.zeros((self.Nx, self.Ny))
        self.diffraction_pattern = np.zeros((self.Nx, self.Ny))
        self.diffraction_wave = np.zeros((self.Nx, self.Ny))
        self.masked_diffraction_wave = np.zeros((self.Nx, self.Ny))
        self.masked_diffraction_pattern = np.zeros((self.Nx, self.Ny))

    def optical_mask(self, mask_dist: Callable[..., np.ndarray], **kwargs):
        calculate = False
        if "calc" in kwargs and kwargs.get("calc") == True:
            calculate = True
            kwargs.pop("calc")

        if len(kwargs) == 0:
            self.apperture = mask_dist(
                self.space_grid_app[self.__ix__],
                self.space_grid_app[self.__iy__],
            )
        else:
            self.apperture = mask_dist(
                self.space_grid_app[self.__ix__],
                self.space_grid_app[self.__iy__],
                **kwargs,
            )

        if calculate:
            self._diffraction_pattern_()

    def intensity_distribution(
        self, diff_patt_dist: Callable[..., np.ndarray], **kwargs
    ):
        calculate = False
        if "calc" in kwargs and kwargs.get("calc") == True:
            calculate = True
            kwargs.pop("calc")

        if len(kwargs) == 0:
            self.diffraction_wave = np.fft.ifftshift(diff_patt_dist(
                self.space_grid_diff[self.__ix__],
                self.space_grid_diff[self.__iy__],
            ))
        else:
            self.diffraction_wave = np.fft.ifftshift(diff_patt_dist(
                self.space_grid_diff[self.__ix__],
                self.space_grid_diff[self.__iy__],
                **kwargs,
            ))
        self.diffraction_pattern = np.absolute(self.diffraction_wave) ** 2
        self.diffraction_pattern = (
            self.diffraction_pattern / self.diffraction_pattern.max()
        )
        
        if calculate:
            self._aperture_pattern_()

    def _diffraction_pattern_(self):
        self.diffraction_wave = np.fft.fftshift(np.fft.fft2(self.apperture))
        self.diffraction_wave = (
            self.diffraction_wave / np.abs(self.diffraction_wave).max()
        )
        self.diffraction_pattern = np.absolute(self.diffraction_wave) ** 2
        self.diffraction_pattern = (
            self.diffraction_pattern / self.diffraction_pattern.max()
        )

    def _aperture_pattern_(self):
        self.apperture = np.fft.ifftshift(np.fft.irfft2(
            self.diffraction_wave, s=self.diffraction_wave.shape
        ))
        self.apperture = np.absolute(self.apperture) ** 2
        self.apperture = self.apperture / self.apperture.max()

    def _diffraction_mask_(
        self, mask_dist: Callable[..., np.ndarray], **kwargs
    ):
        self.masked_diffraction_wave = mask_dist(
            self.space_grid_diff, self.diffraction_wave, **kwargs
        )
        self.masked_diffraction_pattern = np.absolute(
            self.masked_diffraction_pattern
        )

    def get_apperture_bounds(self, min_int: float):
        bound = np.argwhere(self.apperture.T > min_int)
        i_xmax = bound[:, 0].max()
        i_xmin = bound[:, 0].min()
        i_ymax = bound[:, 1].max()
        i_ymin = bound[:, 1].min()

        xmin = self.space_grid_app[0][i_xmin, i_xmin]
        xmax = self.space_grid_app[0][i_xmax, i_xmax]
        ymin = self.space_grid_app[1][i_ymin, i_ymin]
        ymax = self.space_grid_app[1][i_ymax, i_ymax]

        return xmin, xmax, ymin, ymax

    def get_diffraction_bounds(self, min_int: float):
        bound = np.argwhere(self.diffraction_pattern.T > min_int)
        i_xmax = bound[:, 0].max()
        i_xmin = bound[:, 0].min()
        i_ymax = bound[:, 1].max()
        i_ymin = bound[:, 1].min()

        diff_grid = np.fft.fftshift(self.space_grid_diff)

        xmin = diff_grid[0][i_xmin, i_xmin]
        ymin = diff_grid[1][i_ymin, i_ymin]
        xmax = diff_grid[0][i_xmax, i_xmax]
        ymax = diff_grid[1][i_ymax, i_ymax]

        return xmin, xmax, ymin, ymax
