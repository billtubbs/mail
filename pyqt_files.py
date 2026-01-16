import sys
from PyQt6.QtWidgets import (
    QLabel,
    QApplication,
    QWidget,
    QPlainTextEdit,
    QFileDialog,
    QVBoxLayout,
)
from PyQt6.QtCore import *


class App(QWidget):
    def __init__(
        self,
        title="PyQt6 app with file dialogs",
        width=640,
        height=480,
        use_native=True,
    ):
        super().__init__()
        self.title = title
        self.left = 10
        self.top = 10
        self.width = width
        self.height = height
        self.use_native = use_native

        self.label = QLabel()

        self.label.setFixedWidth(420)
        self.label.move(20, 200)
        # self.label.setAlignment(Qt.AlignCenter)
        self.label.setText("")

        self.textbox = QPlainTextEdit(self)
        self.textbox.setReadOnly(True)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.textbox, stretch=1)
        self.setLayout(self.vbox)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

    def get_options(self):
        options = QFileDialog.Option(0)
        if self.use_native is not True:
            options |= QFileDialog.Option.DontUseNativeDialog

        return options

    def show_message(self, message):
        self.label.setText(message)

    def show_text(self, text):
        self.textbox.setPlainText(str(text))

    def selectFolderNameDialog(self, directory=""):
        folderName = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            directory=directory,
            options=self.get_options(),
        )
        return folderName

    def openFileNameDialog(
        self, directory="", filter="All Files (*);;Text Files (*.txt)"
    ):
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            directory=directory,
            filter=filter,
            options=self.get_options(),
        )
        return fileName

    def openFileNamesDialog(
        self, directory="", filter="All Files (*);;Text Files (*.txt)"
    ):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Files",
            directory=directory,
            filter=filter,
            options=self.get_options(),
        )
        return files

    def saveFileDialog(
        self, directory="", filter="All Files (*);;Text Files (*.txt)"
    ):
        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            directory=directory,
            filter=filter,
            options=self.get_options(),
        )
        return fileName


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("macos")
    ex = App()

    # Demonstrate methods
    print(ex.openFileNameDialog())
    print(ex.selectFolderNameDialog())
    ex.show_message("Hello World!")
    print(ex.openFileNamesDialog())
    print(ex.saveFileDialog())
    ex.show()

    sys.exit(app.exec())
