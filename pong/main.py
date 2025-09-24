from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel)
import sys
from PyQt5.QtCore import (Qt, QTimer)




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dx = -14
        self.dy = -3

        widget = QWidget()
        self.setCentralWidget(widget)

        lbl = QLabel(widget)
        lbl.setStyleSheet("background-color: black")
        lbl.setGeometry(0, 0, 1900, 950)

        lbl_up = QLabel(widget)
        lbl_up.setStyleSheet("background-color: white")
        lbl_up.setGeometry(0, 0, 1900, 3)

        lbl_down = QLabel(widget)
        lbl_down.setStyleSheet("background-color: white")
        lbl_down.setGeometry(0, 947, 1900, 3)

        self.first_player = QLabel(widget)
        self.first_player.setStyleSheet("background-color: white")
        self.first_player.setGeometry(5, 400, 15, 150)

        self.second_player = QLabel(widget)
        self.second_player.setStyleSheet("background-color: white")
        self.second_player.setGeometry(1880, 400, 15, 150)

        self.ball = QLabel(widget)
        self.ball.setStyleSheet("background-color: white")
        self.ball.setGeometry(945, 470, 10, 10)

        self.pressed_keys = set()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_positions)
        self.timer.timeout.connect(self.move_ball)
        self.timer.start(30)

    def keyPressEvent(self, event):
        self.pressed_keys.add(event.key())

    def keyReleaseEvent(self, event):
        if event.key() in self.pressed_keys:
            self.pressed_keys.remove(event.key())
        
    def update_positions(self):
        fy = self.first_player.y()
        sy = self.second_player.y()

        if Qt.Key_W in self.pressed_keys:
            if fy > 0:
                self.first_player.move(5, fy-15)
        if Qt.Key_S in self.pressed_keys:
            if fy < 800:
                self.first_player.move(5, fy+15)
        if Qt.Key_Up in self.pressed_keys:
            if sy > 0:
                self.second_player.move(1880, sy-15)
        if Qt.Key_Down in self.pressed_keys:
            if sy < 800:
                self.second_player.move(1880, sy+15)
    
    def move_ball(self):
        bx, by = self.ball.x(), self.ball.y()
        fx, fy = self.first_player.x(), self.first_player.y()
        sx, sy = self.second_player.x(), self.second_player.y()

        bx += self.dx
        by += self.dy

        if by <= 0 or by >= 940:
            self.dy = -self.dy

        if fx < bx < fx + 15 and fy < by < fy + 150:
            self.dx = -self.dx

        if sx - 15 < bx < sx and sy < by < sy + 150:
            self.dx = -self.dx

        self.ball.move(bx, by)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(0, 0, 1900, 950)
    window.show()
    app.exec()