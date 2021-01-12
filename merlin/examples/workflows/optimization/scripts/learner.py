import argparse

import numpy as np
from joblib import dump, load
from sklearn.ensemble import RandomForestRegressor


parser = argparse.ArgumentParser("Learn surrogate model form simulation")
parser.add_argument(
    "-collector_dir",
    help="Collector directory (.npz file), usually '$(collector.workspace)'",
)
args = parser.parse_args()


try:
    all_iter_results = np.load("all_iter_results.npz", allow_pickle=True)
except:
    print("Unable to load the data")

X = all_iter_results["X"]
y = all_iter_results["y"]

surrogate = RandomForestRegressor(max_depth=4, random_state=0, n_estimators=100)
surrogate.fit(X, y)

dump(surrogate, "surrogate.joblib")
