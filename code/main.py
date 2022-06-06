"""QT5 application for recognizing text from an image using tesseract"""
import os
import sys
import uuid
from urllib.error import HTTPError

import cv2
import pytesseract
import sqlite3

from PyQt5 import QtGui
from PyQt5 import uic
from querys import MAKE_DB, LOAD_SAVES, DB_NAME, DELETE_IM, GET_IMAGE, GET_NOTE, GET_SAVES
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QAbstractItemView, QMenu, QAction
from qt_material import apply_stylesheet
from translater import translate

from viewer import Viewer


class TextScan(QMainWindow):
    # сигнал для получения изображения из окна для обрезания
    clicked = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        uic.loadUi('resources/pixels_begin_letters.ui', self)

        # работа с listWidget
        self.listWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.listWidget.itemClicked.connect(self.item_clicked)
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.contextMenuEvent)
        self.listWidget.itemDoubleClicked.connect(self.save_to_scan)

        # изменение языка перевода
        self.tr_eng.triggered.connect(lambda: self.tr_text('ru'))
        self.tr_rus.triggered.connect(lambda: self.tr_text('en'))

        # изменение языка сканирования
        self.language = 'rus+eng'
        self.rus_eng.triggered.connect(lambda: self.change_language('rus+eng'))
        self.rus.triggered.connect(lambda: self.change_language('rus'))
        self.eng.triggered.connect(lambda: self.change_language('eng'))

        # работа с изображением
        self.load.triggered.connect(self.load_image)
        self.right_90.triggered.connect(self.rotate_right)  # поворот изображения направо
        self.left_90.triggered.connect(self.rotate_left)  # поворот изображения налево

        # окно обрезания картинки
        self.act_resize.triggered.connect(self.show_dialog)
        self.view = Viewer()
        self.view.clicked[QPixmap].connect(self.show_image)

        self.plainTextEdit.textChanged.connect(self.ch_copy_btn)

        # работа с буфером
        self.paste.triggered.connect(self.get_buf_image)
        self.setAcceptDrops(True)  # позволяет элементу управления получать события Drop;
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(lambda: print('Data Changed'))
        self.scanbutton.clicked.connect(self.show_text)
        self.lineEdit.textChanged.connect(self.ch_save_btn)
        self.copy_text_btn.clicked.connect(self.copy_text_func)
        self.save_btn.clicked.connect(self.save_data)
        # получение директории программы
        self.dir = os.getcwd()
        # работа с базой данных
        if not os.path.isdir(os.path.join(self.dir, 'db')):
            os.mkdir(os.path.join(self.dir, 'db'))
        self.con = sqlite3.connect(DB_NAME)
        self.cur = self.con.cursor()
        self.cur.execute(MAKE_DB)
        data = self.cur.execute(LOAD_SAVES).fetchall()
        # загрузка сохранений
        self.saves = []
        self.hash_im = []
        for d in data:
            self.saves.append(d[0])
            self.hash_im.append(d[1])
        self.listWidget.addItems(self.saves)

        # переменные
        self.loaded_image = None
        self.filename = None
        self.text = None
        self.loaded_image = None
        self.pr_sc = None
        self.click_flag = None
        self.label_have_im = False

    # функция показа окна для обрезания изображения
    def show_dialog(self):
        try:
            self.view.set_pixmap(QPixmap(self.loaded_image), self.loaded_image.size())
            self.view.show()
        except AttributeError:
            pass

    # определение нажатия на строку в listWidget
    def item_clicked(self):
        self.click_flag = True

    # функция изменения языка сканирования
    def change_language(self, lang='rus+eng'):
        self.language = lang
        self.scanbutton.setText(f"Сканировать ({lang})")

    # функция удаления сохранений
    def delete_data(self):
        hash_im = self.hash_im[self.listWidget.currentRow()]
        self.cur.execute(DELETE_IM, {"hashIm": hash_im})
        self.listWidget.takeItem(self.listWidget.currentRow())
        path = os.path.join(self.dir, '../saves', str(hash_im) + '.png')
        os.remove(path)
        self.saves = [save[0] for save in
                      self.cur.execute('''SELECT note FROM preservation''').fetchall()]
        self.hash_im = [save[0] for save in
                        self.cur.execute('''SELECT hashIm FROM preservation''').fetchall()]
        self.con.commit()

    # функция получения изображения из буфера
    def get_buf_image(self):
        try:
            # изображение скопированно из папки
            path = self.clipboard.mimeData().urls()[0].toLocalFile()
            self.loaded_image = QPixmap(path)
            self.clear_tab()
            self.show_image(QPixmap(self.loaded_image))
            self.filename = path
        except IndexError:
            if not os.path.isdir("cashe"):
                os.mkdir("cashe")
            # изображение скопированно созданием screenshot
            self.loaded_image = self.clipboard.image()
            self.pr_sc = os.path.join(self.dir, 'cashe', 'pr_sc.png')
            self.filename = self.pr_sc
            self.clear_tab()
            self.loaded_image.save(self.filename)
            self.show_image(QPixmap(self.loaded_image))

    # Когда цель перетаскивания входит в label, инициируется событие dragEnterEvent
    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    # Когда цель двигеатся в label, инициируется событие dragMoveEvent
    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            # self.label.setText('Поместите изображение в эту область')
            self.label.setStyleSheet('''QLabel{border: 2px dashed #1E90FF}''')
            event.accept()
        else:
            event.ignore()

    # Когда цель покаидает label, инициируется событие dragMoveEvent
    def dragLeaveEvent(self, event):
        print('Drag Leave')
        self.label.setStyleSheet('''QLabel{border: 2px solid #1E90FF}''')
        self.label.setText('')
        event.accept()

    # Когда цель отпускается в label, инициируется событие dropEvent
    def dropEvent(self, event):
        if event.mimeData().hasImage:
            self.label.setStyleSheet('''QLabel{border: 2px solid #1E90FF}''')
            event.setDropAction(Qt.CopyAction)
            self.filename = event.mimeData().urls()[0].toLocalFile()
            print(self.filename)
            self.loaded_image = QPixmap(self.filename)
            self.clear_tab()
            self.show_image(QPixmap(self.loaded_image))
            event.accept()
        else:
            event.ignore()

    # загрузка изображения, текста и записки при двойном нажатии на сохранение в listWidget
    def save_to_scan(self):
        self.tabWidget.setCurrentWidget(self.tab)
        note = self.listWidget.currentItem().text()
        row_num = self.listWidget.currentRow()
        hash_im = 0
        for i in range(len(self.hash_im)):
            if i == row_num:
                hash_im = self.hash_im[i]
                print(hash_im)
                break
        image = self.cur.execute(GET_IMAGE,
                                 {"hashIm": hash_im}).fetchall()[0][0]
        text = self.cur.execute(GET_NOTE, {"note": note}).fetchall()[0][0]
        self.label_have_im = True
        self.lineEdit.setText(note)
        self.loaded_image = QPixmap(image)
        self.plainTextEdit.setPlainText(text)
        self.show_image(QPixmap(self.loaded_image))
        self.con.commit()

    # функция перевода текста
    def tr_text(self, lang):
        print(lang)
        rem_n = self.plainTextEdit.toPlainText()
        self.plainTextEdit.setPlainText(translate(rem_n,
                                                  f"{'ru' if lang == 'en' else 'en'}|{lang}"))

    # возвращение кнопки в исходный вид при изменении lineEdit
    def ch_save_btn(self):
        self.save_btn.setStyleSheet('')
        self.save_btn.setEnabled(True)
        self.save_btn.setText('Сохранить')

    # возвращение кнопки в исходный вид при изменении plainTextEdit
    def ch_copy_btn(self):
        self.copy_text_btn.setText('Скопировать')
        self.copy_text_btn.setEnabled(True)
        self.copy_text_btn.setStyleSheet("")

    # Функция сохранения текста, пути и записок в базу данных
    def save_data(self):
        if self.label_have_im and self.lineEdit.text() and self.plainTextEdit.toPlainText():
            if not os.path.isdir("../saves"):
                os.mkdir("../saves")
            self.save_btn.setEnabled(False)
            self.save_btn.setText("Сохранено")
            self.save_btn.setStyleSheet("color: #00FF7F;")

            note = self.lineEdit.text()
            self.listWidget.addItem(note)
            hash_im = str(uuid.uuid4())
            text = self.plainTextEdit.toPlainText()
            path = os.path.join(self.dir, '../saves', str(hash_im) + '.png')  # путь к изображению
            self.label.pixmap().save(path)  # сохранение изображения в папку Saves
            self.cur.execute(GET_SAVES,
                             [path, text, note, hash_im])  # передача пути изображения
            self.saves.append(note)
            self.hash_im.append(hash_im)
            self.con.commit()

    # Функция копирования текста из plainTextEdit
    def copy_text_func(self):
        self.clipboard.setText(self.plainTextEdit.toPlainText())
        # изменение кнопки после копирования
        self.copy_text_btn.setText('Скопировано')
        self.copy_text_btn.setStyleSheet("color: #00FF7F;")
        self.copy_text_btn.setEnabled(False)

    # Функция "сканирования" изображения и вывода текста с изображения
    def show_text(self):
        # относителный путь до tesseract.exe
        print(os.path.join(self.dir, 'resources', 'tesseract5.1', 'tesseract.exe'))
        pytesseract.pytesseract.tesseract_cmd = os.path.join(self.dir, 'resources', 'tesseract5.1', 'tesseract.exe')
        try:
            self.loaded_image.save(os.path.join(self.dir, 'cashe', 'im_with_text.png'))
            img = cv2.imread(os.path.join(self.dir, 'cashe', 'im_with_text.png'))
            self.text = pytesseract.image_to_string(img, lang=self.language)
            self.plainTextEdit.setStyleSheet('')
            self.plainTextEdit.setPlainText(self.text)
        except TypeError:
            print("TypeError")
            self.plainTextEdit.setStyleSheet('border: 2px solid #DC143C')
        except AttributeError:
            print("AttributeError")
            self.plainTextEdit.setStyleSheet('border: 2px solid #DC143C')

    # изменение угла на +90 градусов
    def rotate_right(self):
        try:
            t = QTransform().rotate(90)
            self.show_image(QPixmap(self.loaded_image.transformed(t)))
        except AttributeError:
            pass

    # изменение угла на -90 градусов
    def rotate_left(self):
        try:
            t = QTransform().rotate(-90)
            self.show_image(QPixmap(self.loaded_image.transformed(t)))
        except AttributeError:
            pass

    # Показ изображения
    def show_image(self, pixmap):
        try:
            self.loaded_image = pixmap
            self.label.setPixmap(self.loaded_image)
            self.label_have_im = True
            self.label.setScaledContents(True)  # Растягивание изображения
        except AttributeError:
            pass

    # Загрузка изображения через диалог
    def load_image(self):
        try:
            self.filename = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '', '*.jpg *.png *.gif *.bmp')[0]
            self.loaded_image = QPixmap(self.filename)
            if self.filename:
                self.clear_tab()
                self.show_image(QPixmap(self.loaded_image))
                self.label.setStyleSheet('''QLabel{border: 2px solid #1E90FF;}''')
        except AttributeError:
            pass

    # очищение первой облости при загрузке нового изображения
    def clear_tab(self):
        self.label_have_im = False
        self.lineEdit.clear()
        self.plainTextEdit.clear()
        self.label.clear()

    # перехват событий нажатий клавиш
    def keyPressEvent(self, event):
        if int(event.modifiers()) == Qt.ControlModifier:
            if event.key() == Qt.Key_R:
                self.change_language('rus')
            if event.key() == Qt.Key_E:
                self.change_language('eng')
            if event.key() == Qt.Key_D:
                self.change_language('rus+eng')
            if event.key() == Qt.Key_V:
                self.get_buf_image()
        if self.click_flag:
            if event.key() == Qt.Key_Delete:
                self.delete_data()
                self.click_flag = False
            if int(event.modifiers()) == Qt.ControlModifier:
                if event.key() == Qt.Key_T:
                    self.save_to_scan()

    # фунция отображения контекстного меню
    def contextMenuEvent(self, position):
        try:
            if self.listWidget.itemAt(position):
                menu = QMenu()
                follow = QAction("Перейти", self)
                delete = QAction("Удалить     Delete", self)
                menu.addAction(follow)
                menu.addAction(delete)
                follow.triggered.connect(self.save_to_scan)
                delete.triggered.connect(self.delete_data)
                menu.exec(self.listWidget.mapToGlobal(position))
            else:
                pass
        except TypeError:
            pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('resources/icon.ico'))
    demo = TextScan()
    apply_stylesheet(app, theme='dark_blue.xml')
    demo.show()
    sys.exit(app.exec_())
