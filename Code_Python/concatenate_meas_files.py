import os
from pathlib import Path
import pandas as pd

dirname = "winder_measurements/07-29-2023/"
filenames = os.listdir(dirname)
new_filename = dirname+"first_coil_concat.csv"

df = pd.concat((pd.read_csv(dirname+filename) for filename in filenames))

df.to_csv(Path(new_filename),index=False)