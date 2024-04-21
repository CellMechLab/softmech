import h5py
import numpy as np

#open the file
filename = '../testdata/test.hdf5'
experiment = h5py.File(filename,'r')

#list to store the curves
curves = []

#browse the experiment
for struct_id in list(experiment.keys()):
    structure=experiment[struct_id]
    
    #extrat the relevant info for the selected segment
    k = structure.attrs['spring_constant']
    selectedSegment = structure.attrs['selectedSegment']
    F = np.array(structure[f'segment{selectedSegment}']['Force'])
    Z = np.array(structure[f'segment{selectedSegment}']['Z'])
    Time = np.array(structure[f'segment{selectedSegment}']['Time'])
    
    if 'cp' in structure.keys():
        cp = np.array(structure['cp'])
        
        #normalise to the cp
        F = F - cp[1]
        Z = Z - cp[0]
        iContact = np.argmin( Z** 2)
        #extract the portion in contact and calculate the indentation
        Force = F[iContact:]
        Indentation = Z[iContact:] - Force / k
        Delay = Time[iContact:]-Time[iContact]
        #populate the array
        curves.append([Delay,Indentation,Force])

experiment.close()

#do something with the curves
import matplotlib.pyplot as plt
fig,[ax1,ax2,ax3] = plt.subplots(1,3)
for c in curves:
    ax1.plot(c[0],c[1],'r',alpha=0.4)
    ax1.set_xlabel('Time [s]')
    ax1.set_ylabel('Indentation [m]')
    ax2.plot(c[0],c[2],'r',alpha=0.4)
    ax2.set_xlabel('Time [s]')
    ax2.set_ylabel('Force [N]')
    ax3.plot(c[1],c[2],'r',alpha=0.4)
    ax3.set_xlabel('Indentation [m]')
    ax3.set_ylabel('Force [N]')
plt.show()