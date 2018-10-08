from PyQt5.QtWidgets import (QMainWindow, QTextEdit, 
    QAction, QFileDialog, QApplication)
from PyQt5.QtGui import QIcon
import sys

class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initUI()
        
        
    # def initUI(self):      

    #     self.textEdit = QTextEdit()

    #     openFile = QAction(QIcon('open.png'), 'Open', self)
    #     openFile.setShortcut('Ctrl+O')
    #     openFile.setStatusTip('Open new File')
    #     openFile.triggered.connect(self.showDialog)

    #     menubar = self.menuBar()
    #     fileMenu = menubar.addMenu('&File')
    #     fileMenu.addAction(openFile)       
        
    #     self.setGeometry(300, 300, 350, 300)
    #     self.setWindowTitle('File dialog')
    #     self.show()
        
        
    def initUI(self):

        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')

        print(fname[0])        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())