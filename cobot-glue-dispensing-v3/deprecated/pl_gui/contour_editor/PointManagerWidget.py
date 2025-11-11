import os

from PyQt6.QtCore import Qt, QPointF, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QSizePolicy, QLabel
)
from PyQt6.QtGui import QIcon, QFont

from deprecated.pl_gui.contour_editor.SegmentSettingsWidget import SegmentSettingsWidget
from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
from deprecated.pl_gui.specific.enums.GlueType import GlueType
from deprecated.pl_gui.contour_editor.LayerButtonsWidget import LayerButtonsWidget
from deprecated.pl_gui.contour_editor.SegmentButtonsAndComboWidget import SegmentButtonsAndComboWidget
from PyQt6.QtWidgets import QApplication

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
HIDE_ICON = os.path.join(RESOURCE_DIR, "hide.png")
SHOW_ICON = os.path.join(RESOURCE_DIR, "show.png")
BIN_ICON = os.path.join(RESOURCE_DIR, "BIN_BUTTON_SQUARE.png")
PLUS_ICON = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")
LOCK_ICON = os.path.join(RESOURCE_DIR, "locked.png")
UNLOCK_ICON = os.path.join(RESOURCE_DIR, "unlocked.png")
ACTIVE_ICON = os.path.join(RESOURCE_DIR, "active.png")
INACTIVE_ICON = os.path.join(RESOURCE_DIR, "inactive.png")
DROPDOWN_OPEN_ICON = os.path.join(RESOURCE_DIR, "dropdown_open.png")
CLOSED_FOLDER_ICON = os.path.join(RESOURCE_DIR, "close_folder.png")
OPEN_FOLDER_ICON = os.path.join(RESOURCE_DIR, "open_folder.png")

class ListItemData:
    """Data class to store information about list items"""

    def __init__(self, item_type, layer_name=None, seg_index=None, point_index=None, point_type=None):
        self.item_type = item_type  # 'layer', 'segment', 'point'
        self.layer_name = layer_name
        self.seg_index = seg_index
        self.point_index = point_index
        self.point_type = point_type  # 'anchor' or 'control'
        self.is_expanded = True  # For layers and segments


class IndentedWidget(QWidget):
    """Widget with configurable left indentation"""

    def __init__(self, content_widget, indent_level=0, indent_size=20):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(indent_level * indent_size, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(content_widget)
        layout.addStretch()


class ExpandableLayerWidget(QWidget):
    """Layer widget with expand/collapse functionality"""

    def __init__(self, layer_name, layer_buttons_widget, on_expand_toggle):
        super().__init__()

        self.layer_name = layer_name
        self.on_expand_toggle = on_expand_toggle
        self.is_expanded = True

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically

        # Expand/collapse button
        self.expand_icon = QIcon(OPEN_FOLDER_ICON if self.is_expanded else CLOSED_FOLDER_ICON)
        self.expand_btn = QPushButton(self.expand_icon, "")
        self.expand_btn.setIconSize(QSize(50, 50))
        self.expand_btn.setFixedSize(80, 80)
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-weight: bold;
                qproperty-iconSize: 50px 50px;
            }
        """)
        self.expand_btn.setContentsMargins(0, 0, 0, 0)
        self.expand_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.expand_btn.clicked.connect(self._toggle_expansion)
        layout.addWidget(self.expand_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Layer buttons widget
        layout.addWidget(layer_buttons_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

    def _toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        self.expand_btn.setText("▼" if self.is_expanded else "▶")
        if self.on_expand_toggle:
            self.on_expand_toggle(self.layer_name, self.is_expanded)

    def set_expanded(self, expanded):
        self.is_expanded = expanded
        self.expand_btn.setIcon(QIcon(OPEN_FOLDER_ICON if expanded else CLOSED_FOLDER_ICON))
        self.expand_btn.setIconSize(QSize(50, 50))
        # self.expand_btn.setText("▼" if expanded else "▶")


class ExpandableSegmentWidget(QWidget):
    """Segment widget with expand/collapse functionality"""

    def __init__(self, seg_index, segment_buttons_widget, on_expand_toggle):
        super().__init__()

        self.seg_index = seg_index
        self.on_expand_toggle = on_expand_toggle
        self.is_expanded = True

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically

        # Expand/collapse button
        self.expand_btn = QPushButton("▼")
        self.expand_btn.setFixedSize(80, 80)
        self.expand_btn.setStyleSheet("QPushButton { background-color: transparent; border: none;; font-weight: bold; }")
        layout.addWidget(self.expand_btn)

        # Segment buttons widget
        layout.addWidget(segment_buttons_widget)

    def _toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        self.expand_btn.setText("▼" if self.is_expanded else "▶")
        if self.on_expand_toggle:
            self.on_expand_toggle(self.seg_index, self.is_expanded)

    def set_expanded(self, expanded):
        self.is_expanded = expanded
        self.expand_btn.setText("▼" if expanded else "▶")

class PointWidget(QWidget):
    """Widget for displaying point information"""

    def __init__(self, point_label, coordinates):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Point label
        label = QLabel(point_label)
        label.setFont(QFont("Arial", 12))
        if point_label.startswith("P"):
            label.setStyleSheet("color: #0066cc;")  # Blue for anchor points
        else:
            label.setStyleSheet("color: #cc6600;")  # Orange for control points
        label.setFixedWidth(40)
        layout.addWidget(label)

        # Coordinates
        coords_label = QLabel(coordinates)
        coords_label.setFont(QFont("Arial", 12))
        layout.addWidget(coords_label)

        layout.addStretch()


class PointManagerWidget(QWidget):
    def __init__(self, contour_editor=None):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(8, 8, 8, 8)
        self.layout().setSpacing(4)
        self.setStyleSheet("""
            QWidget {
                font-size: 18px;
            }
            QPushButton {
                min-width: 64px;
                min-height: 64px;
                padding: 10px;
                border: None;
            }
            QComboBox {
                min-height: 40px;
                font-size: 18px;
            }
            QListWidget {
                outline: none;
                border: 1px solid #ccc;
                background-color: white;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                border: 1px solid #007acc;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
            }
        """)
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        self.contour_editor = contour_editor
        if self.contour_editor:
            self.contour_editor.pointsUpdated.connect(self.refresh_points)

        self._setup_list_widget()
        self.layout().addWidget(self.list)

        self.layers = {}
        self.layer_items = {}  # Store QListWidgetItem for each layer
        self.segment_items = {}  # Store QListWidgetItem for each segment
        self.expanded_layers = set()  # Track expanded layers
        self.expanded_segments = set()  # Track expanded segments
        self.is_drag_mode = False

        self.initialize_list_structure()

    def _setup_list_widget(self):
        """Initialize and configure the list widget"""
        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)

        # Connect signals
        self.list.itemClicked.connect(self.highlight_selected_point)

    def initialize_list_structure(self):
        """Initialize the list structure with layer items"""
        self.list.clear()
        self.layers = {}
        self.layer_items = {}
        self.expanded_layers = {"External", "Contour", "Fill"}  # Expand all by default

        for name in ["External", "Contour", "Fill"]:
            self._create_layer_item(name)

    def _create_layer_item(self, name):
        """Create a layer item with proper configuration"""
        # Create list item
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 80))

        # Create item data
        item_data = ListItemData('layer', layer_name=name)
        item.setData(Qt.ItemDataRole.UserRole, item_data)

        # Create layer buttons widget
        is_locked = self.contour_editor.manager.isLayerLocked(name) if self.contour_editor else False
        layer_buttons = LayerButtonsWidget(
            layer_name=name,
            layer_item=item,
            on_visibility_toggle=lambda visible: self.set_layer_visibility(name, visible),
            on_add_segment=self._make_add_segment(name, item),
            on_lock_toggle=self._make_layer_lock_toggle(name),
            is_locked=is_locked
        )

        # Create expandable layer widget
        expandable_widget = ExpandableLayerWidget(
            name,
            layer_buttons,
            self._on_layer_expand_toggle
        )

        # Set the initial expanded state
        is_expanded = name in self.expanded_layers
        expandable_widget.set_expanded(is_expanded)

        # Add to list
        self.list.addItem(item)
        self.list.setItemWidget(item, expandable_widget)

        # Store references
        self.layers[name] = item_data
        self.layer_items[name] = item

    def _on_layer_expand_toggle(self, layer_name, is_expanded):
        """Handle layer expand/collapse"""
        if is_expanded:
            self.expanded_layers.add(layer_name)
        else:
            self.expanded_layers.discard(layer_name)

        self.refresh_points()

    def _on_segment_expand_toggle(self, seg_index, is_expanded):
        """Handle segment expand/collapse"""
        if is_expanded:
            self.expanded_segments.add(seg_index)
        else:
            self.expanded_segments.discard(seg_index)

        self.refresh_points()

    def _make_layer_lock_toggle(self, layer_name):
        def toggle_lock(locked):
            if self.contour_editor:
                self.contour_editor.set_layer_locked(layer_name, locked)
                self.contour_editor.update()
            print(f"[ContourEditor] Set {layer_name} locked = {locked}")

        return toggle_lock

    def _make_add_segment(self, layer_name, layer_item):
        """Create an add segment function"""

        def add_segment():
            print(f"Adding new segment to {layer_name}")
            self.contour_editor.addNewSegment(layer_name)
            self.refresh_points()

            # Ensure layer is expanded
            self.expanded_layers.add(layer_name)

        return add_segment

    def set_layer_visibility(self, layer_name, visible):
        """Set the visibility of a layer"""
        print(f"[ContourEditor] Set {layer_name} visibility to {visible}")
        self.contour_editor.set_layer_visibility(layer_name, visible)
        self.update()

    def get_current_selected_layer(self):
        """Get the currently selected layer name"""
        current_item = self.list.currentItem()
        if current_item:
            item_data = current_item.data(Qt.ItemDataRole.UserRole)
            if item_data and item_data.item_type == 'layer':
                return item_data.layer_name
        return "External"

    def refresh_points(self):
        """Refresh the points display in the list"""
        if not self.contour_editor:
            return

        # Save current state
        selected_item_data = None
        current_item = self.list.currentItem()
        if current_item:
            selected_item_data = current_item.data(Qt.ItemDataRole.UserRole)

        # Remember the active segment index
        active_segment_index = getattr(self.contour_editor.manager, "active_segment_index", None)

        # Clear all items except layer headers and rebuild
        self._rebuild_list()

        # Restore selection
        self._restore_selection(selected_item_data)

        # Restore the active segment UI
        if active_segment_index is not None:
            self.set_active_segment_ui(active_segment_index)

    def _rebuild_list(self):
        """Rebuild the entire list structure"""
        # Clear current list
        self.list.clear()
        self.layer_items = {}
        self.segment_items = {}

        # Recreate layer items
        for layer_name in ["External", "Contour", "Fill"]:
            self._create_layer_item(layer_name)

            # Add segments for this layer if expanded
            if layer_name in self.expanded_layers:
                self._add_segments_for_layer(layer_name)

    def _add_segments_for_layer(self, layer_name):
        """Add segments for a specific layer"""
        if not self.contour_editor:
            return

        segments = self.contour_editor.manager.get_segments()

        for seg_index, segment in enumerate(segments):
            layer = getattr(segment, "layer")
            if layer is None or layer.name != layer_name:
                continue

            self._add_segment_item(seg_index, segment, layer_name)

            # Add points for this segment if expanded
            if seg_index in self.expanded_segments:
                self._add_points_for_segment(seg_index, segment)

    def _add_segment_item(self, seg_index, segment, layer_name):
        """Add a segment item to the list"""
        # Create list item
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 100))

        # Create item data
        item_data = ListItemData('segment', layer_name=layer_name, seg_index=seg_index)
        item.setData(Qt.ItemDataRole.UserRole, item_data)

        # Create segment container
        seg_container = self._create_segment_container(item, seg_index, segment, layer_name)

        # Create expandable segment widget
        expandable_widget = ExpandableSegmentWidget(
            seg_index,
            seg_container,
            self._on_segment_expand_toggle
        )

        # Set the initial expanded state
        is_expanded = seg_index in self.expanded_segments
        expandable_widget.set_expanded(is_expanded)

        # Create indented widget
        indented_widget = IndentedWidget(expandable_widget, indent_level=1)

        # Add to list
        self.list.addItem(item)
        self.list.setItemWidget(item, indented_widget)

        # Store reference
        self.segment_items[seg_index] = item

    def _add_points_for_segment(self, seg_index, segment):
        """Add point items for a specific segment"""
        # Add anchor points
        for i, pt in enumerate(segment.points):
            coords = f"({pt.x():.1f}, {pt.y():.1f})" if isinstance(pt, QPointF) else "Invalid"
            self._add_point_item(f"P{i}", coords, seg_index, i, 'anchor')

        # Add control points
        for i, ctrl in enumerate(segment.controls):
            coords = f"({ctrl.x():.1f}, {ctrl.y():.1f})" if isinstance(ctrl, QPointF) else "Invalid"
            self._add_point_item(f"C{i}", coords, seg_index, i, 'control')

    def _add_point_item(self, label, coordinates, seg_index, point_index, point_type):
        """Add a point item to the list"""
        # Create list item
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 30))

        # Create item data
        item_data = ListItemData('point', seg_index=seg_index, point_index=point_index, point_type=point_type)
        item.setData(Qt.ItemDataRole.UserRole, item_data)

        # Create point widget
        point_widget = PointWidget(label, coordinates)

        # Create indented widget
        indented_widget = IndentedWidget(point_widget, indent_level=2)

        # Add to list
        self.list.addItem(item)
        self.list.setItemWidget(item, indented_widget)

    def _create_segment_container(self, seg_item, seg_index, segment, layer_name):
        def on_visibility(btn):
            visible = btn.isChecked()
            btn.setIcon(QIcon(HIDE_ICON if visible else SHOW_ICON))
            self.contour_editor.manager.set_segment_visibility(seg_index, visible)
            self.contour_editor.update()

        def on_activate():
            self.set_active_segment_ui(seg_index)

        def on_delete():
            self.delete_segment(seg_index)

        def on_settings():
            self._on_settings_button_clicked(seg_index)

        def on_layer_change(new_layer_name):
            self.assign_segment_layer(seg_index, new_layer_name)

        def on_long_press(seg_index):
            print(f"Long press detected on segment {seg_index}!")

        return SegmentButtonsAndComboWidget(
            seg_index=seg_index,
            segment=segment,
            layer_name=layer_name,
            on_visibility=on_visibility,
            on_activate=on_activate,
            on_delete=on_delete,
            on_settings=on_settings,
            on_layer_change=on_layer_change,
            on_long_press = on_long_press
        )

    def _show_settings_dialog(self, seg_index, segment):
        # Prepare input keys for the settings widget
        inputKeys = [key.value for key in GlueSettingKey]
        if GlueSettingKey.GLUE_TYPE.value in inputKeys:
            inputKeys.remove(GlueSettingKey.GLUE_TYPE.value)

        inputKeys.append(RobotSettingKey.VELOCITY.value)
        inputKeys.append(RobotSettingKey.ACCELERATION.value)

        comboEnums = [[GlueSettingKey.GLUE_TYPE.value, GlueType]]

        # Create the settings widget
        from PyQt6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog()
        dialog.setWindowTitle(f"Segment {seg_index} Settings")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)

        widget = SegmentSettingsWidget(inputKeys + [GlueSettingKey.GLUE_TYPE.value], comboEnums, segment=segment,
                                       parent=dialog)
        layout = QVBoxLayout(dialog)
        layout.addWidget(widget)
        dialog.setLayout(layout)

        dialog.exec()  # This will keep the dialog open until closed explicitly

    def _on_settings_button_clicked(self, seg_index):
        segment = self.contour_editor.manager.get_segments()[seg_index]
        layer = getattr(segment, "layer", None)
        layer_name = layer.name if layer else "Unknown"
        print(f"Settings button clicked for segment {seg_index} (Layer: {layer_name})")
        self._show_settings_dialog(seg_index, segment)

    def _restore_selection(self, selected_item_data):
        """Restore the selected item based on saved data"""
        if not selected_item_data:
            return

        # Find matching item in the current list
        for i in range(self.list.count()):
            item = self.list.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)

            if self._items_match(item_data, selected_item_data):
                self.list.setCurrentItem(item)
                break

    def _items_match(self, item_data1, item_data2):
        """Check if two item data objects represent the same item"""
        if not item_data1 or not item_data2:
            return False

        if item_data1.item_type != item_data2.item_type:
            return False

        if item_data1.item_type == 'layer':
            return item_data1.layer_name == item_data2.layer_name
        elif item_data1.item_type == 'segment':
            return item_data1.seg_index == item_data2.seg_index
        elif item_data1.item_type == 'point':
            return (item_data1.seg_index == item_data2.seg_index and
                    item_data1.point_index == item_data2.point_index and
                    item_data1.point_type == item_data2.point_type)

        return False

    def set_active_segment_ui(self, seg_index):
        """Update UI to reflect the active segment"""
        self.contour_editor.manager.set_active_segment(seg_index)
        print(f"[DEBUG] Set active segment to {seg_index}")

        # Update all segment active buttons
        for i in range(self.list.count()):
            item = self.list.item(i)
            item_data = item.data(Qt.ItemDataRole.UserRole)

            if item_data and item_data.item_type == 'segment':
                is_active = item_data.seg_index == seg_index

                # Get the item widget (IndentedWidget)
                indented_widget = self.list.itemWidget(item)
                if indented_widget:
                    # Navigate: IndentedWidget -> ExpandableSegmentWidget -> SegmentButtonsAndComboWidget
                    expandable_segment = indented_widget.layout().itemAt(0).widget()
                    if expandable_segment and hasattr(expandable_segment, 'layout'):
                        # Get the SegmentButtonsAndComboWidget (second item in layout, after expand button)
                        segment_buttons_widget = expandable_segment.layout().itemAt(1).widget()
                        if segment_buttons_widget:
                            # Find the active button specifically
                            active_btn = getattr(segment_buttons_widget, 'active_btn', None)
                            if active_btn:
                                print(
                                    f"Updating active button for segment {item_data.seg_index}, is_active: {is_active}")
                                active_btn.setIcon(QIcon(ACTIVE_ICON if is_active else INACTIVE_ICON))
                            index_label = getattr(segment_buttons_widget, 'index_label', None)

                            if index_label:
                                if is_active:
                                    index_label.setText(f"S{item_data.seg_index}")
                                    index_label.setStyleSheet("""
                                        QPushButton {
                                            background-color: #7E6DAD;
                                            color: white;
                                            border-radius: 15px;
                                            font-weight: bold;
                                            text-align: center;
                                            padding: 0px;
                                            min-width: 50px;
                                            min-height: 50px;
                                            max-width: 50px;
                                            max-height: 50px;
                                        }
                                    """)
                                else:
                                    index_label.setText(f"S{item_data.seg_index}")
                                    index_label.setStyleSheet("""
                                        QPushButton {
                                            background-color: #f0f0f0;
                                            color: #666;
                                            border-radius: 15px;
                                            font-weight: normal;
                                            text-align: center;
                                            padding: 0px;
                                            border: 1px solid #ddd;
                                            min-width: 50px;
                                            min-height: 50px;
                                            max-width: 50px;
                                            max-height: 50px;
                                        }
                                    """)
        self.list.viewport().update()
        if self.contour_editor:
            self.contour_editor.update()

    def delete_segment(self, seg_index):
        """Delete a segment"""
        if self.contour_editor:
            print(f"Deleting segment {seg_index}")
            self.contour_editor.manager.delete_segment(seg_index)
            self.contour_editor.update()
            self.refresh_points()

    def assign_segment_layer(self, seg_index, layer_name):
        """Assign a segment to a different layer"""
        print(f"Assigning Segment {seg_index} to layer '{layer_name}'")
        if self.contour_editor:
            self.contour_editor.manager.assign_segment_layer(seg_index, layer_name)
            self.refresh_points()
            self.contour_editor.update()

    def highlight_selected_point(self, item):
        """Handle point selection and highlighting"""
        if not item or not self.contour_editor:
            print("No item selected.")
            return

        item_data = item.data(Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        print(f"Item clicked: {item_data.item_type}")

        try:
            # Handle segment selection
            if item_data.item_type == 'segment':
                self.set_active_segment_ui(item_data.seg_index)
                return

            # Handle point selection
            elif item_data.item_type == 'point':
                seg_index = item_data.seg_index
                point_index = item_data.point_index
                point_type = item_data.point_type

                if point_type == 'anchor':
                    self.contour_editor.selected_point_info = ('anchor', seg_index, point_index)
                elif point_type == 'control':
                    self.contour_editor.selected_point_info = ('control', seg_index, point_index)

                self.set_active_segment_ui(seg_index)

        except Exception as e:
            print(f"Selection error: {e}")


if __name__ == "__main__":
    import sys
    from unittest.mock import MagicMock

    app = QApplication(sys.argv)
    mock_contour_editor = MagicMock()
    mock_manager = MagicMock()
    mock_contour_editor.manager = mock_manager
    widget = PointManagerWidget(contour_editor=mock_contour_editor)
    widget.show()
    sys.exit(app.exec())