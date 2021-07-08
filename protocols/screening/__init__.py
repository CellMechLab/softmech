from ..importer import listModules,getModule

MODULE = 'protocols.screening'

def list():
    return listModules(__path__[0],MODULE)

def get(name):
    mod = getModule(name,MODULE)
    return mod.Screen()
