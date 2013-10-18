
import os
import sys
import re
import mari
from PythonQt import QtCore, QtGui
from globals import *
import utils as imp_utils
#reload(imp_utils)
import xconvert as xc
#reload(xc)

#======================================================================
#	UTIL
#======================================================================
su = imp_utils.ccSysUtil()
mu = imp_utils.ccMariUtil()
#======================================================================
#	VAR
#======================================================================
udimTag = "<UDIM>"
xUserName = os.getenv("USERNAME")
xAsset = os.getenv("SHOT")
xShow = os.getenv("SHOW")

#======================================================================
#	Mair Class
#======================================================================

class X_MariChannel():

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
		self._exportPath = None
		self._obj = None
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

			exportVersionDir = os.path.join(rootPath, self.channelType, self.textureVersion)
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


	def export(self):

		'''
		do the export.
		'''

		print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
		print "Exporting: " + self.channelName + "\n"

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


		#get image set
		imageSet = exportLayer.imageSet()


		#get all valid image uvs to compair with the patches list
		for index in imageSet.uvIndices():

			indexUdim = int(index + 1001)

			if indexUdim in self._patchlist:

				image = imageSet.image(index)
				
				#swap udim tag with the udim number
				exportStr = re.sub(udimTag, str(indexUdim), str(self._exportPath))
				print "exporting: " , exportStr, "..."

				##hangle each image
				#convert 8bit channels to higher bit
				if str(self.channelDepth) == "8":
					print "converting image from 8 bit to 16 bit ..."
					image.convertDepth(16)

				#resize base on user input
				if self._outRes:
					if image.height() > self._outRes:
						print "resize image to ", self._outRes, " ..."
						QnewSize = QtCore.QSize(self._outRes, self._outRes)
						image.resize(QnewSize)

				try:
					#to the export!
					image.saveAs(exportStr)

				except IOError, error:
					#delete the channel if so
					if self._deleteAfterExport:
						self._obj.removeChannel(exportChan)
					return error

				mari.app.processEvents()

				#if exr do mipmap
				#local convert

				if self._outFormat == "exr": 

					if self._localConvert == True:

						#local convert mipmap exr
						if self.ncd == False:

							print "linearizing and mipmaping texture ..."
							mari.app.processEvents()

							callList = ["oiio_maketx",exportStr ,"--colorconvert","sRGB", "linear","--tile", "64", "64", "--hash", "-o", exportStr ]
							su.runCommand(callList)

						elif self.ncd == True:

							print "mipmaping texture ..."
							mari.app.processEvents()

							callList = ["oiio_maketx", exportStr,"--tile", "64", "64", "--hash", "-o", exportStr ]
							su.runCommand(callList)

						#mrx headers
						print "writing mrx headers ..."
						mari.app.processEvents()

						#xc.writeHeadersInplace(exportStr, artist = xUserName, asset = xAsset, show = xShow)

						if (self._localConvert == True and self.ncd == False):
							xc.writeHeadersInplace(exportStr, colorSpace = "linear")
						else:
							xc.writeHeadersInplace(exportStr, colorSpace = "ncd")


				elif self._outFormat == "tif":

					if self._localConvert == True:

						#local convert mipmap exr
						exrExportStr = os.path.join(os.path.split(exportStr)[0], os.path.splitext(os.path.split(exportStr)[1])[0] + ".exr")

						#local convert mipmap exr
						if self.ncd == False:

							print "outputting Linear mipmaped exr ..."
							mari.app.processEvents()

							callList = ["oiio_maketx",exportStr ,"--colorconvert","sRGB", "linear","--tile", "64", "64", "--hash", "-o", exrExportStr ]
							su.runCommand(callList)

						elif self.ncd == True:

							print "outputting mipmaped exr ..."
							mari.app.processEvents()

							callList = ["oiio_maketx", exportStr,"--tile", "64", "64", "--hash", "-o", exrExportStr ]
							su.runCommand(callList)

						#mrx headers
						print "writing mrx headers ..."
						mari.app.processEvents()
						
						#xc.writeHeadersInplace(exportStr, artist = xUserName, asset = xAsset, show = xShow)

						if (self._localConvert == True and self.ncd == False):
							xc.writeHeadersInplace(exrExportStr, colorSpace = "linear")
						else:
							xc.writeHeadersInplace(exrExportStr, colorSpace = "ncd")


		#delete the channel if so
		if self._deleteAfterExport:
			print "deleting export channel ..."
			self._obj.removeChannel(exportChan)



		def localProcess(self, texture):
			pass




		#all Done :)
		return None

