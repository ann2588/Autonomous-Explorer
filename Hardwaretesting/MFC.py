import asyncio
from alicat import FlowController



#%%
import asyncio
from alicat import FlowController
async def setup():
    async with FlowController('COM5') as flow_controller:
        await flow_controller.set_gas('Ar') # Set calibration as Ar
        await flow_controller.close()

#%%
async def n2on(flowrate=20):
    async with FlowController('COM5') as Ar_controller:
    #await flow_controller.set_gas('Ar') # Set calibration as Ar
        await Ar_controller.set_flow_rate(flowrate)
        await Ar_controller.close()

async def n2off(flowrate=0):
    async with FlowController('COM5') as Ar_controller:
    #await flow_controller.set_gas('Ar') # Set calibration as Ar
        await Ar_controller.set_flow_rate(flowrate)
        await Ar_controller.close()


#%%
async def H2on(flowrate=20):
    async with FlowController('COM6') as h2_controller:
    #await flow_controller.set_gas('Ar') # Set calibration as Ar
        await h2_controller.set_flow_rate(flowrate)
        await h2_controller.close()

async def H2off(flowrate=0):
    async with FlowController('COM6') as h2_controller:
    #await flow_controller.set_gas('Ar') # Set calibration as Ar
        await h2_controller.set_flow_rate(flowrate)
        await h2_controller.close()

#asyncio.run(MFCsetup())

#asyncio.run(MFC.close())
#asyncio.run(MFC.n2off())
#asyncio.run(MFC.n2on()) #Please assign desire flow rate