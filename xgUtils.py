#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import re
from types import ListType, TupleType
from PythonQt import QtGui
import subprocess
import shlex

#############################
try:
	import mari
except:
	pass


debug = 0

#======================================================================
#	SYSTEM UTILS
#======================================================================
class ccSysUtil:

	def __init__(self, show_name=None, shot_name=None):
		self._mShow = show_name
		self._mShot = shot_name
		pass

	def printGotham(self):
		#test action bound. prints Gotham
		print "Gotham!!"

	def runCommand(self, cmd, stdin=None, env=None):
	    """
	    Runs a command-line command
	    """

	    mycmd=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	    output, error=mycmd.communicate()
	    while not mycmd.wait():
	    	# do stuff
	    	return 0



	    #if not isList(cmd):
	        #cmd = shlex.split(cmd)
	    #opts = dict(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	    #if env:
	    #    opts.update(env=env)
	    #if stdin:
	    #    opts.update(stdin=subprocess.PIPE)
	    #    stdout, stderr=subprocess.Popen(cmd, **opts).communicate(stdin)
	    #else :
	    #    stdout, stderr=subprocess.Popen(cmd, **opts).communicate()
	    #return stdout, stderr

	def isList(self, item):
	    """
	    Returns true if the argument is a list
	    """
	    retval = False
	    if type(item) in (ListType, TupleType) :
	        retval = True

	def getLatestTextureVersion(self, outputDir, textureType, padding=3):
	    '''
	    return False if not exist, needs to be created.
	    '''
	    checkPath = os.path.join(outputDir, textureType)

	    #if passed in path does not exist or is not a directory. return
	    if os.path.exists(checkPath) and os.path.isdir(checkPath):
	        
	        if debug: print checkPath
	        
	        versionNumList =[]

	        dirContents = os.listdir(checkPath)
	        if debug: print dirContents

	        #if directory is empty. return.
	        if len(dirContents) == 0:
	        	return None

	        for item in dirContents:
	            if ("v" in item) and os.path.isdir(os.path.join(checkPath, item)):
	                if "_" in item:
	                    item = item.split("_")[0]
	                versionNum = int(item.split("v")[1])
	                versionNumList.append(versionNum)
				
				#if no version found. return.
	            if len(versionNumList) == 0:
	            	return None

                versionNumList.sort()
                if debug : print versionNumList
                latestVer = str(versionNumList[-1])

	        if padding != 0:
	        	return latestVer.zfill(padding)
	        else:
	        	return latestVer

	    else:
	        return None

	def getNewVersion(self, outputDir, textureType, padding=3):
	    '''
	    return False if not exist, needs to be created.
	    todo: bug! "new folder"
	    '''
	    checkPath = os.path.join(outputDir, textureType)

	    #if passed in path does not exist or is not a directory. return
	    if os.path.exists(checkPath) and os.path.isdir(checkPath):
	        
	        if debug: print checkPath
	        
	        versionNumList =[]

	        dirContents = os.listdir(checkPath)
	        if debug: print dirContents

	        #if directory is empty. return.
	        if len(dirContents) == 0:
	        	return None

	        for item in dirContents:
	            if ("v" in item) and os.path.isdir(os.path.join(checkPath, item)):
	                if "_" in item:
	                    item = item.split("_")[0]
	                versionNum = int(item.split("v")[1])
	                versionNumList.append(versionNum)
				
				#if no version found. return.
	            if len(versionNumList) == 0:
	            	return None

                versionNumList.sort()
                if debug : print versionNumList
                latestVer = str(versionNumList[-1])

                newVersion = int(latestVer) + 1

	        if padding != 0:
	        	return "v"+ str(newVersion).zfill(padding)
	        else:
	        	return "v"+ str(newVersion)

	    else:
	        return None

	def listDir(self, dir, type=None):
		dirList = []
		if (os.path.exists(dir) == False):
			return None
		else:
			dirContents = os.listdir(dir)
			for c in dirContents:
				path = os.path.join(dir, c)
				if os.path.isdir(path):
					dirList.append(c)
			return dirList

	def mergeLists(self, list_one, list_twe):
		in_first = set(list_one)
		in_second = set(list_twe)
		in_second_but_not_in_first = in_second - in_first
		resultList = list_one + list(in_second_but_not_in_first)
		return resultList

	def sameListItems(self, list_one, list_twe):
		in_second_and_in_first = set(list_one) & set(list_twe)
		return list(in_second_and_in_first)

	def listDiff(self, a, b):
		b = set(b)
		return [aa for aa in a if aa not in b]

	def removeNameIndexes(self, string):
	     #remove intgers in a string
	     return map(int, re.findall(r'\d+', string))
#======================================================================
#	MARI UTILS
#======================================================================

class ccMariUtil:

	def __init__(self, show_name=None, shot_name=None):

		self._mShow = show_name
		self._mShot = shot_name
		self.mariDirName = "Mari"
		self.mariTempDirName = "temp"

	def isProjectSuitable(self):
		'''
		check current project state.
		'''
		messageBox = QtGui.QMessageBox(parent=None, title="Message.")

		if mari.projects.current() is None:

			self.messageBox("Please open a project.")


			return False

		geo = mari.geo.current()
		if geo is None:

			self.messageBox("Please select an object to export texture from.")

			return False
		#if geo.currentChannel().currentLayer() == None:
		#	mari.utils.message("No channels to get paint from.")
		#	return False
		return True

	def messageBox(self, message):
	    messageBox = QtGui.QMessageBox(parent=None)
	    messageBox.setText(message)
	    messageBox.exec_()

	def setUserMariDir(self):
		'''
		query/create path of temp mari Dir for current user.
		'''
		mariTempDir = os.path.join(os.getenv("HOME"), self.mariDirName, self.mariTempDirName)
		if debug: print "mari tmp dir is: " + mariTempDir

		if os.path.exists(mariTempDir):
			print "mari user temp dir exist."

		elif not os.path.exists(mariTempDir):
			print "mari user temp dir does not exist. make " + mariTempDir
			#make dir
			os.makedirs(mariTempDir)

		return mariTempDir

	def udimToMariIndex(self,udim):
		'''
		translate UDIM number into mari index.
		'''
		mariIndex = udim-1001
		return mariIndex

	def getSelectedPatchs(self):
		'''
		get a list of selected UDIM patches on current geo.
		'''
		selectedList = []
		geo = mari.geo.current()
		patchList = mari.geo.current().patchList()
		for patch in patchList:
			if patch.isSelected() == True:
				print patch.name() + " is selected."
				selectedList.append(patch.udim())
			else:
				pass
		return selectedList

	def getAllPatchs(self):
		'''
		get a list of selected UDIM patches on current geo.
		'''
		selectedList = []
		geo = mari.geo.current()
		patchList = mari.geo.current().patchList()
		for patch in patchList:
			selectedList.append(patch.udim())

		return selectedList

	def fitBufferToUdim(udim):
		'''
		In Uv view. frame and fit the paint buffer to a given uv tile.
		'''
		can = mari.canvases.current()
		if can.camera().type() != 2:
			print "current viwe is not UV view."
			return
		cam = can.camera()
		cam.setScale(1)
		uvIndex =  mu.udimToMariIndex(udim)
		udim_V = uvIndex/10
		udim_U = uvIndex%10
		vectorN_x = udim_U+0.5
		vectorN_y = udim_V+0.5
		lookvec = mari.VectorN(vectorN_x,vectorN_y,1.0)
		#move the camera accordingly.!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		cam.setScale(0.5)
		cam.setLookAt(lookvec)
		pBuffer = mari.canvases.paintBuffer()
		defaultSize = PythonQt.Qt.QSizeF(1,-1)
		defaultPoint = PythonQt.Qt.QPoint(0.0,0.0)
		defaultPos = PythonQt.Qt.QPointF(defaultPoint)
		#move the bufer accordingly.
		pBuffer.setRotation(0)
		pBuffer.setScale(defaultSize)
		pBuffer.setTranslation(defaultPos)

	def getChannelDepth(self,chanName):
		geo = mari.geo.current()
		chan = geo.channel(chanName)
		chanDepth = chan.depth()
		return chanDepth

	def channelLayerCount(self,chanName):
		geo = mari.geo.current()
		chan = geo.channel(chanName)
		chanCount = len(chan.layerList())
		return chanCount

	def getChannelMetadata(self, chanName):
		'''
		retrun channel Metadata as dict.
		'''
		geo = mari.geo.current()
		chan = geo.channel(chanName)
		metadatas = chan.metadataNames()
		metadataDict = dict()
		if metadatas:
			for m in metadatas:
				metadataDict[m]=chan.metadata(m)
			return metadataDict
		else:
			#print "no metadatas found."
			return None


	def getChannelColorSpace(self,chanName):
		pass

	def addMetadata(self):
		pass

	def getLatestVersion(self):
		pass
	
	def makeDir(self):
		pass

	def fileTemplate(self):
		pass

	def exportPath(self):
		pass



class lookDevTexture():
	def __init__(self, path):
		pass
	def textureUser(self):
		#returns the user of the 
		pass

def printGotham():
	#test action bound. prints Gotham
	print "Gotham!!"


if __name__=="__main__":
	pass