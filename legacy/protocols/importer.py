from os import walk
from importlib import import_module

def listModules(mypath,mypackage):
    modules = {}
    for (dirpath, dirnames, filenames) in walk(mypath):
        for f in filenames:
            if (f[0]!='_') :
                myid = f[:-3]
                try:
                    mod = import_module('.'+myid,mypackage)
                    myname = mod.NAME
                    modules[myid]=myname
                except ModuleNotFoundError:
                    pass
    return modules

def getModule(mymodule,mypackage):
    mod = import_module('.'+mymodule,mypackage)
    return mod