
#======================
# xg Texture Export
#======================
import os
import sys
import mari
import subprocess
from PythonQt import QtCore, QtGui
from functools import partial
import utils as imp_utils
#reload(imp_utils)
import globals
#reload(globals)
import xgNewTypeGui
#reload(xgNewTypeGui)
import xgTextureExportGui
#reload(xgTextureExportGui)
import xMariChannel
#reload (xMariChannel)

#======================================================================
#	UTIL
#======================================================================
debug = 0

g_export_cancelled = None

mu = imp_utils.ccMariUtil()
su = imp_utils.ccSysUtil(os.getenv("SHOW"), os.getenv("SHOT"))

#======================================================================
#   WINDOW
#======================================================================

def debugMsg(message):
    if debug == 1:
        print message

class TextureExportWindow():
    '''
    the main export gui class.
    '''
    CHAN_NAME_COL = 0
    CHAN_TYPE_COL = 1
    TEX_VERSION_COL = 2
    CHAN_DEPTH_COL = 3
    TEXT_VARIATION_COL = 4
    #===========================#
    NEW_VER = "v001"
    DEFAULT_VARIATION = "N/A"
    #===========================#
    in_export_list_chan=[]

    def __init__(self):

        # Check that we're starting from a state where exporting channels is possible
        if not mu.isProjectSuitable():
            return

        #geral info from mari
        userAssetDir = os.getenv("USER_SHOT_DIR")
        self.defaultExportPath = os.path.join(userAssetDir,"textures")
        self.currentMariAsset = mari.projects.current().name()

        #set up ui
        self.gui = QtGui
        self.ui = xgTextureExportGui.Ui_xgTextureExportGUI()
        self.ui.setupUi()

        #fill inital ui info
        self.ui.exportPathLineEdit.setText(self.defaultExportPath + "/" +self.currentMariAsset)
        #channelList = sorted(mari.geo.current().channelList())
        channelList = mari.geo.current().channelList()

        #create channel objects for all channels in the list
        for chan in channelList:
            if chan.isLocked():
                continue
            self.ui.channelsList_ListWidget.addItem(chan.name())

        #connect callbacks
        self.ui.browseButton.connect("clicked()", self.browseForFolder)
        self.ui.cancel_Button.connect("clicked()", self.ui.reject)
        self.ui.export_Button.connect("clicked()", self.export)
        self.ui.addChannel_Button.connect("clicked()", self.addChannel)
        self.ui.removeChannel_Button.connect("clicked()", self.removeChannel)
        self.ui.exportPathLineEdit.connect("textChanged(QString)", self.exportPathUpdate)
        self.ui.exportPathLineEdit.connect("textEdited(QString)", self.exportPathUpdate)

        #set ui title
        self.show = os.environ.get("SHOW", None)
        self.shot = os.environ.get("SHOT", None)
        self.ui.setWindowTitle("X Texture Export: "+self.show+" | "+self.shot)

        #set export chan list to empty
        self.in_export_list_chan=[]

    def showUI(self):
        '''
        show gui.
        '''
        if not mu.isProjectSuitable():
            return
    	#show ui.
        self.ui.show()

    def browseForFolder(self):
        '''
        browser for choosing the output dir. 
        '''
        #Get Folder
        defaultDir = self.ui.exportPathLineEdit.text
        fileDialog = self.gui.QFileDialog(0,"Select Directory for Export")
        fileDialog.setDirectory(defaultDir)
        dirname = fileDialog.getExistingDirectory()
        if dirname:
            self.ui.exportPathLineEdit.setText(dirname)

    def exportPathUpdate(self):
        '''
        clear the table widget when export path is updated.
        '''
        # reset display and remove any existing rows
        self.ui.exportChannelsList_tableWidget.clearContents()
        for i in range (self.ui.exportChannelsList_tableWidget.rowCount, 0, -1):
            self.ui.exportChannelsList_tableWidget.removeRow(i - 1)

        self.in_export_list_chan=[]


    def addChannel(self):
        '''
        add selected channel to export table widget and setup inital col content.
        '''
        selected_chan = [item.text() for item in self.ui.channelsList_ListWidget.selectedItems()]
        # disable column sorting temporarily, this makes sure that Qt doesn't
        # try to sort rows as they're added
        self.ui.exportChannelsList_tableWidget.setSortingEnabled(False)

        currentRow = self.ui.exportChannelsList_tableWidget.rowCount
 
        for chan in selected_chan:

            if chan in self.in_export_list_chan:
                continue

            else:
                self.ui.exportChannelsList_tableWidget.insertRow(currentRow)
                chanDepth = mu.getChannelDepth(chan)

                ncdCheckText = str(chanDepth)

                exportPath = self.ui.exportPathLineEdit.text

                #init cell item
                self.chanNameItem = xLable(chan, currentRow, self.CHAN_NAME_COL)
                self.chanTypeCombo = xComboBox(chan, currentRow, self.CHAN_TYPE_COL, exportPath)

                self.dataCheckBox = xNcdCheckBox(ncdCheckText, currentRow, self.CHAN_DEPTH_COL)
                self.dataCheckBox.configCheckState(self.chanTypeCombo.itemText(self.chanTypeCombo.currentIndex))
                self.texVariationhItem = xTableItem(self.DEFAULT_VARIATION, currentRow, self.TEXT_VARIATION_COL)
                
                #check if there is an existing version for the texture type
                latestVer = su.getNewVersion(exportPath, self.chanTypeCombo.currentText)

                if not latestVer:
                    self.versionLabel = xLable(self.NEW_VER)
                else:
                    self.versionLabel = xLable(latestVer)

                #add cell items
                self.ui.exportChannelsList_tableWidget.setCellWidget(self.chanNameItem.itemRow,self.chanNameItem.itemCul, self.chanNameItem)
                self.ui.exportChannelsList_tableWidget.setCellWidget(self.chanTypeCombo.itemRow,self.chanTypeCombo.itemCul, self.chanTypeCombo)
                self.ui.exportChannelsList_tableWidget.setCellWidget(self.dataCheckBox.itemRow,self.dataCheckBox.itemCul, self.dataCheckBox)
                self.ui.exportChannelsList_tableWidget.setItem(self.texVariationhItem.itemRow,self.texVariationhItem.itemCul, self.texVariationhItem)
                self.ui.exportChannelsList_tableWidget.setCellWidget(currentRow,self.TEX_VERSION_COL, self.versionLabel)
                #print "cell items added"

                #connect callback
                self.chanTypeCombo.connect("currentIndexChanged(QString)", partial(self.itemChanged, comboBox = self.chanTypeCombo ,checkBox = self.dataCheckBox))

                self.in_export_list_chan.append(chan)

                currentRow = currentRow+1


    def removeChannel(self):
        '''
        add selected channel to export table widget and setup inital col content.
        '''
        rows = self.ui.exportChannelsList_tableWidget.rowCount
        selRow = self.ui.exportChannelsList_tableWidget.currentRow()

        if selRow == -1:
            return

        channelLabel = self.ui.exportChannelsList_tableWidget.cellWidget(selRow, self.CHAN_NAME_COL).text
        self.ui.exportChannelsList_tableWidget.removeRow(selRow)
        self.in_export_list_chan.remove(channelLabel)

        for row in range(selRow, rows-1):
            channelCombo = self.ui.exportChannelsList_tableWidget.cellWidget(row, self.CHAN_TYPE_COL)
            channelCombo.itemRow -= 1

    def itemChanged(self, QString, comboBox, checkBox):
        '''
        when combo box is updated on a channel.
        update version number and variation setting based on the new update.
        '''
        #update comboBox attr
        comboBox.name = QString
        #get the current export path
        exportPath = self.ui.exportPathLineEdit.text
        if debug: print "changeddd! update version!!!!", QString, itemRow

        #update object values
        if QString in globals.CHANNEL_DEFAULTS:
            comboBox.typeAbbr = globals.CHANNEL_DEFAULTS[QString]["abbr"]
            checkBox.configCheckState(QString)

        #if selected in New. ask for input
        elif QString == "New...":
            #get existing types
            currentTypes=[]
            for index in range(0, comboBox.count):
                currentTypes.append(comboBox.itemText(index))

            newTypeGUI = NewTextureTypeWindow(currentTypes)
            
            #block
            newTypeGUI.ui.exec_()

            if newTypeGUI.ui.result():
                comboBox.newType = newTypeGUI.ui.typeName_lineEdit.text
                comboBox.removeItem(comboBox.count-1)
                comboBox.removeItem(comboBox.count-1)
                comboBox.addItem(comboBox.newType)
                comboBox.setCurrentIndex(comboBox.count-1)

                #store the new value in the combo box objext
                comboBox.newAbbr = newTypeGUI.ui.nameTag_lineEdit.text
                comboBox.typeAbbr = comboBox.newAbbr

                if newTypeGUI.ui.color_radioButton.isChecked():
                    checkBox.setChecked(False)
                elif newTypeGUI.ui.noncolor_radioButton.isChecked():
                    checkBox.setChecked(True)

            else:
                if debug: print "cancel create new type."
                comboBox.configChannelType()
                pass

        else:
            comboBox.configChannelType(setItem=False)
            checkBox.configCheckState(QString)

        #get the latest version
        latestVer = su.getNewVersion(exportPath, QString)
        if not latestVer:
            self.versionLabel = xLable(self.NEW_VER)
        else:
            self.versionLabel = xLable(latestVer)

        #update table widget
        self.ui.exportChannelsList_tableWidget.setCellWidget(comboBox.itemRow,self.TEX_VERSION_COL, self.versionLabel)
        
        comboBox.setStyle(1)
        
        if debug: print latestVer
        if debug: print comboBox.typeAbbr

    def export(self):
        '''
        export!
        '''
        ##preflight check
        #since textureManager assumes all exr are linear. if submit to farm. tifs' only.
        if self.ui.processTextures_ComboBox.currentIndex == 2:
            if self.ui.outFormat_ComboBox.currentText != "tif":
                mari.utils.message("Farm convert supports tif only.")
                return

        export_channel_List = []
        fail_channel_List = []

        rootDir = self.ui.exportPathLineEdit.text

        #Find a way to share these with all xmc objects
        obj = mari.geo.current()
        outFormat = self.ui.outFormat_ComboBox.currentText
        outRes = self.ui.resolution_ComboBox.currentIndex


        if rootDir == "" :
            mari.utils.message("Please select an output directory.")
            return

        channelCount = self.ui.exportChannelsList_tableWidget.rowCount

        if (channelCount == 0):
            mari.utils.message("Nothing to export ...")
            return

        #check if the export path is not in the SHOT directory.
        #create root folder if doesnt exist
        if not os.path.exists(rootDir):
            try:
                os.makedirs(rootDir)
                print "Directory created: ", rootDir
            except OSError:
                errors.append("Error creating directory: '%s'" % rootDir)
                return errors

        print "prepairing to export ..."
        print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

        #=============X CHANNEL PREP=============#
        for row in range(0,channelCount):

            ## make sure all the needed data is set before start exporting
            channelLabel = self.ui.exportChannelsList_tableWidget.cellWidget(row, self.CHAN_NAME_COL)
            channelCombo = self.ui.exportChannelsList_tableWidget.cellWidget(row, self.CHAN_TYPE_COL)
            chennelComboIndex = channelCombo.currentIndex
            channelVerLabel = self.ui.exportChannelsList_tableWidget.cellWidget(row, self.TEX_VERSION_COL)
            channelDepthCheckText = self.ui.exportChannelsList_tableWidget.cellWidget(row, self.CHAN_DEPTH_COL)
            channelVariationItem = self.ui.exportChannelsList_tableWidget.item(row, self.TEXT_VARIATION_COL)

            #info for each channel
            channelName = channelLabel.text
            channelType = channelCombo.itemText(chennelComboIndex)
            channelAbbr = channelCombo.typeAbbr
            textureVersion = channelVerLabel.text
            channelDepth = channelDepthCheckText.name
            ncd =  channelDepthCheckText.isChecked()
            textureVariation = channelVariationItem.text()

            #create xMariChannel object and store in the list
            xmc = xMariChannel.X_MariChannel(channelName, channelType, channelAbbr, textureVersion, ncd, channelDepth, textureVariation)
            
            #fill in needed variables
            xmc._patchlist = mu.getAllPatchs()
            xmc._obj = obj
            xmc._deleteAfterExport = self.ui.clearExpChan_CheckBox.isChecked()

            if self.ui.processTextures_ComboBox.currentIndex == 1:
                xmc._localConvert = True
            else:
                xmc._localConvert = False

            xmc._outFormat = outFormat
            xmc._outRes = self.imageResolution(outRes)

            #generate name and export path
            xmc.exportName()
            
            #move this to export loop so create dir before export but not all at once
            xmc.exportPath(rootDir)

            #store in the list
            if xmc._readytoExport:
                export_channel_List.append(xmc)
            else:
                fail_channel_List.append(xmc)

            #if the list is succesfuly created. start the acturl exprot process.

        #=============EXPORT PREP=============#
        #init progress dialog
        channel_count = len(export_channel_List)
        print ("Exporting %s channels." % channel_count) 
        #calculate the progress bar stepSize 
        prog_step_size = 100.0 / float(channel_count) 
        prog_current_step = 0.0 
        #generate progress UI 
        ProgressDialog.instance = ProgressDialog()
        ProgressDialog.instance.show()
        print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

        #=============EXPORT=============#

        for xmc in export_channel_List:

            #print xChannel info
            xmc.printChannelInfo()
            #make prograss bar
            ProgressDialog.instance.progress_text.setText("Exporting..." + xmc.channelName)
            #Processes events such as redrawing the screen and updating the GUI.
            mari.app.processEvents()

            #EXPORT
            error = xmc.export()

            #if error
            if error:
                print "error exporting image:" ,error
                fail_channel_List.append(xmc)

            elif g_export_cancelled: 
                raise UserCancelledException()

            #update progress bar
            ProgressDialog.instance.pbar.setValue(prog_step_size)
            prog_step_size += prog_step_size
            print"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

        #close after progress UI 
        ProgressDialog.instance.close() 

        #close the ui
        self.ui.reject()


        channelCheck = su.sameListItems(fail_channel_List,export_channel_List)
        if len(channelCheck) != 0:
            for chan in channelCheck:
                export_channel_List.remove(chan)

        #show export message
        exp_message ="XXX    xgTextureExport    XXX" + "\n"+ "\n"
        exp_message +="XXX    SHOW: " + self.show + "\n"
        exp_message +="XXX    SHOT: " + self.shot + "\n"+"\n"

        exp_message += "CHANNELS EXPORTED:"+ "\n"
        exp_message += "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"+ "\n"+ "\n"
        for xmc in export_channel_List:
            exp_message += "Channel: " + xmc.channelName + "\n"
            exp_message += "Path:"+ "\n" + xmc._exportPath + "\n"+ "\n"
        exp_message += "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"+ "\n"+ "\n"

        if len(fail_channel_List) != 0:
            exp_message += "CHANNELS FAILED:"+ "\n"
            exp_message += "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"+ "\n"
            for xmc in fail_channel_List:
                exp_message += "Channel: " + xmc.channelName + "\n"


        #texturePublish
        #submit to texturePublish
        if self.ui.processTextures_ComboBox.currentIndex == 2:

            print "submitting following path to texturePublish:"

            for xmc in export_channel_List:

                print "channel ", xmc.channelName, ": non-color is:", xmc.ncd
                print "path submitted to farm is: ", os.path.split(xmc._exportPath)[0]

                self.texturePublish(os.path.split(xmc._exportPath)[0], xmc.ncd)

            exp_message += "Exported Textures Submitted to farm!"+ "\n"


        self.box = xMessage(exp_message)
        self.box.show()

    def texturePublish(self, path, ncd):
        '''
        submit to texturePublish.
        '''
        ## ask for user input on asset name, use asset neme for now ...
        callList = ["texturePublish", "-a", str(mari.projects.current().name())]

        if ncd  == True:
                callList.append("-n")
        elif ncd  == False:
                callList.append("-c")
        else:
            pass

        callList.append(str(path))

        callList.append("--convert")

        print callList
        #print su.runCommand(callList)
        su.runCommand(callList)


    def imageResolution(self, index):
        if index == 0:
            return None
        if index == 1:
            return 8192
        if index == 2:
            return 4096
        if index == 3:
            return 2048
        if index == 4:
            return 1024


#======================================================================
#   WIDGET CLASSES
#======================================================================

class UserCancelledException(Exception): 
    pass

class xTableItem(QtGui.QTableWidgetItem):

    def __init__(self, name, itemRow, itemCul, exportDir=None):
        super(xTableItem ,self).__init__()

        label = QtGui.QLabel(name).text
        self.setText(label)
        self.itemRow = itemRow
        self.itemCul = itemCul
        if self.itemCul == 4:
            self.col = QtGui.QColor(10, 100, 100)
        else:
            self.col = QtGui.QColor(0, 0, 0)

        #set background color
        self.setBackground(self.col)

class xComboBox(QtGui.QComboBox):
    '''
    channel type combo box.
    this class also holds information that will be used at export time.
    '''
    def __init__(self, name, itemRow, itemCul, exportDir=None):
        super(xComboBox ,self).__init__()

        self.exportDir = exportDir
        self.name = name
        self.itemRow = itemRow
        self.itemCul = itemCul
        self.types = list(globals.CHANNEL_DEFAULTS)
        #==========================================
        self.typeAbbr = None
        self.newType = None
        self.newAbbr = None
        #==========================================

        # create combolist items
        self.setToolTip("define output texture type. \nthis will also be the root folder name for the texture.")
        self.setObjectName(self.name)
        #get current existing dirs
        currentDirTypes = su.listDir(self.exportDir)
        if currentDirTypes:
            #merge the default type with found folders
            self.types = su.mergeLists(self.types, currentDirTypes)
        else:
            pass

        #add Items to comboBox
        self.addItems(self.types)
        #option to set new texture type
        self.insertSeparator(self.count)
        self.addItem("New...")

        #set item based on channel name and metadata
        self.configChannelType()

    def configChannelType(self, setItem = True):
        for texType in globals.CHANNEL_DEFAULTS:
            for key in globals.CHANNEL_DEFAULTS[texType]["channels"]:
                if key in self.name.lower():
                    if debug: print "found: ", key, "set texture type to: ", texType
                    #set item
                    if setItem:
                        for index in range(self.count-1):
                            if self.itemText(index) == texType:
                                self.setCurrentIndex(index)

                    self.typeAbbr = globals.CHANNEL_DEFAULTS[texType]["abbr"]
                    self.setStyle(1)
                    return True

        if debug: print "unknown type."

        if self.newAbbr:
            self.typeAbbr = self.newAbbr
        else:
            self.typeAbbr = None

        #set to a default type
        if setItem:
            self.setCurrentIndex(9)

        self.setStyle(0)
        return False

    def setStyle(self, style=1):

        if style == 1:
            styleSheet = "QComboBox{background-color: rgb(50, 50, 50)} QAbstractItemView{background-color: rgb(50, 50, 50)}"

        if style == 0:
            styleSheet = "QComboBox{background-color: rgb(150, 20, 10)} QAbstractItemView{background-color: rgb(50, 50, 50)}"

        self.setStyleSheet(styleSheet)


class xLable(QtGui.QLabel):
    def __init__(self, name, itemRow=None, itemCul=None, exportDir=None):
        super(xLable ,self).__init__()
        self.name = name
        self.exportDir = exportDir
        self.itemRow = itemRow
        self.itemCul = itemCul
        self.setText(self.name)


class ProgressDialog(QtGui.QDialog):
    instance = None
    def __init__(self):
        super(ProgressDialog, self).__init__()
        self.setWindowTitle('Exporting...')
        #set layout
        self.v_layout = QtGui.QVBoxLayout()
        self.setLayout(self.v_layout)
        #create cancel button & connect
        self.cancel_button = QtGui.QPushButton("Cancel")
        mari.utils.connect(self.cancel_button.clicked, lambda: self.cancel())
        #create other widgets
        self.pbar = QtGui.QProgressBar(self)
        self.progress_text = QtGui.QLabel(self)
        self.progress_text.setText('Exporting...')
        self.pbar.setValue(0)
        
        #add widgets
        self.v_layout.addWidget(self.pbar)
        self.v_layout.addWidget(self.progress_text)
        self.v_layout.addWidget(self.cancel_button)

    def cancel(self):
        global g_export_cancelled
        g_export_cancelled = True


class xNcdCheckBox(QtGui.QCheckBox):
    def __init__(self, name, itemRow, itemCul):
        super(xNcdCheckBox,self).__init__()
        self.name = name
        self.itemRow = itemRow
        self.itemCul = itemCul
        #self.setText(self.name)

    def configCheckState(self, comboText):
        if comboText in list(globals.CHANNEL_DEFAULTS):
            if globals.CHANNEL_DEFAULTS[comboText]["ncd"]:
                self.setChecked(True)
            else:
                self.setChecked(False)
        else:
            self.setChecked(False)

class xMessage(QtGui.QMessageBox):
    def __init__(self, message):
        super(xMessage ,self).__init__()
        self.message = message
        self.setText(message)
        self.addButton("OK", QtGui.QMessageBox.ActionRole)


#======================================================================
#   NEW TYPE WINDOW
#======================================================================

class NewTextureTypeWindow():

    def __init__(self, currentTypes):

        #set up ui
        self.gui = QtGui
        self.ui = xgNewTypeGui.Ui_xgNewTypeGUI()
        self.currentTypes = currentTypes
        self.ui.setupUi()

        if debug: print self.currentTypes

        #setup validators
        nameRe=QtCore.QRegExp("\w{1,}")
        nameValidator=QtGui.QRegExpValidator(nameRe, self.ui.typeName_lineEdit)
        self.ui.typeName_lineEdit.setValidator(nameValidator)

        tagRe=QtCore.QRegExp("[a-z][a-z][a-z][a-z]")
        tagValidator=QtGui.QRegExpValidator(tagRe, self.ui.nameTag_lineEdit)
        self.ui.nameTag_lineEdit.setValidator(tagValidator)

        #connect callbacks
        self.ui.cancel_Button.connect("clicked()", self.ui.reject)
        self.ui.ok_button.connect("clicked()", self.okClicked)

    def okClicked(self):

        error = ""
        isColor = self.ui.color_radioButton.isChecked()
        isNoncolor = self.ui.noncolor_radioButton.isChecked()

        if self.ui.typeName_lineEdit.text == "":
            error = "please enter new texture type name."

        elif self.ui.typeName_lineEdit.text in self.currentTypes:
            error = self.ui.typeName_lineEdit.text + " already exist."
        
        elif self.ui.nameTag_lineEdit.text == "":
            error = "please enter new texture type file name tag."

        elif (isColor==False | isNoncolor==False) :
            error = "please select texture data type."

        if error != "":
            mari.utils.message(error)
            return

        self.ui.accept()


class AssetNameWindow():
    pass



#======================================================================
#   RUN
#======================================================================
if __name__ == "__main__":
    pass
    #GUI = TextureExportWindow()
	#GUI.showUI()
