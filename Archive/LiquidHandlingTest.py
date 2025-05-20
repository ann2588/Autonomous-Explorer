#%%
from Utilities.liquidhandling import *
from Utilities.electrochemistry import *

#%% #Please check each of this function working properly (i.e. the container was rinsed by assigned liquid and the
# the waste is pumped out thoroughly

volume_assigned = '12mL'

## Rinsing with electrolyte series
Rinsing('voir', 'water', 'electrolyte', 1, volume_assigned = '50mL')
Rinsing('cell','water', 'electrolyte', 1, volume_assigned = '26mL') # no issue

# To Rinse the cell with electrolyte, the voir has to be rinsed by electrolyte first.
Rinsing('cell','water', 'spelec', 1, volume_assigned = '26mL')#no  issue
Rinsing('cell', 'water', 'electrolyte', 1, volume_assigned = '26mL')#no issue
Rinsing('cell','water', 'hno3', 1, volume_assigned = '26mL')
Rinsing('cell','water', 'regen', 1, volume_assigned = '26mL')
Rinsing('cell', 'water', 'cu', 1, volume_assigned = '26mL')

#Final clean up
Rinsing('cell', 'water', 'water', 1, volume_assigned = '26mL')

os.system(f'python {script_path} -m "{message_completed}"')


