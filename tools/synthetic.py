import numpy as np

E = 6245
N = 40
R = 3400e-9
cp = 3.0e-6
indmax = 7e-6
cpoint = 1000
indpoint = 7000
noiselevel = 1e-10
noisewidth = 1e-9
k = 0.032

def hertz(x, R, E, nu=0.5):
    return 4*E/3/(1-nu**2)*np.sqrt(R)*x**1.5

def emptyCurve():
    curve = {
        "filename": "noname",
        "date": "2021-12-02",
        "device_manufacturer": "synthetic",
        "tip":{
            "geometry": "sphere",
            "radius": R
        },
        "spring_constant": k, 
		"segment": "approach",
        "speed": 1.25e-6,
        "data":{
            "F":[],
            "Z":[]
        }
    }
    return curve

xpost = np.linspace(0, indmax, indpoint)
Fpost = hertz(xpost, R, E)
zpost = xpost+Fpost/k

curves = []
for i in range(N):
    
    realcp = cp  + 100.0e-9*np.random.normal(scale=1)
    zpre = np.linspace(0, realcp, cpoint)
    Fpre = np.zeros(len(zpre))

    F = np.append(Fpre, Fpost)
    z = np.append(zpre, zpost+realcp)

    # now randomize it
    noise = noiselevel * np.random.normal(scale=.1, size=F.shape)
    F += noise
    
    cv = emptyCurve()
    cv['data']['Z']=list(z)
    cv['data']['F']=list(F)
    curves.append(cv)

import json

exp = {'Description':'Synthetic data','E':str(E)}
pro = {}
cvs = curves

json.dump({'experiment':exp,'protocol':pro,'curves':curves},open('synth.json','w'))

import matplotlib.pyplot as plt
for c in curves:
    plt.plot(c['data']['Z'],c['data']['F'])
plt.show()

print('Terminated')
