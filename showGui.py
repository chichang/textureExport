#======================
# Mr.X Mari Tools
#======================

import os
import sys
sys.path.insert(0, "/USERS/chichang/tools/mari/textureExport/")
import shlex
import utils as imp_utils
import xgTextureExport
reload(xgTextureExport)
reload(imp_utils)

#======================================================================
#	VARS
#======================================================================

debug = 0
menuName = "Mr.X"
mu = imp_utils.ccMariUtil()
su = imp_utils.ccSysUtil(os.getenv("SHOW"), os.getenv("SHOT"))

#======================================================================
#	MARI 
#======================================================================
def createDefaultChans(channelDict):
	'''
	creates defalt channels specified in the defaultChannels dictionary.
	'''
	geo = mari.geo.current()
	geoChannels = geo.channelList()
	for channel in channelDict:
		if channel not in geoChannels:
			try:
				geo.createChannel(channel, 8192, 8192, channelDict[channel])
			except:
				pass

#======================================================================
#  SIGNAL CALLBACKS
#======================================================================
_retainBuffer = 0
_bufferScale = 0
_bufferRotation = 0
_bufferTranslate = 0
pBuffer = mari.canvases.paintBuffer()

def preBake():
	'''
	pre bake signal call. store paint buffer attrs.
	'''
	if _retainBuffer ==0:
		if debug: print "retain buffer is off."
		return
	elif _retainBuffer ==1:
		if debug: print "store buffer attrs"
		global _bufferScale, _bufferRotation, _bufferTranslate
		#stor buffer attrs
		_bufferScale = pBuffer.scale()
		_bufferRotation = pBuffer.rotation()
		_bufferTranslate = pBuffer.translation()

def postBake():
	'''
	post bake signal call. set paint buffer attrs.
	'''
	if _retainBuffer ==0:
		if debug: print "retain buffer is off."
		return
	elif _retainBuffer ==1:
		if debug: print "set buffer atters"
		#set buffer attrs
		pBuffer.setScale(_bufferScale)
		pBuffer.setRotation(_bufferRotation)
		pBuffer.setTranslation(_bufferTranslate)

def retainBufferSet(mode):
	'''
	set retainBuffer check variable and update Menue
	'''
	global _retainBuffer
	if mode == "on":
		_retainBuffer = 1
		if debug: print "turn on retain buffer."
		mari.menus.removeAction(retainBufferOn, "MainWindow/"+menuName)
		mari.menus.addAction(retainBufferOff, "MainWindow/"+menuName)

	elif mode == "off":
		_retainBuffer = 0
		if debug: print "turn off retain buffer."
		mari.menus.removeAction(retainBufferOff, "MainWindow/"+menuName)
		mari.menus.addAction(retainBufferOn, "MainWindow/"+menuName)

def showTextureExportGUI():
	#versionCheck
	if mari.app.version().major() != 2:
		mari.utils.message("Sorry. Mari 2.0 only.")
	else:
		GUI = xgTextureExport.TextureExportWindow()
		GUI.showUI()

#======================================================================
#   MENU
#======================================================================
createChannelsAction = mari.actions.create("Create Default Channels", 'createDefaultChans(defaultChannels)')
retainBufferOn = mari.actions.create("Turn On Retain Paint Buffer", 'retainBufferSet("on")')
retainBufferOff = mari.actions.create("Turn Off Retain Paint Buffer", 'retainBufferSet("off")')
textureExport = mari.actions.create("Export Textures", 'showTextureExportGUI()')

def addGothamMenu():
	#gotham tools
	mari.menus.addAction(textureExport, "MainWindow/"+menuName)
	#mari.menus.addAction(createChannelsAction, "MainWindow/"+menuName)
	mari.menus.addSeparator("MainWindow/"+menuName)
	mari.menus.addAction(retainBufferOn, "MainWindow/"+menuName)

	#connect signal callbacks
	connect(mari.canvases.paintBuffer().aboutToBake, preBake)
	connect(mari.canvases.paintBuffer().baked, postBake)

#======================================================================
#   ADD MENU
#======================================================================
if __name__=="__main__":
	#addGothamMenu()
	print "Mr.X Tools Added to Menu."
	showTextureExportGUI()