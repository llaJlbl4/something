import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFrame
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap

PIECE_SIZE = 100
GRID_SIZE = 2
SNAP_DISTANCE = 30


class DraggableLabel(QLabel):
    def __init__(self, name, image_path, parent=None):
        super().__init__(parent)
        self.name = name
        self.setPixmap(QPixmap(image_path).scaled(PIECE_SIZE, PIECE_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.setFixedSize(PIECE_SIZE, PIECE_SIZE)
        self.setStyleSheet("border: 1px solid gray; background: white;")
        self.setAlignment(Qt.AlignCenter)
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self.parent().snap_to_grid(self)
        self.parent().check_position()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Собери картинку!")
        self.setGeometry(300, 200, 800, 500)
        self.setStyleSheet("background-color: #f0f0f0;")

        self.area_size = PIECE_SIZE * GRID_SIZE
        self.play_area = QFrame(self)
        self.play_area.setGeometry(400, 100, self.area_size, self.area_size)
        self.play_area.setStyleSheet("background-color: white; border: 3px dashed #888;")

        self.labels = {
            "piece1": DraggableLabel("piece1", "1.png", self),
            "piece2": DraggableLabel("piece2", "2.png", self),
            "piece3": DraggableLabel("piece3", "3.png", self),
            "piece4": DraggableLabel("piece4", "4.png", self)
        }

        self.target_positions = {
            "piece1": (0, 0),
            "piece2": (PIECE_SIZE, 0),
            "piece3": (0, PIECE_SIZE),
            "piece4": (PIECE_SIZE, PIECE_SIZE),
        }

        for label in self.labels.values():
            x = random.randint(50, 250)
            y = random.randint(50, 350)
            label.move(x, y)

    def snap_to_grid(self, label: DraggableLabel):
        target_x, target_y = self.target_positions[label.name]
        target_x += self.play_area.x()
        target_y += self.play_area.y()
        if abs(label.x() - target_x) < SNAP_DISTANCE and abs(label.y() - target_y) < SNAP_DISTANCE:
            label.move(target_x, target_y)

    def check_position(self):
        correct = True
        for name, (target_x, target_y) in self.target_positions.items():
            label = self.labels[name]
            target_x += self.play_area.x()
            target_y += self.play_area.y()
            if label.x() != target_x or label.y() != target_y:
                correct = False
                break
        if correct:
            print("🎉 Картинка собрана правильно!")
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
