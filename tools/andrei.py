import h5py
import numpy as np
import matplotlib.pyplot as plt

#open the file
filename = '../testdata/test.hdf5'
experiment = h5py.File(filename,'r')

fig,[ax1,ax2,ax3,ax4] = plt.subplots(1,4)
ax1.set_xlabel('Time [s]')
ax1.set_ylabel('Z [nm]')
ax1.set_title('Piezo')
ax2.set_xlabel('Time [s]')
ax2.set_ylabel('Force [nN]')
ax2.set_title('Force')
ax2.set_xlabel('Position [nm]')
ax2.set_ylabel('Force [nN]')
ax2.set_title('F vs Z approach')
ax4.set_xlabel('Indentation [nm]')
ax4.set_ylabel('Force [nN]')
ax4.set_title('F vs Ind approach')
alpha=0.2
#browse the experiment
for struct_id in list(experiment.keys()):
    structure=experiment[struct_id]
    #extrat the relevant info for the selected segment
    k = structure.attrs['spring_constant']
    selectedSegment = structure.attrs['selectedSegment']
    nseg = structure.attrs['segments']
    

    for iseg in range(nseg):    
        Force = np.array(structure[f'segment{iseg}']['Force'])
        Zpos = np.array(structure[f'segment{iseg}']['Z'])
        Time = np.array(structure[f'segment{iseg}']['Time'])
        col = 'r'
        if iseg==selectedSegment:
            col='g'
        ax1.plot(Time,Zpos*1e9,col,alpha=alpha)        
        ax2.plot(Time,Force*1e9,col,alpha=alpha)
        
        if 'cp' in structure.keys():
            cp = np.array(structure['cp'])
            #normalise to the cp
            Force = Force - cp[1]
            Zpos = Zpos - cp[0]
            Indentation = Zpos - Force/k
            
            if iseg==selectedSegment:
                ax3.plot(Zpos,Force*1e9,'g',alpha=alpha)
                icp = np.argmin(Zpos**2)
                ax4.plot(Indentation[icp:],Force[icp:]*1e9,'g',alpha=alpha)        
            
experiment.close()

plt.show()