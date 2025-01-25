from Closed_Loop_Platform.Utilities import portaccess  # Chang your portaccess here
from alicat import FlowController
from alicat import FlowMeter

#%%
## Dictionary to store CO2 ratios and corresponding MFC settings
gas_ratio = [0, 2, 8, 10, 25, 50, 75, 100]
gas_shortname = ['Ar', 'C-2', 'C-8', 'C-10', 'C-15', 'C-20', 'C-25', 'C-50', 'C-75', 'CO2']
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
def control_gas_flow(flow_controller, operation='open', flow_rate=30, pressure=30):
    if operation == 'open':
        flow_controller.set_flow_rate(flow_rate)
        flow_controller.set_pressure(pressure)
        print(f"Flow rate set to {flow_rate} sccm.")
    elif operation == 'close':
        flow_controller.set_flow_rate(0)
        print("Flow rate closed.")
    elif operation == 'inject':
        flow_controller.set_pressure(pressure)
        print(f"Pressure set to {pressure}.")
    else:
        raise AssertionError('Please provide a valid command to MFC.')
def control_co2_ar_ratio(co2_ratio, flowrate = 30):
    total_flow_rate = flowrate
    flow_co2 = total_flow_rate * (co2_ratio / 100)
    flow_ar = total_flow_rate - flow_co2

    mfc_co2.set_flow_rate(flow_co2)
    mfc_ar.set_flow_rate(flow_ar)
    mfc_co2ar.set_flow_rate(total_flow_rate*0.8)
    mfc_co2ar.set_pressure(pressure = 14.6)
    print(f"CO2 flow: {flow_co2} sccm, Ar flow: {flow_ar} sccm")

def close_all_gas():
    mfc_ar.set_flow_rate(0)
    mfc_co2.set_flow_rate(0)
    mfc_co2ar.set_flow_rate(0)

def read_all_gas():
    print('Reading values:')
    print(f'Ar flow rate: {readpoint("mass_flow", mfc_ar)}')
    print(f'CO2 flow rate: {readpoint("mass_flow", mfc_co2)}')
    print(f'Gas flow into cell: {readpoint("mass_flow", mfc_co2ar)}')
    print(f'Total flow into GC: {readpoint("mass_flow", mfm)}')