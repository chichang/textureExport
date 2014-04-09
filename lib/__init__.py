#!/usr/bin/python2.6
import ConfigParser
from thread import get_ident as _get_ident
import sys
import simplejson as json
from UserDict import DictMixin

__all__ = ['process', 'Node', 'Odict', 'SuperConfig', 'isList']

class Node(object):
    """base node class for Texturizer (based on mTools.MClass)"""
    def __init__(self, name=None, parent=None):
        
        self._parent = None
        self._name = None
        self._gui = None

        self.setParent(parent)
        self._attrs = dict()

        self.stderr = sys.stderr.write
        self.stdout = sys.stdout.write

    def pprint(self):
        attrs = self._attrs.copy()
        for k, v in attrs.iteritems():
            if type(v) not in [str, list, tuple, dict]:                
                attrs.update({k: unicode(v)})
        return json.dumps(attrs, indent=4)

    def setParent(self, val):
        self._parent = val
        return val

    def getParent(self):
        return self._parent

    def getAttrs(self):          
        return self._attrs

    def getAttr(self, attr):
        return self._attrs.get(attr)
    
    #TODO: check this    
    def setAttr(self, attr, val):
        if isList(self.getAttr(attr)):
            self._attrs[attr].append(val)
            #self.__setattr__(attr, val)
        self._attrs[attr] = val
        self.__setattr__(attr, val)
        return self._attrs[attr]
    
    def remAttr(self, attr):
        if self.getAttr(attr):
            return self._attrs.pop(attr)
        
    def setGui(self, gui):
        self._gui = gui
        
    def getGui(self):
        return self._gui
    
    def write(self, line):
        self.stdout(line)
        if self.getGui() :
            self.getGui().write(linein=line)


class Odict(dict, DictMixin):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__end
        except AttributeError:
            self.clear()
        self.update(*args, **kwds)

    def clear(self):
        self.__end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.__map = {}                 # key --> [key, prev, next]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self.__end
            curr = end[1]
            curr[2] = end[1] = self.__map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next = self.__map.pop(key)
        prev[2] = next
        next[1] = prev

    def __iter__(self):
        end = self.__end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.__end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = self.__map, self.__end
        del self.__map, self.__end
        inst_dict = vars(self).copy()
        self.__map, self.__end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems


    def __repr__(self):
        if not self:
            return '{}'
        #return '{%r}' %  self.items()
        dictrepr = dict.__repr__(self)
        #return '{%s}' %  dictrepr
        return '%s' %  dictrepr
    
    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, Odict):
            if len(self) != len(other):
                return False
            for p, q in  zip(self.items(), other.items()):
                if p != q:
                    return False
            return True
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other


class SuperConfig(ConfigParser.ConfigParser):
    '''ConfigParser object that can save and load lists as well as strings'''
    def __init__(self, **kwargs):
        ConfigParser.ConfigParser.__init__(self, **kwargs)
    
    def get(self, section, option):
        """ Get a parameter
        if the returning value is a list, convert string value to a python list"""
        try:
            value = ConfigParser.ConfigParser.get(self, section, option)
            if value:
                if (value[0] == "[") and (value[-1] == "]"):
                    return eval(value)
                
            return value
        except:
            return ''
        
        
def isList(item):
    from types import ListType, TupleType
    retval = False
    if type(item) in (ListType, TupleType):
        retval = True

    return retval