import sys
import os
import cv2
import threading
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import time
from Util.FaceCompare import face_cmp
from Util import IdxDatManage, Log
from Controls import tableview
from Util import GlobalUtil
################################
from collections import namedtuple
preview = namedtuple("preview", "id title image")
################################
sys.path.insert(0, '../socket-keyboard')

strOnnxDirPath = "./onnx"
strImgTmpDirPath = "./Images"
WIN_W = 1000
WIN_H = 740

def ResetCtrlImage(ctrl, imgPath='', isResource=True):
    rc = ctrl.rect()
    if type(ctrl) == QWidget:
        bImgData = IdxDatManage.getImgData(imgPath)
        pixmap = QPixmap()
        pixmap.loadFromData(bImgData)
        palette = ctrl.palette()
        brush = QBrush(pixmap.scaled(rc.width(), rc.height()))
        palette.setBrush(QPalette.Window, brush)
        ctrl.setPalette(palette)
    else:
        if isResource:
            bImgData = IdxDatManage.getImgData(imgPath)
            pixmap = QPixmap()
            pixmap.loadFromData(bImgData)
        else:
            pixmap = filepath2pixmap(imgPath)
        ctrl.setPixmap(pixmap.scaled(rc.width(), rc.height()))

class Ui_MainWindow(object):
    isSelectDirectory = False
    imgInfo1 = {}
    imgInfo2 = {}
    strTargetDirPath = ""

    def setupUi(self, MainWindow):
        self.centralwidget = QWidget(MainWindow)
        # self.centralwidget.setStyleSheet("background-image:url('./Resource/BKGround.jpg')")
        # ResetCtrlImage(self.centralwidget, 'BKGround.jpg')
        # -------------------------------------
        rcWnd = QRect(0, 0, WIN_W, WIN_H)
        self.labelBKG = QLabel(self.centralwidget)
        self.labelBKG.setGeometry(rcWnd)
        ResetCtrlImage(self.labelBKG, 'BKGround.jpg')
        # -------------------------------------
        margin = 10
        between = 20
        left = margin
        top = margin
        # -------------------------------------
        width = 70
        height = 70
        self.logo = QLabel(self.centralwidget)
        self.logo.setGeometry(left, top, width, height)
        ResetCtrlImage(self.logo, 'logo.jpg')
        # -------------------------------------
        strStyle = "background:transparent;color:white;font-size:14px;"
        left = margin + 10
        top += height + 10
        width = int((rcWnd.width() - (margin * 2 + between)) / 2)
        height = 30
        self.labelSubject = QLabel(self.centralwidget)
        self.labelSubject.setGeometry(left, top, width, height)
        self.labelSubject.setStyleSheet(strStyle)
        self.labelSubject.setText("Subject")

        left = rcWnd.right() - margin - width + 10
        self.labelTarget = QLabel(self.centralwidget)
        self.labelTarget.setGeometry(left, top, width, height)
        self.labelTarget.setStyleSheet(strStyle)
        self.labelTarget.setText("Target")
        # -------------------------------------
        strStyle = "background:transparent;border: 2px solid yellow;color:white;font-size:20px;"
        left = margin
        top += height + 10
        width = int((rcWnd.width() - (margin * 2 + between)) / 2)
        height = 300
        self.labelImage1 = QLabel(self.centralwidget)
        clickable(self.labelImage1).connect(self.onShowImage1)
        self.labelImage1.setGeometry(left, top, width, height)
        self.labelImage1.setStyleSheet(strStyle)
        self.labelImage1.setAlignment(Qt.AlignCenter)
        ResetCtrlImage(self.labelImage1, 'logo.jpg')

        left = rcWnd.right() - margin - width
        self.labelImage2 = QLabel(self.centralwidget)
        clickable(self.labelImage2).connect(self.onShowImage2)
        self.labelImage2.setGeometry(left, top, width, height)
        self.labelImage2.setStyleSheet(strStyle)
        self.labelImage2.setAlignment(Qt.AlignCenter)
        ResetCtrlImage(self.labelImage2, 'logo.jpg')
        # -------------------------------------
        strStyle = "background:transparent;border: 0px;color:white;font-size:14px;"
        left = margin
        top += height + 10
        height = 50
        self.labelImage1Content = QLabel(self.centralwidget)
        self.labelImage1Content.setGeometry(left, top, width, height)
        self.labelImage1Content.setText("Gender: \nAge:")
        self.labelImage1Content.setStyleSheet(strStyle)

        left = rcWnd.right() - margin - width
        self.labelImage2Content = QLabel(self.centralwidget)
        self.labelImage2Content.setGeometry(left, top, width, height)
        self.labelImage2Content.setText("Gender: \nAge:")
        self.labelImage2Content.setStyleSheet(strStyle)
        # -------------------------------------
        strStyle = "background:transparent;border: 0px;"
        top += height + between
        width = 230
        height = 60
        left = int((rcWnd.width() - width) / 2)
        self.btnCompare = QLabel(self.centralwidget)
        self.btnCompare.setStyleSheet(strStyle)
        self.btnCompare.setText("Compare")
        self.btnCompare.setGeometry(left, top, width, height)
        ResetCtrlImage(self.btnCompare, 'Compare.png')
        clickable(self.btnCompare).connect(self.onCompare)
        # -------------------------------------
        strStyle = "background:transparent;border: 0px;color:white;font-size:14px;font-weight:bold;"
        width = 400
        height = 55
        left = int((rcWnd.width() - width) / 2)
        self.labelMatchStatus = QLabel(self.centralwidget)
        self.labelMatchStatus.setGeometry(left, top, width, height)
        self.labelMatchStatus.setStyleSheet(strStyle)
        self.labelMatchStatus.setAlignment(Qt.AlignCenter)
        # -------------------------------------
        top += height + between
        width = 400
        bottom = rcWnd.bottom() - margin
        height = bottom - top
        left = int((rcWnd.width() - width) / 2)
        strStyle = "background:transparent;border: 1px solid red;color:white;font-size:14px;"
        self.editCmpResult = QTextEdit(self.centralwidget)
        self.editCmpResult.setText("")
        self.editCmpResult.setGeometry(left, top, width, height)
        self.editCmpResult.setReadOnly(True)
        self.editCmpResult.setStyleSheet(strStyle)
        # -------------------------------------
        strStyle = "background:transparent;border: 1px solid red;color:white;font-size:14px;"
        left = margin
        width = rcWnd.width() - margin * 2
        top -= 147
        height += 147
        self.tbView = tableview.createTableView(self.centralwidget)
        self.tbView.setGeometry(left, top, width, height)
        self.tbView.setStyleSheet(strStyle)
        # -------------------------------------
        strStyle = "background:transparent;border: 0px;color:white;font-size:14px;"
        width = 80
        height = 30
        left = rcWnd.right() - (width + margin)
        top = 60
        self.radioBtnFile = QRadioButton(self.centralwidget)
        clickable(self.radioBtnFile).connect(self.onSelectFile)
        self.radioBtnFile.setGeometry(left, top, width, height)
        self.radioBtnFile.setStyleSheet(strStyle)
        self.radioBtnFile.setText("File")
        self.radioBtnFile.setChecked(True)

        top += height
        self.radioBtnDir = QRadioButton(self.centralwidget)
        clickable(self.radioBtnDir).connect(self.onSelectDirectory)
        self.radioBtnDir.setGeometry(left, top, width, height)
        self.radioBtnDir.setStyleSheet(strStyle)
        self.radioBtnDir.setText("Directory")
        # -------------------------------------
        self.ShowCtrls()
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        # -------------------------------------

    def ShowCtrls(self, showMode=-1):
        if showMode == -1:#init
            self.btnCompare.setVisible(False)
            self.labelMatchStatus.setVisible(False)
            self.editCmpResult.setVisible(False)
            self.tbView.setVisible(False)
        if showMode == 0:#ready match
            self.btnCompare.setVisible(True)
            self.labelMatchStatus.setVisible(False)
            self.editCmpResult.setVisible(False)
            self.tbView.setVisible(False)
        elif showMode == 1:# hat matched result
            self.btnCompare.setVisible(False)
            if self.isSelectDirectory:
                self.labelMatchStatus.setVisible(False)
                self.editCmpResult.setVisible(False)
                self.tbView.setVisible(True)
            else:
                self.labelMatchStatus.setVisible(True)
                self.editCmpResult.setVisible(True)
                self.tbView.setVisible(False)


    def onSelectFile(self):
        self.isSelectDirectory = False
        self.radioBtnFile.setChecked(True)
        self.radioBtnDir.setChecked(False)
        self.labelImage2Content.setVisible(True)

    def onSelectDirectory(self):
        self.isSelectDirectory = True
        self.radioBtnDir.setChecked(True)
        self.radioBtnFile.setChecked(False)
        self.labelImage2Content.setVisible(False)

    def ImgsToTableview(self, _aryMatchFaces):
        tableview.clearTableView(self.centralwidget)
        print("aryMatchFaces - size", len(_aryMatchFaces))
        for n, matchFace in enumerate(_aryMatchFaces):
            image = QImage(matchFace['new_path'])
            item = preview(n, matchFace['new_path'], image)
            self.centralwidget.model.previews.append(item)
        self.centralwidget.model.layoutChanged.emit()
        self.tbView.resizeRowsToContents()
        self.tbView.resizeColumnsToContents()
    def onCompare(self):
        x = threading.Thread(target=self.CompareThread(), args=(1,), daemon=True)
        x.start()
        x.join()
    def CompareThread(self):
        self.ShowCtrls(-1)

        if os.path.exists(strImgTmpDirPath) == False:
            os.mkdir(strImgTmpDirPath)

        try:
            strImgPath1 = self.imgInfo1['path']
        except:
            return

        if self.isSelectDirectory:
            strImgPath2 = self.strTargetDirPath
        else:
            try:
                strImgPath2 = self.imgInfo2['path']
            except:
                return

        if len(strImgPath1) == 0 or len(strImgPath2) == 0:
            return

        st = time.time()
        subjectInfo = self.imgInfo1
        subjectInfo['faces'] = [subjectInfo['faces'][0]]

        targetPathList = []
        if self.isSelectDirectory:
            files = os.listdir(strImgPath2)
            for file in files:
                targetPathList.append(strImgPath2 + "/" + file)
        else:
            targetPathList.append(strImgPath2)

        aryMatchFaces = []
        for targetPath in targetPathList:
            if os.path.isdir(targetPath):
                continue

            targetInfo = face_cmp.getFacesFromFile(targetPath)
            if targetInfo == None:
                continue

            subjectFaces = subjectInfo['faces'].copy()
            if face_cmp.compareFaces(subjectFaces, targetInfo['faces']) == False:
                continue

            newImage = targetInfo['image'].copy()
            aryBuf = face_cmp.DrawMatchFacesRect(targetPath, newImage, subjectFaces, strImgTmpDirPath, self.isSelectDirectory, targetInfo['ImgWidth'], aryMatchFaces)
            if len(aryBuf) == 0:
                continue

        # aryMatchFaces.sort(key=lambda x: x.get('new_match_score'), reverse=True)
        aryMatchFaces.sort(key=face_cmp.extract_time, reverse=True)

        et = time.time()
        elapsed_time = et - st
        strExecuteTime = 'Execution time: ' + "{:.2f}".format(elapsed_time) + ' s'
        strMsg1 = ""
        strMsg2 = ""
        subjectFace = self.imgInfo1['faces'][0]
        if self.isSelectDirectory == False:
            if len(aryMatchFaces) == 0:
                targetFace = self.imgInfo2['faces'][0]
                strMsg1 = "Subject photo has not matched to target photo"
            else:
                ResetCtrlImage(self.labelImage2, subjectFace['new_path'], False)
                targetFace = subjectFace['new_cmp_info']['new_match_face']
                matchFaceCmp = aryMatchFaces[0]['new_cmp_info']
                strMsg1 = matchFaceCmp['new_match_msg'] + "\n" + \
                         "Confidence Score: " + matchFaceCmp['new_match_score_str'] + "\n" + \
                         matchFaceCmp['new_match_value']
                strMsg2 = strExecuteTime + "\n" + \
                         "Confidence Score: " + str(matchFaceCmp['new_match_score']) + "\n"

            strMsg2 += "Subject Size: (" + str(subjectFace['new_width']) + ", " + str(subjectFace['new_height']) + ")\n"
            strMsg2 += "Target Size: (" + str(targetFace['new_width']) + ", " + str(targetFace['new_height']) + ")\n"
            strMsg2 += "Subject Sex: " + str(subjectFace.sex) + "\n"
            strMsg2 += "Target Sex: " + str(targetFace.sex) + "\n"
            strMsg2 += "Subject Age: " + str(subjectFace.age) + "\n"
            strMsg2 += "Target Age: " + str(targetFace.age) + "\n"
            strMsg2 += "Subject Eye: left-" + str(subjectFace['new_eye'][0]) + " right-" + str(subjectFace['new_eye'][1]) + "\n"
            strMsg2 += "Target Eye: left-" + str(targetFace['new_eye'][0]) + " right-" + str(
                targetFace['new_eye'][1]) + "\n"
            strMsg2 += "Subject Noise: " + str(subjectFace['new_noise']) + "\n"
            strMsg2 += "Target Noise: " + str(targetFace['new_noise']) + "\n"
            strMsg2 += "Subject Mouth: " + str(subjectFace['new_mouth'][0]) + ", " + str(subjectFace['new_mouth'][1]) + "\n"
            strMsg2 += "Target Mouth: " + str(targetFace['new_mouth'][0]) + ", " + str(targetFace['new_mouth'][1]) + "\n"
            strMsg2 += "Target Age: " + str(targetFace.age)

            self.labelMatchStatus.setText(strMsg1)
            self.editCmpResult.setText(strMsg2)
        else:
            self.ImgsToTableview(aryMatchFaces)
        GlobalUtil.removeAllFiles(strImgTmpDirPath)
        self.ShowCtrls(1)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        # MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        # self.btnCompare.setText(_translate("MainWindow", "Push Button"))

    def changelabeltext(self):

        # changing the text of label after button get clicked
        self.labelImage1.setText("You clicked PushButton")

        # Hiding pushbutton from the main window
        # after button get clicked.
        self.btnCompare.hide()

    def ResetImage(self, ctrlImage, ctrlContent, isPath1 = True):
        file, check = QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()",
                                                  "",
                                                  "All Files (*.*);;png Files (*.png);;jpg Files (*.jpg);;jpeg Files (*.jpeg);;bmp Files (*.bmp)")

        if len(file) == 0:
            return

        st = time.time()
        ctrlImage.setText(file)
        ResetCtrlImage(ctrlImage, file, False)
        imgInfo = face_cmp.getFacesFromFile(file)
        if imgInfo is None:
            return

        if isPath1:
            self.imgInfo1 = imgInfo
        else:
            self.imgInfo2 = imgInfo

        et = time.time()
        elapsed_time = et - st
        strContent = 'Execution time: ' + "{:.2f}".format(elapsed_time) + ' s\n' + \
                     "Gender: " + str(imgInfo['faces'][0].sex) + "\n" + \
                     "Age: " + str(imgInfo['faces'][0].age)
        ctrlContent.setText(strContent)
        self.ShowCtrls(0)

    def onShowImage1(self):
        face_cmp.config(_onnxRootPath=strOnnxDirPath)
        self.ResetImage(self.labelImage1, self.labelImage1Content)

    def onShowImage2(self):
        face_cmp.config(_onnxRootPath=strOnnxDirPath)
        if self.isSelectDirectory == False:
            self.ResetImage(self.labelImage2, self.labelImage2Content, False)
        else:
            file = str(QFileDialog.getExistingDirectory(self.centralwidget, "Select Directory"))
            self.labelImage2.setText(file)
            self.strTargetDirPath = file
            self.ShowCtrls(0)

def main():
    IdxDatManage.LoadIdxFile()
    QApplication.setApplicationName('Face Compare')
    app = QApplication(sys.argv)
    app.setStyleSheet("QPushButton{font-size: 14pt;color:white;border:1px solid red;background:transparent;}")
    MainWindow = QMainWindow()
    MainWindow.setMaximumSize(WIN_W, WIN_H)
    MainWindow.setMinimumSize(WIN_W, WIN_H)
    bImgData = IdxDatManage.getImgData('logo.jpg')
    pixmap = QPixmap()
    pixmap.loadFromData(bImgData)
    icon = QIcon(pixmap)
    app.setWindowIcon(QIcon(icon))
    MainWindow.setWindowIcon(QIcon(icon))
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
