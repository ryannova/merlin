import numpy as np
import math
import argparse
import json

def N_Rosenbrock(X):
  X = X.T
  total = 0
  for i in range(X.shape[0] - 1):
    total += 100*((X[i+1] - X[i] ** 2) ** 2) + (1 - X[i]) ** 2
  return total

def rastrigin(X, A=10):
  first_term = A * len(inputs)
  return first_term + sum([(x**2 - A * np.cos(2 * math.pi * x)) for x in X])

def ackley(X):
  firstSum = 0.0
  secondSum = 0.0
  for x in X:
    firstSum += x**2.0
    secondSum += np.cos(2.0 * np.pi * x)
  n = float(len(X))
  return -20.0 * np.exp(-0.2 * np.sqrt(firstSum / n)) - np.exp(secondSum / n) + 20 + np.e

parser = argparse.ArgumentParser("Generate some samples!")
parser.add_argument( "-function",
                    choices=['ackley', 'rastrigin', 'rosen'],
                    default='rosen')
parser.add_argument( "-ID")
parser.add_argument( "-inputs", nargs='+')
args = parser.parse_args()

run_id = args.ID
inputs = args.inputs
function_name = args.function
inputs = np.array(inputs).astype(np.float)

if function_name == 'rastrigin':
    test_function = rastrigin
elif function_name == 'ackley':
    test_function = ackley
else:
    test_function = N_Rosenbrock

outputs = test_function(inputs)
print(outputs)

results = {run_id:{"Inputs":inputs.tolist(),
                    "Outputs":outputs.tolist()
                    }
           }

json.dump(results, open('simulation_results.json', 'w'), indent=4)
