"""
Animation Manager for PyQt6 Material Design Components

This module centralizes all animation logic from the folder interface,
providing consistent Material Design timing and easing curves.
"""

from typing import Optional, Callable, Union, List
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize, QTimer,
    QParallelAnimationGroup, QSequentialAnimationGroup, QObject, pyqtSignal
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


class MaterialDesignTiming:
    """Material Design animation timing constants"""
    FAST = 100
    SHORT = 150
    MEDIUM = 300
    LONG = 500
    EXTRA_LONG = 700


class MaterialDesignEasing:
    """Material Design easing curve presets"""
    STANDARD = QEasingCurve.Type.OutCubic
    EMPHASIZED = QEasingCurve.Type.OutQuart
    DECELERATED = QEasingCurve.Type.OutCubic
    ACCELERATED = QEasingCurve.Type.InCubic
    LINEAR = QEasingCurve.Type.Linear


class AnimationManager(QObject):
    """Centralized animation management with Material Design principles"""

    animation_finished = pyqtSignal(str)  # Animation name/id
    all_animations_finished = pyqtSignal()

    def __init__(self, target_widget: QWidget, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.target = target_widget
        self.animations = {}
        self.animation_groups = {}
        self._active_animations = set()

    def create_fade_animation(
            self,
            duration: int = MaterialDesignTiming.MEDIUM,
            easing: QEasingCurve.Type = MaterialDesignEasing.STANDARD,
            animation_id: str = "fade"
    ) -> QPropertyAnimation:
        """Create opacity fade animation"""
        animation = QPropertyAnimation(self.target, b"windowOpacity")
        animation.setDuration(duration)
        animation.setEasingCurve(easing)

        # Store and connect
        self.animations[animation_id] = animation
        animation.finished.connect(lambda: self._on_animation_finished(animation_id))

        return animation

    def create_geometry_animation(
            self,
            duration: int = MaterialDesignTiming.MEDIUM,
            easing: QEasingCurve.Type = MaterialDesignEasing.STANDARD,
            animation_id: str = "geometry"
    ) -> QPropertyAnimation:
        """Create geometry/scale animation"""
        animation = QPropertyAnimation(self.target, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(easing)

        self.animations[animation_id] = animation
        animation.finished.connect(lambda: self._on_animation_finished(animation_id))

        return animation

    def fade_in(
            self,
            start_opacity: float = 0.0,
            end_opacity: float = 1.0,
            duration: int = MaterialDesignTiming.MEDIUM,
            callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """Material Design fade-in animation"""
        animation = self.create_fade_animation(duration, MaterialDesignEasing.DECELERATED, "fade_in")
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)

        if callback:
            animation.finished.connect(callback)

        self.target.setWindowOpacity(start_opacity)
        self.target.show()
        self.target.raise_()

        self._active_animations.add("fade_in")
        animation.start()
        return animation

    def fade_out(
            self,
            start_opacity: float = 1.0,
            end_opacity: float = 0.0,
            duration: int = MaterialDesignTiming.MEDIUM,
            hide_on_finish: bool = True,
            callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """Material Design fade-out animation"""
        animation = self.create_fade_animation(duration, MaterialDesignEasing.ACCELERATED, "fade_out")
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)

        if hide_on_finish:
            animation.finished.connect(self.target.hide)

        if callback:
            animation.finished.connect(callback)

        self._active_animations.add("fade_out")
        animation.start()
        return animation

    def scale_in_from_center(
            self,
            center_pos: QPoint,
            scale_factor: float = 0.8,
            duration: int = MaterialDesignTiming.MEDIUM,
            callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """Material Design scale-in from center point"""
        current_size = self.target.size()
        final_rect = QRect(
            center_pos.x() - current_size.width() // 2,
            center_pos.y() - current_size.height() // 2,
            current_size.width(),
            current_size.height()
        )

        # Calculate scaled start rectangle
        start_width = int(current_size.width() * scale_factor)
        start_height = int(current_size.height() * scale_factor)
        start_rect = QRect(
            center_pos.x() - start_width // 2,
            center_pos.y() - start_height // 2,
            start_width,
            start_height
        )

        animation = self.create_geometry_animation(duration, MaterialDesignEasing.DECELERATED, "scale_in")
        animation.setStartValue(start_rect)
        animation.setEndValue(final_rect)

        if callback:
            animation.finished.connect(callback)

        # Set initial state
        self.target.setGeometry(start_rect)
        self.target.show()
        self.target.raise_()

        self._active_animations.add("scale_in")
        animation.start()
        return animation

    def scale_out_to_center(
            self,
            center_pos: Optional[QPoint] = None,
            scale_factor: float = 0.8,
            duration: int = MaterialDesignTiming.MEDIUM,
            hide_on_finish: bool = True,
            callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """Material Design scale-out to center point"""
        if center_pos is None:
            center_pos = self.target.geometry().center()

        current_rect = self.target.geometry()

        # Calculate scaled end rectangle
        end_width = int(current_rect.width() * scale_factor)
        end_height = int(current_rect.height() * scale_factor)
        end_rect = QRect(
            center_pos.x() - end_width // 2,
            center_pos.y() - end_height // 2,
            end_width,
            end_height
        )

        animation = self.create_geometry_animation(duration, MaterialDesignEasing.ACCELERATED, "scale_out")
        animation.setStartValue(current_rect)
        animation.setEndValue(end_rect)

        if hide_on_finish:
            animation.finished.connect(self.target.hide)

        if callback:
            animation.finished.connect(callback)

        self._active_animations.add("scale_out")
        animation.start()
        return animation

    def combined_fade_and_scale_in(
            self,
            center_pos: QPoint,
            scale_factor: float = 0.8,
            opacity_start: float = 0.0,
            opacity_end: float = 1.0,
            duration: int = MaterialDesignTiming.MEDIUM,
            callback: Optional[Callable] = None
    ) -> QParallelAnimationGroup:
        """Combined fade and scale animation for Material Design entrance"""
        # Create individual animations without auto-starting
        fade_anim = self.create_fade_animation(duration, MaterialDesignEasing.DECELERATED, "combined_fade")
        fade_anim.setStartValue(opacity_start)
        fade_anim.setEndValue(opacity_end)

        scale_anim = self.create_geometry_animation(duration, MaterialDesignEasing.DECELERATED, "combined_scale")

        # Setup geometry values
        current_size = self.target.size()
        final_rect = QRect(
            center_pos.x() - current_size.width() // 2,
            center_pos.y() - current_size.height() // 2,
            current_size.width(),
            current_size.height()
        )

        start_width = int(current_size.width() * scale_factor)
        start_height = int(current_size.height() * scale_factor)
        start_rect = QRect(
            center_pos.x() - start_width // 2,
            center_pos.y() - start_height // 2,
            start_width,
            start_height
        )

        scale_anim.setStartValue(start_rect)
        scale_anim.setEndValue(final_rect)

        # Create parallel group
        group = QParallelAnimationGroup(self)
        group.addAnimation(fade_anim)
        group.addAnimation(scale_anim)

        if callback:
            group.finished.connect(callback)

        # Store group
        self.animation_groups["combined_in"] = group
        group.finished.connect(lambda: self._on_animation_finished("combined_in"))

        # Set initial state
        self.target.setGeometry(start_rect)
        self.target.setWindowOpacity(opacity_start)
        self.target.show()
        self.target.raise_()

        self._active_animations.add("combined_in")
        group.start()
        return group

    def combined_fade_and_scale_out(
            self,
            center_pos: Optional[QPoint] = None,
            scale_factor: float = 0.8,
            opacity_start: float = 1.0,
            opacity_end: float = 0.0,
            duration: int = MaterialDesignTiming.MEDIUM,
            hide_on_finish: bool = True,
            callback: Optional[Callable] = None
    ) -> QParallelAnimationGroup:
        """Combined fade and scale animation for Material Design exit"""
        if center_pos is None:
            center_pos = self.target.geometry().center()

        # Create individual animations
        fade_anim = self.create_fade_animation(duration, MaterialDesignEasing.ACCELERATED, "combined_fade_out")
        fade_anim.setStartValue(opacity_start)
        fade_anim.setEndValue(opacity_end)

        scale_anim = self.create_geometry_animation(duration, MaterialDesignEasing.ACCELERATED, "combined_scale_out")

        # Setup geometry values
        current_rect = self.target.geometry()
        end_width = int(current_rect.width() * scale_factor)
        end_height = int(current_rect.height() * scale_factor)
        end_rect = QRect(
            center_pos.x() - end_width // 2,
            center_pos.y() - end_height // 2,
            end_width,
            end_height
        )

        scale_anim.setStartValue(current_rect)
        scale_anim.setEndValue(end_rect)

        # Create parallel group
        group = QParallelAnimationGroup(self)
        group.addAnimation(fade_anim)
        group.addAnimation(scale_anim)

        if hide_on_finish:
            group.finished.connect(self.target.hide)

        if callback:
            group.finished.connect(callback)

        # Store group
        self.animation_groups["combined_out"] = group
        group.finished.connect(lambda: self._on_animation_finished("combined_out"))

        self._active_animations.add("combined_out")
        group.start()
        return group

    def create_floating_icon_show_animation(
            self,
            start_offset: QPoint = QPoint(0, 16),
            duration: int = MaterialDesignTiming.MEDIUM
    ) -> QParallelAnimationGroup:
        """Animation for showing floating action button"""
        # Geometry animation (slide up effect)
        start_pos = self.target.pos() + start_offset
        end_pos = self.target.pos()

        start_size = QSize(0, 0)
        end_size = self.target.size()

        geometry_anim = self.create_geometry_animation(duration, MaterialDesignEasing.DECELERATED, "fab_geometry")
        geometry_anim.setStartValue(QRect(start_pos, start_size))
        geometry_anim.setEndValue(QRect(end_pos, end_size))

        # Fade animation
        fade_anim = self.create_fade_animation(duration, MaterialDesignEasing.DECELERATED, "fab_fade")
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)

        # Combine animations
        group = QParallelAnimationGroup(self)
        group.addAnimation(geometry_anim)
        group.addAnimation(fade_anim)

        self.animation_groups["fab_show"] = group
        group.finished.connect(lambda: self._on_animation_finished("fab_show"))

        self.target.show()
        self.target.raise_()

        self._active_animations.add("fab_show")
        group.start()
        return group

    def create_floating_icon_hide_animation(
            self,
            duration: int = MaterialDesignTiming.SHORT,
            callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """Animation for hiding floating action button"""
        animation = self.create_fade_animation(duration, MaterialDesignEasing.ACCELERATED, "fab_hide")
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.finished.connect(self.target.hide)

        if callback:
            animation.finished.connect(callback)

        self._active_animations.add("fab_hide")
        animation.start()
        return animation

    def create_button_press_animation(
            self,
            scale_factor: float = 0.95,
            duration: int = MaterialDesignTiming.FAST
    ) -> QPropertyAnimation:
        """Material Design button press feedback animation"""
        current_rect = self.target.geometry()
        center = current_rect.center()

        new_width = int(current_rect.width() * scale_factor)
        new_height = int(current_rect.height() * scale_factor)
        new_x = center.x() - new_width // 2
        new_y = center.y() - new_height // 2

        scaled_rect = QRect(new_x, new_y, new_width, new_height)

        animation = self.create_geometry_animation(duration, MaterialDesignEasing.STANDARD, "button_press")
        animation.setStartValue(current_rect)
        animation.setEndValue(scaled_rect)

        self._active_animations.add("button_press")
        animation.start()
        return animation

    def create_button_release_animation(
            self,
            original_rect: Optional[QRect] = None,
            duration: int = MaterialDesignTiming.FAST
    ) -> QPropertyAnimation:
        """Material Design button release feedback animation"""
        if original_rect is None:
            # Calculate original rect from current scaled rect (assuming 0.95 scale factor)
            current_rect = self.target.geometry()
            center = current_rect.center()
            original_width = int(current_rect.width() / 0.95)
            original_height = int(current_rect.height() / 0.95)
            original_x = center.x() - original_width // 2
            original_y = center.y() - original_height // 2
            original_rect = QRect(original_x, original_y, original_width, original_height)

        animation = self.create_geometry_animation(duration, MaterialDesignEasing.STANDARD, "button_release")
        animation.setStartValue(self.target.geometry())
        animation.setEndValue(original_rect)

        self._active_animations.add("button_release")
        animation.start()
        return animation

    def stop_animation(self, animation_id: str) -> bool:
        """Stop specific animation by ID"""
        if animation_id in self.animations:
            self.animations[animation_id].stop()
            self._active_animations.discard(animation_id)
            return True
        elif animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()
            self._active_animations.discard(animation_id)
            return True
        return False

    def stop_all_animations(self):
        """Stop all active animations"""
        for animation in self.animations.values():
            animation.stop()
        for group in self.animation_groups.values():
            group.stop()
        self._active_animations.clear()

    def is_animation_active(self, animation_id: str) -> bool:
        """Check if specific animation is currently running"""
        return animation_id in self._active_animations

    def has_active_animations(self) -> bool:
        """Check if any animations are currently running"""
        return len(self._active_animations) > 0

    def _on_animation_finished(self, animation_id: str):
        """Internal handler for animation completion"""
        self._active_animations.discard(animation_id)
        self.animation_finished.emit(animation_id)

        if not self._active_animations:
            self.all_animations_finished.emit()

    def cleanup(self):
        """Clean up all animations and groups"""
        self.stop_all_animations()

        for animation in self.animations.values():
            animation.deleteLater()

        for group in self.animation_groups.values():
            group.deleteLater()

        self.animations.clear()
        self.animation_groups.clear()
        self._active_animations.clear()


# Utility functions for common animation patterns
def create_material_entrance_animation(
        widget: QWidget,
        center_pos: QPoint,
        duration: int = MaterialDesignTiming.MEDIUM,
        callback: Optional[Callable] = None
) -> AnimationManager:
    """Create a standard Material Design entrance animation"""
    manager = AnimationManager(widget)
    manager.combined_fade_and_scale_in(center_pos, duration=duration, callback=callback)
    return manager


def create_material_exit_animation(
        widget: QWidget,
        duration: int = MaterialDesignTiming.MEDIUM,
        callback: Optional[Callable] = None
) -> AnimationManager:
    """Create a standard Material Design exit animation"""
    manager = AnimationManager(widget)
    manager.combined_fade_and_scale_out(duration=duration, callback=callback)
    return manager


def create_fab_animation(
        widget: QWidget,
        show: bool = True,
        callback: Optional[Callable] = None
) -> AnimationManager:
    """Create floating action button show/hide animation"""
    manager = AnimationManager(widget)
    if show:
        manager.create_floating_icon_show_animation()
    else:
        manager.create_floating_icon_hide_animation(callback=callback)
    return manager


# Example usage patterns for migration
class AnimationPatterns:
    """Common animation patterns used in the folder interface"""

    @staticmethod
    def folder_open_animation(expanded_view_widget: QWidget, center_pos: QPoint) -> AnimationManager:
        """Standard folder opening animation"""
        manager = AnimationManager(expanded_view_widget)
        manager.combined_fade_and_scale_in(center_pos)
        return manager

    @staticmethod
    def folder_close_animation(expanded_view_widget: QWidget) -> AnimationManager:
        """Standard folder closing animation"""
        manager = AnimationManager(expanded_view_widget)
        manager.combined_fade_and_scale_out()
        return manager

    @staticmethod
    def floating_icon_transition(floating_icon_widget: QWidget, show: bool) -> AnimationManager:
        """Floating icon show/hide transition"""
        manager = AnimationManager(floating_icon_widget)
        if show:
            manager.create_floating_icon_show_animation()
        else:
            manager.create_floating_icon_hide_animation()
        return manager


if __name__ == "__main__":
    # Example usage for testing
    from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
    import sys

    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Animation Manager Test")
    window.resize(400, 300)

    layout = QVBoxLayout(window)

    test_widget = QWidget(window)
    test_widget.setFixedSize(200, 150)
    test_widget.setStyleSheet("background-color: #6750A4; border-radius: 12px;")
    layout.addWidget(test_widget)

    # Test buttons
    fade_in_btn = QPushButton("Fade In")
    fade_out_btn = QPushButton("Fade Out")
    scale_in_btn = QPushButton("Scale In")
    combined_btn = QPushButton("Combined Animation")

    layout.addWidget(fade_in_btn)
    layout.addWidget(fade_out_btn)
    layout.addWidget(scale_in_btn)
    layout.addWidget(combined_btn)

    # Create animation manager
    anim_manager = AnimationManager(test_widget)

    # Connect buttons
    fade_in_btn.clicked.connect(lambda: anim_manager.fade_in())
    fade_out_btn.clicked.connect(lambda: anim_manager.fade_out(hide_on_finish=False))
    scale_in_btn.clicked.connect(lambda: anim_manager.scale_in_from_center(window.rect().center()))
    combined_btn.clicked.connect(lambda: anim_manager.combined_fade_and_scale_in(window.rect().center()))

    window.show()
    sys.exit(app.exec())