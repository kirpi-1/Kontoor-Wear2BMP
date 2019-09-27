from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import (QPushButton, QWidget,
                             QLineEdit, QApplication)
from PyQt5.QtCore import QSettings, QPoint, QSize, Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPalette
from PyQt5 import uic
from PyQt5 import QtCore
import sys, os
import urllib3


class LAIZER(QMainWindow):
    def __init__(self,ctx):
        super(LAIZER, self).__init__()
        uic.loadUi(ctx.get_resource("wear2bmpGUI.ui"), self)
        self.baseURL = "http://192.168.1.13:5000"
        self.curpath,exename = os.path.split(os.path.realpath(sys.argv[0]))
        self.settings = QSettings(os.path.join(self.curpath,"settings.ini"), QSettings.IniFormat)
        self.loadSettings()

        self.button_inputFiles.clicked.connect(self.browseForFiles)
        self.button_selectAll.clicked.connect(self.makeSelection(2))
        self.button_deselectAll.clicked.connect(self.makeSelection(0))
        self.button_clearSelected.clicked.connect(self.clearSelected)
        self.button_toggleHighlighted.clicked.connect(self.toggleHighlighted)
        self.button_go.clicked.connect(self.goCallback)
        self.button_outputFolder.clicked.connect(self.browseForFolder)

        self.centralwidget.installEventFilter(self)
        self.http = urllib3.PoolManager()


    def loadSettings(self):
        size = self.settings.value("size", QSize(800, 850))
        pos = self.settings.value("pos", QPoint(50, 50))
        self.baseURL = self.settings.value("url","http://192.168.1.13:5000")
        outputFolder = self.settings.value("outputFolder", self.curpath)
        self.resize(size)
        self.move(pos)
        self.text_outputFolder.clear();
        self.text_outputFolder.insertPlainText(outputFolder)

    def saveSettings(self):
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("url",self.baseURL)
        self.settings.setValue("outputFolder",self.text_outputFolder.toPlainText())

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

    def isLegalFile(self,filename):
        if os.path.isfile(filename):
            _list = self.list_filenames
            for i in range(_list.count()):
                item = _list.item(i)
                if item.text() == filename:
                    self.statusBar().showMessage(
                        "Warning: One or more items not added because they were already on the list", 10000)
                    return False

            root,ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext != '.png' and ext !='.jpg' and ext!=".jpeg":
                self.statusBar().showMessage(
                    "Error: Can only add .png and .jpg file types",10000
                )
                return False
            return True
        else:
            if os.path.isdir(filename):
                self.statusBar().showMessage("Error: Cannot add directories to the file list", 10000)
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
        self.text_outputFolder.clear()
        self.text_outputFolder.insertPlainText(file)

    def browseForFiles(self):
        file = QFileDialog.getOpenFileNames(self, "Select Files")
        for i in range(len(file[0])):
            self.addFileName(file[0][i])

    def goCallback(self):
        if self.text_outputFolder.toPlainText()=="":
            self.statusBar().showMessage("Error: Output folder not set",10000)
        if not os.path.isdir(self.text_outputFolder.toPlainText()):
            self.statusBar().showMessage("Error: Output folder is not valid (did you make a typo?)",10000)
        print("Uploading")
        #multiple_files = [
        #    ('images', ('1.png', open('E:/Project/Webapp/1.png', 'rb').read(), 'image/png')),
        #    ('images', ('2.jpg', open('E:/Project/Webapp/2.jpg', 'rb').read(), 'image/jpg')),
        #    ('images', ('3.jpg', open('E:/Project/Webapp/3.jpg', 'rb').read(), 'image/jpg')),
        #];

        files = [];
        for i in range(self.list_filenames.count()):
            path = self.list_filenames.item(i).text();
            name = os.path.basename(path);
            filename,ext = os.path.splitext(name);
            #print(path, '\t', ext[1:].lower())
            header = ('images',(name,open(path,'rb').read(),'image/'+ext[1:].lower()));
            files.append(header);
        r = self.http.request('POST', self.baseURL + "/App", fields=files,preload_content=False)
        self.statusBar().showMessage("Uplaoding...")
        dotCount = 0;
        with open(os.path.join(self.text_outputFolder.toPlainText(),"results.zip"), 'wb') as out:
            while True:
                data = r.read(128)
                if not data:
                    break
                out.write(data)
                msg = "Downloading"
                for i in range(dotCount):
                    msg = msg + "."
                dotCount = dotCount + 1
                if(dotCount>100):
                    dotCount=0
                self.statusBar().showMessage("Downloading", 10000)
        r.release_conn()



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

