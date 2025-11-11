import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QGridLayout, QPushButton, QFrame, QScrollArea, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QMimeData, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize
from PyQt6.QtGui import QDrag, QPainter, QPixmap, QFont, QPalette, QColor, QIcon


class MenuIcon(QPushButton):
    """Material Design 3 app icon with proper touch targets and visual feedback"""

    button_clicked = pyqtSignal(str)

    def __init__(self, icon_label, icon_path, icon_text="📱", callback=None, parent=None):
        super().__init__(parent)
        self.icon_label = icon_label
        self.icon_path = icon_path
        self.icon_text = icon_text
        self.callback = callback

        # Material Design touch target size (minimum 48dp)
        self.setFixedSize(112, 112)  # 112dp for comfortable touch interaction
        self.setup_ui()
        self.setup_animations()

        # Connect callback if provided
        if self.callback is not None:
            self.button_clicked.connect(self.callback)

    def setup_ui(self):
        """Setup Material Design 3 styling with proper tokens"""

        # Material Design 3 filled button styling
        self.setStyleSheet("""
            QPushButton {
                background: #6750A4;
                color: #FFFFFF;
                border: none;
                border-radius: 28px;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                text-align: center;
                padding: 8px;
            }
            QPushButton:hover {
                background: #7965AF;
            }
            QPushButton:pressed {
                background: #5A3D99;
            }
            QPushButton:disabled {
                background: #E8DEF8;
                color: #79747E;
            }
        """)

        # Material Design elevation shadow (level 1)
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(103, 80, 164, 40))  # Primary color shadow
            shadow.setOffset(0, 2)
            self.setGraphicsEffect(shadow)
        except:
            pass

        # Setup icon and text with Material Design principles
        self.setup_icon_content()

        # Material Design tooltip
        # self.setToolTip(self.icon_label)

    def setup_icon_content(self):
        """Setup icon content following Material Design icon guidelines"""

        # Try to load actual icon first
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                icon = QIcon(self.icon_path)
                if not icon.isNull():
                    self.setIcon(icon)
                    # Material Design icon size (24dp standard, scaled for larger button)
                    icon_size = int(self.width() * 0.5)  # 50% of button size
                    self.setIconSize(QSize(icon_size, icon_size))
                    self.setText("")  # No text when using icon
                    return
            except Exception as e:
                print(f"Error loading icon: {e}")

        # Fallback to Material Design text representation
        self.setup_fallback_text()

    def setup_fallback_text(self):
        """Setup fallback text with Material Design typography"""

        # Use emoji or abbreviation for better visual representation
        if self.icon_text and self.icon_text != "📱":
            display_text = self.icon_text
        else:
            # Create abbreviation from app name (Material Design pattern)
            words = self.icon_label.split()
            if len(words) >= 2:
                display_text = ''.join(word[0].upper() for word in words[:2])
            else:
                display_text = self.icon_label[:2].upper()

        self.setText(display_text)

        # Adjust font size based on text length for optimal readability
        if len(display_text) <= 2:
            font_size = 18  # Larger for abbreviations
        else:
            font_size = 14  # Smaller for longer text

        # Update stylesheet for text-only display
        self.setStyleSheet(self.styleSheet() + f"""
            QPushButton {{
                font-size: {font_size}px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
        """)

    def setup_animations(self):
        """Setup Material Design interaction animations"""

        # Scale animation for press feedback
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(100)  # Material Design fast timing
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Opacity animation for hover feedback
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(150)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        """Material Design hover state"""
        super().enterEvent(event)

        # Update shadow for hover state (Material Design elevation change)
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(16)
            shadow.setColor(QColor(103, 80, 164, 60))  # Deeper shadow on hover
            shadow.setOffset(0, 4)
            self.setGraphicsEffect(shadow)
        except:
            pass

    def leaveEvent(self, event):
        """Material Design normal state restoration"""
        super().leaveEvent(event)

        # Restore normal shadow
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(103, 80, 164, 40))
            shadow.setOffset(0, 2)
            self.setGraphicsEffect(shadow)
        except:
            pass

    def mousePressEvent(self, event):
        """Material Design press interaction with scale feedback"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Material Design scale-down animation for press feedback
            current_rect = self.geometry()
            scale_factor = 0.95  # Subtle scale reduction

            new_width = int(current_rect.width() * scale_factor)
            new_height = int(current_rect.height() * scale_factor)
            new_x = current_rect.x() + (current_rect.width() - new_width) // 2
            new_y = current_rect.y() + (current_rect.height() - new_height) // 2

            scaled_rect = QRect(new_x, new_y, new_width, new_height)

            self.scale_animation.setStartValue(current_rect)
            self.scale_animation.setEndValue(scaled_rect)
            self.scale_animation.start()

            # Emit signal for app selection
            self.button_clicked.emit(self.icon_label)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Material Design release interaction with scale restoration"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Restore original size with Material Design timing
            original_rect = self.geometry()
            scale_factor = 1.0 / 0.95  # Restore to original size

            new_width = int(original_rect.width() * scale_factor)
            new_height = int(original_rect.height() * scale_factor)
            new_x = original_rect.x() - (new_width - original_rect.width()) // 2
            new_y = original_rect.y() - (new_height - original_rect.height()) // 2

            restored_rect = QRect(new_x, new_y, new_width, new_height)

            self.scale_animation.setStartValue(original_rect)
            self.scale_animation.setEndValue(restored_rect)
            self.scale_animation.start()

        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Custom paint event for Material Design visual consistency"""
        super().paintEvent(event)

        # Additional Material Design visual enhancements can be added here
        # For now, we rely on stylesheet and shadow effects

    def sizeHint(self):
        """Material Design size hint"""
        return QSize(112, 112)  # Consistent Material Design touch target

    def minimumSizeHint(self):
        """Minimum size following Material Design guidelines"""
        return QSize(48, 48)  # Material Design minimum touch target

    def set_icon_from_path(self, icon_path):
        """Update icon from new path with Material Design handling"""
        self.icon_path = icon_path
        self.setup_icon_content()

    def set_material_style(self, style_variant="primary"):
        """Apply different Material Design style variants"""

        style_variants = {
            "primary": {
                "background": "#6750A4",
                "hover": "#7965AF",
                "pressed": "#5A3D99",
                "text_color": "#FFFFFF"
            },
            "secondary": {
                "background": "#E8DEF8",
                "hover": "#DDD2EA",
                "pressed": "#D1C6DD",
                "text_color": "#6750A4"
            },
            "tertiary": {
                "background": "#F7F2FA",
                "hover": "#F0EBEF",
                "pressed": "#E9E3E4",
                "text_color": "#7D5260"
            }
        }

        if style_variant in style_variants:
            colors = style_variants[style_variant]

            self.setStyleSheet(f"""
                QPushButton {{
                    background: {colors['background']};
                    color: {colors['text_color']};
                    border: none;
                    border-radius: 28px;
                    font-size: 12px;
                    font-weight: 500;
                    font-family: 'Roboto', 'Segoe UI', sans-serif;
                    text-align: center;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background: {colors['hover']};
                }}
                QPushButton:pressed {{
                    background: {colors['pressed']};
                }}
                QPushButton:disabled {{
                    background: #E8DEF8;
                    color: #79747E;
                }}
            """)

    def set_material_size(self, size_variant="standard"):
        """Apply different Material Design size variants"""

        size_variants = {
            "compact": QSize(80, 80),
            "standard": QSize(112, 112),
            "large": QSize(144, 144)
        }

        if size_variant in size_variants:
            new_size = size_variants[size_variant]
            self.setFixedSize(new_size)

            # Update border radius proportionally
            radius = min(new_size.width(), new_size.height()) // 4

            current_style = self.styleSheet()
            # Update border-radius in stylesheet
            import re
            updated_style = re.sub(
                r'border-radius:\s*\d+px',
                f'border-radius: {radius}px',
                current_style
            )
            self.setStyleSheet(updated_style)

            # Update icon size proportionally
            if hasattr(self, 'icon') and not self.icon().isNull():
                icon_size = min(new_size.width(), new_size.height()) // 2
                self.setIconSize(QSize(icon_size, icon_size))


# Demo application to showcase Material Design MenuIcon
class MaterialMenuIconDemo(QWidget):
    """Demo application showcasing Material Design 3 MenuIcon variants"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup demo interface with Material Design"""
        self.setWindowTitle("Material Design 3 MenuIcon Demo")
        self.resize(800, 600)

        # Material Design background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFBFE,
                    stop:1 #F7F2FA);
                font-family: 'Roboto', 'Segoe UI', sans-serif;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(48, 48, 48, 48)
        main_layout.setSpacing(32)

        # Title
        title = QLabel("Material Design 3 MenuIcon Components")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                font-size: 28px;
                font-weight: 400;
                margin-bottom: 16px;
            }
        """)
        main_layout.addWidget(title)

        # Create demo sections
        self.create_style_variants_section(main_layout)
        self.create_size_variants_section(main_layout)
        self.create_app_icons_section(main_layout)

    def create_style_variants_section(self, parent_layout):
        """Create style variants demonstration"""
        section_label = QLabel("Style Variants")
        section_label.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                font-size: 20px;
                font-weight: 500;
                margin-bottom: 8px;
            }
        """)
        parent_layout.addWidget(section_label)

        style_layout = QHBoxLayout()
        style_layout.setSpacing(24)

        # Primary style
        primary_icon = MenuIcon("Primary", "", "PR", self.on_icon_clicked)
        primary_icon.set_material_style("primary")
        style_layout.addWidget(primary_icon)

        # Secondary style
        secondary_icon = MenuIcon("Secondary", "", "SE", self.on_icon_clicked)
        secondary_icon.set_material_style("secondary")
        style_layout.addWidget(secondary_icon)

        # Tertiary style
        tertiary_icon = MenuIcon("Tertiary", "", "TE", self.on_icon_clicked)
        tertiary_icon.set_material_style("tertiary")
        style_layout.addWidget(tertiary_icon)

        style_layout.addStretch()
        parent_layout.addLayout(style_layout)

    def create_size_variants_section(self, parent_layout):
        """Create size variants demonstration"""
        section_label = QLabel("Size Variants")
        section_label.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                font-size: 20px;
                font-weight: 500;
                margin-bottom: 8px;
            }
        """)
        parent_layout.addWidget(section_label)

        size_layout = QHBoxLayout()
        size_layout.setSpacing(24)
        size_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Compact size
        compact_icon = MenuIcon("Compact", "", "CO", self.on_icon_clicked)
        compact_icon.set_material_size("compact")
        size_layout.addWidget(compact_icon)

        # Standard size
        standard_icon = MenuIcon("Standard", "", "ST", self.on_icon_clicked)
        standard_icon.set_material_size("standard")
        size_layout.addWidget(standard_icon)

        # Large size
        large_icon = MenuIcon("Large", "", "LA", self.on_icon_clicked)
        large_icon.set_material_size("large")
        size_layout.addWidget(large_icon)

        size_layout.addStretch()
        parent_layout.addLayout(size_layout)

    def create_app_icons_section(self, parent_layout):
        """Create realistic app icons demonstration"""
        section_label = QLabel("Application Icons")
        section_label.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                font-size: 20px;
                font-weight: 500;
                margin-bottom: 8px;
            }
        """)
        parent_layout.addWidget(section_label)

        apps_layout = QGridLayout()
        apps_layout.setSpacing(16)

        # Sample apps with realistic names
        apps = [
            ("Settings", "⚙️"),
            ("Gallery", "🖼️"),
            ("Calendar", "📅"),
            ("Messages", "💬"),
            ("Camera", "📷"),
            ("Music", "🎵"),
            ("Files", "📁"),
            ("Calculator", "🧮")
        ]

        for i, (name, emoji) in enumerate(apps):
            row = i // 4
            col = i % 4

            app_icon = MenuIcon(name, "", emoji, self.on_icon_clicked)
            apps_layout.addWidget(app_icon, row, col)

        parent_layout.addLayout(apps_layout)
        parent_layout.addStretch()

    def on_icon_clicked(self, icon_name):
        """Handle icon click with Material Design feedback"""
        print(f"Material Design Icon clicked: {icon_name}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Material Design application setup
    app.setStyle('Fusion')

    # Set Material Design font
    font = QFont("Roboto", 10)
    if not font.exactMatch():
        font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Material Design application styling
    app.setStyleSheet("""
        QToolTip {
            background: #313033;
            color: #FFFFFF;
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
    """)

    # Create and show demo
    demo = MaterialMenuIconDemo()
    demo.show()

    print("Material Design 3 MenuIcon Demo")
    print("• Click any icon to see interaction feedback")
    print("• Hover over icons to see elevation changes")
    print("• Observe Material Design animation timing")

    sys.exit(app.exec())