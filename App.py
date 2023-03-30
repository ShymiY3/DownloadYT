from pytube import YouTube, exceptions
from PyQt5 import QtCore, QtGui, QtWidgets
from GUI import *
import os, sys




class App():
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.Window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.Window)
        self.ui.b_load.clicked.connect(self.load)
        self.ui.b_cancel.clicked.connect(self.cancel)
        self.ui.b_save.clicked.connect(self.save)

    def load(self):
        self.url= self.ui.le_load.text()
        self.ui.b_load.setEnabled(False)
        try:
            self.download = DownloadV(self.url)
            self.ui.pb_load.setMaximum(0)
            self.ui.Title.setText(self.download.title)
            self.thread = ThreadLoad(self.download)
            self.thread.start()
            self.thread.signal_error.connect(lambda: self.ui.DisplayError("Invalid link", "Please make sure it's the right link"))
            self.thread.signal_end.connect(self.set_combobox)
            self.thread.signal_end.connect(lambda: self.ui.pb_load.setMaximum(1))
            self.thread.signal_end.connect(lambda: self.ui.b_load.setEnabled(True))
            self.thread.signal_end.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.p_down))
            self.thread.signal_error.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.p_load))
            self.thread.signal_error.connect(lambda: self.ui.DisplayError("Invalid link", "Please make sure it's the right link"))
            self.thread.signal_error.connect(lambda: self.ui.pb_load.setMaximum(1))
            self.thread.signal_error.connect(lambda: self.ui.b_load.setEnabled(True))
        except Exception as e:
            self.ui.DisplayError("Invalid link", "Please make sure it's the right link")
            self.ui.pb_load.setMaximum(1)
            self.ui.b_load.setEnabled(True)
            print(e)

    def set_combobox(self):
        for i in self.download.quality:
            self.ui.cb_quality.addItem(f"Resolution: {i['res']} \t FPS: {i['fps']}", i["itag"])

    def save(self):
        path = str(QtWidgets.QFileDialog.getExistingDirectory(self.ui.p_down, "Select directory"))
        self.download.download(self.ui.cb_quality.currentData(), path)

    def cancel(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.p_load)
        self.ui.cb_quality.clear()
        del self.download


    def run(self):
        self.Window.show()
        sys.exit(self.app.exec_())

class DownloadV():
    def __init__(self, url):
        self.yt = YouTube(url)
        self.title = self.yt.title

    def get_streams(self):
        
        self.streams = [i for i in self.yt.streams]
        self.quality = []
        for s in self.streams:
            if (s.type == "video" and s.is_progressive):
                self.quality.append({
                    "itag": s.itag, 
                    "res": s.resolution,
                    "fps": s.fps,
                    "progressive": s.is_progressive,
                    "type": s.mime_type})
        
        for s in self.streams:
            if (s.type == "video" and s.is_progressive==False):
                for item in self.quality:
                    if s.fps == item["fps"] and s.resolution == item["res"]:
                        if s.mime_type == "mp4" and item["progressive"]==False:
                            self.quality.append({
                                "itag": s.itag, 
                                "res": s.resolution,
                                "fps": s.fps,
                                "progressive": s.is_progressive,
                                "type": s.mime_type})
                        break
                else:
                    self.quality.append({
                            "itag": s.itag, 
                            "res": s.resolution,
                            "fps": s.fps,
                            "progressive": s.is_progressive,
                            "type": s.mime_type})
                    

    
    def download(self, itag, output):
        stream = self.yt.streams.get_by_itag(itag)
        stream.download(output_path=output)
                        
#                        , filename=fr"{self.title} - {stream.resolution} | {stream.fps}

        

class ThreadLoad(QtCore.QThread):
    signal_end = QtCore.pyqtSignal()
    signal_error = QtCore.pyqtSignal()

    def __init__(self, download: DownloadV, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.download = download

    def run(self):
        #try:
        self.download.get_streams()
        self.signal_end.emit()
        #except Exception as e: 
            #self.signal_error.emit()
            #print(e)
        