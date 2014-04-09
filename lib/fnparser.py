#!/X/tools/binlinux/xpython
import os, re
from string import Template
from string import Template
import logging
from . import Odict as dict
from .. import globals
from .. import util
from .. import logger

reload(globals)

__version__ = '2.09'

class FileNameParser(object):
    """
    class FileNameParser():
    
        DESCRIPTION:        
            This class analyzes a file texture name and can perform intelligent substitution. 
            This object also attempts to guess the material channel information based on the name
        
        NOTES:            
            needs fullpathOut - fullpath will reflects the original texture, and won't take up any changes
    
        VERSION HISTORY:
            v2.08
                - updated getCoord with an update argument, to prevent inadvertant updating of texture coord when a 
                  user has four digits at the end of the basename                  
                
            v2.07
                - added error checking for bad file names
                - added __basenameFull to validate basenames

    """
    def __init__(self, debug=False, verbose=False):
        
        self._tileExprs = globals.TILEEXPRS
        
        if debug:
            logger.enableDebugging()
            
        self.__verbose          = verbose
        self.__version          = __version__  
        self._whchExpr          = "\<(?P<typ>UDIM|UVTILE)\>"        
        self._fileExpr          = "^(?P<head>.*)%s(?P<tail>.*)"
        self._chanExpr          =  '(_|\.)(?P<channel>%s)(_|\.)'      # TODO: this fails if texture channel is first in string
        #self._chanExpr         =  '(_|\.)(?P<channel>%s)(_|\.|)'     # changing this to accomdate a channel name at the end of the base 
        self._baseExpr          = ''                                  # the string used to replace the channel later, if need be  
        self._fnExpr            = ''                                  # string containing 
        
        self.__path             = ''  
        self.__isTiled          = False
        self.__filename         = ''                                  # filename in (the original filename)
        self.__filenameOut      = ''  
        self.__fullpath         = ''
        self.__fullpathOut      = ''
        self.__basenameFull     = ''
        self.__attrs            = dict()
        self.__valid            = True                              # is filename valid?
        self.debug              = debug
        
        self.rules = dict(                                          # deprecated
          standard              = '${base}.${fileext}',                   
          tiled                 = '${base}.${coord}.${fileext}',                  
          )
        
    def __call__(self, *args):
        self.__filename = args[0]
        self.parse(args[0], verbose=self.__verbose)
    
    def pprint(self, debug=False):
        """ For parser debugging """
        if debug:
            attrs=['self._whchExpr', 'self._fileExpr', 'self._chanExpr', 'self._baseExpr', 'self._fnExpr']
            maxStr=max([len(x) for x in attrs])
            for attr in attrs:
                val=eval(attr)
                spc=((maxStr+1)-len(attr))
                print '%s%s: %s%s%s' % (attr, ' '*spc, val, ' '*((40 - spc) - len(val)), ' ')
        else:
            mx=max([len(k) for k in self.attrs.keys()])
            for attr in 'base coord channel ttype fileext path'.split():
                spc= mx - len(attr) + 5
                if attr in self.attrs.keys():
                    if self.attrs.get(attr):
                        if attr!='channel':                    
                            print '%s:%s"%s"' % (attr, ' '*spc, self.attrs.get(attr))
                        else:
                            print '%s:%s"%s"' % (attr, ' '*spc, self.properChannel())
            
    
    def _setName(self, val):
        """ Function to just set the file name without regard for rules """
        if val:
            fn = os.path.split(val)[-1]
            bn, fileext = os.path.splitext(fn)
            fileext = re.sub('^\.', '', fileext)
            self.__filename=fn
            self.__filenameOut=fn  # set this initially, so that we always have a value to form fullpath out
            self.attrs.update(base=bn, fileext=fileext)
            coord, ttype = self.getCoord(bn)
            # REMOVE COORD FROM BASENAME
            if ttype:
                if not coord:
                    bn=util.stripName(re.sub('<%s>' % ttype, '', bn))
                else:                
                    bn=util.stripName(re.sub(coord, '', bn))
                    
            self.attrs.update(base=bn)
            channel = self.getChannel(fn)
            
            self._fnExpr = re.sub(self.basename, '${base}', self.filename)
            if self.isTiled:
                self._fnExpr = re.sub(self.coord, '${coord}', self._fnExpr)
            self._fnExpr = re.sub(self.fileext, '${fileext}', self._fnExpr)   
                    
            #self.validate()
            
            if channel:
                self._baseExpr=re.sub(channel, '${channel}', bn)
            
            channel_proper=self.properChannel(channel)
            self.attrs.update(channel=channel)
        
    def parse(self, path='', verbose=False):
        """ Parse attributes from the file name """
        if path:
            self.__fullpath=path
        else:
            path=self.fullpath
        
        if path:
            fp, fn = os.path.split(path)
            bn, fileext = os.path.splitext(fn)
            fileext = re.sub('^\.', '', fileext)
            self.__path=fp
            self.__filename=fn
            self.__filenameOut=fn  # set this initially, so that we always have a value to form fullpath out
            
            # BUILD ATTRS
            self.attrs.update(path=fp, base=bn, fileext=fileext)
            coord, ttype = self.getCoord(bn)

            # REMOVE COORD FROM BASENAME
            if ttype:
                if not coord:
                    bn=util.stripName(re.sub('<%s>' % ttype, '', bn))
                else:                
                    bn=util.stripName(re.sub(coord, '', bn))
                    
            self.attrs.update(base=bn)
            channel = self.getChannel(fn)
            
            self._fnExpr = re.sub(self.basename, '${base}', self.filename)
            if self.isTiled:
                if self.coord:
                    self._fnExpr = re.sub(self.coord, '${coord}', self._fnExpr)
            self._fnExpr = re.sub(self.fileext, '${fileext}', self._fnExpr)   
                    
            #self.validate()
            
            if channel:
                self._baseExpr=re.sub(channel, '${channel}', bn)
            
            channel_proper=self.properChannel(channel)
            self.attrs.update(channel=channel)

    def reset(self):
        """ Reset the texture to the original path """
        self.parse(self.fullpath)
    
    def getCoord(self, basename, verbose=False, update=True):
        """ Returns the tiled texture coordinate & type, if any """
        #logger.getLogger().debug('FileNameParser.getCoord: "%s" %% "%s, %s"' % (self._fileExpr, self._whchExpr, basename))           
        tileMatch = re.match(self._fileExpr % self._whchExpr, basename)
        tilecoord=''
        tiletype =''
        
        # figure out based on proxy...
        if tileMatch:
            try:
                head = tileMatch.group("head")    
                tail = tileMatch.group("tail")
                tiletype=tileMatch.group("typ")
                self.__attrs.update(ttype=tiletype)
                if verbose:
                    logger.getLogger().info('head: %s' % head)
                if verbose:
                    logger.getLogger().info('tail: %s' % tail)           
            except:
                pass
            
        # figure out based on filename
        else:            
            for tile_type in self._tileExprs.keys():
                coordExpr = self._fileExpr % self._tileExprs.get(tile_type)
                coordMatch = re.search(coordExpr, basename)
                if coordMatch:                   
                    tilecoord = coordMatch.group("coord")
                    if tile_type=='UDIM':
                        if not 1001 <= int(tilecoord) <= 3010:
                            continue

                    self.isTiled=True
                    tiletype = tile_type
                    if update:
                        self.__attrs.update(coord = tilecoord)
                        self.__attrs.update(ttype = tiletype)
            
        return tilecoord, tiletype
    
    def identifyTile(self, coord):
        """ Identifies the tiletype based on the coord """
        for key in self._tileExprs.keys():
            matchStr=re.sub('^_', '', self._tileExprs.get(key))
            #coordMatch = re.search(self._tileExprs.get(key), coord)
            coordMatch = re.search(matchStr, coord)
            if coordMatch:
                self.isTiled=True
                tilecoord = coordMatch.group("coord")
                tiletype = key
                self.__attrs.update(coord = tilecoord)
                self.__attrs.update(ttype = tiletype)
                # if we're renaming, make sure to add adjust the separator 
                if tiletype=='UDIM':
                    self._fnExpr=re.sub('\$\{base\}\$\{coord\}', '${base}.${coord}', self._fnExpr)
                if tiletype=='UVTILE':                    
                    self._fnExpr=re.sub('\$\{base\}_\$\{coord\}', '${base}${coord}', self._fnExpr)
                    self._fnExpr=re.sub('\$\{base\}\.\$\{coord\}', '${base}${coord}', self._fnExpr)
    
    def getChannel(self, basename):
        """
        Attempt to parse the channel from the filename, returns the string 
        found in the name if that string exists in the global dictionary
        """
        channel = ''
        for chan, info in globals.CHANNEL_MAPPING.iteritems():
            for chanabbr in info.get('channels'):
                cexpr = self._chanExpr % '%s|%s|%s' % (chanabbr, chanabbr.upper(), chanabbr.title())
                cmatch = re.search(cexpr, basename)
                if cmatch:
                    try:
                        channel=cmatch.group('channel')
                        #channel=channel.lower
                    except Exception, err:
                        pass
        return channel
    
    def update(self):
        if self._baseExpr:
            result = Template(self._baseExpr).substitute(self.attrs)
            if self.__verbose:
                print 'updating texture name: ', result
    
    # DEPRECATED
    def updateBasename(self, basename):
        """ If the basename changes, update the _creplExpr attribute and get a new base attribute """
        if self.attrs.get('channel'):
            channel=self.attrs.get('channel')
            cur_base = self.attrs.get('base')
            creplExpr=self._baseExpr
            base=self.attrs.get('base')
            
            # if the channel is not part of the basename, it must be the abbreviated channel
            if not channel in base:                
                channel=self.channelAbbr(channel)
                
            tmp=re.sub(channel, '', base)
            base=re.sub('(\.|_)$', '', tmp)
            creplExpr=re.sub(base, '%s', creplExpr)
            self._baseExpr=re.sub(base, '%s', self._baseExpr)
            if self.debug:
                print '1:', self._baseExpr
            self._baseExpr=self._baseExpr % ( basename, '%s')
            if self.debug:
                print '2:', self._baseExpr
            return self._baseExpr % channel
        else:
            return basename
    
    def changeChannel(self, channel, short=True):
        """ Change the textures channel and update the basename """
        chan_abbr=''
        for chan, info in globals.CHANNEL_MAPPING.iteritems():
            if channel==chan:
                if short:
                    chan_abbr=info.get('abbr')
            else:                    
                chan_abbr=channel
                
        self.attrs.update(channel=chan_abbr)
        if self._baseExpr:
            basename = Template(self._baseExpr).substitute(self.attrs)
            self.attrs.update(base=basename)
        elif self._fnExpr:            
            if not '${channel}' in self._fnExpr:
                self._baseExpr='${base}_${channel}'
                #self._fnExpr = re.sub('\${base}', self._baseExpr, self._fnExpr)
                self._baseExpr=re.sub('\${base}', self.attrs.get('base'), self._baseExpr)
                
            newbase=Template(self._baseExpr).substitute(self.attrs)
            self.attrs.update(base=newbase)
            self.__filenameOut = Template(self._fnExpr).substitute(self.attrs)           

        
    def properChannel(self, chan='', short=False):
        """ get the proper channel from globals """
        if not chan:
            chan=self.channel
            
        result=chan
        for k in globals.CHANNEL_MAPPING.keys():
            global_channels=[x.lower() for x in globals.CHANNEL_MAPPING.get(k).get('channels')]
            if chan.lower() in global_channels:
                if not short:
                    result=k
                else:
                    result=globals.CHANNEL_MAPPING.get(k).get('abbr')
        return result
    
    def channelAbbr(self, chan):
        """ get the abbrviated channel from globals """
        result=''
        for k in globals.CHANNEL_MAPPING.keys():
            if chan==k:
                result=globals.CHANNEL_MAPPING.get(chan).get('abbr')
        return result
    
    #- PROPERTIES ---- 
    
    @property
    def path(self):
        #return self.__path
        return self.attrs.get('path')
    
    @path.setter
    def path(self, val):
        self.__path = val
        self.__attrs.update(path=val)
        return self.__path
    
    @property
    def fullpath(self):
        return self.__fullpath
      
    @property
    def fullpathOut(self):
        self.__fullpathOut = os.path.join(self.__path, self.__filenameOut)
        return self.__fullpathOut
    
    @property
    def filenameOut(self):
        """ Build the outgoing file name """
        # figure out the template rule based on the existing attributes
        #rule=self.rules.get('standard')
        base=Template(self._baseExpr).substitute(self.attrs)
        if self.ttype=='UVTILE':
            self._fnExpr=re.sub('\.\$\{coord\}', '_${coord}', self._fnExpr)  
        newfn=Template(self._fnExpr).substitute(self.attrs)
        self.__filenameOut=Template(self._fnExpr).substitute(self.attrs)
        return self.__filenameOut
    
    @filenameOut.setter
    def filenameOut(self, val):
        self.__filenameOut=val
        return self.__filenameOut
    
    @property
    def isProxy(self):
        retval=False
        if self.attrs.get('coord') in 'UVTILE UDIM'.split():
            retval=True
        return retval
    
    @property
    def proxyName(self):
        """ Returns the proxy file name for the texture """
        self._pfnExpr=re.sub('\${coord}', '<${ttype}>', self._fnExpr)
        return Template(self._pfnExpr).substitute(self.attrs)
    
    @property
    def isTiled(self):
        return self.__isTiled
    
    @isTiled.setter
    def isTiled(self, val):
        self.__isTiled=val
        return self.__isTiled
    
    @property
    def filename(self):
        return self.__filename
    
    @property
    def basename(self):        
        return self.attrs.get('base')
    
    @basename.setter
    def basename(self, val):
        val=util.getValidName(val)
        if self.__verbose:
            print '# valid basename: ', val
        if self.coordSep:
            val=val.rstrip(self.coordSep)
        if self._baseExpr:
            self._baseExpr = re.sub('%s' % self.channel, '${channel}', val)
        self.attrs.update(base=val)
        #print 'FileNameParser.basename: ', self.attrs.get('base') 
        return self.attrs.get('base')

    @property
    def basenameFull(self):
        """ Build the basename & coord """
        base=Template(self._baseExpr).substitute(self.attrs)
        newfn=Template(self._fnExpr).substitute(self.attrs)
        fn=Template(self._fnExpr).substitute(self.attrs)
        self.__basenameFull=os.path.splitext(fn)[0]
        return self.__basenameFull

    @property
    def ttype(self):
        result=''
        if self.isTiled:
            result=self.attrs.get('ttype')
        return result

    @property
    def coord(self):
        result=''
        if self.isTiled:
            result=self.attrs.get('coord')
        return result
    
    @coord.setter
    def coord(self, val):
        self.attrs.update(coord=val)
        self.isTiled=True
        self.identifyTile(val)
        return self.attrs.get('coord')
    
    @property
    def fileext(self):
        return self.attrs.get('fileext')
    
    @fileext.setter
    def fileext(self, val):
        self.attrs.update({'fileext':val})
        return self.attrs.get('fileext')
    
    @property
    def attrs(self):
        return self.__attrs
    
    @attrs.setter
    def attrs(self, val):
        self.__attrs.update({val[0]:val[1]})
        return self.__attrs
    
    @property
    def channel(self):
        retval=''
        if self.attrs.get('channel'):
            retval=self.attrs.get('channel')
        return retval
    
    @channel.setter
    def channel(self, val):
        if val:
            self.attrs['channel']=val
            self.changeChannel(val)
            return self.attrs.get('channel')
            
    @property
    def coordSep(self):
        """ Returns the character separating the basename and coordinate """
        retval=''
        sepmatch=re.search('\${base}(?P<coordsep>\.|_)\${coord}', self._fnExpr)
        if sepmatch:
            try:
                retval=sepmatch.group('coordsep')
            except:
                pass
        return retval
    
    @coordSep.setter
    def coordSep(self, val):
        cur_sep=self.coordSep
        if cur_sep=='.':
            cur_sep='\.'
        self._fnExpr=re.sub(cur_sep, val, self._fnExpr, 1)
        #self.validate()
    
    def validate(self):
        self._fnExpr=re.sub(r'\s', '', self._fnExpr)
        return self._fnExpr
    
    def valid(self):
        """ Flags invalid strings """
        return util.validString(self.fullpathOut)
    
    #- DEBUG --
    def _baseExpr(self):
        return self._baseExpr
    
    