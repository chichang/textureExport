"""
Texture Scanning Utility
"""
import os
import re
import time
from . import Odict as dict
from .. import logger
from .. import util

reload(util)

class Scanner(object):
    """
    class Scanner():
    
        DESCRIPTION:              
            This class scans files/directories/maya/nuke/houdini scenes for textures and passes them
            to the TextureManager class
            
        USAGE:        
            Scanner.scan(path, files, verbose)

    """

    def __init__(self, parent=None, **kwargs):
        self.__env		 = kwargs.get('env', 'standalone')
        self.__debug     = kwargs.get('debug', False)
        self.__parent 	 = parent
        self.textures    = None
        self.__scanState = False
        self.__asset     = ''
        logger.getLogger().info('loading Texture %s Scanner...' % self.__env.title())
        
        if self.__debug:
            logger.enableDebugging()
        
    def getParent(self):
        return self.__parent
    
    def getAsset(self):
        return self.__asset
    
    def setAsset(self, val):
        self.__asset=val
        return self.__asset        
        
    def scan(self, path=None, files=[], verbose=False, swatches=False):
        """
    	Scan for textures
    	"""
        #path=os.path.realpath(path)
        textures=dict()
        if path:
            if verbose:
                logger.getLogger().info('scanning directory: %s' % os.path.realpath(path))
            textures=self._scanDirectory(path, files)
        if swatches:  
            self._createSwatches(textures)          
        return textures

    def _scanDirectory(self, path, files=[], swatches=False):
        """
        Scan the specified directory for textures
        """
        if os.path.exists(path):
            # we are scanning a directory
            textures=util.getTextureFiles(path, files)
        else:
            logger.getLogger().error('%s is not a valid directory' % path)
            
        self.textures=textures
        if swatches:
            self._createSwatches(textures)
        return self.textures

    def _scanMaya(self, swatches=False):
        """
        Scans a maya scene for textures
        """
        from ..util import maya_util
        logger.getLogger().info('scanning Maya scene...')
        textures=maya_util.getSceneTextures()
        if swatches:
            self._createSwatches(textures)
        return textures
    
    def _scanNuke(self, swatches=False):        
        """
        Scans a nuke script for textures
        """
        from ..util import nuke_util
        logger.getLogger().info('scanning Nuke script...')
        textures=nuke_util.getScriptTextures()
        if swatches:
            self._createSwatches(textures)
        return textures
    
    def _createSwatches(self, textures, swatchsize=128):
        import subprocess
        tstart=time.time()        
        for t in textures:
            texture_path, texture_file=os.path.split(t)
            texture_basename, texture_filext=os.path.splitext(texture_file)
            swatch_dir=os.path.join(texture_path, '.txSwatches')
            if not os.path.exists(swatch_dir):
                util.mkdirPath(swatch_dir)
            
            swatch_file=os.path.join(swatch_dir, '%s.jpg' % texture_basename)
            cmd='oiiotool --resize %dx%d %s -o %s' % (swatchsize, swatchsize, t, swatch_file)
            swatch_cmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            frout, frerr = swatch_cmd.communicate()
            if not swatch_cmd.wait():
                continue

        tend=time.time()
        readTime, tstart = tend - tstart, tend
        logger.getLogger().info('Swatch creation completed in: %1.2f seconds ( %d images )' % (readTime, len(textures)))

    def importTextures(self, palette):
        """ Import textures from an existing palette """
        result=dict()
        
        from . import xpalette
        
        if os.path.exists(palette):
            xpal=xpalette.XPalette()
            xpal.read(palette)
            
            if xpal.asset:
                self.setAsset(xpal.asset)
                
            try:
                for tex_attributes in xpal.getTextures().get('textures'):
                    texture=tex_attributes.get('parent')
                    if texture not in result.keys():
                        result[texture]=dict()
                        result.get(texture).update(**tex_attributes)

            except:
                logger.getLogger().warning('cannot get textures from palette: "%s"' % palette)
        
        self.textures=result
        return result

    def getTextureFiles(self):
        """
        Returns a list of all the textures in the scan
        """
        alltextures=[]
        if self.textures:            
            tpath=self.textures.get('path')
            if self.textures.get('nontiled'):
                for pname in self.textures.get('tiled').keys():
                    for f in self.textures.get('tiled').get(pname).get('files'):
                        alltextures.append(f.get('file'))
            if self.textures.get('nontiled'):
                for tn in self.textures.get('nontiled'):
                    alltextures.append(os.path.join(tpath, tn))
        return sorted(alltextures)

    def setTextures(self, textures, **kwargs):
        """
        Add textures manually
        """
        pass
