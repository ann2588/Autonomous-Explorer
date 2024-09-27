from Utilities import portaccess #Chang your portaccess here
import time
from alicat import FlowController
from alicat import FlowMeter
#%%
# Dictionary to store CO2 ratios and corresponding MFC settings
gas_ratio = [0, 2, 8, 10, 25, 50, 75, 100]
#gas_ratio = [2, 8, 10, 15]
gas_shortname = ['Ar', 'C-2', 'C-8', 'C-10', 'C-20', 'C-25', 'C-50', 'C-75', 'N2']
#gas_shortname = ['C-2', 'C-8', 'C-10', 'C-15']
gas_num = [23, 22, 21, 140]
gas_dict = {el: ex for el, ex in zip(gas_shortname, gas_num)}


#%%MFC initialization
mfc_co2 = FlowController(port = portaccess.port_MFC_co2)
mfc_ar = FlowController(port = portaccess.port_MFC_Ar)
mfc_co2ar = FlowController(port = portaccess.port_MFC_Arco2)
mfm = FlowMeter(port = portaccess.port_MFM)
#%%
def readpoint(data:str, flowcontroller):
    '''
    Available input:
    'mass_flow'
    'pressure'
    'temperature
    'gas'
    '''
    datas = flowcontroller.get()  # Get the full dictionary
    read = datas.get(data)
    return read

#%%
def control_gas_flow(flow_controller, operation='open', flow_rate=30, pressure=50):
    if operation == 'open':
        flow_controller.set_flow_rate(flow_rate)
        print(f"Flow rate set to {flow_rate} sccm.")
    elif operation == 'close':
        flow_controller.set_flow_rate(0)
        print("Flow rate closed.")
    elif operation == 'inject':
        flow_controller.set_pressure(pressure)
        print(f"Pressure set to {pressure}.")
    else:
        raise AssertionError('Please provide a valid command to MFC.')

def control_co2_ar_ratio(ratio):
    total_flow_rate = 30
    flow_co2 = total_flow_rate * (ratio / 100)
    flow_ar = total_flow_rate - flow_co2

    mfc_co2.set_flow_rate(flow_co2)
    mfc_ar.set_flow_rate(flow_ar)
    print(f"CO2 flow: {flow_co2} sccm, Ar flow: {flow_ar} sccm")
#%%
def start_experiment():
    try:
        # Loop through each gas ratio
        for ratio in gas_ratio:
            print(f"Setting CO2/Ar ratio to {ratio}%")

            # Control CO2 and Ar flow rates
            control_co2_ar_ratio(mfc_co2, mfc_ar, ratio)

            # Set the mixed gas MFC to appropriate settings
            gas_key = f'C-{ratio}' if ratio > 0 else 'Ar'  # Handle the case for pure Ar
            mfc_co2ar.set_gas(gas_key)
            mfc_co2ar.set_flow_rate(50) ###

            print(f"Running experiment with CO2/Ar ratio {ratio}%.")
            print('Reading value:')
            print(f'Ar flow rate : {readpoint("mass_flow", mfc_ar)}')
            print(f'CO2 flow rate : {readpoint("mass_flow", mfc_co2)}')
            print(f'flow rate into cell : {readpoint("mass_flow", mfc_co2ar)}')
            print(f'flow rate after cell : {readpoint("mass_flow", mfm)}')

            # Simulate experiment run time
            time.sleep(30) #waiting for equilibrium


            # Close the gas flow after each run
            control_gas_flow(mfc_co2, operation='close')
            control_gas_flow(mfc_ar, operation='close')
            control_gas_flow(mfc_co2ar, operation='close')

            print(f"Experiment completed for ratio {ratio}%.\n")

            # Console input to continue or stop the experiment
            user_input = input("Do you want to continue to the next gas ratio? (y/n): ").strip().lower()
            if user_input != 'y':
                print("Experiment stopped by user.")
                break

    except Exception as e:
        print(f"Error occurred: {e}")

