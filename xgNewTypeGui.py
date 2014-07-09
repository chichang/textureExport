#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# Form implementation generated from reading ui file 'xgTextureExportGui.ui'
#
# Created: Thu May  9 14:17:02 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PythonQt import QtCore, QtGui
#currentMariAsset = mari.projects.current().name()

class Ui_xgNewTypeGUI(QtGui.QDialog):

    def __init__(self):
        super(Ui_xgNewTypeGUI, self).__init__()

    def setupUi(self):
        #set Main Window Title.
        self.setWindowTitle("Define New Type")
        self.setObjectName("xgNewTypeGUI")
        self.setEnabled(True)
        self.resize(400, 220)

        self.centralwidget = QtGui.QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.master_gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.master_gridLayout.setObjectName("master_gridLayout")
        self.options_GroupBox = QtGui.QGroupBox("Options", self.centralwidget)
        self.options_GroupBox.setObjectName("options_GroupBox")
        self.master_gridLayout.addWidget(self.options_GroupBox, 0, 0, 1, 1)

        self.main_GridLayout = QtGui.QGridLayout()
        self.main_GridLayout.setObjectName("main_GridLayout")
        self.typeName_label = QtGui.QLabel("Texture Type Name: ",self.centralwidget)
        self.typeName_label.setObjectName("typeName_label")
        self.main_GridLayout.addWidget(self.typeName_label, 0, 0, 1, 1)

        self.ok_button = QtGui.QPushButton("OK", self.centralwidget)
        self.ok_button.setMinimumSize(QtCore.QSize(0, 45))
        self.ok_button.setStyleSheet("QPushButton{background-color: rgb(50, 200, 185); color: rgb(50,50,50)}")
        self.ok_button.setObjectName("ok_button")
        self.main_GridLayout.addWidget(self.ok_button, 8, 2, 1, 1)

        self.cancel_Button = QtGui.QPushButton("Cancel",self.centralwidget)
        self.cancel_Button.setMinimumSize(QtCore.QSize(0, 45))
        self.cancel_Button.setObjectName("cancel_Button")
        self.main_GridLayout.addWidget(self.cancel_Button, 8, 0, 1, 1)

        self.nameTag_label = QtGui.QLabel("File Name Tag: ",self.centralwidget)
        self.nameTag_label.setObjectName("nameTag_label")
        self.main_GridLayout.addWidget(self.nameTag_label, 1, 0, 1, 1)

        self.dataType_label = QtGui.QLabel("Texture Data Type: ",self.centralwidget)
        self.dataType_label.setObjectName("dataType_label")
        self.main_GridLayout.addWidget(self.dataType_label, 5, 0, 1, 1)

        self.color_radioButton = QtGui.QRadioButton("Color",self.centralwidget)
        self.color_radioButton.setObjectName("color_radioButton")
        self.main_GridLayout.addWidget(self.color_radioButton, 5, 2, 1, 1)

        self.typeName_lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.typeName_lineEdit.setMinimumSize(QtCore.QSize(0, 30))
        self.typeName_lineEdit.setObjectName("typeName_lineEdit")
        self.typeName_lineEdit.setText("diffuse")
        self.main_GridLayout.addWidget(self.typeName_lineEdit, 0, 2, 1, 1)

        self.nameTag_lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.nameTag_lineEdit.setMinimumSize(QtCore.QSize(0, 30))
        self.nameTag_lineEdit.setMaximumSize(QtCore.QSize(100, 16777215))
        self.nameTag_lineEdit.setObjectName("nameTag_lineEdit")
        self.nameTag_lineEdit.setText("col")
        self.main_GridLayout.addWidget(self.nameTag_lineEdit, 1, 2, 1, 1)

        self.noncolor_radioButton = QtGui.QRadioButton("Non-Color",self.centralwidget)
        self.noncolor_radioButton.setObjectName("noncolor_radioButton")


        self.main_GridLayout.addWidget(self.noncolor_radioButton, 6, 2, 1, 1)

        self.master_gridLayout.addLayout(self.main_GridLayout, 1, 0, 1, 1)

        self.setLayout(self.master_gridLayout)