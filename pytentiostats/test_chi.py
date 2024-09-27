import pytentiostats as pstat




folder = 'C:/Users/guazh/data/chitesting/'
#folder = 'C:/Users/oliverrz/Desktop/Oliver/Data/220214_potentiostats-library'
#path_pstat = 'C:/Users/oliverrz/Desktop/chi760e'
path_pstat = 'C:/chi'
pstat_model = 'chi760f'
#pstat.Setup(model=model, path_exe=path, folder=child_filepath)
pstat.Setup(folder_save=folder, pstat_model=pstat_model, path_pstat=path_pstat, verbose=1)

#tech = ITCURVE()
#tech.run

tech = CV()
tech.bipot(E=1)
tech.run()

tech = OCP()
tech.run()



