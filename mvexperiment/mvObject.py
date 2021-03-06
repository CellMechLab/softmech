import os
import pickle
import uuid


class MvAbstract(object):
    def __init__(self):
        self._children = []
        self.uniqid = uuid.uuid1()

    def __iter__(self):
        return self._children.__iter__()

    def __len__(self):
        return len(self._children)

    def __cmp__(self, other):
        if isinstance(self, other):
            return self.uniqid == other.uniqid
        else:
            return self.uniqid == other

    def search(self, text):
        for c in self._children:
            if c.uniqid == text:
                return c
        return False

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._children[index]
        else:
            for child in self:
                if child == index:
                    return child
                else:
                    found = self.search(index)
                    if found is not False:
                        return found
            raise KeyError(
                "ID {} not found in the descending leaves".format(index))

    def __setitem__(self, key, value):
        self._children[key] = value

    def __delitem__(self, key):
        del(self._children[key])

    def append(self, child):
        if hasattr(child, 'parent'):
            child.parent = self
        self._children.append(child)


class MvObject(MvAbstract):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self._haystack = None
        self._empty = True
        self._leaf = False
        self.categories = {}

    @property
    def haystack(self):
        if self._haystack is None:
            if self.is_leaf() is True:
                self._haystack = [self]
            else:
                self._haystack = []
                for child in self:
                    self._haystack.extend(child.haystack)
        return self._haystack

    def add_category(self, name):
        if name not in self.categories:
            self.categories[name] = None
            if self.is_leaf() is False:
                for child in self:
                    child.add_category(name)
        self.parent.add_category(name)

    def set_category(self, name, value, recursive=True):
        self.add_category(name)
        self.categories[name] = value
        if recursive is True and self.is_leaf() is False:
            for child in self:
                child.set_category(name, value, recursive)

    @haystack.setter
    def haystack(self, haystack):
        self._haystack = None

    def search(self, text):
        if self.is_leaf() is True:
            return False
        for c in self.haystack:
            if c.uniqid == text:
                return c
        return False

    def is_leaf(self):
        return self._leaf

    def is_empty(self):
        return self._empty

    def save(self, filename=None):
        if filename is None:
            filename = uuid.uuid1() + '.pickle'
        fpickle = open(filename, 'w')
        pickle.dump(self, fpickle)
        fpickle.close()


def load(filename):
    if os.path.isfile(filename) is False:
        raise FileNotFoundError('Haystack file {} not found'.format(filename))
    fpickle = open(filename, 'r')
    e = pickle.load(fpickle)
    fpickle.close()
    return e
