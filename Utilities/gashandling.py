from Utilities import portaccess, valve_slvc  # Chang your portaccess here
import time
from alicat import FlowController
from alicat import FlowMeter
from liquidhandling import changing_port
#%%
## Dictionary to store CO2 ratios and corresponding MFC settings
gas_ratio = [0, 2, 8, 10, 25, 50, 75, 100]
gas_shortname = ['N2', 'C-2', 'C-8', 'C-10', 'C-15', 'C-20', 'C-25', 'C-50', 'C-75', 'CO2']
#gas_dict = {el: ex for el, ex in zip(gas_shortname, gas_num)}


#%% MFC initialization
mfc_co2 = FlowController(port = portaccess.port_MFC_co2)
mfc_ar = FlowController(port = portaccess.port_MFC_Ar)
mfc_co2ar = FlowController(port = portaccess.port_MFC_Arco2)
mfc_swtv = FlowController(port = portaccess.port_MFC_ArSWTV)
mfm = FlowMeter(port = portaccess.port_MFM)
#%%
def readpoint(data:str, flowcontroller):
    """
    Read the assigned value from device
    :param
        data: 'mass_flow', 'pressure', 'temperature, 'gas'
        flowcontroller: mfc_co2, mfc_co2ar, mfc_swtv, mfc_ar, mfm
    :return readpoint in string
    """
    datas = flowcontroller.get()  # Get the full dictionary
    read = datas.get(data)
    return read

#%%
def control_gas_flow(flow_controller, operation='open', flow_rate=30, pressure=20):
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

def close_all_gas():
    mfc_ar.set_flow_rate(0)
    mfc_co2.set_flow_rate(0)
    mfc_co2ar.set_flowrate(0)
