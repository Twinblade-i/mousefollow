import os
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from pynput import keyboard


def is_int(char):
    try:
        x = int(char)
        return True
    except ValueError:
        return False


class Mover(QtCore.QThread):
    signal = QtCore.pyqtSignal("PyQt_PyObject")

    def run(self):
        while True:
            self.signal.emit("")
            time.sleep(0.0333)


class RedDot(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.scale_factor = 1.7
        self.initUI()

    def initUI(self):
        for child in self.findChildren(QtWidgets.QLabel):
            child.deleteLater()
        label = QtWidgets.QLabel(self)
        if os.path.isfile("pointer.png"):
            pixmap = QtGui.QPixmap("pointer.png")
        else:
            ba = QtCore.QByteArray.fromBase64(dot_data)
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(ba, "PNG")
        pixmap = pixmap.scaled(
            int(pixmap.width() * self.scale_factor),
            int(pixmap.height() * self.scale_factor),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )
        label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.setMinimumSize(pixmap.width(), pixmap.height())
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def set_scale_factor(self, factor):
        was_visible = self.isVisible()
        self.scale_factor = factor
        self.initUI()
        if was_visible:
            self.show()


class DrawBox(QtWidgets.QWidget):
    mouseup = QtCore.pyqtSignal("PyQt_PyObject")

    def __init__(self):
        super().__init__()
        self.initUI()
        self.setMouseTracking(True)

    def initUI(self):
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.6)

        self.mouse_down_loc = [0, 0]
        self.mouse_up_loc = [0, 0]
        self.mouse_loc = [0, 0]
        self.dragging = False

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
            if hasattr(self.parent(), "drawbox_visible"):
                self.parent().drawbox_visible = False

    def mousePressEvent(self, event):
        self.mouse_down_loc = [event.pos().x(), event.pos().y()]
        self.dragging = True
        self.update()

    def mouseReleaseEvent(self, event):
        self.mouse_up_loc = [event.pos().x(), event.pos().y()]
        self.dragging = False
        self.update()
        self.mouseup.emit("")
        self.hide()

    def mouseMoveEvent(self, event):
        self.mouse_loc = [event.pos().x(), event.pos().y()]
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QColor(255, 0, 0))

        if self.dragging:
            x = self.mouse_loc[0]
            y = self.mouse_loc[1]
        else:
            x = self.mouse_up_loc[0]
            y = self.mouse_up_loc[1]

        ox = self.mouse_down_loc[0]
        oy = self.mouse_down_loc[1]

        painter.drawLine(ox, oy, x, oy)
        painter.drawLine(ox, y, x, y)
        painter.drawLine(ox, oy, ox, y)
        painter.drawLine(x, y, x, oy)


class Master(QtWidgets.QDialog):
    def __init__(self, parent=None):
        self.config_dir = (
            os.path.join(  # new directory: ~/.config/mousefollow/settings.ini
                os.path.expanduser("~"), ".config", "mousefollow"
            )
        )
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, "settings.ini")

        super(Master, self).__init__(parent)
        self.screens = app.screens()
        self.drawbox_visible = False
        self.tray_icon = None
        self.setupUI()
        self.init_tray_icon()

        self.laser_visible = False  # laser visible status
        self.alt_r_pressed = False
        self.alt_f9_pressed = False
        self.esc_pressed = False

        self.listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        )
        self.listener.start()

        self.key_timer = QtCore.QTimer(self)
        self.key_timer.timeout.connect(self.handle_key_events)
        self.key_timer.start(30)

    def save_ini(self):
        vals = [
            "target_monitor: " + str(self.target_monitor),
            "preview_left: " + str(self.preview_left),
            "preview_right: " + str(self.preview_right),
            "preview_top: " + str(self.preview_top),
            "preview_bottom: " + str(self.preview_bottom),
            "dot_scale: " + str(self.size_spin.value()),
        ]
        with open(self.config_path, "w") as f:
            f.write("\n".join(vals))

    def load_ini(self):
        try:
            with open(self.config_path, "r") as f:
                text = f.read()
            lines = text.split("\n")
            self.settings = {}
            for line in lines:
                key = line.split(":")[0]
                val = line.split(":")[-1].strip()
                self.settings[key] = val

        except FileNotFoundError:
            self.settings = {
                "target_monitor": self.screens[0].name(),
                "preview_left": "60",
                "preview_right": "1258",
                "preview_top": "149",
                "preview_bottom": "823",
                "dot_scale": "1.7",
            }

            if len(self.screens) > 1:
                self.settings["target_monitor"] = self.screens[1].name()

        self.target_monitor = self.settings["target_monitor"]
        self.preview_left = int(self.settings["preview_left"])
        self.preview_right = int(self.settings["preview_right"])
        self.preview_top = int(self.settings["preview_top"])
        self.preview_bottom = int(self.settings["preview_bottom"])
        self.dot_scale = float(self.settings.get("dot_scale", 1.7))

    def setupUI(self):
        self.load_ini()

        ba = QtCore.QByteArray.fromBase64(dot_data)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(ba, "PNG")

        icon = QtGui.QIcon()
        icon.addPixmap(pixmap)

        self.setWindowIcon(icon)
        self.setWindowTitle("MouseFollow")
        self.setWindowFlags(
            QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        self.v_layout = QtWidgets.QVBoxLayout(self)

        self.screen_layout = QtWidgets.QHBoxLayout()

        self.target_monitor_label = QtWidgets.QLabel("Target Monitor:")
        self.target_monitor_cb = QtWidgets.QComboBox()

        for i in range(len(self.screens)):
            self.target_monitor_cb.addItem(self.screens[i].name())
            if self.screens[i].name() == self.target_monitor:
                self.target_monitor_cb.setCurrentIndex(i)

        self.target_monitor_cb.currentIndexChanged.connect(self.set_target_monitor)

        self.screen_layout.addWidget(self.target_monitor_label)
        self.screen_layout.addWidget(self.target_monitor_cb)
        self.v_layout.addLayout(self.screen_layout)

        # adjusting laser spot size
        self.size_layout = QtWidgets.QHBoxLayout()
        self.size_label = QtWidgets.QLabel("Laser Size:")
        self.size_spin = QtWidgets.QDoubleSpinBox()
        self.size_spin.setRange(0.5, 5.0)
        self.size_spin.setSingleStep(0.1)
        self.size_spin.setValue(self.dot_scale)
        self.size_spin.valueChanged.connect(self.change_dot_size)
        self.size_layout.addWidget(self.size_label)
        self.size_layout.addWidget(self.size_spin)
        self.v_layout.addLayout(self.size_layout)

        self.draw_label = QtWidgets.QLabel("Draw: F9")
        self.v_layout.addWidget(self.draw_label)

        self.laser_label = QtWidgets.QLabel("Laser: Right Alt")
        self.v_layout.addWidget(self.laser_label)

        self.red_dot = RedDot()
        self.red_dot.set_scale_factor(self.dot_scale)
        self.draw_box = DrawBox()
        self.draw_box.mouseup.connect(self.save_preview_pos)

        self.thread = Mover()
        self.thread.signal.connect(self.move_dot)
        self.thread.start()

        # an Exit Button
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        self.exit_btn = QtWidgets.QPushButton("Exit")
        self.exit_btn.clicked.connect(QtWidgets.qApp.quit)
        self.button_layout.addWidget(self.exit_btn)
        self.v_layout.addLayout(self.button_layout)

        self.resize(300, 130)
        self.show()

    def change_dot_size(self, value):
        # first simulate closing, then adjust and simulate opening again
        was_visible = self.laser_visible
        if was_visible:
            self.laser_visible = False
            self.handle_key_events()
        self.red_dot.set_scale_factor(value)
        if was_visible:
            self.laser_visible = True
            self.handle_key_events()
        self.save_ini()

    def set_target_monitor(self):
        self.target_monitor = self.target_monitor_cb.currentText()
        self.save_ini()

    def save_preview_pos(self):
        drawbox_geometry = self.draw_box.geometry()

        self.preview_left = drawbox_geometry.left() + self.draw_box.mouse_down_loc[0]
        self.preview_top = drawbox_geometry.top() + self.draw_box.mouse_down_loc[1]
        self.preview_right = drawbox_geometry.left() + self.draw_box.mouse_up_loc[0]
        self.preview_bottom = drawbox_geometry.top() + self.draw_box.mouse_up_loc[1]

        if self.preview_left > self.preview_right:
            self.preview_right, self.preview_left = (
                self.preview_left,
                self.preview_right,
            )
        if self.preview_top > self.preview_bottom:
            self.preview_top, self.preview_bottom = (
                self.preview_bottom,
                self.preview_top,
            )

        self.save_ini()

    def move_dot(self):
        if self.red_dot.isVisible():
            laser_width = self.red_dot.frameGeometry().width()
            laser_height = self.red_dot.frameGeometry().height()

            pos = QtGui.QCursor().pos()
            x = pos.x()
            y = pos.y()

            width = self.preview_right - self.preview_left
            height = self.preview_bottom - self.preview_top

            if width == 0:
                self.preview_left = 0
                self.preview_right = 1920
                width = self.preview_right - self.preview_left

            if height == 0:
                self.preview_top = 0
                self.preview_bottom = 1080
                height = self.preview_bottom - self.preview_top

            x_fac = (x - self.preview_left) / width
            y_fac = (y - self.preview_top) / height

            for screen in self.screens:
                if screen.name() == self.target_monitor_cb.currentText():
                    target_screen = screen
                    break

            geometry = target_screen.geometry()
            new_x = geometry.left() + (geometry.width() * x_fac) - (laser_width / 2)
            new_y = geometry.top() + (geometry.height() * y_fac) - (laser_height / 2)

            if new_x < geometry.left():
                new_x = geometry.left()
            elif new_x > geometry.left() + geometry.width() - laser_width:
                new_x = geometry.left() + geometry.width() - laser_width

            if new_y < geometry.top():
                new_y = geometry.top()
            elif new_y > geometry.top() + geometry.height() - laser_width:
                new_y = geometry.top() + geometry.height() - laser_width

            self.red_dot.move(int(new_x), int(new_y))

    def on_press(self, key):
        try:
            if key == keyboard.Key.alt_r:  # origin: Alt_l
                if not self.alt_r_pressed:
                    self.laser_visible = not self.laser_visible
                self.alt_r_pressed = True
            elif key == keyboard.Key.f9:  # origin: Alt_r
                self.alt_f9_pressed = True
            elif key == keyboard.Key.esc:
                self.esc_pressed = True
        except Exception:
            pass

    def on_release(self, key):
        try:
            if key == keyboard.Key.alt_r:  # origin: Alt_l
                self.alt_r_pressed = False
            elif key == keyboard.Key.f9:  # origin: Alt_r
                self.alt_f9_pressed = False
            elif key == keyboard.Key.esc:
                self.esc_pressed = False
        except Exception:
            pass

    def handle_key_events(self):
        if self.laser_visible and not self.red_dot.isVisible():
            self.red_dot.show()
        if not self.laser_visible and self.red_dot.isVisible():
            self.red_dot.hide()

        if self.alt_f9_pressed and not self.drawbox_visible:
            pos = QtGui.QCursor().pos()
            x = pos.x()
            y = pos.y()
            for screen in self.screens:
                geometry = screen.geometry()
                left = geometry.left()
                top = geometry.top()
                width = geometry.width()
                height = geometry.height()
                if x >= left and x < left + width and y >= top and y < top + height:
                    source_screen = screen
                    break
            self.draw_box.setGeometry(source_screen.geometry())
            self.draw_box.show()
            self.draw_box.raise_()
            self.draw_box.activateWindow()
            self.draw_box.setFocus()
            self.drawbox_visible = True
        elif (
            not self.alt_f9_pressed
            and self.drawbox_visible
            and not self.draw_box.isVisible()
        ):
            self.drawbox_visible = False

        if self.esc_pressed:
            if self.drawbox_visible:
                self.draw_box.hide()
                self.drawbox_visible = False
            self.esc_pressed = False

    def init_tray_icon(self):
        # tray icon
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        icon = self.windowIcon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("MouseFollow")

        # tray menu
        menu = QtWidgets.QMenu()
        restore_action = menu.addAction("Display main interface")
        quit_action = menu.addAction("Exit")
        restore_action.triggered.connect(self.show_main_window)
        quit_action.triggered.connect(QtWidgets.qApp.quit)
        self.tray_icon.setContextMenu(menu)

        # Double-click the tray icon to restore the window
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def show_main_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show_main_window()

    def changeEvent(self, event):
        super().changeEvent(event)

    def closeEvent(self, event):
        # hide to tray when closed, not exit
        event.ignore()
        self.hide()


if __name__ == "__main__":
    import sys

    dot_data = bytes(
        "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",
        encoding="utf-8",
    )
    app = QtWidgets.QApplication(sys.argv)
    gui = Master()
    sys.exit(app.exec_())
