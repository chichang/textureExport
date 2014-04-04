#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Form implementation generated from reading ui file 'xgTextureExportGui.ui'
#
# Created: Thu May  9 14:17:02 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PythonQt import QtCore, QtGui
from globals import *

#currentMariAsset = mari.projects.current().name()

class Ui_xgTextureExportGUI(QtGui.QDialog):

    def __init__(self):
        super(Ui_xgTextureExportGUI, self).__init__()

    def setupUi(self):
        #set Main Window Title.
        self.setWindowTitle("xg Texture Exporter")
        self.setObjectName("xgTextureExportGUI")
        self.setEnabled(True)
        self.resize(545, 702)
        ##===================================== CentralLayout ============================
        self.centralwidget = QtGui.QWidget()
        self.centralwidget.setObjectName("centralwidget")
        ##===================================== MasterLayout ============================
        self.master_GridLayout = QtGui.QGridLayout(self.centralwidget)
        self.master_GridLayout.setObjectName("master_GridLayout")
        ##===================================== TopLayout ============================
        self.top_GridLayout = QtGui.QGridLayout()
        self.top_GridLayout.setObjectName("top_GridLayout")
        ##=======exportPathLine======##
        self.exportPathLineEdit = QtGui.QLineEdit(self.centralwidget)
        self.exportPathLineEdit.setMinimumSize(QtCore.QSize(0, 30))
        self.exportPathLineEdit.setObjectName("exportPathLineEdit")
        self.top_GridLayout.addWidget(self.exportPathLineEdit, 2, 0, 1, 1)
        ##=======FolderLable=======##
        self.outputFolderLabel = QtGui.QLabel("Output Folder", self.centralwidget)
        setBold(self.outputFolderLabel)
        self.outputFolderLabel.setObjectName("outputFolderLabel")
        self.top_GridLayout.addWidget(self.outputFolderLabel, 0, 0, 1, 1)
        ##=======BrowseButton=======##
        self.browseButton = xgPushButton("browseButton", "Browse" ,0 ,"Choose texture output directory.")
        self.browseButton.setMinimumSize(QtCore.QSize(0, 30))
        self.top_GridLayout.addWidget(self.browseButton, 2, 1, 1, 1)
        self.master_GridLayout.addLayout(self.top_GridLayout, 0, 0, 1, 1)
        ##===================================== MidLayout ============================
        self.mid_HBoxLayout = QtGui.QHBoxLayout()
        self.mid_HBoxLayout.setObjectName("mid_HBoxLayout")
        self.midLeft_GridLayout = QtGui.QGridLayout()
        self.midLeft_GridLayout.setObjectName("midLeft_GridLayout")
        ##=======channelsLable=======##
        self.channels_Label = QtGui.QLabel("Channels",self.centralwidget)
        setBold(self.channels_Label)
        self.channels_Label.setObjectName("channels_Label")
        self.midLeft_GridLayout.addWidget(self.channels_Label, 0, 0, 1, 1)
        ##=======ChannelButtons=======##
        self.removeChannel_Button = xgPushButton("removeChannel_Button", "-", 0, "remove selected channels from export list.")
        self.removeChannel_Button.setMinimumSize(QtCore.QSize(0, 45))
        self.addChannel_Button = xgPushButton("addChannel_Button", "+", 0, "add selected channels to export list.")
        self.addChannel_Button.setMinimumSize(QtCore.QSize(0, 45))
        self.midLeft_GridLayout.addWidget(self.addChannel_Button, 2, 0, 1, 1)
        self.midLeft_GridLayout.addWidget(self.removeChannel_Button, 2, 1, 1, 1)

        ##=======ChannelList=======##
        self.channelsList_ListWidget = ChannelsToExportList()
        self.channelsList_ListWidget.isSortingEnabled()
        self.channelsList_ListWidget.setSortingEnabled(False)

        self.channelsList_ListWidget.setObjectName("channelsList_ListWidget")
        QtGui.QListWidgetItem(self.channelsList_ListWidget)
        self.midLeft_GridLayout.addWidget(self.channelsList_ListWidget, 1, 0, 1, 2)
        self.mid_HBoxLayout.addLayout(self.midLeft_GridLayout)
        self.options_GroupBox = QtGui.QGroupBox("Options",self.centralwidget)
        self.options_GroupBox.setObjectName("options_GroupBox")

        self.outputFormat_Label = QtGui.QLabel("Output Format :", self.options_GroupBox)
        self.outputFormat_Label.setGeometry(QtCore.QRect(20, 40, 121, 21))
        self.outputFormat_Label.setObjectName("outputFormat_Label")

        self.resolution_Label = QtGui.QLabel("Resolution:", self.options_GroupBox)
        self.resolution_Label.setGeometry(QtCore.QRect(20, 70, 121, 21))
        self.resolution_Label.setObjectName("resolution_Label")

        self.processTextures_Label = QtGui.QLabel("process textures:", self.options_GroupBox)
        self.processTextures_Label.setGeometry(QtCore.QRect(20, 100, 121, 21))
        self.processTextures_Label.setObjectName("processTextures_Label")

        ##=======Options=======##
        self.outFormat_ComboBox = QtGui.QComboBox(self.options_GroupBox)
        self.outFormat_ComboBox.setToolTip("define output texture format.")
        self.outFormat_ComboBox.setGeometry(QtCore.QRect(130, 40, 81, 25))
        self.outFormat_ComboBox.setEditable(False)
        self.outFormat_ComboBox.setObjectName("outFormat_ComboBox")
        self.outFormat_ComboBox.addItem("exr")
        self.outFormat_ComboBox.addItem("tif")
        self.outFormat_ComboBox.setCurrentIndex(1)

        self.resolution_ComboBox = QtGui.QComboBox(self.options_GroupBox)
        self.resolution_ComboBox.setToolTip("define output texture resolution.")
        self.resolution_ComboBox.setGeometry(QtCore.QRect(100, 70, 111, 25))
        self.resolution_ComboBox.setObjectName("resolution_ComboBox")
        self.resolution_ComboBox.addItem("channel res")
        self.resolution_ComboBox.addItem("full (8K)")
        self.resolution_ComboBox.addItem("heigh (4K)")
        self.resolution_ComboBox.addItem("mid (2K)")
        self.resolution_ComboBox.addItem("low (1K)")

        self.processTextures_ComboBox = QtGui.QComboBox(self.options_GroupBox)
        self.processTextures_ComboBox.setToolTip("define textures processing method.")
        self.processTextures_ComboBox.setGeometry(QtCore.QRect(135, 100, 105, 25))
        self.processTextures_ComboBox.setObjectName("processTextures_ComboBox")
        self.processTextures_ComboBox.addItem("None")
        self.processTextures_ComboBox.addItem("Local process")
        self.processTextures_ComboBox.addItem("Farm process")

        self.clearExpChan_CheckBox = QtGui.QCheckBox("Clear export channels", self.options_GroupBox)
        self.clearExpChan_CheckBox.setGeometry(QtCore.QRect(20, 130, 181, 23))
        self.clearExpChan_CheckBox.setChecked(False)
        self.clearExpChan_CheckBox.setObjectName("clearExpChan_CheckBox")
        self.clearExpChan_CheckBox.setToolTip("delete the flattened channels after export.")

        '''
        self.linear_CheckBox = QtGui.QCheckBox("Local process textures.", self.options_GroupBox)
        self.linear_CheckBox.setToolTip("convert textures to Mipmap exr localy.")
        self.linear_CheckBox.setGeometry(QtCore.QRect(20, 130, 181, 23))
        #self.linear_CheckBox.setChecked(True)
        self.linear_CheckBox.setObjectName("linear_CheckBox")

        self.texturePublish_CheckBox = QtGui.QCheckBox("Farm process textures.", self.options_GroupBox)
        self.texturePublish_CheckBox.setToolTip("process textures on the farm via texturePublish. \n (convert only will not publish.)")
        self.texturePublish_CheckBox.setGeometry(QtCore.QRect(20, 160, 181, 23))
        #self.texturePublish_CheckBox.setCheckable(False)
        self.texturePublish_CheckBox.setObjectName("texturePublish_CheckBox")

        self.publish_CheckBox = QtGui.QCheckBox("Publish After Export", self.options_GroupBox)
        self.publish_CheckBox.setGeometry(QtCore.QRect(20, 190, 181, 23))
        self.publish_CheckBox.setCheckable(False)
        self.publish_CheckBox.setObjectName("publish_CheckBox")
        '''

        self.mid_HBoxLayout.addWidget(self.options_GroupBox)
        self.master_GridLayout.addLayout(self.mid_HBoxLayout, 1, 0, 1, 1)
        self.bottom_VBoxLayout = QtGui.QVBoxLayout()
        self.bottom_VBoxLayout.setObjectName("bottom_VBoxLayout")
        self.exportChannels_Label = QtGui.QLabel("Channels For Export", self.centralwidget)
        self.exportChannels_Label.setObjectName("exportChannels_Label")
        setBold(self.exportChannels_Label)
        self.bottom_VBoxLayout.addWidget(self.exportChannels_Label)

        ##======table=======##
        self.exportChannelsList_tableWidget = QtGui.QTableWidget(self.centralwidget)
        self.exportChannelsList_tableWidget.setWordWrap(True)
        self.exportChannelsList_tableWidget.setCornerButtonEnabled(True)
        #self.exportChannelsList_tableWidget.setRowCount(2)
        self.exportChannelsList_tableWidget.setObjectName("exportChannelsList_tableWidget")
        self.exportChannelsList_tableWidget.setColumnCount(5)
        self.exportChannelsList_tableWidget.setRowCount(0)
        self.exportChannelsList_tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.exportChannelsList_tableWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.exportChannelsList_tableWidget.horizontalHeader().setVisible(True)
        self.exportChannelsList_tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.exportChannelsList_tableWidget.horizontalHeader().setMinimumSectionSize(25)
        self.exportChannelsList_tableWidget.horizontalHeader().setSortIndicatorShown(False)
        #self.exportChannelsList_tableWidget.horizontalHeader().setStretchLastSection(True)
        self.exportChannelsList_tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.exportChannelsList_tableWidget.verticalHeader().setDefaultSectionSize(28)
        self.exportChannelsList_tableWidget.verticalHeader().setMinimumSectionSize(10)

        self.itemLine0 = QtGui.QLineEdit("channel")
        self.item0 = QtGui.QTableWidgetItem(self.itemLine0.text)
        self.exportChannelsList_tableWidget.setHorizontalHeaderItem(0, self.item0)
        self.itemLine1 = QtGui.QLineEdit("type")
        self.item1 = QtGui.QTableWidgetItem(self.itemLine1.text)
        self.exportChannelsList_tableWidget.setHorizontalHeaderItem(1, self.item1)
        self.itemLine2 = QtGui.QLineEdit("version")
        self.item2 = QtGui.QTableWidgetItem(self.itemLine2.text)
        self.exportChannelsList_tableWidget.setHorizontalHeaderItem(2, self.item2)
        self.itemLine3 = QtGui.QLineEdit("non_color")
        self.item3 = QtGui.QTableWidgetItem(self.itemLine3.text)
        self.exportChannelsList_tableWidget.setHorizontalHeaderItem(3, self.item3)
        self.itemLine4 = QtGui.QLineEdit("variation")
        self.item4 = QtGui.QTableWidgetItem(self.itemLine4.text)
        self.exportChannelsList_tableWidget.setHorizontalHeaderItem(4, self.item4)

        self.exportChannelsList_tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.bottom_VBoxLayout.addWidget(self.exportChannelsList_tableWidget)
        self.exportButton_HBoxLayout = QtGui.QHBoxLayout()
        self.exportButton_HBoxLayout.setObjectName("exportButton_HBoxLayout")

        self.cancel_Button = xgPushButton("cancel_Button", "Cancel", 1)
        self.cancel_Button.setMinimumSize(QtCore.QSize(0, 45))
        self.exportButton_HBoxLayout.addWidget(self.cancel_Button)
        self.export_Button = xgPushButton("export_Button", "Export", 0)
        self.export_Button.setMinimumSize(QtCore.QSize(400, 45))
        self.exportButton_HBoxLayout.addWidget(self.export_Button)

        self.bottom_VBoxLayout.addLayout(self.exportButton_HBoxLayout)
        self.master_GridLayout.addLayout(self.bottom_VBoxLayout, 2, 0, 1, 1)
        self.setLayout(self.master_GridLayout)

class xgPushButton(QtGui.QPushButton):
    def __init__(self, name, title, bnScheme, tooltip = None):
        super(xgPushButton, self).__init__()
        self.name = name
        self.title = title
        self.bnScheme = bnScheme
        self.tooltip = tooltip

        self.setText(self.title)
        self.setToolTip(self.tooltip)
        
        if (self.bnScheme == 0):
            styleSheet = "QPushButton{background-color: rgb(50, 200, 255); color: rgb(50,50,50)}"

        elif (self.bnScheme == 1):
            styleSheet = "QPushButton{background-color: rgb(80, 80, 80); color: rgb(200,200,200)}"

        self.setStyleSheet(styleSheet)
        self.setObjectName(self.name)

class xgComboBox(QtGui.QComboBox):
    def __init__(self, name, title, bnScheme, tooltip = None):
        super(xgComboBox, self).__init__()
        self.name = name
        self.title = title
        self.bnScheme = bnScheme
        self.tooltip = tooltip

        self.setText(self.title)
        self.setToolTip(self.tooltip)
        
        if (self.bnScheme == 0):
            styleSheet = "QPushButton{background-color: rgb(50, 200, 255); color: rgb(50,50,50)}"%()

        elif (self.bnScheme == 1):
            styleSheet = "QPushButton{background-color: rgb(80, 80, 80); color: rgb(200,200,200)}"

        self.setStyleSheet(styleSheet)
        self.setObjectName(self.name)

class ChannelsToExportList(QtGui.QListWidget):
    def __init__(self, title="For Export"):
        super(ChannelsToExportList, self).__init__()
        self._title = title
        self.setSelectionMode(self.ExtendedSelection)

def setBold(widget):
    font = widget.font
    font.setWeight(75)
    widget.setFont(font)

