from scipy.stats import qmc
import numpy as np
import pandas as pd
from pathlib import Path

variable_names = ["initial_organic", "isocratic_time", "gradient_time", "organic_ratio"]
lower_bounds = [5, 0, 1, 0]
upper_bounds = [60, 5, 10, 100]
n_initial = 5
output_directory = "./results" 

def LHS_initial_experiments(variable_names, n_initial, lower_bounds, upper_bounds, save_dir="."):
    # calculate the number of dimensions based on variable_names
    n_dimension = len(variable_names)

    # LHS gernation 
    sampler = qmc.LatinHypercube(d=n_dimension)
    sample = sampler.random(n=n_initial)
    sample_scaled = qmc.scale(sample, lower_bounds, upper_bounds)
    sample_scaled = np.round(sample_scaled, 1)  # save one digit
    dataframe = pd.DataFrame(sample_scaled, columns=variable_names)
    
    # save csv file
    export_folder = Path(save_dir)
    export_folder.mkdir(parents=True, exist_ok=True)
    file_name = f"LHS_initial_{n_initial}_experiments.csv"
    file_path = export_folder / file_name
    dataframe.to_csv(file_path, index=False)
    return dataframe

