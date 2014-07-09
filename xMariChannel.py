
import os
import sys
import re
import mari
import json
from PythonQt import QtCore, QtGui
from globals import *
import xgUtils as imp_utils
reload(imp_utils)


##todo:  handle layer group check

#======================================================================
#	UTIL
#======================================================================
su = imp_utils.ccSysUtil()
mu = imp_utils.ccMariUtil()
#======================================================================
#	VAR
#======================================================================
udimTag = "<UDIM>"
udimTemplate = "$UDIM"
xUserName = os.getenv("USERNAME")
xAsset = os.getenv("SHOT")
xShow = os.getenv("SHOW")
chanInfoFile = "chanInfo.json"

#======================================================================
#	Mair Class
#======================================================================

class X_MariChannel_ST():

	def __init__(self, 
				channelName, 
				channelType,
				channelAbbr, 
				textureVersion,
				ncd,
				channelDepth, 
				textureVariation):

		self.channelName = channelName
		self.channelType = channelType
		self.channelAbbr = channelAbbr
		self.textureVersion = textureVersion
		self.ncd = ncd
		self.channelDepth = channelDepth
		self.textureVariation = textureVariation
		#=======================================
		self._hasVariation = False
		self._deleteAfterExport = None
		self._outFormat = None
		self._outRes = None
		self._deleteAfterExport = None
		self._localConvert = None
		self._patchlist = []
		self._exportName = None
		self._exportTypePath = None
		self._exportPath = None
		self._obj = None
		self._exportedTextures = []
		#=======================================
		self.EXPORT_LAYER = "Base"
		self.DEFAULT_VARIATION = "N/A"
		#=======================================
		self._readytoExport = True
		#set true if texture variation is specified
		if (self.textureVariation != self.DEFAULT_VARIATION):
			self._hasVariation = True


	def printChannelInfo(self):

		'''
		print info of the channel.
		'''
		print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		print "obj: ", self._obj
		print "export format: ", self._outFormat
		print "export resolution: ", self._outRes
		print "xxxxxxxxxxx Channel Name: " + self.channelName
		print "channel type: " + self.channelType
		print "channel file tag: " + self.channelAbbr
		print "texture version: " + self.textureVersion
		print "channel ncd: " + str(self.ncd)
		print "channel depth: " + self.channelDepth
		print "texture variation: " + self.textureVariation
		print "patches: " + str(self._patchlist)
		print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

	def exportName(self):

		'''
		setup the file name template used to export.
		'''

		print "generating file name template for: " + self.channelName + " ..."
		geoName = self._obj.name()

		#if not found abbr set default here
		if not self.channelAbbr:
			self.channelAbbr = self.channelType[0:4].lower()

		#texture color space
		if (self._localConvert == True and self.ncd == False):
			colorSpace = "linh"

		elif (self._localConvert == False and self.ncd == False):
			colorSpace = "srgbh"

		else:
			colorSpace = "ncdh"

		#setup the name
		exportName = ""
		exportName += geoName + "_"
		exportName += self.channelAbbr + "_"
		#check for variations
		if self._hasVariation:
			exportName += self.textureVariation + "_"
		exportName += colorSpace + "_"
		exportName += udimTag + "."
		exportName += self._outFormat

		#set name template
		self._exportName = exportName
		print "name template for " + self.channelName + " is: " + self._exportName
		print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		

	def exportPath(self, rootPath):

		'''
		set up the full export file path used to export.
		'''

		print "generating file export path for: " + self.channelName + " ..."
		#check if export name is avaluable
		if self._exportName:

			#root dir for texture type
			exportTypeDir = os.path.join(rootPath, self.channelType)
			self._exportTypePath = exportTypeDir

			exportVersionDir = os.path.join(exportTypeDir, self.textureVersion)

			print "export directory for " + self.channelName + " is: " + exportVersionDir
			print "creating directory ..."

			#if the directory already exist. exit out to prevent overwrite.
			if os.path.exists(exportVersionDir):
				print "directory " + exportVersionDir + " exist...  channel will not export."
				self._readytoExport = False
				return None

			try:
				os.makedirs(exportVersionDir)
				print "Directory created: ", exportVersionDir
			except OSError:
				errors.append("Error creating directory: '%s'" % exportVersionDir)
				self._readytoExport = False
				return errors

		#set the export full path
		self._exportPath = os.path.join(exportVersionDir, self._exportName)
		print "export path for " + self.channelName + " is: " + self._exportPath
		print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

	def updateMetaData(self):
		'''
		update channel metadata before export.
		'''
		#TODO: instead of grabbing the channel. inherite it?
		channelToUpdate = self._obj.channel(self.channelName)
		#check and create channel metadate
		print "updateing " + self.channelName + " channel metadata."
		channelToUpdate.setMetadata("channelType", self.channelType)
		channelToUpdate.setMetadata("textureVariation", self.textureVariation)

	def updateChanInfo(self):
		'''
		update channel info json.
		'''
		chanInfoToUpdate = os.path.join(self._exportTypePath, chanInfoFile)
		print "updating channel info: " + chanInfoToUpdate

		channelInfo = dict()
		channelInfo.update(channelAbbr=self.channelAbbr)
		channelInfo.update(ncd=self.ncd)

		with open(chanInfoToUpdate, 'w') as outfile:
			json.dump(channelInfo, outfile)


	def export(self, patches = False):

		'''
		do the export.
		'''

		print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		print "Exporting: " + self.channelName + "\n"

		#update channel metadata.
		self.updateMetaData()
		#update channel info.
		self.updateChanInfo()

		#if there is only one "paintable" layer in the channel. export the layer.
		if mu.channelLayerCount(self.channelName) == 1:
			print "only one layer found in " + self.channelName
			#grab the channel
			exportChan = self._obj.channel(self.channelName)
			exportLayer = exportChan.layerList()[0]
			print "exporting layer " + str(exportLayer)
			#do not delet the channel after export
			self._deleteAfterExport = False

		else:
			#making export channel
			newChanName = self.channelName+"_Export"
			print "creating export channel: " + newChanName + "\n"
			exportChan = self._obj.createDuplicateChannel(self._obj.channel(self.channelName), newChanName)

			#flatten channel
			print "flattening channel ..."

			exportChan.flatten()
			exportChan.setLocked(1)
			exportLayer = exportChan.layer(self.EXPORT_LAYER)


		##prepair each image to be exported
		#get all valid image uvs to compair with the patches list
		imageSet = exportLayer.imageSet()
		for index in imageSet.uvIndices():
			indexUdim = int(index + 1001)
			if indexUdim in self._patchlist:
				image = imageSet.image(index)
				#swap udim tag with the udim number
				exportStr = re.sub(udimTag, str(indexUdim), str(self._exportPath))

				if str(self.channelDepth) == "8":
					print "converting image from 8 bit to 16 bit ..."
					image.convertDepth(16)

				#resize base on user input
				if self._outRes:
					if image.height() > self._outRes:
						print "resize image to ", self._outRes, " ..."
						QnewSize = QtCore.QSize(self._outRes, self._outRes)
						image.resize(QnewSize)

				#todo: add this after exported.
				self._exportedTextures.append(exportStr)
		

		#setup export path template
		exportTemplate = re.sub(udimTag, udimTemplate, str(self._exportPath))

		print "exporting:" + exportTemplate + "..."
		mari.app.processEvents()


		if patches:
			try:
				exportLayer.exportSelectedPatches(exportTemplate)
			except IOError, error:
				#delete the channel if so
				if self._deleteAfterExport:
					self._obj.removeChannel(exportChan)
				return None

		else:
			try:
				exportLayer.exportImages(exportTemplate)
			except IOError, error:
				#delete the channel if so
				if self._deleteAfterExport:
					self._obj.removeChannel(exportChan)
				return None

		mari.app.processEvents()

		#delete the channel if so
		if self._deleteAfterExport:
			print "deleting export channel ..."
			self._obj.removeChannel(exportChan)

		#all Done :)
		return self._exportedTextures

