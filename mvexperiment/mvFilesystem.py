import os
import time
import zipfile

from . import mvObject
from .pathto import Path as ppath

#from .zippo import Path as zpath


class MvNode(mvObject.MvObject):
    _leaf_ext = ['.png']

    def __init__(self, filename=None, parent=None):
        super().__init__(parent)
        self._filehandler = None
        # try:
        if filename is not None:
            if str(filename) == filename:
                if '.zip' in filename:
                    if os.path.exists('./tmp') is False:
                        os.mkdir('./tmp')
                    name = '{}-{}-{}-{}-{}'.format(*time.gmtime()[:5])
                    zp = zipfile.ZipFile(filename)
                    zp.extractall(path='./tmp/'+name)
                    self._filehandler = ppath('./tmp/'+name)
                else:
                    self._filehandler = ppath(filename)
            else:
                self._filehandler = filename
        # except:
        #    raise FileNotFoundError("Location set to a wrong value {}".format(filename))

    @property
    def filename(self):
        return self._filehandler

    @property
    def basename(self):
        return self._filehandler.name

    @property
    def name(self):
        return self._filehandler.name

    def is_leaf(self):
        return self._filehandler.is_file()

    def check(self):
        return True

    def browse(self):
        if self._filehandler is None:
            raise FileNotFoundError("Location not set")
        if self.is_leaf() is True:
            return
        for ddir in self._filehandler.iterdir():
            if ddir.is_dir() is True:
                newdir = self.__class__(parent=self, filename=ddir)
                newdir.browse()
                if newdir.is_empty() is False:
                    self.append(newdir)
                    self._empty = False
            elif ddir.is_file() is True:
                if self._leaf_ext is not None:
                    if str(self._leaf_ext) == self._leaf_ext:
                        self._leaf_ext = [self._leaf_ext]
                    for ex in self._leaf_ext:
                        if ddir.name[-len(ex):] == ex:
                            newleaf = self.__class__(
                                parent=self, filename=ddir)
                            if newleaf.check() is not False:
                                self.append(newleaf)
                                self._empty = False
