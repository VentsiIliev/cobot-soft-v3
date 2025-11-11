from io import BytesIO
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt, QEvent, QPoint
from PyQt6.QtGui import QPixmap, QFont, QMouseEvent, QCursor

class DraggableLabel(QLabel):
    #\"\"\"QLabel that supports click\-and\-drag panning (swipe) for a parent QScrollArea.\"\"\"
    def __init__(self, parent=None, scroll_area=None):
        super().__init__(parent)
        self._scroll_area = scroll_area
        self._dragging = False
        self._last_pos = QPoint()
        # Accept mouse events and touch as mouse
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TouchPadAcceptSingleTouchEvents, True)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_pos = event.globalPosition().toPoint()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self._scroll_area is not None:
            current = event.globalPosition().toPoint()
            delta = current - self._last_pos
            hbar = self._scroll_area.horizontalScrollBar()
            vbar = self._scroll_area.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            self._last_pos = current
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def event(self, ev: QEvent):
        # Treat touch events like mouse for basic swipe support on touchscreens
        def _touch_points(event):
            for name in ('touchPoints', 'points'):
                attr = getattr(event, name, None)
                if callable(attr):
                    try:
                        return attr()
                    except Exception:
                        continue
                elif attr:
                    return attr
            return []

        ttype = ev.type()
        if ttype == QEvent.Type.TouchBegin:
            pts = _touch_points(ev)
            if not pts:
                return super().event(ev)
            self._dragging = True
            touch_point = pts[0]
            try:
                self._last_pos = touch_point.screenPos().toPoint()
            except Exception:
                if hasattr(touch_point, 'pos'):
                    self._last_pos = touch_point.pos().toPoint()
            return True

        if ttype == QEvent.Type.TouchUpdate and self._dragging and self._scroll_area is not None:
            pts = _touch_points(ev)
            if not pts:
                return super().event(ev)
            touch_point = pts[0]
            try:
                current = touch_point.screenPos().toPoint()
            except Exception:
                current = touch_point.pos().toPoint() if hasattr(touch_point, 'pos') else self._last_pos
            delta = current - self._last_pos
            hbar = self._scroll_area.horizontalScrollBar()
            vbar = self._scroll_area.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            self._last_pos = current
            return True

        if ttype == QEvent.Type.TouchEnd:
            self._dragging = False
            return True

        return super().event(ev)


