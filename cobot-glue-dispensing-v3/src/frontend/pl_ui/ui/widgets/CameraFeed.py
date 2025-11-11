import time
from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, \
    QFrame, QSizePolicy, QApplication
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QMouseEvent
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QPushButton

import numpy as np


class ClickableGraphicsView(QGraphicsView):
    def __init__(self, parent, toggle_callback):
        super().__init__(parent)
        self.toggle_callback = toggle_callback

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.toggle_callback()


@dataclass
class CameraFeedConfig:
    updateFrequency: int = 30  # in milliseconds
    screen_size: tuple = (320, 180)
    resolution_small: tuple = (320, 180)
    resolution_large: tuple = (1280, 720)
    current_resolution: tuple = (320, 180)


class CameraFeed(QFrame):
    def __init__(self,cameraFeedConfig=CameraFeedConfig(), updateCallback=None, toggleCallback=None):
        super().__init__()
        self.graphics_view = ClickableGraphicsView(self, self.toggle_resolution)
        self.cameraFeedConfig = cameraFeedConfig
        self.updateCallback = updateCallback
        self.toggleCallback = toggleCallback
        self.updateFrequency = self.cameraFeedConfig.updateFrequency  # in milliseconds
        self.screen_size = self.cameraFeedConfig.screen_size  # (width, height)
        self.setMaximumSize(self.cameraFeedConfig.resolution_large[0], self.cameraFeedConfig.resolution_large[1])
        screen_width = self.screen_size[0]
        screen_height = self.screen_size[1]

        # Set widget size (80% of screen) and max cap
        # self.setFixedSize(int(screen_width * 0.8), int(screen_height * 0.8))
        self.setFixedSize(screen_width, screen_height)
        self.setMaximumSize(self.screen_size[0], self.screen_size[1])
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: transparent; border: none;")

        # Layout for the frame
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Graphics view (DO NOT overwrite the ClickableGraphicsView instance!)
        self.graphics_view.setFixedSize(self.size())
        self.graphics_view.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.graphics_view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.graphics_view.setContentsMargins(0, 0, 0, 0)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setStyleSheet("border: none;")

        self.layout.addWidget(self.graphics_view)

        # Scene
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Feed control
        self.is_feed_paused = False
        self.clicked_points = []
        self.transformedPoints = []

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateCameraLabel)
        self.timer.start(self.updateFrequency)

        self.resolution_small = self.cameraFeedConfig.resolution_small
        self.resolution_large = self.cameraFeedConfig.resolution_large
        self.current_resolution = self.cameraFeedConfig.current_resolution

    def toggle_resolution(self):
        # print("Res toggled")

        if self.current_resolution == self.resolution_small:
            self.current_resolution = self.resolution_large
        else:
            self.current_resolution = self.resolution_small

        if self.toggleCallback is not None:
            self.toggleCallback()

        width, height = self.current_resolution
        self.setFixedSize(width, height)
        self.graphics_view.setFixedSize(width, height)
        # print(f"Switched to: {width}x{height}")

    def set_image(self, image):
        if isinstance(image, str):
            pixmap = QPixmap(image)
        elif isinstance(image, np.ndarray):
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
        else:
            print("Unsupported image type")
            return

        if pixmap.isNull():
            print("Failed to load image")
            return

        resized_pixmap = pixmap.scaled(self.size().width(), self.size().height(),
                                       Qt.AspectRatioMode.IgnoreAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)

        self.scene.clear()
        pixmap_item = QGraphicsPixmapItem(resized_pixmap)
        self.scene.addItem(pixmap_item)
        self.graphics_view.setScene(self.scene)

    def updateCameraLabel(self):
        # start_time = time.time()
        if self.is_feed_paused:
            return
        try:
            frame = self.updateCallback()
            if frame is not None:
                self.set_image(frame)
            else:
                return
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            pass
            # elapsed = (time.time() - start_time) * 1000
            # print(f"updateCameraLabel execution time: {elapsed:.2f} ms")

    def pause_feed(self, static_image=None):
        self.is_feed_paused = True
        self.clicked_points.clear()

        if static_image is not None:
            if isinstance(static_image, str):
                pixmap = QPixmap(static_image)
            elif isinstance(static_image, np.ndarray):
                height, width, channel = static_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(static_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
            else:
                raise TypeError("Unsupported image type")

            resized_pixmap = pixmap.scaled(self.size().width(), self.size().height(),
                                           Qt.AspectRatioMode.IgnoreAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            self.scene.clear()
            pixmap_item = QGraphicsPixmapItem(resized_pixmap)
            self.scene.addItem(pixmap_item)
            self.graphics_view.setScene(self.scene)

    def resume_feed(self):
        self.is_feed_paused = False
        self.timer.start(self.updateFrequency)
        print("Feed resumed.")
        return self.clicked_points
