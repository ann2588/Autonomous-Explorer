#%%
import pandas as pd
import numpy as np

doepath = r"Closed_Loop_Platform/DoERandomBatch10.csv" # PLACE THE PATH OF YOUR DoE.csv here
def doeprocess(doepath: str):
    '''
    This function processes the provided DoE in a CSV file into dictionaries for CuDep, CO2ratio, and IL.
    '''
    # Define the elements and categories
    element = ['CuConc', 'Volt', 'Time', 'CO2ratio', 'IL1', 'IL2', 'IL3', 'IL4', 'IL5', 'blank']
    # Read the CSV file
    trials = pd.read_csv(doepath, sep=',', index_col=0)

    # Process each row in the CSV file
    exp_dicts = {}
    for i in range(trials.shape[0]):
        ext = trials.iloc[i].tolist()
        element_dict = {el: ex for el, ex in zip(element, ext)}
        exp_dicts[f'EXP{i+1:04}'] = element_dict
    return exp_dicts

if __name__ == '__main__':
    exp_dicts = doeprocess(doepath)
    print(exp_dicts)