import os
import clr

dir_path = 'C:\\Peak488Win10\\PeaksimpleConnectorTestClient'
assemblydir = os.path.join(dir_path, 'PeaksimpleClient', 'PeaksimpleConnector.dll')
clr.AddReference(assemblydir)
#%%
import Peaksimple
Connector = Peaksimple.PeaksimpleConnector()

print(dir(Connector))