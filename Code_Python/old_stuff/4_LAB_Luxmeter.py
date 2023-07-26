import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


luxes = pd.read_csv(".//Code_PC_RASPY//4_LAB_Luses.csv",delimiter=";")

luxes.plot()
plt.show()