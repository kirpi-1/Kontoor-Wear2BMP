from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import *

def on_top_clicked():
    alert = QMessageBox()
    alert.setText('You clicked the button')
    alert.exec_()

app = QApplication([])
window = QWidget();
label = QLabel('hello world')
# set general palette rules for whole gui
palette = QPalette()
palette.setColor(QPalette.ButtonText, Qt.red)
app.setPalette(palette)
app.setStyleSheet("QPushButton { margin: 10ex; }")

topButton = QPushButton('Top')
topButton.clicked.connect(on_top_clicked)

okayCancelLayout = QHBoxLayout();
okayCancelLayout.addWidget(QPushButton("Okay"));
okayCancelLayout.addWidget(QPushButton('Cancel'));

layout = QVBoxLayout();
layout2 = QHBoxLayout();
layout.addWidget(topButton)
layout.addWidget(QPushButton('Bottom'))
# set specific palette rule for widget 0 ('Top' button)
palette2 = QPalette()
palette2.setColor(QPalette.ButtonText, Qt.blue)
palette2.setColor(QPalette.WindowText, Qt.darkGreen)
layout.itemAt(0).widget().setPalette(palette2)

label.setPalette(palette2)
layout2.addWidget(label)
layout2.addLayout(layout)
layout2.itemAt(0).widget().setPalette(palette2)
window.setLayout(layout2)

window.show();

app.exec_()
