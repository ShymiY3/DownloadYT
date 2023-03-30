from pytube import YouTube, exceptions
from PyQt5 import QtCore, QtGui, QtWidgets
from GUI import *
import os, sys
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from proglog import TqdmProgressBarLogger


#main app
class App():
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.Window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.Window)
        self.ui.b_load.clicked.connect(self.load)
        self.ui.b_cancel.clicked.connect(self.cancel)
        self.ui.b_save.clicked.connect(self.save)

    #load button
    def load(self):
        self.url= self.ui.le_load.text()
        self.ui.b_load.setEnabled(False)
        try:
            self.download = DownloadV(self.url)
            self.ui.pb_load.setMaximum(0)
            self.ui.Title.setText(self.download.title)
            self.threadLoad = ThreadLoad(self.download)
            self.threadLoad.start()
            self.threadLoad.signal_error.connect(lambda: self.ui.DisplayError("Invalid link", "Please make sure it's the right link"))
            self.threadLoad.signal_end.connect(self.set_combobox)
            self.threadLoad.signal_end.connect(lambda: self.ui.pb_load.setMaximum(1))
            self.threadLoad.signal_end.connect(lambda: self.ui.b_load.setEnabled(True))
            self.threadLoad.signal_end.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.p_down))
            self.threadLoad.signal_error.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.p_load))
            self.threadLoad.signal_error.connect(lambda: self.ui.DisplayError("Invalid link", "Please make sure it's the right link"))
            self.threadLoad.signal_error.connect(lambda: self.ui.pb_load.setMaximum(1))
            self.threadLoad.signal_error.connect(lambda: self.ui.b_load.setEnabled(True))
        except Exception as e:
            self.ui.DisplayError("Invalid link", "Please make sure it's the right link")
            self.ui.pb_load.setMaximum(1)
            self.ui.b_load.setEnabled(True)
    #combobox
    def set_combobox(self):
        for i in self.download.quality:
            self.ui.cb_quality.addItem(f"Resolution: {i['res']} \t FPS: {i['fps']}", i["itag"])
    
    #save button
    def save(self):
        self.ui.b_save.setEnabled(False)
        self.ui.cb_quality.setEnabled(False)
        try:
            path = str(QtWidgets.QFileDialog.getExistingDirectory(self.ui.p_down, "Select directory"))
            self.threadDown = ThreadDownload(self.download, self.ui.cb_quality.currentData(), path)
            self.threadDown.start()
            self.threadDown.signal_end.connect(lambda: self.ui.b_save.setEnabled(True))
            self.threadDown.signal_end.connect(lambda: self.ui.cb_quality.setEnabled(True))
            self.threadDown.signal_end.connect(lambda: self.ui.pb_down.setValue(0))
            self.download.signal_prog.connect(lambda x: self.ui.pb_down.setValue(x))
            self.download.signal_prog.connect(lambda x: print("Loading", "\t", x))
        except Exception as e:
            self.ui.b_save.setEnabled(True)
            self.ui.cb_quality.setEnabled(True)
            print(e)

    #cancel button
    def cancel(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.p_load)
        self.ui.cb_quality.clear()
        self.threadDown.terminate()
        self.ui.pb_down.setValue(100)
        self.ui.b_save.setEnabled(True)
        del self.download


    def run(self):
        self.Window.show()
        sys.exit(self.app.exec_())

#Donwload function
class DownloadV(QtCore.QObject):
    signal_prog = QtCore.pyqtSignal(int)
    
    def __init__(self, url, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.yt = YouTube(url, on_progress_callback=self.progress_Check)
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
        if stream.is_progressive:
            video_path = stream.download(output_path=output, filename=self.title+".mp4")
        else:
            video_path = stream.download(output_path=output, filename='v!@#$%.mp4', skip_existing=False)
            video_clip = VideoFileClip(video_path)
            audio = self.yt.streams.get_audio_only()
            audio_path = audio.download(output_path=output, filename='a!@#$%.mp4')
            audio_clip = AudioFileClip(audio_path)
            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(os.path.join(output, self.title + ".mp4"))
            os.remove(audio_path)
            os.remove(video_path)

    def progress_Check(self, stream = None, chunk = None, remaining = None, file_handle = None):
        self.signal_prog.emit(int((stream.filesize - remaining)/stream.filesize*100))

        
#Thread to download
class ThreadDownload(QtCore.QThread):
    signal_end = QtCore.pyqtSignal()
    signal_error = QtCore.pyqtSignal()
    
    def __init__(self, download: DownloadV, itag: int, output: str, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.d = download
        self.i = itag
        self.o = output

    def run(self):
        self.d.download(self.i, self.o)
        self.signal_end.emit()

    def stop(self):
        self.threadactive = False
        self.wait()

#Thread to load streams
class ThreadLoad(QtCore.QThread):
    signal_end = QtCore.pyqtSignal()
    signal_error = QtCore.pyqtSignal()

    def __init__(self, download: DownloadV, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.download = download

    def run(self):
        try:
            self.download.get_streams()
            self.signal_end.emit()
        except Exception as e: 
            self.signal_error.emit()
            print(e)

#in progress
class MyBarLogger(TqdmProgressBarLogger):
    def callback(self, **changes):
        # Every time the logger is updated, this function is called
        if len(self.bars):
            self.percentage = next(reversed(self.bars.items()))[1]['index'] / next(reversed(self.bars.items()))[1]['total']
        