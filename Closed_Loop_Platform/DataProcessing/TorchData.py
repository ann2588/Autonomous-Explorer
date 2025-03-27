import pandas as pd

# Read the new experimental data
df_expdata = pd.read_csv("/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/DataProcessing/experiment_data.csv", sep = ',')

# Read existing data
df_input = pd.read_csv("/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/experimental_conditions.csv", sep = ',')
df_output = pd.read_csv("/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/updated_objective_data.csv", sep = ',')

# Create new dataframes for the experimental data
new_input = pd.DataFrame()
new_output = pd.DataFrame()

# Mapping for df_input
column_mapping_input = {
    'ExpID': 'Exp',
    'CuConc': 'Cu',
    'DepositionVoltage': 'Volt',
    'Deposition time': 'Time',
    'CO2ratio': 'CO2ratio',
    'IL1': 'IL1',
    'IL2': 'IL2',
    'IL3': 'IL3',
    'IL4': 'IL4',
    'IL5': 'IL5',
    'blank': 'Blank'
}

# Mapping for df_output
column_mapping_output = {
    'ExpID': 'Exp#',
    'Catalysis Current': 'Average Current Density',
    'FECO': 'Average CO'
}

# Update new_input
for old_col, new_col in column_mapping_input.items():
    new_input[new_col] = df_expdata[old_col]

# Update new_output
for old_col, new_col in column_mapping_output.items():
    new_output[new_col] = df_expdata[old_col]

# Set fixed values for voltage columns in new_output
new_output['V'] = '0p3V'
new_output['The bulk electrolysis potential'] = '-2.2 V'

# Append new data to existing dataframes
df_input_combined = pd.concat([df_input, new_input], ignore_index=True)
df_output_combined = pd.concat([df_output, new_output], ignore_index=True)

# Remove any duplicate rows based on experiment ID
df_input_combined = df_input_combined.drop_duplicates(subset=['Exp'], keep='last')
df_output_combined = df_output_combined.drop_duplicates(subset=['Exp#'], keep='last')

# Save the updated dataframes
df_input_combined.to_csv("/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/experimental_conditions.csv", index=False)
df_output_combined.to_csv("/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/updated_objective_data.csv", index=False)

print("df_expdata columns:", df_expdata.columns.tolist())
print("df_input columns:", df_input.columns.tolist())
print("df_output columns:", df_output.columns.tolist())