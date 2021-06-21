import numpy as np
#import afmformats

from .curve import (MODE_DIRECTION_BACKWARD, MODE_DIRECTION_FORWARD,
                    MODE_DIRECTIONS_PAUSE, Segment)
from .mvFilesystem import MvNode


class DataSet(MvNode):
    _leaf_ext = ['.txt']

    def __init__(self, filename=None, parent=None):
        super().__init__(parent=parent, filename=filename)
        self._header = None
        self.cantilever_k = 1.0  # elastic constant of the cantilever in nN/nm
        self.cantilever_lever = 1.0  # calibration factor InvOls in nm/V
        self.cantilever_type = 'Colloidal probe'
        # the name of the file the text output was created from
        self.original_filename = None
        self.tip_radius = 1000.0  # radius of the tip, used for sphere, in nm
        self.tip_shape = 'sphere'  # onest shapes are 'sphere' , 'cone' , 'flat'
        # store for the full time tracks, add additional channels
        self.data = {'time': [], 'force': [], 'deflection': [], 'z': []}
        self.protocol = []  # a list of protsegments parameters
        # in case a default speed was set and it is not readable from the segment
        self.protocol_speed = None
        self.version = None
        self.forwardSegment = 0
        self.hertz = {}
        self.hertz['threshold'] = None
        self.hertz['thresholdType'] = 'indentation'
        self.xpos = None
        self.ypos = None
        self.valid = True

    def setRadius(self, value, recursive=True):
        self.tip_radius = value
        if recursive is True:
            for c in self.haystack:
                c.tip_radius = value

    def setForwardSegment(self, value, recursive=True):
        self.forwardSegment = value
        if recursive is True:
            for c in self.haystack:
                c.forwardSegment = value

    def open(self):
        self.header()
        self.load()
        self.createSegments()

    def check(self):
        # Implement this function to get a signature of the filetype (not only by the extension)
        return True  # True = this is a known file, False otherwise

    def header(self):
        # Implement this function to populate the header, see the constructor for critical info
        pass

    def load(self):
        pass

    def createSegments(self):
        pass


##################################
##### Optics11 Chiaro ############
##################################

def cross(x1, x2, th, dth):
    th1 = th+dth
    th2 = th-dth
    if np.sign(x1-th1) != np.sign(x2-th1):
        return True
    if np.sign(x1-th2) != np.sign(x2-th2):
        return True
    return False


class ChiaroBase(DataSet):

    def check(self):
        f = open(self.filename)
        signature = f.readline()
        f.close()
        if signature[0:5] == 'Date\t':
            return True
        return False

    def header(self):
        f = open(self.filename)
        targets = ['Tip radius (um)', 'Calibration factor', 'k (N/m)', 'SMDuration (s)',
                   'Piezo Indentation Sweep Settings', 'Profile:', 'E[eff] (Pa)', 'X-position (um)', 'Y-position (um)',
                   'Software version','Time (s)','Measurement','Loading / unloading time (s)','Depth (nm)']
        reading_protocol = False
        self.version = 'old'
        self.DMA = False
        for line in f:
            if reading_protocol is False or self.DMA is True:
                if line[0:len(targets[0])] == targets[0]:
                    self.tip_radius = float(line.strip().replace(',', '.').split('\t')[
                                            1])*1000.0  # NB: internal units are nm
                elif line[0:len(targets[1])] == targets[1]:
                    self.cantilever_lever = float(line.strip().replace(',', '.').split('\t')[
                                                  1])  # NB: so called geometric factor
                elif line[0:len(targets[2])] == targets[2]:
                    self.cantilever_k = float(
                        line.strip().replace(',', '.').split('\t')[1])
                elif line[0:len(targets[3])] == targets[3]:
                    delay = float(line.strip().replace(',', '.')[len(targets[3]):])
                    self.protocol.append([0, delay])
                elif line[0:len(targets[12])] == targets[12]:
                    cv_time = float(line.strip().replace(',', '.')[len(targets[12]):])
                    self.protocol.append([cv_depth, cv_time])
                elif line[0:len(targets[13])] == targets[13]:
                    cv_depth = float(line.strip().replace(',', '.')[len(targets[13]):])
                elif line[0:len(targets[6])] == targets[6]:
                    # saved in Pa, internally in GPa; this is Eeff (i.e. including 1-\nu^2)
                    self.youngProvided = float(
                        line.strip().replace(',', '.').split('\t')[1])/1.0e9
                elif line[0:len(targets[7])] == targets[7]:
                    self.xpos = float(
                        line[len(targets[7]):].strip().replace(',', '.'))
                elif line[0:len(targets[8])] == targets[8]:
                    self.ypos = float(
                        line[len(targets[8]):].strip().replace(',', '.'))
                elif line[0:len(targets[5])] == targets[5]:
                    reading_protocol = True
                elif line[0:len(targets[4])] == targets[4]:
                    reading_protocol = True
                elif line[0:len(targets[9])] == targets[9]:
                    self.version = line[len(targets[9])+1:].strip()
                elif line[0:len(targets[11])] == targets[11]:
                    meas = line[len(targets[11])+1:].strip()
                    if meas == 'DMA':
                        self.DMA = True
                elif line[0:len(targets[10])] == targets[10]:
                    break
            else:
                if line.strip() == '':
                    reading_protocol = False
                else:
                    slices = line.strip().replace(',', '.').split('\t')
                    self.protocol.append([float(slices[1]), float(slices[3])])
        f.close()

    def load(self):
        f = open(self.filename)
        stopLine = 'Time (s)'
        numeric = False
        data = []
        for riga in f:
            if numeric is False:
                if riga[0:len(stopLine)] == stopLine:
                    numeric = True
            else:
                line = riga.strip().replace(',', '.').split('\t')
                # Time (s)	Load (uN)	Indentation (nm)	Cantilever (nm)	Piezo (nm)	Auxiliary
                # skip 2 = indentation and #5 auxiliary if present
                data.append([float(line[0]), float(line[1]),
                             float(line[3]), float(line[4])])
        f.close()
        data = np.array(data)

        self.data['time'] = data[:, 0]
        self.data['force'] = data[:, 1]*1000.0
        self.data['deflection'] = data[:, 2]
        self.data['z'] = data[:, 3]

    def toggleIndCal(self, value=False):
        for c in self:
            if c.basename == 'Calib' or c.basename == 'Indentations':
                for s in c.haystack:
                    s.active = value


class Chiaro(ChiaroBase):

    def createSegments(self, bias=30):        
        sign = +1
        actualPos = 2
        nodi = []
        nodi.append(0)
        wait = 0
        for nextThreshold, nextTime in self.protocol:
            for j in range(actualPos, len(self.data['z'])):
                if self.data['time'][j] > wait + nextTime:
                    if self.version != 'old' or  (cross(self.data['z'][j], self.data['z'][j-1], nextThreshold, bias)) is True:
                        nodi.append(j)
                        wait = self.data['time'][j]
                        break
            actualPos = j
        nodi.append(len(self.data['z'])-1)
        self.nodi = nodi
        for i in range(len(nodi) - 1):
            z = self.data['z'][nodi[i]:nodi[i + 1]]
            f = self.data['force'][nodi[i]:nodi[i + 1]]
            t = self.data['time'][nodi[i]:nodi[i + 1]]
            self.append(Segment(self, z, f))
            beg = int(len(z) / 3)
            end = int(2 * len(z) / 3)
            # for future reference maybe worth adding a fit ?
            self[-1].speed = (z[end] - z[beg]) / (t[end] - t[beg])


class ChiaroGenova(ChiaroBase):
    # this procedure works for old text curves from Genova, not last version
    # waiting for the feedback from Optics11 to get it corrected
    def createSegments(self):
        vs = self.protocol
        nodi = []
        nodi.append(0)
        j = 0
        nexttime = vs[j][1]
        nextvalue = vs[j][0]
        timefound = False
        valuefound = False
        for i in range(len(self.data['time'])):
            if i == len(self.data['time']) - 1:
                nodi.append(i)
            else:
                if self.data['time'][i] <= nexttime and self.data['time'][i + 1] > nexttime:
                    timefound = True
                if (self.data['z'][i] <= nextvalue and self.data['z'][i + 1] > nextvalue) or (
                        self.data['z'][i] >= nextvalue and self.data['z'][i + 1] < nextvalue):
                    valuefound = True
            if timefound and valuefound:
                nodi.append(i)
                nexttime = self.data['time'][i]
                timefound = False
                valuefound = False
                if (j + 1 == len(vs)):
                    nodi.append(len(self.data['time']) - 1)
                    break
                else:
                    j += 1
                    nexttime += vs[j][1]
                    nextvalue = vs[j][0]
        self.nodi = nodi
        for i in range(len(nodi)-1):
            z = self.data['z'][nodi[i]:nodi[i+1]]
            f = self.data['force'][nodi[i]:nodi[i+1]]
            t = self.data['time'][nodi[i]:nodi[i+1]]
            self.append(Segment(self, z, f))
            beg = int(len(z)/3)
            end = int(2*len(z)/3)
            # for future reference maybe worth adding a fit ?
            self[-1].speed = (z[end]-z[beg])/(t[end]-t[beg])

##################################
##### Nanosurf ###################
##################################


class NanoSurf(DataSet):

    def check(self):
        f = open(self.filename)
        signature = f.readline()
        f.close()
        if signature[0:9] == '#Filename':
            return True
        return False

    def header(self):
        f = open(self.filename)
        targets = ['#Cantilever=', '#Spring-Constant=',
                   '#Deflection-Sensitivity=', '#Filename=', '#SpecMap', '#SpecMode']

        def outNum(text):
            s = ''
            for c in text:
                if c.isdigit() or c in ['.', 'e', '-', '+']:
                    s += c
                else:
                    break
            return float(s)
        map_dim = [None, None]
        map_size = [None, None]
        isMap = False
        for line in f:
            if line[0:len(targets[2])] == targets[2]:  # 1.4736e-07m/V
                # NB: internal units are nm/V
                self.cantilever_lever = outNum(line[len(targets[2]):])*1e9
            elif line[0:len(targets[1])] == targets[1]:
                # NB: internal units are nm/V
                self.cantilever_k = outNum(line[len(targets[1]):])
            elif line[0:len(targets[0])] == targets[0]:
                self.cantilever_type = line[len(
                    targets[0]):].strip()  # guess the radius
                data = self.cantilever_type.strip().split('-')
                if len(data) > 1:
                    if 'um' in data[1]:
                        radius = float(data[1].replace('um', ''))*1000.0
                        self.tip_radius = radius
                    if len(data) > 2:
                        if 'um/s' in data[2]:
                            speed = float(data[1].replace('um/s', '')) * 1000.0
                            self.protocol_speed = speed
            elif line[0:len(targets[3])] == targets[3]:
                self.original_filename = line[len(targets[3]):].strip()
            elif line[0:len(targets[5])] == targets[5]:
                if line[line.find('=')+1:].strip() == 'Map':
                    isMap = True
            elif (line[0:len(targets[4])] == targets[4]) and (isMap is True):
                tp = line[line.find('-')+1:line.find('=')]
                if tp == 'Dim':
                    map_dim = line[line.find('=')+1:].split(';')
                elif tp == 'Size':
                    map_size = line[line.find('=')+1:].split(';')
                elif tp == 'CurIndex':
                    curindex = int(line[line.find('=') + 1:])
                    nx = int(map_size[0])
                    ny = int(map_size[1])
                    coordinates = []
                    dx = (float(map_dim[1]) - float(map_dim[0]))/(nx-1)
                    dy = (float(map_dim[3]) - float(map_dim[2]))/(ny-1)
                    for i in range(nx):
                        for j in range(ny):
                            coordinates.append((i*dx, j*dy))
                    self.xpos, self.ypos = coordinates[curindex]
            elif line[0] != '#':
                break
        f.close()

    def load(self):
        data = []
        dummy = True
        collected = 0
        f = open(self.filename)
        for line in f:
            if dummy is True:
                if line[0:10] == '#Spec-Data':
                    dummy = False
                    self.protocol.append(collected)
                    # Note the header line
                    # Spec-Data=Z-Axis Sensor [m];Deflection [V];Z-Axis-Out [m]
                    # Spec-Data=Z-Axis Sensor [m];Deflection [N];Z-Axis-Out [m]
                    # Units for Deflection can be either V or N !
                    self.data_channels = line[11:].strip().split(';')
                elif line[0:11] == '#Spec-Phase':
                    self.append(Segment(self))
                elif line[0:10] == '#Spec-Name':
                    if line[16:].strip() == 'forward':
                        self[-1].direction = MODE_DIRECTION_FORWARD
                    elif line[16:].strip() == 'backward':
                        self[-1].direction = MODE_DIRECTION_BACKWARD
                    else:
                        self[-1].direction = MODE_DIRECTIONS_PAUSE
                elif line[0:10] == '#Spec-Data':
                    self[-1].header = line[11:].strip()
            elif dummy is False:
                if line.strip() == '':
                    dummy = True
                else:
                    data.append(
                        [i for i in map(float, line.strip().split(';'))])
                    collected += 1
        self.protocol.append(len(data))
        f.close()
        data = np.array(data)
        # Now get as much information as possible out of the curves
        # Spec-Data=Z-Axis Sensor [m];Deflection [N];Z-Axis-Out [m]
        # mmmm, try to guess it

        check = np.abs(np.mean(data[:100, 1])*1e9)
        if check < 1000:
            self.data['force'] = data[:, 1]*1e9
        else:
            self.data['force'] = data[:, 1] * self.cantilever_lever
        self.data['z'] = data[:, 0]*1e9

    def createSegments(self):
        for i in range(len(self.protocol)-1):
            z = self.data['z'][self.protocol[i]:self.protocol[i+1]]
            f = self.data['force'][self.protocol[i]:self.protocol[i+1]]
            self[i].setData(z, f, reorder=True)


##########################
###Synthetic Hertz Data###
##########################

# Data file: .tsv file with force and displacement colums
            # only one segment, can add more
            # No header, use mother class default parameters for K, R

class Easytsv(DataSet):
    _leaf_ext = ['.tsv']

    def check(self):
        f = open(self.filename)
        l1 = f.readline().strip()
        f.close()
        if l1 == '#easy_tsv':
            return True
        else:
            return False

    def load(self):
        f = open(self.filename)
        lines = list()
        for i in range(3):  # first three lines of the file
            lines.append(f.readline().strip())  # strip removes \n
        f.close()
        # K value needed by program
        self.cantilever_k = float(lines[1][lines[1].find(':')+1:].strip())
        # R value needed by program
        self.tip_radius = float(lines[2][lines[2].find(':')+1:].strip())
        data = np.loadtxt(self.filename, delimiter='\t', skiprows=4)
        self.data['force'] = data[:, 1]
        self.data['z'] = data[:, 0]

    def createSegments(self):
        self.append(Segment(self))
        self[0].setData(self.data['z'], self.data['force'])


# JPK not used as metadata does not contain tip radius

# class Jpk(DataSet):
#     _leaf_ext = ['.jpk-force']

#     def check(self):
#         return True

#     '''
#     def check(self):
#         f = open(self.filename)
#         l1 = f.readline().strip()
#         f.close()
#         if l1 == '#easy_tsv':
#             return True
#         else:
#             return False
#     '''

#     def load(self):
#         f = afmformats.load_data(self.filename)

#         # inspect the columns
#         print(f[0].columns)

#         fd = afmformats.afm_fdist.AFMForceDistance(
#             f[0]._raw_data, f[0].metadata, diskcache=False)

#         self.data['force'] = [fd.appr['force']*1e9, fd.retr['force']*1e9]
#         self.data['z'] = [
#             np.flip(fd.appr['height (piezo)']*1e9), np.flip(fd.retr['height (piezo)']*1e9)]

#         metadata = fd.metadata
#         print(fd.metadata)
#         self.cantilever_k = metadata['spring constant']
#         # need to give user chance to input tip radius in interface when jpk is clicked
#         self.tip_radius = 5000  # nm

#     def createSegments(self):
#         segment = ['forward', 'backward']
#         for i in range(len(segment)+1):
#             self.append(Segment(self, self.data['z'], self.data['force']))
#             self[i].setData(self.data['z'][i-1], self.data['force'][i-1])
