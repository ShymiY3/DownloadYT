from pytube import YouTube
from PyQt5 import QtCore, QtGui, QtWidgets
from GUI import *
import os, sys
from threading import Thread

class App():
    def __init__(self):
        self.url = ""
        self.streams = []
        self.app = QtWidgets.QApplication(sys.argv)
        self.Window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.Window)
        self.ui.b_load.clicked.connect(self.load)

    def load(self):
        self.url = self.ui.le_load.text()
        self.th =Thread(target=self.get_streams)
        self.th.start
        

    def get_streams(self):
        try:
            self.yt = YouTube(self.url)
            self.ui.pb_load.setMaximum(0)
            for i in self.yt.streams:
                self.streams.append(i)
                print(i)
        except: 
            self.ui.DisplayError("Invalid link", "Please make sure it's the right link")
        self.ui.pb_load.setMaximum(1)
        self.th.join()
        
    def run(self):
        self.Window.show()
        sys.exit(self.app.exec_())
