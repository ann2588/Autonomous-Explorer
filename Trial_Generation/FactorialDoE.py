'''
This script will generate factorial design of experiment with given parameter space and constraint.
It's better to run it on google colab where have enough calculation resource than a local computer.
'''

desire_numbers = 10

import numpy as np
import itertools
import csv

# Define parameter ranges and steps
parameters = {
    "Cu (Conti)": np.arange(0.2, 0.6, 0.1).round(1).tolist(),  # 0.2 to 0.5 inclusive, step 0.1
    "Volt": np.arange(-1.0, -0.1, 0.1).round(1).tolist(),  # -1.0 to -0.2 inclusive, step 0.1
    "Time": list(range(30, 181, 10)),  # 30 to 180 inclusive, step 10
    "CO2ratio": list(range(0, 101, 5)),  # 0 to 100 inclusive, step 5
    "IL1": list(range(1, 51, 5)),  # 1 to 50 inclusive, step 5
    "IL2": list(range(1, 51, 5)),  # Same as IL1
    "IL3": list(range(1, 51, 5)),  # Same as IL1
    "IL4": list(range(1, 51, 5)),  # Same as IL1
    "IL5": list(range(1, 51, 5)),  # Same as IL1
    "Blank": list(range(1, 51, 5))  # 1 to 50 inclusive, step 5
}

# Output file path
file_path = "Factorial_Design_10_Trials.csv"

# Open a CSV file to write incrementally
with open(file_path, mode="w", newline="") as file:
    writer = csv.writer(file)
    # Write the header
    writer.writerow(parameters.keys())

    # Generate combinations incrementally
    valid_trials = 0  # Counter for valid trials
    for combination in itertools.product(*parameters.values()):
        # Convert the combination into a dictionary for easier manipulation
        combination_dict = dict(zip(parameters.keys(), combination))

        # Apply the constraint: IL1 + IL2 + IL3 + IL4 + IL5 + Blank == 50
        if (
                combination_dict["IL1"]
                + combination_dict["IL2"]
                + combination_dict["IL3"]
                + combination_dict["IL4"]
                + combination_dict["IL5"]
                + combination_dict["Blank"]
                == 50
        ):
            # Write the valid combination to the file
            writer.writerow(combination)
            valid_trials += 1

        # Stop after finding 10 valid trials
        if valid_trials == desire_numbers:
            break

print(f"10 trials satisfying the constraint saved to {file_path}")