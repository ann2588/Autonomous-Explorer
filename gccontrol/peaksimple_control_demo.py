"""
Created on Thu Oct 14 17:30:17 2021

This script is an example of how to import the PeaksimpleConnector class into
Python using the python.NET package
@author: Briley Bourgeois
"""

import os

import clr  # python.NET is imported with the name clr (Common Language Runtime)

dir_path = os.path.dirname(os.path.realpath(__file__))
assemblydir = os.path.join(dir_path, 'PeaksimpleClient', 'PeaksimpleConnector.dll')

clr.AddReference(assemblydir)  # Add the assembly to python.NET

# Now that the Assembly has been added to python.NET,
# it can be imported like a normal module
import Peaksimple  # Import the assembly namespace, which has a different name

ctrl_file = 'C:\\Peak498Win10\\GCMETHOD\\0819-2020_90-210C_11min.CON'
gc = GC_Connector()
data_path = 'C:\\Peak489Win10\\GCDATA\\20221117_CodeTest'
gc.sample_set_size = 2
gc.update_gc_settings(data_path)
gc.peaksimple.IsConnected()
