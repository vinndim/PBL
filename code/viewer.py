from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt


class Viewer(QtWidgets.QGraphicsView):
    clicked = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(QtWidgets.QGraphicsScene(), parent)
        self.pixmap_item = self.scene().addPixmap(QtGui.QPixmap())
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setBackgroundRole(QtGui.QPalette.Dark)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.rubberBandChanged.connect(self.on_rubber_band_changed)
        self.last_rect = QtCore.QPointF()
        self.setWindowTitle("Обрезание изображения")
        self.setCursor(QCursor(QtCore.Qt.CrossCursor))

    # функция получения изображения и его размера
    def set_pixmap(self, pixmap, size):
        self.pixmap_item.setPixmap(pixmap)
        self.resize(size)
        print(pixmap.size())
        self.setFixedSize(size)

    # функция обрезания изображения
    @QtCore.pyqtSlot(QtCore.QRect, QtCore.QPointF, QtCore.QPointF)
    def on_rubber_band_changed(self, rubberBandRect, fromScenePoint, toScenePoint):
        if rubberBandRect.isNull():
            pixmap = self.pixmap_item.pixmap()
            rect = self.pixmap_item.mapFromScene(self.last_rect).boundingRect().toRect()
            if not rect.intersected(pixmap.rect()).isNull():
                crop_pixmap = pixmap.copy(rect)
                self.send_im(crop_pixmap)
            self.last_rect = QtCore.QRectF()
            self.close()
        else:
            self.last_rect = QtCore.QRectF(fromScenePoint, toScenePoint)

    # функция передачи обрезанного изображения
    def send_im(self, crop_pixmap):
        self.clicked.emit(crop_pixmap)
