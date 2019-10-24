from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import (QPushButton, QWidget,
                             QLineEdit, QApplication, QMessageBox)
from PyQt5.QtCore import QSettings, QPoint, QSize, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette, QPixmap, QIcon
from PyQt5 import uic
from PyQt5 import QtCore
import sys, os, platform, subprocess
import urllib3
from zipfile import ZipFile
import threading
import time
import logging

logging.basicConfig(filename="./guiLog.txt", format='%(asctime)s-%(levelname)s-%message', datefmt='%d-%b-%y %H:%M:%S')

class LAIZER(QMainWindow):
    def __init__(self,ctx):
        super(LAIZER, self).__init__()
        uic.loadUi(ctx.get_resource("wear2bmpGUI2.ui"), self)
        self.baseURL = "http://13.52.220.35:5000"
        self.curpath, exename = os.path.split(os.path.realpath(sys.argv[0]))
        settingsPath = os.path.join(self.curpath,"settings.ini")
        self.settings = QSettings(settingsPath, QSettings.IniFormat)
        logging.info(f'loading settings file from: {settingsPath}')
        print(f'loading settings file from: {settingsPath}')
        self.loadSettings()
        self.saveSettings()

        self.button_inputFiles.clicked.connect(self.browseForFiles)
        self.button_selectAll.clicked.connect(self.makeSelection(2))
        self.button_deselectAll.clicked.connect(self.makeSelection(0))
        self.button_clearSelected.clicked.connect(self.clearSelected)
        self.button_toggleHighlighted.clicked.connect(self.toggleHighlighted)
        self.button_go.clicked.connect(self.goCallback)
        self.button_outputFolder.clicked.connect(self.browseForFolder)

        self.list_filenames.itemDoubleClicked.connect(self.onListItemClicked)
        p = self.label_inputImage.sizePolicy()
        p.setHeightForWidth(True)
        self.label_inputImage.setSizePolicy(p)
        p = self.label_outputImage.sizePolicy()
        p.setHeightForWidth(True)
        self.label_outputImage.setSizePolicy(p)

        self.inputImagePath = ""
        self.outputImagePath = ""


        self.centralwidget.installEventFilter(self)
        self.http = urllib3.PoolManager()
        self.connectedEvent = threading.Event()
        self.downloadingEvent = threading.Event()
        self.errorEvent = threading.Event()
        self.r = 0

    def resizeEvent(self, event):
        self.showInputOutput()

    def open_file(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def loadSettings(self):
        size = self.settings.value("size", QSize(800, 850))
        pos = self.settings.value("pos", QPoint(50, 50))
        self.baseURL = self.settings.value("url", "http://70.184.65.226:5000")
        outputFolder = self.settings.value("outputFolder", self.curpath)
        self.resize(size)
        self.move(pos)
        self.text_outputFolder.clear()
        self.text_outputFolder.insertPlainText(outputFolder)

    def saveSettings(self):
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("url", self.baseURL)
        self.settings.setValue("outputFolder", self.text_outputFolder.toPlainText())

    def closeEvent(self, event):
        print("closing")
        self.saveSettings()

    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.DragEnter or
                event.type() == QtCore.QEvent.DragMove or
                event.type() == QtCore.QEvent.DragLeave or
                event.type() == QtCore.QEvent.Drop):
            event.accept()
            if event.type() == QtCore.QEvent.Drop:
                self.dropAction(event)
            return True
        else:
            event.ignore()
        return False

    def dropAction(self, event):
        if event.mimeData().hasUrls:
            for i in event.mimeData().urls():
                self.addFileName(i.toLocalFile())

    def makeSelection(self, state):
        _list = self.list_filenames

        def selectAll():
            for i in range(_list.count()):
                check_box = _list.item(i)
                check_box.setCheckState(state)
        return selectAll

    def isLegalFile(self, filename):
        if os.path.isfile(filename):
            _list = self.list_filenames
            for i in range(_list.count()):
                item = _list.item(i)
                if item.text() == filename:
                    self.statusBar().showMessage(
                        "Warning: One or more items not added because they were already on the list", 10000)
                    logging.warning("Warning: One or more items not added because they were already on the list")
                    return False

            root, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext != '.png' and ext != '.jpg' and ext != ".jpeg":
                self.statusBar().showMessage(
                    "Error: Can only add .png and .jpg file types", 10000
                )
                logging.error("Can only add .png and .jpg file types")
                return False
            return True
        else:
            if os.path.isdir(filename):
                self.statusBar().showMessage("Error: Cannot add directories to the file list", 10000)
                logging.error("Cannot add directories to the file list")
            return False

    def addFileName(self, filename):
        if self.isLegalFile(filename):  # if it is a legal file
            _list = self.list_filenames
            item = QListWidgetItem(filename)
            item.setCheckState(False)
            _list.addItem(item)

    def clearSelected(self):
        _list = self.list_filenames
        print('clearing')
        i = 0
        count = _list.count()
        while i < count:
            item = _list.item(i)
            # print(i,type(item),"check state:", item.checkState())
            if item.checkState() > 0:
                _list.takeItem(i)
                count = count - 1
            else:
                i = i + 1

    def toggleHighlighted(self):
        for i in self.list_filenames.selectedItems():
            c = i.checkState()
            if c == 0:
                i.setCheckState(2)
            else:
                i.setCheckState(0)

    def browseForFolder(self):
        file = QFileDialog.getExistingDirectory(self, "Select Directory")
        print(file)
        if file != "":
            self.text_outputFolder.setPlainText(file)

    def onListItemClicked(self,item):
        self.inputImagePath = item.text()
        self.outputImagePath = os.path.join(self.text_outputFolder.toPlainText(),"output",os.path.basename(item.text()))
        self.showInputOutput()

    def showInputOutput(self):
        pixmap = QPixmap(self.inputImagePath)
        if pixmap:
            h = self.label_inputImage.height()
            w = self.label_inputImage.width()
            s = h
            if h > w: s = w
            self.label_inputImage.setPixmap(pixmap.scaledToHeight(s))

        pixmap = QPixmap(self.outputImagePath)
        if pixmap:
            h = self.label_outputImage.height()
            w = self.label_outputImage.width()
            s = h
            if h > w: s = w
            self.label_outputImage.setPixmap(pixmap.scaledToHeight(s))

    def browseForFiles(self):
        file = QFileDialog.getOpenFileNames(self, "Select Files")
        for i in range(len(file[0])):
            self.addFileName(file[0][i])

    def goCallback(self):
        self.statusBar().showMessage("",1000)
        self.connectedEvent.clear()
        self.downloadingEvent.clear()
        self.errorEvent.clear()
        self.button_go.setText("Waiting for server")
        self.button_go.setEnabled(False)
        error = False
        httpRequestThread = []
        msg = ""
        if self.text_outputFolder.toPlainText() == "":
            msg = "Error: Output folder not set"
            logging.error
            error = True
        if not os.path.isdir(self.text_outputFolder.toPlainText()):
            msg ="Error: Output folder is not valid (did you make a typo?)"
            error = True
        if self.list_filenames.count() == 0:
            error = True
            self.statusBar().showMessage("Error: File list is empty",5000)
        if not error:
            files = []
            for i in range(self.list_filenames.count()):
                path = self.list_filenames.item(i).text()
                name = os.path.basename(path)
                filename, ext = os.path.splitext(name)
                # print(path, '\t', ext[1:].lower())
                header = ('images', (name, open(path, 'rb').read(), 'image/'+ext[1:].lower()))
                files.append(header)
            print("Uploading to " + self.baseURL)
            httpRequestThread = threading.Thread(target=self.httpRequest, args=(files,))
            httpRequestThread.start()
            #while httpRequestThread.is_alive():
            #    time.sleep(1)
            #if not self.errorEvent.isSet():
            #    print("httpRequestThread joined successfully")
            #else:
            #    print("found an error")
            #    self.statusBar().showMessage("an exception occurred",5000)
        else:
            self.statusBar().showMessage(msg, 5000)
            self.button_go.setText("Upload")
            self.button_go.setEnabled(True)
            self.showInputOutput()
        #    self.statusBar().showMessage("Something went wrong contacting the server")

    def httpRequest(self, files):
        print("trying to contact server")
        try:
            print('Uploading data...')
            self.statusBar().showMessage("Uploading data...", 1000)
            self.r = self.http.request('POST', self.baseURL + "/App", fields=files)
            self.connectedEvent.set()
            self.statusBar().showMessage("Finished uploading data, now checking status", 1000)
            print("uploaded")
            print(self.r.status)
            # wait for response from server about status
            self.r = self.http.request('GET', self.baseURL + "/CheckStatus", preload_content=False)
            rval = self.r.data.decode('ascii')
            self.statusBar().showMessage("Request status: " + rval, 1000)
            while rval == 'running' or rval == 'received':
                self.r = self.http.request('GET', self.baseURL + "/CheckStatus", preload_content=False)
                rval = self.r.data.decode('ascii')
                self.statusBar().showMessage("Request status: " + rval, 1000)
                time.sleep(5)
            # if request finished successfully, send download request
            print("status: ", rval)
            if rval == 'finished':
                self.r = self.http.request('GET', self.baseURL + "/download", preload_content=False)
                with open(os.path.join(self.text_outputFolder.toPlainText(), "results.zip"), 'wb') as out:
                    self.downloadingEvent.set()
                    while True:
                        data = self.r.read(128)
                        if not data:
                            break
                        out.write(data)
                self.r.release_conn()
                self.statusBar().showMessage("Finished Downloading", 3000)
                if not os.path.isdir(self.text_outputFolder.toPlainText()+"/output"):
                    print("trying to mkdir at " + self.text_outputFolder.toPlainText()+"/output")
                    os.mkdir(self.text_outputFolder.toPlainText()+"/output")
                with ZipFile(self.text_outputFolder.toPlainText()+'/results.zip', 'r') as zipObj:
                    zipObj.extractall(path=self.text_outputFolder.toPlainText()+"/output")
                self.open_file(self.text_outputFolder.toPlainText()+"/output")
            else:
                raise Exception(self.r.data)
        except Exception as e:
            print("an exception occurred: ", e)
            self.statusBar().showMessage("an exception occurred: " + str(e), 5000)
            self.errorEvent.set()
        finally:
            #self.r.release_conn()
            self.button_go.setText("Upload")
            self.button_go.setEnabled(True)
            self.showInputOutput()

    def statusBarWaiting(self, base, event):
        print("started")
        dotCount = 0
        while not event.isSet() and not self.errorEvent.isSet():
            msg = base
            for i in range(dotCount):
                msg = msg + "."
            dotCount = dotCount + 1
            if dotCount > 100:
                dotCount = 0
            self.statusBar().showMessage(msg, 100)
            # print(msg)
            time.sleep(.1)
        dotCount = 0


class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext

    def run(self):                              # 2. Implement run()
        window = LAIZER(self)
        version = self.build_settings['version']
        window.setWindowTitle("wear2bmpGUI v" + version)
        window.show()
        return self.app.exec_()                 # 3. End run() with this line


if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit(exit_code)

