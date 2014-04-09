#!/X/tools/binlinux/xpython
import logging
import os, re
import simplejson as json
from .  import fnparser
from xconvert import detailedInfo, readHeaders, writeHeaders, addHeaders, clearHeaders, newIINFO
from . import Odict as dict
from . import Node
from .. import globals
from .. import logger
from .. import util

reload(fnparser)
reload(globals)

__version__ = '1.10'

_fnparser_version_ = fnparser.__version__
logger.getLogger().debug('FileNameParser version: %s' % _fnparser_version_)

"""
New features:
    
    1). consistent info format between XTexture/XPalette
    2). easier inheriting of proxy/tile attrs


"""
class XTexture(Node):
    """
    class XTexture():
    
        DESCRIPTION:        
            This class represents a single texture in the texture publishing pipeline


        USAGE:
            Querying:
                XTexture.attrs:
                    Shows parser attributes (file name)

                XTexture.info:
                    Shows palette info (internal use)

                XTexture.fileattrs:
                    Shows texture attributes (file info, IINFO, etc.)
                    
                info keys: ['tag', 'file', 'info', 'nodes', 'parent', 'colorSpace']
    
    XTexture.info{
        XTexture.fileattrs{ (info)
    
    v1.10
        - added _setDeepInfo method to override key attributes
        
    v1.09
        - added warnings dictionary for the texture to pass warning flags to the manager

    v1.07
        - added pathIn, filenameIn
    
    v1.06
        - added _msgLen, msgStr method
    
    v1.05
        - noncolor always set at initialization, publish tag added
        - added 'tileType', 'coord' attributes to aid importing palettes
        - added default colorspace
        - added readable attribute to flag broken textures before they get converted
        - updated 
        
    v1.04
        - updated colorspace methods to not set/return values in lowercase
    
    v1.03
        - added XTexture.__texture attribute to store the original value
        - added __repr__ for output
        - added formatResolution
    
    v1.02
        - added support for color/noncolor
    
    v1.01
        - added error checking for bad file names ( from parser )
        - 'parent' attribute is no longer a dictionary
        
    """
    def __init__(self, texture=None, parent=None, **kwargs):
        Node.__init__(self, parent=parent)

        self.__version  = __version__
        self.__texture  = ''                # the texture assigned to this node
        self.__env      = kwargs.get('env', 'standalone')
        self.__debug    = kwargs.get('debug', False)
        self.__verbose  = kwargs.get('verbose', False)
        self.__mode     = kwargs.get('mode', 'default')
        
        self.__attrs    = dict(
             texture    = '',               # the texture, in whatever form we are dealing with
             parent     = '',               # the origin texture (ie the original artist texture (NOT the parent GUI)         
             )
        self.__note_attrs=[]                # attributes to be added to the notes GUI
        
        self.__info=dict()                  # holds the texture's attributes
        self.__info.update(publish=True)    # is the texture to be published
        self.__info.update(tag='')          # tag for color/non color
        self.__info.update(file='')         # filenameOut
        
        self.__info.update(info=dict()) 
        self.__info.update(nodes=dict())
        self.__info.update(tiled=False)
        self.__info.update(parent='')
        self.__fileattrs    = dict()        # file attributes
        self.__parser = fnparser.FileNameParser(debug=self.__debug)
        self.__proxy_path=''                # path for the proxy texture
        self.__pathIn=''                    # store the incoming path (for renames)
        self.__filenameIn=''                # store the incoming filename (for renames)
        self.__readable = True              # is the texture readable?
        self._msgLen = 0                    # lex to calculate buffer
        self.__isLib = False   
        self._lib_expr = "(/X/projects/(\w+)/SHOTS/(\w+)/lib/textures/([\w]+))/(\w+)/(\w+)/(.*)$"
        
        
        self.__warnings = dict(
               unknown_channel=False,
               )
        
        
        if texture:
            if os.path.exists(texture):
                logger.getLogger().debug('creating XTexture: %s' % texture)
                self.__texture = texture
                self.__pathIn, self.__filenameIn=os.path.split(texture)
                self.__parser(texture)
                self.__fileattrs=self.getFileAttributes(texture)
                self.__attrs=self.parser.attrs
            else:
                # retain a proxy path for tiles
                self.__proxy_path=texture                       
            
            if self.__mode=='default':
                if 'resolution' not in self.__fileattrs.keys():
                    self.__readable = False
                    self.valid=False
                    self.__fileattrs.update(colorspace='')

        # PRIVATE STUFF
        self.__private = dict()
        self.__private.update(channels=self._check_channels())
        
        if self.__debug:
            logger.enableDebugging()
    
    def __repr__(self):
        return '<XTexture: %s>' % self.__texture
    
    def getFileAttributes(self, texture):
        """
        Build the basic texture attributes
        """
        tex_attrs=dict()
        headers=dict()
        statinfo=None
        
        if self.__mode=='default':
            tex_attrs = detailedInfo(texture)
            headers=readHeaders(texture)
            statinfo = os.stat(texture)
            
        # BUILD ATTRIBUTES  
        attrs=dict()

        if self.__env=='maya':
            attrs.update(shader_conn=dict())
            attrs.update(displacement=False)            
        
        if tex_attrs:
            for attr, val in tex_attrs.iteritems():
                if attr=='filename':
                    self.__info['parent']=val
                elif attr=='channel':
                    # CHANNEL SUBSTITUTION
                    val=re.sub(', ', '', val)
                    attrs.update({'channels':val})
                else:
                    attrs.update({attr:val})
        
        attrs.update(noncolor=True)        
        if statinfo:
            attrs.update(bytes=statinfo.st_size)
            attrs.update(size=util.getSizeInKilobytes(statinfo.st_size))
        else:
            attrs.update(bytes=0)
        attrs.update(bounds=None)
        attrs.update(user=util.getOwner(texture))
        attrs.update(date='')
        attrs.update(valid=self.valid)
        attrs.update(colorspace='sRGB')
        
        # PULL ATTRIBUTES FROM THE PARSER
        if self.__parser.fileext.lower()=='exr':
            attrs.update(colorspace='linear')

        if self.__parser.isTiled:
            self.__info.update(tiled=True)
            attrs.update({'tileType':self.__parser.ttype})
            attrs.update({'coord':self.__parser.coord})
        
        # ADD COLOR/NON-COLOR DATA HERE - JEP CHECK
        if self.__parser.channel:
            chan=self.__parser.channel
            attrs.update({'type':self.__parser.properChannel(chan)})
            if self.__parser.properChannel(chan, short=True) in 'col sov sdf ssc sca scrm'.split():
                attrs.update(noncolor=False)
        else:
            logger.getLogger().debug('cannot determine channel for texture "%s"' % texture)


        self.__info.update(info=attrs)
        
        
        libexpr = re.compile(self._lib_expr) 
        fmatch = libexpr.match(texture)
        if fmatch:
            self.isLib=True
        
        if headers:
            if 'ColorSpace' in headers.keys():
                logger.getLogger().debug('detected mrx:colorspace: "%s"' % headers.get('ColorSpace'))
                # TODO: why add this twice? Check please...
                self.__fileattrs.update(colorspace=headers.get('ColorSpace'))
                self.__info.get('info').update(colorspace=headers.get('ColorSpace'))
        
        self.buildNotes()
        return attrs
    
    def buildNotes(self):
        """
        Builds the notes attribute, for flagging certain texture attributes
        """
        if self.info.get('info').get('mudbox'):
            self.__note_attrs.append('mudbox')

        if self.info.get('info').get('depth') not in globals.OIIO_DATATYPES.values():
            if self.info.get('info').get('depth')=='uint1':
                self.__note_attrs.append('no data')
            else:
                self.__note_attrs.append(self.info.get('info').get('depth'))

        # ALERT FOR INVALID FILENAMES
        if not self.valid:
            self._addNote('invalid filename')

    @property
    def parser(self):
        return self.__parser

    # - ATTRIBUTES ----

    @property
    def info(self):
        return self.__info
    
    @property
    def fileattrs(self):
        return self.__fileattrs
    
    @fileattrs.setter
    def fileattrs(self, val):
        self.__fileattrs=val
        return self.__fileattrs
    
    @property
    def attrs(self):
        return self.__attrs

    @property
    def private(self):
        return self.__private

    @property
    def notes(self, nice=True):
        """
        Return the notes attribute, formatted if needed
        """
        retval=''
        if self.__note_attrs:            
            if nice:
                for attr in self.__note_attrs:
                    if attr:
                        retval+='%s, ' % attr
                retval=retval.rstrip(', ')
            else:
                retval=self.__note_attrs
                
        return retval

    def proxyPath(self):
        return self.__proxy_path

    def getPrivateAttr(self, attr):
        retval=''
        if attr in self.__private.keys():
            retval=self.__private.get(attr)
        return retval
    
    def addNode(self, val):
        if val not in self.__info.get('nodes'):
            self.__info['nodes'].append(val)
    
    def getNodes(self):
        return self.__info.get('nodes', [])
    
    # - INTERNAL ----
    def _addNote(self, val):
        """
        Add a texture note
        """
        self.__note_attrs.append(val)
        return self.__note_attrs
    
    def _check_channels(self):
        retval=str(self.fileattrs.get('channels'))
        retval=re.sub(',', '', retval)
        if self.fileattrs.get('channels'):
            if self.fileattrs.get('channels') not in ['RGB', 'RGBA', 'RGBAZ', 'R', 'G', 'B', 'A', 'Z']:
                self.__note_attrs.append('Unknown Channel: %s' % self.fileattrs.get('channels'))
        return retval
    
    def _msgStr(self, idx, cutoff=0):
        """
        Format an information string for the command line output
        """
        si=str(idx)
        ilen=5-len(si)

        idxstr='%d.%s'% (idx, ' '*ilen)
        tlen=len(self.__texture)
        spcLen=self._msgLen-tlen
        spacer=' '*spcLen
        chan=self.properChannel
        chan_spc_len=12-len(chan)
        res=self.resolution()
        nc=self.fileattrs.get('noncolor')
        ncmsg='   color'
        if nc:
            ncmsg='noncolor'
        
        cs='  sRGB'
        if self.colorspace.lower()=='linear':
            cs='linear'
        
        msg = '%s %s    %s     %s%s  %s    %s   %s  ' % (idxstr, self.__texture, spacer, ' '*chan_spc_len, chan, res, ncmsg, cs)
        headers=readHeaders(self.__texture)
        if headers:
            for k, v in headers.iteritems():
                if k in 'artist asset colorspace noncolor'.split():
                    hstr='mrx_%s:%s' % (k, v)
                    hstrl=30-len(hstr)                    
                    msg+='%s%s' % (hstr, ' '*hstrl)
        
        return msg
    
    # - ATTRIBUTES ----
    @property
    def mode(self):
        return self.__mode

    @mode.setter
    def mode(self, val):
        self.__mode=val
        return self.__mode

    def pprint(self):
        """
        "Pretty print" of the XTexture's attributes
        """
        return json.dumps(self.info, indent=5).strip('{}')
    
    @property
    def texture(self):
        return self.__texture
    
    # TODO: clean this one up
    def setInfo(self, **kwargs):
        """
        Updates the XTexture primary attributes with keyword/value. In the event we need to 
        update file attributes manually, send the values to the parser as well
        
        Primary attributes are:       
        publish, tag, file, info, nodes, tiled, parent
        """
        for attr, val in kwargs.iteritems():
            if attr=='file':
                self.__parser._setName(val)
            self.__info.update({attr:val})
    
    def _setDeepInfo(self, **kwargs):
        """
        Updates the info dictionary with keyword/value. In the event we need to 
        update file attributes manually, send the values to the parser as well
        
        Common attributes are:
        channels, depth, resolution, format, noncolor, bytes, size,
        bounds, user, date, valid, colorspace, tileType, coord, type
        """
        for attr, val in kwargs.iteritems():
            if attr=='tileType':
                self.__parser.attrs.update(ttype=val)
            if attr=='coord':
                self.__parser.attrs.update(coord=val)
            if attr=='type':
                self.__parser.channel=val
            self.__info.get('info').update({attr:val})
    
    def setTiled(self, val):
        """
        Flags the texture as tiled
        """
        self.__info.update(tiled=val)
    
    def setAttr(self, **kwargs):
        """
        Updates the info:info dictionary with keyword/value
        """
        for attr, val in kwargs.iteritems():
            self.__fileattrs.update({attr:val})

    @property
    def bytes(self):
        return self.__info.get('info').get('bytes', 0)
    
    @property
    def noncolor(self):
        return self.__fileattrs.get('noncolor')
    
    @noncolor.setter
    def noncolor(self, val):
        self.__fileattrs.update(noncolor=val)
        return self.__fileattrs.get('noncolor')
    
    @property
    def depth(self):
        return self.info.get('info').get('depth')

    @property
    def colorspace(self):
        try:
            return self.__fileattrs.get('colorspace')
        except:
            return ''
        #return self.info.get('colorSpace')
    
    @colorspace.setter
    def colorspace(self, val):
        self.__fileattrs.update(colorspace=val)
        return self.__fileattrs.get('colorspace')
    
    @property
    def mipmapped(self):
        retval=False
        if 'mipmap_levels' in self.info.get('info').keys():
            retval=True
        return retval
    
    @property
    def typ(self):
        return self.info.get('info').get('type')
    
    @typ.setter
    def typ(self, val):
        self.__fileattrs.update({'type':val})
        return self.__fileattrs.get('type')
    
    def resolution(self, nice=False):
        result='0x0'
        try:
            if not nice:
                result = '%sx%s' % (str(self.__fileattrs['resolution'][0]), str(self.__fileattrs['resolution'][1]))
            else:
                try:
                    result = util.formatResolution(self.__fileattrs['resolution'][0], self.__fileattrs['resolution'][1])
                except:
                    result = '-----------'
        except:
            pass
        
        rl=11-len(result)
        return '%s%s' % (' '*rl, result)
    
    @property
    def readable(self):
        return self.__readable
    
    # - PARSER ----

    @property
    def fullpath(self):
        return self.__parser.fullpath

    @property
    def pathIn(self):
        return self.__pathIn

    @property
    def filenameIn(self):
        return self.__filenameIn
    
    @property
    def fullpathOut(self):
        return self.__parser.fullpathOut

    @property
    def filenameOut(self):
        return self.__parser.filenameOut
   
    @filenameOut.setter
    def filenameOut(self, val):
        self.__parser.filenameOut=val
        return self.__parser.filenameOut

    @property
    def isProxy(self):
        return self.__parser.isProxy

    @property
    def isTiled(self):
        return self.__parser.isTiled

    @property
    def filename(self):
        return self.__parser.filename
    
    @property
    def basename(self):
        return self.__parser.basename

    @basename.setter
    def basename(self, val):
        self.__parser.attrs.update(base=val)
        return self.__parser.attrs.get('base') 

    @property
    def ttype(self):
        result=''
        if self.isTiled:
            result=self.__parser.attrs.get('ttype')
        return result

    @property
    def coord(self):
        result=''
        if self.isTiled:
            result=self.__parser.attrs.get('coord')
        return result
    
    @coord.setter
    def coord(self, val):
        self.__parser.coord=val
        self.__parser.isTiled=True
        return self.__parser.attrs.get('coord')
    
    @property
    def fileext(self):
        return self.__parser.attrs.get('fileext')
    
    @fileext.setter
    def fileext(self, val):
        self.__parser.fileext=val
        return self.__parser.attrs.get('fileext')
    
    @property
    def channel(self):
        retval=''
        if self.__parser.attrs.get('channel'):
            retval=self.__parser.attrs.get('channel')
        return retval
    
    @channel.setter
    def channel(self, val):
        self.__parser.attrs['channel']=val
        self.__parser.changeChannel(val)
        return self.__parser.attrs.get('channel')
    
    @property
    def properChannel(self):
        return self.parser.properChannel()
    
    @property
    def valid(self):
        if self.isProxy:
            self.__valid=False
        elif not self.__readable:
            self.__valid=False
        else:
            self.__valid=self.__parser.valid()
        return self.__valid
    
    @valid.setter
    def valid(self, val):
        self.__valid=val
        return self.__valid
    
    @property
    def basenameFull(self):
        return self.__parser.basenameFull
    
    @property
    def isLib(self):
        return self.__isLib
    
    @isLib.setter
    def isLib(self, val):
        self.__isLib=val
        return self.__isLib

class TiledTexture(XTexture):
    
    def __init__(self, texture=None, parent=None):
        XTexture.__init__(self, parent=parent)