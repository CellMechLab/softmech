from ..importer import listModules,getModule

MODULE = 'protocols.filters'

def list():
    return listModules(__path__[0],MODULE)

def get(name):
    mod = getModule(name,MODULE)
    return mod.Filter()