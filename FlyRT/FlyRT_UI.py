import sys
import cv2
import time
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QFileDialog, QApplication
from PyQt5.QtGui import QIcon
from os import system
import os
import config

import select_arena_roi as saROI
import FlyRTcore

cwd = os.getcwd()
qtCreatorFile = cwd+r"\FlyRT.ui"
 
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class ErrorMsg(QtWidgets.QMessageBox):
    def __init__(self, msg, parent=None):
        super(ErrorMsg, self).__init__(parent)
        self.setIcon(QtWidgets.QMessageBox.Critical)
        self.setText(msg)
        self.setWindowTitle('Error')

class WarningMsg(QtWidgets.QMessageBox):
    def __init__(self, msg, parent=None):
        super(WarningMsg, self).__init__(parent)
        self.setIcon(QtWidgets.QMessageBox.Warning)
        self.setText(msg)
        self.setWindowTitle('Warning')
        

class FlyRT(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle('FlyRT')
        self.setFixedSize(self.size())

        self.StartTrackingPB.clicked.connect(self.start_tracking)
        self.StopTrackingPB.clicked.connect(self.stop_tracking)
        self.ViewThresholdPB.clicked.connect(self.view_threshold)
        self.SetArenaROIPB.clicked.connect(self.select_arena_roi)
        self.InputVidPB.clicked.connect(self.selectInputFile)

        self.crop = None
        self.inpath = None


    def analysis_radio_button_clicked(self):
        print(self.PostHocRadioButton.checkedId())
        print(self.RTRadioButton.checkedId())
    
    def update_param_dict(self):
        self.FlyRT_params = {}

        self.FlyRT_params['record'] = self.RecordCheck.isChecked()
        self.FlyRT_params['log'] = self.LogCheck.isChecked()

        if self.LogCheck.isChecked():
            self.FlyRT_params['IFD'] = self.IFDCheck.isChecked()
            self.FlyRT_params['heading'] = self.HeadingCheck.isChecked()
            self.FlyRT_params['wings'] = self.WingsCheck.isChecked()
        else:
            self.FlyRT_params['IFD'] = False
            self.FlyRT_params['heading'] = False
            self.FlyRT_params['wings'] = False


        if (self.VidScaleCheck.isChecked()):
            self.FlyRT_params['scaling'] = self.VidScaleTextEdit.toPlainText()
        else:
            self.FlyRT_params['scaling'] = None

        self.FlyRT_params['arena_mms'] = self.ArenaDiameterSpin.value()

        self.FlyRT_params['drop_frames'] = self.DiscardFramesCheck.isChecked()

        self.FlyRT_params['thresh_val'] = self.ThreshValueSpin.value()

        if self.PostHocRadioButton.isChecked():
            self.FlyRT_params['analysis_type'] = "posthoc"
        else:
            self.FlyRT_params['analysis_type'] = "realtime"

        self.FlyRT_params['n_inds'] = self.NIndsSpin.value()
        self.FlyRT_params['mask_on'] = self.MaskOnCheck.isChecked()

        self.FlyRT_params['arduino'] = self.IFDExperimentRadioButton.isChecked()
        self.FlyRT_params['comm'] = self.ArduinoCommText.toPlainText()
        self.FlyRT_params['baud'] = self.baudRateSpin.value()
        self.FlyRT_params['pulse_len'] = self.pulseLenSpin.value()
        self.FlyRT_params['pulse_lockout'] = self.arduinoLockoutTimeSpin.value()
        self.FlyRT_params['IFD_thresh'] = self.IFDThreshSpin.value()
        self.FlyRT_params['IFD_time_thresh'] = self.TimeBelowIFDThreshSpin.value()

        if self.PostHocRadioButton.isChecked():
            self.FLIR = False
        if self.RTFLIRRadioButton.isChecked():
            self.FLIR = True
        else:
            self.FLIR = False

        self.FlyRT_params['FLIR'] = self.FLIR
        self.FlyRT_params['path'] = self.inpath



    def view_threshold(self):
        self.update_param_dict()

        if (self.crop is None):
            msg = 'Must specify input video source and ROI before viewing threshold  '
            self.error = ErrorMsg(msg)
            self.error.show()
            return None

        cv2.destroyAllWindows()

        if self.crop is not None:
            img = self.crop
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            cap = cv2.VideoCapture(self.inpath)
            time.sleep(1)
            ret, frame = cap.read()

            if ret==True:
                img = frame.copy()
                img = cv2.resize(img, None, fx = 0.5, fy = 0.5, interpolation = cv2.INTER_LINEAR)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cap.release()

        thresh_val = self.ThreshValueSpin.value()

        ret, thresh_img = cv2.threshold(img, thresh_val, 255,0)
        cv2.imshow("Threshold Value: {}".format(thresh_val), thresh_img)
        
        cv2.waitKey(0)

    def selectInputFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Select Input Video', '/home')

        self.inpath = str(fname[0])
        self.InputVidPathLabel.setText(self.inpath)   


    def select_arena_roi(self):
        self.update_param_dict()

        if (self.PostHocRadioButton.isChecked()) and (self.inpath is None):
            msg = 'Must specify input video before selecting ROI  '
            self.error = ErrorMsg(msg)
            self.error.show()
            return None

        if (self.PostHocRadioButton.isChecked()==False) and (self.RTUSBRadioButton.isChecked()==False) and (self.RTFLIRRadioButton.isChecked()==False):
            msg = 'Must specify analysis type from choices above before selecting ROI  '
            self.error = ErrorMsg(msg)
            self.error.show()
            return None

        self.idx = 0
        if self.FLIR==False:
            self.mask, self.r, self.crop = saROI.launch_GUI(self.inpath)
        else:
            self.mask, self.r, self.crop = saROI.launch_FLIR_GUI(self.idx)

        

    def get_param_dict(self):
        return self.FlyRT_params

    def start_tracking(self):
        try:
            if self.warning:
                pass
        except AttributeError:
            if self.ArenaDiameterSpin.value() == 0:
                msg = 'No Arena Diameter is defined.\nYou may still begin tracking but Inter-Fly Distance will be measured in pixels rather than millimeters and may cause other functins to behave unexpectedly.'
                self.warning = WarningMsg(msg)
                self.warning.show()
                return None
            else:
                pass



        config.stop_bit = False
        self.update_param_dict()
        try:
            FlyRTcore.run(self.FlyRT_params, self.crop, self.r, self.mask)
        except TypeError:
            msg = 'Unable to track animals. Try: \n - Adjust threshold \n - Ensure the number of animals present matches the defined value  '
            self.error = ErrorMsg(msg)
            self.error.show()
            return None


    def stop_tracking(self):
        config.stop_bit = True


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = FlyRT()
    window.show()
    sys.exit(app.exec_())