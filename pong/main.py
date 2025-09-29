from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel,QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QFrame)
from PyQt5.QtGui import (QFont, QPixmap)
from PyQt5.QtCore import (Qt, QTimer, QPoint)
import sys
import sqlite3
import hashlib
import random

DB_PATH = "pong/users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def create_user(conn, username, password) -> bool:
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def verify_user(conn, username, password) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row and row[0] == hash_password(password):
        return True
    return False


class DraggableLabel(QLabel):
    def __init__(self, name, image_path, parent=None):
        super().__init__(parent)
        self.name = name
        self.setPixmap(QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.setFixedSize(100, 100)
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


class CaptchaWindow(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.setWindowTitle("Собери картинку!")
        self.setGeometry(300, 200, 800, 500)
        self.setStyleSheet("background-color: #f0f0f0;")

        self.callback = callback
        self.area_size = 200
        self.play_area = QFrame(self)
        self.play_area.setGeometry(400, 100, self.area_size, self.area_size)
        self.play_area.setStyleSheet("background-color: white; border: 3px dashed #888;")

        self.labels = {
            "piece1": DraggableLabel("piece1", "pong/captcha/1.png", self),
            "piece2": DraggableLabel("piece2", "pong/captcha/2.png", self),
            "piece3": DraggableLabel("piece3", "pong/captcha/3.png", self),
            "piece4": DraggableLabel("piece4", "pong/captcha/4.png", self)
        }

        self.target_positions = {
            "piece1": (0, 0),
            "piece2": (100, 0),
            "piece3": (0, 100),
            "piece4": (100, 100),
        }

        for label in self.labels.values():
            x = random.randint(50, 250)
            y = random.randint(50, 350)
            label.move(x, y)

    def snap_to_grid(self, label: DraggableLabel):
        target_x, target_y = self.target_positions[label.name]
        target_x += self.play_area.x()
        target_y += self.play_area.y()
        if abs(label.x() - target_x) < 30 and abs(label.y() - target_y) < 30:
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
            QMessageBox.information(self, "Успех", "Картинка собрана правильно!")
            self.close()
            self.callback()


class AuthWindow(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Авторизация / Регистрация")
        self.setGeometry(600, 300, 300, 150)

        layout = QVBoxLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Имя пользователя")
        layout.addWidget(self.username_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_edit)

        self.login_btn = QPushButton("Войти")
        self.register_btn = QPushButton("Зарегистрироваться")
        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)
        self.setLayout(layout)

        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.register)

    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if verify_user(self.conn, username, password):
            self.main = MainWindow()
            self.main.show()
            self.main.setGeometry(0, 50, 1900, 950)
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.\nПройдите капчу!")
            self.captcha = CaptchaWindow(self.enable_login)
            self.captcha.show()
            self.login_btn.setEnabled(False)

    def enable_login(self):
        self.login_btn.setEnabled(True)

    def register(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if create_user(self.conn, username, password):
            QMessageBox.information(self, "Успех", "Пользователь зарегистрирован")
        else:
            QMessageBox.warning(self, "Ошибка", "Такой пользователь уже существует")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dx = -30
        self.dy = -10
        self.game_started = False

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

        self.first_score = QLabel(widget)
        self.first_score.setText("0")
        self.first_score.setStyleSheet("color: white")
        self.first_score.setFont(QFont("Times", 100))
        self.first_score.setGeometry(700, 50, 150, 150)

        self.second_score = QLabel(widget)
        self.second_score.setText("0")
        self.second_score.setStyleSheet("color: white")
        self.second_score.setFont(QFont("Times", 100))
        self.second_score.setGeometry(1100, 50, 150, 150)

        self.first_player = QLabel(widget)
        self.first_player.setStyleSheet("background-color: white")
        self.first_player.setGeometry(5, 400, 21, 150)

        self.second_player = QLabel(widget)
        self.second_player.setStyleSheet("background-color: white")
        self.second_player.setGeometry(1880, 400, 21, 150)

        self.ball = QLabel(widget)
        self.ball.setStyleSheet("background-color: white")
        self.ball.setGeometry(945, 470, 10, 10)

        self.start_label = QLabel("Нажмите ПРОБЕЛ, чтобы начать", widget)
        self.start_label.setStyleSheet("color: yellow")
        self.start_label.setFont(QFont("Times", 40))
        self.start_label.setGeometry(550, 400, 800, 100)
        self.start_label.setAlignment(Qt.AlignCenter)

        self.pressed_keys = set()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_positions)
        self.timer.timeout.connect(self.move_ball)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not self.game_started:
            self.start_game()
        else:
            self.pressed_keys.add(event.key())

    def keyReleaseEvent(self, event):
        if event.key() in self.pressed_keys:
            self.pressed_keys.remove(event.key())

    def start_game(self):
        self.game_started = True
        self.start_label.hide()
        self.timer.start(30)

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
        fs = self.first_score.text()
        ss = self.second_score.text()

        bx += self.dx
        by += self.dy

        if by <= 0 or by >= 940:
            self.dy = -self.dy

        if fx < bx < fx + 21 and fy < by < fy + 150:
            self.dx = -self.dx

        if sx - 21 < bx < sx and sy < by < sy + 150:
            self.dx = -self.dx

        if bx <= 0:
            self.second_score.setText(f"{int(ss)+1}")
            self.ball.move(945, 470)
        elif bx >= 1900:
            self.first_score.setText(f"{int(fs)+1}")
            self.ball.move(945, 470)
        else:
            self.ball.move(bx, by)

        if int(self.first_score.text()) >= 10 or int(self.second_score.text()) >= 10:
            self.timer.stop()
            winner = "Первый игрок" if int(self.first_score.text()) >= 10 else "Второй игрок"
            QMessageBox.information(self, "Матч завершён", f"{winner} победил!")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    conn = init_db()
    auth = AuthWindow(conn)
    auth.show()
    app.exec()
