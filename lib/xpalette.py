#!/X/tools/binlinux/xpython
import os
import sys 
import re
from datetime import datetime
import simplejson as json
from DefinedAssets import *

from . import Odict as dict
from .. import logger
from .. import globals
from .. import util

__version__ = '1.030'

class XPalette(dict): 
    """
    Class XPalette():
    
        Description:        
            The XPalette describes a single asset texture publish in the Mr. X texture publishing pipeline. The palette 
            references all of the currently published textures, in varying resolutions and formats.
    
        USAGE:        
            Create a instance of the class and set the palette data with XPalette.setData(). For each lod, create a list of 
            XTexture objects and use the XPalette.setTextures method.
            
        METHODS:        
            XPalette.getOutput():
                Returns the entire palette structure
            
            XPalette.getOptions():
                Return the options
            
            XPalette.getData():
                Returns the current palette data, without the palette type ( has attributes )
            
            XPalette.setData(data, typ='texturePublish'):
                Sets the data value of the current palette. Type defaults to 'texturePublish'
                
            XPalette.getTextures(lod):
                Gets the current textures for the given lod
                
            XPalette.getTextureLODs():
                Returns the LODs stored in this palette
                
            XPalette.getPaletteType():
                Returns the palette type (texturePublish, processTextures, convertTextures etc)
    
    v1.020
        - added introspection & audit functions
 
    v1.019
        - updates to major methods to support legacy json palettes
    
    v1.018
        - added support for collating textures
    
    v1.017
        - fixed parseOptions for new format
        - added collate method  
        
    v1.016
        - added getTextureTiles, getLodTotals, getLodSize
        - fixes for reading bad palettes >1.016
        
    v1.010
        - new palette/Texturizer format
        
    """
    
    def __init__(self, palette='', **kwargs):
        dict.__init__(self)
        
        self.__verbose = kwargs.get('verbose', False)
        
        if self.__verbose:
            logger.getLogger().info('Initializing XPalette...')
                
        self.setPalette(palette)        
        self.options        = {}
        self.resolutions    = ['source', 'hires', 'hires', 'hires']
        self.formats        = ['exr', 'png', 'rat']
        self.textures       = []
        self.__xpalette     = {}    # palette data, formatted for file output
        self.__rootdir      = ''
        self.__asset        = None
        self.data           = {}          # data for the parser
        
        ## LEGACY SUPPORT ##
        self.legacy=False
        self.texture_flag='textures'
        ##
        
        # stamp the palette with a version
        self._rev = __version__
        self.data.update(XPalette_version=self._rev)
        self.sortlist = ('bytes', 'size', 'exporter', 'maya', 'options', 'source', 'fullres_exr', 'fullres_rat', 'fullres_png', 'hires_exr', 'hires_rat', 'hires_png', 'lores_exr', 'lores_rat', 'lores_png', 'midres_exr', 'midres_rat', 'midres_png', 'tinyres_exr', 'tinyres_rat', 'tinyres_png')
        self.doctype = 'texturePublish'
        
        self.lib_expr = re.compile("(/X/projects/(\w+)/SHOTS/(\w+)/lib/textures/([\w]+))/(\w+)/(\w+)/(.*)$")
        self.__audit_data = dict(
             missing_textures = dict(),              
             )

        if palette:            
            self.read(palette, verbose=self.__verbose)
                            
    def read(self, palette='', f='json', sort=False, verbose=False):
        """ reads the palette (json or xml) and converts it into a dictionary
        if Texturizer_version > 0.37, new palette format... """
        self.__verbose=verbose
        
        if not palette:
            if self.getPalette():
                palette = self.getPalette()
                
        if palette:
            if os.path.exists(palette):
                self.setPalette(palette)
                self._palette_type = re.sub('^\.', '', os.path.splitext(os.path.split(palette)[1])[1]).lower()
                palette_name=os.path.split(palette)[-1]
                if self.__verbose:
                    logger.getLogger().info('parsing %s palette: "%s"' % (self._palette_type.upper(), palette_name))
                                    
                if self._palette_type == 'json':
                    json_data = open(palette).read()
                    tmp_data = json.loads(json_data, object_pairs_hook=dict)
                    self.__xpalette = tmp_data                        
                    self.doctype = self.__xpalette.keys()[0]
                    self.data = self.__xpalette.get(self.doctype)
                    try:
                        if self.data.get('Texturizer_version'):
                            logger.getLogger().warning('palette "%s" is an older version: %s, some options may be limited' % (palette_name, self.data.get('Texturizer_version')))
                            self.legacy=True
                            self.texture_flag='texture'
                    except:
                        logger.getLogger().error('palette "%s" is not the correct type' % palette) 
                    
                #sort the items
                if sort:
                    sorted(self.data.items(), key=lambda x: {'options': 2, 'exporter': 1, 'maya':3, 'source':4}[x[0]])     
                
                self.parseOptions()
            else:
                logger.getLogger().warning('palette "%s" does not exist' % palette) 

    def write(self, filename='', format='json', quiet=False):
        """
        Writes texture data to a palette. Setting the __xpalette attribute determines the type of palette that is written
        """
        if not filename:
            filename=self.getPalette()
            
        if format == 'json':
            try:
                fn = open(filename, 'w')
                if not quiet:
                    logger.getLogger().info('writing palette: %s' % filename)
                    
                json.dump(self.getOutput(), fn, indent=4)
                fn.close()
            except Exception, err:
                logger.getLogger().error('palette write error: %s' % err)

    
    def pprint(self):
        """ 'Pretty print' the palette output for easier reading  """
        if self.__xpalette:
            print json.dumps(self.__xpalette, indent=4)
            
    def getOutput(self):
        """ returns the entire output of the current palette """
        return self.__xpalette
    
    def getData(self):
        """ returns just the data portion of the current palette """
        return self.data
    
    def setData(self, data, typ='texturePublish'):
        """ sets the attributes portion of the palette (from XOptions) """
        self.data.update(XPalette_version=__version__)
        self.doctype = typ
        self.__xpalette = {typ: data}
    
    def setPalette(self, palette):
        """ Sets the palette file attribute (if we're reading a palette) """
        self.__palette =  palette
        
    def getPalette(self):
        """ Gets the current palette file """
        return self.__palette

    def getPaletteType(self):
        """ Gets the current palette type """
        return self.getOutput().keys()[0]
    
    def getDescription(self):
        """ Get the palette description """
        return self.data.get('description', '')
    
    def setPaletteType(self, typ):
        """ Sets the type of palette we are publishing (ie "texturePublish", "processTextures" etc) """
        data = self.__xpalette
        curtyp = self.getPaletteType()
        curData = self.__xpalette.get(curtyp)
        self.__xpalette = {typ:curData}
        return self.getPaletteType()
        
    def parseOptions(self):
        """ Gets the options saved with the palette and maps it to attributes """
        if self.__verbose:
            if not self.legacy:
                logger.getLogger().info('building %s options...' % self.doctype)
            else:
                logger.getLogger().info('building %s legacy options...' % self.doctype)
        # OLD
        #dataTypes = ['size', 'bytes', 'options', 'exporter', 'maya']        
        if self.legacy:
            dataTypes=['bytes', 'size', 'Texturizer_version', 'options', 'exporter', 'maya', 'source', 
                           'fullres_exr', 'hires_exr', 'hires_rat', 'hires_png', 'midres_exr', 'midres_png', 
                           'lores_exr', 'lores_png', 'tinyres_exr', 'tinyres_png']
        else:            
            dataTypes= ['size', 'total_textures', 'conversion_options', 'maya', 'textures']
               
        
        for data in dataTypes:
            cmd = 'self.data.get("%s", None)' % data
            try:
                result = eval(cmd)
            except Exception, err:
                result = dict()
                logger.getLogger().warning('palette did not contain the necessary data, please re-publish ( %s )' % err)
                return
            
            self.__setattr__(data, result)
            if self.legacy:
                try:
                    self.resolution = self.options.get('resolution', 'source')
                    self.conversion_options=self.options
                except:
                    logger.getLogger().warning('palette did not contain the necessary data, please re-publish ( %s )' % err)
                
            if self.__verbose:
                if self.__asset:
                    logger.getLogger().info('Asset: "%s"' % self.__asset)

    @property
    def asset(self):
        self.__asset=self.conversion_options.get('asset', None)
        return self.__asset
        
    
    @property
    def rootdir(self):
        # fix for os.path.join error
        self.__rootdir=re.sub('\/$', '', self.conversion_options.get('rootDir', ''))
        return self.__rootdir
    
    @rootdir.setter
    def rootdir(self, val):
        val=re.sub('\/$', '', val)
        self.conversion_options.update(rootDir=val)
        self.__rootdir=self.conversion_options.get('rootDir')
        return self.__rootdir
    
    def getRootdir(self):
        return self.rootdir

    def setTextures(self, xtextures, lod=globals.DEFAULT_LOD, typ='texturePublish'):
        """ Translates the XTextures scanned in the GUI and outputs them to a palette """
        if self.__xpalette:
            
            # ------------------ CURRENT PALETTE DATA  ------------------ #
            
            data = self.__xpalette.get(typ)
            if data:
                
                # ------------------ FORMAT TEXTURE BLOCK  ------------------ #
                
                rootdir = data.get('options').get('rootDir')
                self.__xpalette.get(typ).get('textures')[lod] = dict()
                self.__xpalette.get(typ).get('textures')[lod].update(bytes = 0)
                self.__xpalette.get(typ).get('textures')[lod].update(size = '0g')
                self.__xpalette.get(typ).get('textures')[lod].update(textures = [])
                
                res_size = 0
                
                # ------------------ GET ATTRIBUTES FROM CURRENT XTEXTURES  ------------------ #
                

                for xtex in xtextures:
                    res_size += int(xtex.bytes)
                    self.__xpalette.get(typ).get('textures').get(lod).get('textures').append(xtex.info)
                
                realsize = util.getSizeInKilobytes(res_size)
                self.__xpalette.get(typ).get('textures')[lod].update(bytes = res_size)
                self.__xpalette.get(typ)[lod].get('textures').update(size = realsize)
                
            # if the wrong type of palette is requested, raise an error
            else:
                logger.getLogger().warning('Incorrect palette type requested, current palette type is "%s" ' % self.getPaletteType())
    
    def getOptions(self, typ):
        """ Returns a portion of the palette data """
        if self.getData:
            if self.data.get(typ):
                return self.data.get(typ)

    def getConversionOption(self, val):
        """ Returns a value from the conversion options """
        result=''
        if self.getData().get('conversion_options'):
            if val in self.getData().get('conversion_options').keys():
                result=self.getData().get('conversion_options').get(val)
            else:
                logger.getLogger().warning('please query from the following: "%s"' % '", "'.join(self.getData().keys()))
        else:
            logger.getLogger().error('fatal palette error: palette has no conversion options')
        return result
    
    
    #- TEXTURE PARSING----
    def getTextures(self, lod=globals.DEFAULT_LOD):
        """ gets the textures stored in this palette, by lod type """
        result=[]
        if self.data:
            if not self.legacy:
                if lod in self.data.get('textures').keys():
                    if self.__verbose:
                        logger.getLogger().info('getting textures for LOD "%s"...' % lod)
                    try:
                        self.textures = self.data.get('textures').get(lod)
                        result=self.textures
                    except:
                        if self.__verbose:
                            logger.getLogger().warning('error getting textures for LOD "%s"...' % lod)
                else:
                    logger.getLogger().warning('cannot find textures for LOD "%s"...' % lod)
            ## LEGACY START ##
            else:
                if lod in self.data.keys():
                    if self.__verbose:
                        logger.getLogger().info('getting textures for LOD "%s"...' % lod)
                    try:
                        self.textures = self.data.get(lod)
                        result=self.textures
                    except:
                        if self.__verbose:
                            logger.getLogger().warning('error getting textures for LOD "%s"...' % lod)

                else:
                    logger.getLogger().warning('cannot find textures for LOD "%s"...' % lod)
            ## LEGACY END ##
        return result
                
    def getTextureFiles(self, lod=globals.DEFAULT_LOD, udim=True):
        """ Returns a list of actual files from the lod """
        result=[]
        textures=self.getTextures(lod).get(self.texture_flag)
        for t in textures:
            fn=t.get('file')
            fn=re.sub('^\/', '', fn)
            texfile=os.path.join(self.rootdir, fn)
            if os.path.exists(texfile):
                result.append(texfile)
            else:
                # IF THE TEXTURES WERE NOT PUBLISHED, LETS USE THE PARENT TEXTURE
                parent=t.get('parent')
                if os.path.exists(parent):
                    result.append(parent)
        result = sorted(list(set(result)))
        if udim:
            return self._convertTiles(result)
        else:
            return result
    
    def getPaletteChannels(self, lod=globals.DEFAULT_LOD):
        """ get the texture type (material channel) from a palette/LOD """
        channels = []
        textures=self.getTextures(lod).get(self.texture_flag)
        for t in textures:
            channels.append(t.get('info').get('type'))
        return sorted(list(set(channels)))
    
    def getTexturesFromChannel(self, chan, lod=globals.DEFAULT_LOD, udim=True):
        """ get the textures from a given (material) channel """
        result = []
        textures=self.getTextures(lod).get(self.texture_flag)
        for t in textures:
            try:
                channel = t.get('info').get('type')
                if channel == chan:
                    fn=t.get('file')
                    fn=re.sub('^\/', '', fn)
                    texfile=os.path.join(self.rootdir, fn)               
                    result.append(texfile)
            except:
                pass
        result = sorted(list(set(result)))
        if udim:
            return self._convertTiles(result)
        else:
            return result
    
    def _getPaletteColorFiles(self, lod=globals.DEFAULT_LOD, udim=True):
        """ get the texture type (material channel) from a palette/LOD """
        result = []
        textures=self.getTextures(lod).get(self.texture_flag)
        for t in textures:
            if not t.get('info').get('noncolor'):
                fn=t.get('file')
                fn=re.sub('^\/', '', fn)
                texfile=os.path.join(self.rootdir, fn)               
                result.append(texfile)
        result = sorted(list(set(result)))
        if udim:
            return self._convertTiles(result)
        else:
            return result

    def _getPaletteNonColorFiles(self, lod=globals.DEFAULT_LOD, udim=True):
        """ get the texture type (material channel) from a palette/LOD """
        result = []
        textures=self.getTextures(lod).get(self.texture_flag)
        for t in textures:
            if t.get('info').get('noncolor'):
                fn=t.get('file')
                fn=re.sub('^\/', '', fn)
                texfile=os.path.join(self.rootdir, fn)               
                result.append(texfile)
        result = sorted(list(set(result)))
        if udim:
            return self._convertTiles(result)
        else:
            return result

    def publishedTextures(self, lod=globals.DEFAULT_LOD):
        """
        Returns the published textures for the given lod in this palette
        """
        result=[]
        rootdir=self.getRootdir()
        if self.getTextures(lod):
            texture=self.getTextures(lod).get('textures')
            for t in texture:
                result.append('%s%s' % (rootdir, t.get('file')))        
        return result

    def getLodTotals(self, lod=globals.DEFAULT_LOD):
        return len(self.getTextureFiles(lod))
        
    def getLodSize(self, lod=globals.DEFAULT_LOD):
        return self.getTextures(lod).get('size')
    
    def _convertTiles(self, textures):
        """ conversion utility for getting UDIM strings from a list of textures """
        result = []
        for texture in textures:
            proxyName = util.convertTileName(texture)
            if proxyName and proxyName not in result:
                result.append(proxyName)
        return sorted(result)        
    
    #-- AUDITING -----
    
    def _checkTotals(self):
        """ Check the totals """
        verbose=self.__verbose
        self.__verbose=False
        for lod in self.getTextureLODs():
            texfiles=self.getTextureFiles(lod)
            if texfiles:
                logger.getLogger().info('found %d textures for lod "%s"' % (len(texfiles), lod))
            else:
                logger.getLogger().warning('found no textures for lod "%s"' % lod)
        self.__verbose=verbose
    
    def _checkLODSize(self, lod=globals.DEFAULT_LOD):
        pass
    
    def _checkPublished(self):
        """ Checks whether published textures exist... """
        rootdir=self.getRootdir()
        for texture in self.getTextures().get('textures'):
            published_texture=os.path.join(rootdir, texture.get('file'))
            parent_texture=texture.get('parent')
            if not os.path.exists(published_texture):
                logger.getLogger().warning( 'texture "%s" does not exist' % published_texture)
                if os.path.exists(parent_texture):
                    logger.getLogger().warning( 'parent texture "%s" not published' % parent_texture) 
    
    def _textureAudit(self):
        """ Compares source textures with the LODs in this palette """
        self.__verbose=False
        logger.getLogger().info('checking palette for irregularities')
        source_textures=self.getTextureFiles('source')
        for lod in self.getTextureLODs():
            for source_texture in source_textures:
                if not self.getTextureSibling(source_texture, lod):
                    logger.getLogger().warning('missing %s texture for source "%s"' % (lod, source_texture))
                    if lod not in self.__audit_data.get('missing_textures').keys():
                        self.__audit_data.get('missing_textures').update({lod:[]})
                    self.__audit_data.get('missing_textures')[lod].append(source_texture)
    
    def _auditData(self):
        return self.__audit_data
    
    def getTotalSize(self):
        """ Gets the total size of the publish """
        pass
    
    # UDPATED
    def getTextureTiles(self, lod=globals.DEFAULT_LOD):
        """ Given an lod, returns a dict of tile proxy name, list of texture tiles """
        rootdir=self.getRootdir()
        tileData=dict()
        if lod in self.getTextureLODs():
            for tex in self.getTextures(lod).get(self.texture_flag):
                fn=tex.get('file')
                # FIX FOR FULLRES
                try:
                    if fn.count(re.search('(v\d{1,4})', fn).group())>1:
                        fn=re.sub('%s/%s' % (re.search('(v\d{1,4})', fn).group(), re.search('(v\d{1,4})', fn).group()), '%s' % re.search('(v\d{1,4})', fn).group(), fn)
                except:
                    pass
                
                tileName=util.convertTileName(re.sub('^\/', '', fn))
                if util.convertTileName(os.path.join(rootdir, tileName)):
                    if tileName not in tileData.keys():
                        tileData[tileName]=sorted([re.sub(rootdir, '', x) for x in util.convertTileName(os.path.join(rootdir, tileName))])
                else:
                    tileData[tex.get('file')]=[]
        else:
            logger.getLogger().error('lod "%s" is not in this palette' % lod)
        return tileData    
    
    def convertTextures(self, *args):
        if len(args) < 2:
            logger.getLogger().warning('please specify a source and destination LOD value')
        else:
            source_lod = args[0]
            dest_lod = args[1]
            if self.getTextures(source_lod):
                textures = self.getTextures(source_lod)
                print json.dumps(textures, indent=4)
                
    def getTextureLODs(self):
        """
        Returns the current resolutions stored in this palette
        """
        #return [x for x in self.data.keys() if x in v for k, v in lods.iteritems()]
        if self.getData():
            if not self.legacy:
                try:
                    lods = sorted(self.getData().get(self.texture_flag).keys())
                except:
                    lods=[]
            else:
                lods=sorted(self.getTextureTypes())
        return lods
    
       
    # DEPRECATED: legacy, use getTextureLODs
    def getTextureTypes(self):
        """ Returns the current resolutions stored in this palette """
        #return [x for x in self.data.keys() if x in v for k, v in lods.iteritems()]
        sections=[]
        if self.getData():
            if self.getData().get('options'):
                lods = self.getData().get('options').get('lod')
                sections = ['source', ]
                for lod, toggle in lods.items():
                    if toggle:
                        for f in self.getData().get('options').get('formats'):
                            lodStr = '%sres_%s' % (util.getAbbr(lod), f)
                            if lodStr in self.getData().keys():
                                sections.append('%sres_%s' % (util.getAbbr(lod), f))
        return sections
    
    def getTextureSibling(self, texture, lod, ttype=''):
        """ Returns a texture "sibling" given a texture and an LOD """
        # parse the texture dir
        if self.__verbose:
            logger.getLogger().info('searching palette: %s' % self.getPalette())
        result=''
        inputbn=os.path.splitext(os.path.split(texture)[-1])[0]
        if lod in self.getTextureLODs():
            for tex in self.getTextures(lod).get(self.texture_flag):
                filename=tex.get('file')
                basename=os.path.splitext(os.path.split(filename)[-1])[0]
                if basename==inputbn:
                    result = '%s%s' % (self.rootdir, filename)
        else:
            logger.getLogger().warning('LOD "%s" not in palette: %s' % (lod, self.getPalette()))
        return result
       
    def getMayaNodeFromTexture(self, texture):
        """ Returns the node(s) for the current texture """
        result=''
        rootdir=self.getRootdir()
        texture_file=re.sub(rootdir, '', texture)
        attrs=self.getTextureAttrs(texture)
        resolution = attrs.get('resolution')
        format = attrs.get('format')
        lod = '%s_%s' % (resolution, format)
        if 'src' in lod:
            lod=globals.DEFAULT_LOD
        
        if lod in self.getTextureLODs():
            lodtextures=self.getTextures(lod).get(self.texture_flag)
            for ltex in lodtextures:
                if ltex.get('file') == texture_file:
                    result=ltex.get('node').get('nodes')
                
        return result
        
    def getTextureAttrs(self, filename):
        """ Builds basic texture attributes from a texture file
        ** copied from texture_util.py """
        result=dict()
        fmatch = self.lib_expr.match(filename)
        format=os.path.splitext(os.path.split(filename)[-1])[-1]
        format=re.sub('^\.', '', format)
        if fmatch.groups():
            result.update(show = fmatch.group(2))
            result.update(shot = fmatch.group(3) )
            result.update(asset = re.sub("_tex_dir$", "", fmatch.group(4)))
            if result.get('asset'):
                result.update(resolution = re.sub("%s_tex_" % result.get('asset'), "", fmatch.group(5)))
            result.update(format=format)
            result.update(version = fmatch.group(6))
            result.update(texdir = fmatch.group(1) )
            if result.get('texdir'):
                result.update(paldir = os.path.join(result.get('texdir'), "%s_tex_palette_json" % result.get('asset')))
        return result
    
    def updateMayaFile(self, lod='fullres_exr'):
        """ Given a publish palette, update a maya scene with the published textures """
        import maya.cmds as mc
        updateData=dict()
        lib_root=self.getRootdir()
        for texture in self.getTextures(lod).get('textures'):
            #print texture.keys()['publish', 'tag', 'file', 'info', 'nodes', 'tiled', 'parent']
            lib_tex=os.path.join(lib_root,  texture['file'])
            if texture.get('info').get('tileType'):
                lib_tex=re.sub(texture.get('info').get('coord'), '<%s>' % texture.get('info').get('tileType'), lib_tex)
            nodes=[]            
            if texture.get('nodes'):
                nodes=texture.get('nodes')
                for node in nodes:
                    if node not in updateData.keys():
                        updateData[node]=lib_tex
        if updateData:
            for node, texstr in updateData.iteritems():
                if mc.objExists(node):
                    logger.getLogger().info('updating file node "%s" with texture: %s' % (node, texstr))
                    mc.setAttr('%s.ftn' % node, texstr, type='string')
                else:
                    logger.getLogger().warning('node "%s" does not exist, skipping' % node)                
                            
    
    def updateMayaBatch(self, inputFile, lod=globals.DEFAULT_LOD):
        """ This method is called via mayabatch, opens and updates the maya scene file based on the latest published palette """
        import maya.cmds as mc        
        mc.file(inputFile, o=True, f=True)
        print '# [XPalette]: opening Maya file: "%s"' % inputFile
        
        # save the final Maya file
        #mayaUpdated = re.sub('PREPARED_FOR_TEXTURIZER', 'UPDATED_BY_TEXTURIZER', inputFile)
        #mc.file(rn=mayaUpdated)
        #mc.file(s=True, typ="mayaAscii")
        #print 'saving Maya file: %s' % mayaUpdated
        
        self.updateMayaFileNodes(lod=lod)
        mc.file(s=True, typ="mayaAscii")

    def updateHoudiniFileNodes(self, lod=globals.DEFAULT_LOD):
        pass
    
    def updateNukeFileNodes(self, lod=globals.DEFAULT_LOD):
        pass
    
    def updateTextures(self, lod='midres_png'):
        if not self.textures:
            self.getTextures(lod)            
        for texture in self.textures:
            texFile = os.path.join(self.__rootdir, texture.get('file'))

    def setTexturesResolution(self, texres):
        pass

    #- NUKE -----

    def getNukeTextures(self, lod):
        import nuke
        for tex in self.getTextures(lod):
            input = os.path.join(self.getRootdir(), tex.get('file'))            
    
    #- COLLATION -----
    
    def collate(self, palettes=[]):
        """ Collates a directory of palettes into a final palette """        
        outfile=''
        collated_textures=dict()
        total_source_textures=0
        total_bytes=0
        
        lod_sizes=dict()
        da=None
        assetNames=None
        initial_palette=False
        if palettes:            
            logger.getLogger().info('collating %d palettes...' % len(palettes))
            pal_index=0
            
            # LOOP THROUGH PALETTES...    
            for p in sorted(palettes):
                if os.path.exists(p):
                    json_data = open(p).read()
                    tmp_data = json.loads(json_data, object_pairs_hook=dict)
                    logger.getLogger().info('reading palette: %s' % p)
                    if not pal_index:
                        outfile=re.sub('\d+\.json$', 'json', p)
                        self.__xpalette = tmp_data
                        self.doctype = self.__xpalette.keys()[0]
                        self.data = self.__xpalette.get(self.doctype)
                    
                    #print json.dumps(self.data.get('textures'), indent=5)                    
                    #master_textures=self.data.get('textures')
                    total_source_textures+=tmp_data.get(self.doctype).get('total_textures')
                    
                    show = self.getConversionOption('show')
                    shot = self.getConversionOption('shot')
                    myAsset = self.getConversionOption('asset')
                    rootDir = self.getConversionOption('rootDir')
                    libdir = self.getConversionOption('libdir')      
                    self.data.get('conversion_options').update(rootDir=os.path.join(libdir, myAsset))
                    
                    # NEED TO GET THE LAST PUBLISHED VERSION OF THE TEXTURES
                    if not initial_palette:
                        da=DefinedAssets(show, shot)
                        assetNames = [asset.name() for asset in da.assets()]
                        initial_palette=True
                        
                    textures=tmp_data.get(self.doctype).get(self.texture_flag)
                    lods=textures.keys()
                    
                    for lod in lods:
                        LOD_TOTAL=0 # this represents the number of textures in the current LOD
                        if lod in globals.valid_lods():
                            # lod = 'fullres_exr'
                            define=''
                            if lod!='source':
                                # hi, lo, mid
                                tmp_res=re.sub('res_\w+', '', lod)
                                lod_names=[k for k, v in globals.ABBREVIATIONS.iteritems() if v==tmp_res]
                                lod_name=lod_names[0]                            
                                lod_abbr=globals.ABBREVIATIONS.get(lod_name)
                                define='%s_tex_%sres' % (myAsset, lod_abbr)
                            else:
                                lod_name='source'
                                lod_abbr=globals.ABBREVIATIONS.get(lod_name)
                                define='%s_tex_%s' % (myAsset, lod_abbr)
                            
                            lastVersion =1
                            newVersion  = ''
                            if define in assetNames:
                                
                                pubAsset=da.getAsset(define)
                                lastVersion=int(da.getLastVersion(pubAsset))
                                newVersion='v%03d' % lastVersion
                                if not lastVersion:
                                    #logger.getLogger().error('Define "%s" is returning last published version: "%s"' % (define, newVersion))
                                    # HAXX...need to figure out why this define addition fails
                                    newVersion='v001'
                            else:
                                logger.getLogger().warning('asset "%s" is not defined, skipping...' % define)
                                
                            if lod not in collated_textures.keys():
                                collated_textures[lod]=dict()
                                collated_textures.get(lod).update(bytes=0)
                                collated_textures.get(lod).update(size='0mb')
                                collated_textures.get(lod).update(total=0)
                                collated_textures.get(lod).update(textures=[])
                                total_lodbytes=0
                            
                            if lod not in lod_sizes.keys():
                                lod_sizes[lod]=0
                            
                            textures_list=textures.get(lod).get(self.texture_flag)                            
                            lod_size=textures.get(lod).get('bytes')                            
                            #print '%s: %s' % (lod, util.getSizeInKilobytes(lod_size))                                              
                            collated_textures.get(lod)['textures'].extend(textures_list)
                            total_lodbytes+=lod_size
                            size=textures.get(lod).get('size')
                            lod_textures=textures.get(lod).get(self.texture_flag)                            
                            
                            # UDPATE THE FILE ATTR
                            for lt in lod_textures:
                                if lt.get('file'):
                                    if newVersion:
                                        lib_dir, fn=os.path.split(lt.get('file'))
                                        lt.update(file=os.path.join(lib_dir, newVersion, fn))
    
                                texture_size=lt.get('info').get('bytes')
                                #print 'texture size: ', texture_size
                            
                            LOD_BYTES=lod_sizes.get(lod)
                            LOD_BYTES+=lod_size
                            LOD_TOTAL+=len(textures_list)
                            tmp_bytes=collated_textures.get(lod).get('bytes')
                            tmp_bytes+=lod_size
                            collated_textures.get(lod).update(bytes=tmp_bytes)
                            collated_textures.get(lod).update(total=LOD_TOTAL)
                            collated_textures.get(lod).update(size=util.getSizeInKilobytes(tmp_bytes))
                            logger.getLogger().debug('LOD "%s" stats: "%s"' % (lod, util.getSizeInKilobytes(tmp_bytes)))
                            total_bytes+=tmp_bytes
                            
                
                else:
                    logger.getLogger().error('palette: "%s" does not exist, aborting...' % p)
                    
                pal_index+=1
            
            # ELSE..
            logger.getLogger().info('finalizing collation...')
            
        # WRITE THE FINAL COLLATED PALETTE        
        # DISCARD UNECESSARY VARIABLES
        try:
            self.data.get('conversion_options').pop('libdir')
            #self.data.get('conversion_options').pop('usrPublishDir')
        except:
            pass
        
        for k in lod_sizes.keys():
            if k in self.data.get('textures'):
                self.data.get('textures').get(k).update(bytes=lod_sizes.get(k))                
                self.data.get('textures').get(k).update(size=util.getSizeInKilobytes(lod_sizes.get(k)))
                logger.getLogger().info('updating stats for LOD: "%s"...' % k)
            else:
                logger.getLogger().warning('LOD "%s" does not have stats, skipping...' % k)
        
        self.data.update(bytes=total_bytes)
        self.data.update(size=util.getSizeInKilobytes(total_bytes))
        self.data.update(textures=collated_textures)
        self.data.update(total_textures=total_source_textures)
        self.data.get('conversion_options').update(date=datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        if outfile:
            try:
                fn = open(outfile, 'w')
                logger.getLogger().info('writing collated palette: %s' % outfile)
                json.dump(self.getOutput(), fn, indent=4)
                fn.close()
            except IOError:
                logger.getLogger().error('cannot write file %s, check file permissions' % outfile)
                sys.exit(1)
            
            return outfile
        else:
            logger.getLogger().error('please specify a palette file')
            sys.exit(1)
