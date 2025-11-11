from PyQt6.QtCore import QSize, QDate, pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QScrollArea, QGridLayout
from PyQt6.QtWidgets import QHBoxLayout, QDateEdit, QPushButton, QSizePolicy, QSplitter, QListWidget, QListWidgetItem, \
    QFrame
from PyQt6.QtWidgets import QScroller

from src.frontend.pl_ui.localization import TranslationKeys, TranslatableMixin
from src.frontend.pl_ui.ui.widgets.FloatingToggleButton import FloatingToggleButton
from src.frontend.pl_ui.ui.windows.gallery.FilterPanel import FilterPanel  # Import our new filter panel
from src.frontend.pl_ui.ui.windows.gallery.SelectionActionBar import SelectionActionBar
from src.frontend.pl_ui.ui.windows.gallery.ThumbnailWidget import ThumbnailWidget
from src.frontend.pl_ui.utils.IconLoader import GALLERY_PLACEHOLDER_ICON, GALLERY_APPLY_BUTTON_ICON, GALLERY_REMOVE_BUTTON_ICON, \
    GALLERY_SELECT_BUTTON_ICON

# Define the resource directory and placeholder image path
PLACEHOLDER_IMAGE_PATH = GALLERY_PLACEHOLDER_ICON
APPLY_BUTTON_ICON_PATH = GALLERY_APPLY_BUTTON_ICON
SELECT_BUTTON_ICON_PATH = GALLERY_SELECT_BUTTON_ICON
REMOVE_BUTTON_ICON_PATH = GALLERY_REMOVE_BUTTON_ICON


class GalleryContent(QFrame, TranslatableMixin):
    edit_requested = pyqtSignal(str)
    def __init__(self, thumbnails=None, workpieces=None, onApplyCallback=None,controller = None):
        QFrame.__init__(self)
        TranslatableMixin.__init_translation__(self)
        
        self.thumbnails = thumbnails
        self.controller = controller
        if self.thumbnails is None:
            self.thumbnails = []
            if workpieces is not None and len(workpieces) != 0:
                from src.frontend.pl_ui.ui.windows.gallery.utils import create_thumbnail_widget_from_workpiece
                self.thumbnails = []
                for wp in workpieces:
                    thumbnail = create_thumbnail_widget_from_workpiece(wp, wp.workpieceId, "default")
                    self.thumbnails.append(thumbnail)
                print("thumbnails", len(self.thumbnails))
            else:
                print("Workpieces is None or Empty")

        self.workpieces = workpieces
        self.onApplyCallback = onApplyCallback
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)  # Enable touch events for the widget

        # Multi-selection state
        self.selection_mode = False
        self.selected_thumbnails = set()
        self.selection_action_bar = None

        # Single selection highlight state
        self.highlighted_thumbnail = None
        self.setWindowTitle("Date Picker and Thumbnail Viewer")
        self.setGeometry(100, 100, 800, 400)
        # self.setStyleSheet("border: none; background: transparent;")  # Transparent background
        self.setStyleSheet("border: none; background: white;")  # Transparent background
        # Store references to the preview image labels and timestamps
        self.preview_images = []
        self.timestamps = []  # List to store timestamps corresponding to the images

        # Store all thumbnail widgets for filtering
        self.all_thumbnails = []
        self.visible_thumbnails = []

        # Main layout: Horizontal layout with two sections (left and right)
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(1)

        # Create a splitter to manage the left and right sections
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Section Layout: Date Picker and Thumbnails
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        left_layout.setSpacing(1)  # Spacing between widgets in the layout

        # Create Date Pickers for "From" and "To" date range
        self.from_date_picker = QDateEdit(self)
        self.from_date_picker.setCalendarPopup(True)
        self.from_date_picker.setDate(QDate.currentDate())  # Set default "from" date to today's date
        self.from_date_picker.setStyleSheet("""
                    QDateEdit {
                        background-color: white;
                        border: 2px solid #905BA9;
                        border-radius: 5px;
                        padding: 4px;
                        color: black;
                    }

                    QCalendarWidget QWidget#qt_calendar_navigationbar {
                        background-color: #905BA9;  /* Your custom color */
                    }
                    QDateEdit::drop-down {
                        background-color: #905BA9;
                        border: none;
                        width: 20px;
                        border-radius: 3px;
                    }

                    QCalendarWidget {
                        background-color: white;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                    }
                    QCalendarWidget QAbstractItemView {
                        background-color: white;
                        selection-background-color: #905BA9;
                        selection-color: white;
                    }
                    QCalendarWidget QToolButton {
                        background-color: #905BA9;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 5px;
                    }


                    QCalendarWidget QToolButton:hover {
                        background-color: #7a4791;
                    }
                    QCalendarWidget QSpinBox {
                        background-color: white;
                        border: 1px solid #ccc;
                        border-radius: 3px;
                    }
                    QMenu {
                    background: white;
                    color: black;
                }
                """)

        self.to_date_picker = QDateEdit(self)
        self.to_date_picker.setCalendarPopup(True)
        self.to_date_picker.setDate(QDate.currentDate())  # Set default "to" date to today's date
        self.to_date_picker.setStyleSheet("""
            QDateEdit {
                background-color: white;
                border: 2px solid #905BA9;
                border-radius: 5px;
                padding: 4px;
                color: black;
            }

             QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #905BA9;  /* Your custom color */
            }

            QDateEdit::drop-down {
                background-color: #905BA9;
                border: none;
                width: 20px;
                border-radius: 3px;
            }

            QMenu {
                background: white;
                color: black;
            }

            QCalendarWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                selection-background-color: #905BA9;
                selection-color: white;
            }
            QCalendarWidget QToolButton {
                background-color: #905BA9;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #7a4791;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)

        # Label for the date range (text set in retranslate())
        self.date_range_label = QLabel(self)

        # Add the date pickers and label to the layout
        left_layout.addWidget(self.date_range_label)
        self.from_label = QLabel()
        left_layout.addWidget(self.from_label)
        left_layout.addWidget(self.from_date_picker)
        self.to_label = QLabel()
        left_layout.addWidget(self.to_label)
        left_layout.addWidget(self.to_date_picker)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(spacer)  # Add spacer to push thumbnails to the top
        spacer.setMaximumHeight(2)
        spacer.setStyleSheet("background-color: #f0f0f0;")  # Transparent spacer

        # Thumbnails Section
        self.thumbnail_layout = QGridLayout()
        self.thumbnail_layout.setSpacing(1)  # Spacing between thumbnails
        self.thumbnail_layout.setHorizontalSpacing(10)  # Horizontal spacing
        self.thumbnail_layout.setVerticalSpacing(10)  # Vertical spacing
        self.thumbnail_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the grid layout

        # Load the placeholder image once
        self.placeholder_pixmap = QPixmap(100, 100)
        self.placeholder_pixmap.load(PLACEHOLDER_IMAGE_PATH)

        self.thumbnail_size = (120, 120)  # Initial thumbnail size (width, height)

        if self.thumbnails is None:
            # Add sample thumbnails (This can be dynamic in a real use case)
            print("No thumbnails, adding placeholders")
            self.add_placeholders()
        else:
            print("Add self.thumbnails")
            for i, t in enumerate(self.thumbnails):
                # Connect the clicked signal to your preview function
                t.clicked.connect(
                    lambda t=t, i=i, timestamp=t.timestamp, filename=t.filename: self.on_thumbnail_clicked(t, i, timestamp, filename))

                # Connect the long press signal
                t.long_pressed.connect(
                    lambda i=i, timestamp=t.timestamp, filename=t.filename: self.on_thumbnail_long_press(i, timestamp, filename))

                # Add the thumbnail widget directly to the grid layout
                self.thumbnail_layout.addWidget(t, i // 4, i % 4)  # 4 columns grid
                self.all_thumbnails.append(t)
                self.visible_thumbnails.append(t)

        # Scrollable Area for Thumbnails with only vertical scroll enabled
        self.scroll_area = QScrollArea(self)
        self.scroll_area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }

            QScrollBar::handle:vertical {
                background: #905ba9;  /* Change this to your desired color */
                min-height: 20px;
                border-radius: 6px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disable horizontal scrollbar
        self.scroll_area.setWidget(self.create_thumbnail_widget())

        # Enable scrolling by pixel
        QScroller.grabGesture(self.scroll_area.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        # Ensure touch events are enabled for the scroll area
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)

        # Add date picker and scroll area for thumbnails to the left section
        left_layout.addWidget(self.scroll_area)

        # Right Section Layout: Preview area
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the right layout
        # right_layout.setSpacing(1)

        # Create horizontal splitter for the right section
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top half: Preview label and images
        preview_layout = QVBoxLayout()
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)  # Align top-center
        preview_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the preview layout
        # preview_layout.setSpacing(1)  # Reduced spacing between label and image

        # Preview label at the top
        # self.preview_label = QLabel("Select a Thumbnail to Preview", self)
        self.preview_label = QLabel("", self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)

        # Preview image section - 50% of the right section's width
        self.preview_image_label = QLabel(self)
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ensure the preview image scales responsively within the layout
        self.preview_image_label.setSizePolicy(QSizePolicy.Policy.Expanding,
                                               QSizePolicy.Policy.Expanding)  # Ensure it takes space

        preview_layout.addWidget(self.preview_image_label)

        # Create a widget for the top section of the right side and set layout
        top_widget = QWidget(self)
        top_widget.setLayout(preview_layout)

        # Set a thin border for the top widget to separate it from the bottom section
        top_widget.setStyleSheet("border-bottom: 2px solid #f0f0f0;")  # Thin border between top and bottom sections

        # Bottom half: List and Button section
        selectedImagesLayout = QVBoxLayout()
        selectedImagesLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the button layout

        # Create a list widget to display the preview image text labels
        self.label_list = QListWidget(self)
        self.label_list.itemClicked.connect(self.display_selected_image)
        self.label_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #905BA9;  /* Custom selection color */
                color: white;               /* Optional: text color */
            }

            QListWidget::item {
                padding: 5px;
            }
        """)
        selectedImagesLayout.addWidget(self.label_list)

        bottom_widget = self.createButtons(selectedImagesLayout)

        # Add the top and bottom widgets to the horizontal splitter in the right layout
        right_splitter.addWidget(top_widget)
        right_splitter.addWidget(bottom_widget)

        # Set the initial sizes of the top and bottom sections to 50% each
        right_splitter.setSizes([self.height() // 2, self.height() // 2])

        # Add the splitter to the right layout
        right_layout.addWidget(right_splitter)

        # Create two widgets for the left and right sections
        left_widget = QWidget(self)
        left_widget.setLayout(left_layout)

        right_widget = QWidget(self)
        right_widget.setLayout(right_layout)

        # Add the widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Set the initial sizes of both sections to be 50% each
        splitter.setSizes([self.width() // 2, self.width() // 2])

        # Add the splitter to the main layout
        main_layout.addWidget(splitter)

        # Connect date pickers' dateChanged signal to filter thumbnails
        self.from_date_picker.dateChanged.connect(self.filter_thumbnails_by_date)
        self.to_date_picker.dateChanged.connect(self.filter_thumbnails_by_date)

        # Create the filter panel
        self.filter_panel = FilterPanel(self)
        self.setup_filter_panel()

        self.createFloatingArrowButton()
        
        # Initialize translations after UI is created
        if hasattr(self, 'retranslate'):
            self.retranslate()

    def tr(self, key, **params):
        """
        Custom translation method that overrides QFrame.tr().
        This ensures our translation system is used instead of PyQt's.
        """
        return self.translator.get(key, **params)

    def setup_filter_panel(self):
        """Setup the filter panel and connect its signals"""
        # Connect filter panel signals
        self.filter_panel.filtersChanged.connect(self.apply_filters)
        self.filter_panel.filtersCleared.connect(self.clear_filters)
        self.filter_panel.closeRequested.connect(self.hide_filter_panel)

    def createFloatingArrowButton(self):
        self.floating_toggle_button = FloatingToggleButton(self, on_toggle_callback=self.toggle_filter_panel)

    def position_floating_button(self):
        """Position the floating button correctly, adjusting for filter panel visibility"""
        if hasattr(self, "floating_toggle_button"):
            panel_width = self.filter_panel.width() if (self.filter_panel and self.filter_panel.is_visible) else 0
            self.floating_toggle_button.reposition(is_panel_visible=self.filter_panel.is_visible,
                                                   panel_width=panel_width)

    def toggle_filter_panel(self):
        """Toggle the filter panel visibility"""
        if self.filter_panel.is_visible:
            self.hide_filter_panel()
        else:
            self.show_filter_panel()

    def position_floating_button(self):
        """Position the floating button correctly, adjusting for filter panel visibility"""
        if hasattr(self, "floating_toggle_button"):
            parent_height = self.height()
            button_height = self.floating_toggle_button.height()
            y = (parent_height - button_height) // 2

            # Adjust x position if filter panel is visible
            filter_panel_width = self.filter_panel.width() if (
                    hasattr(self, "filter_panel") and self.filter_panel.is_visible) else 0
            x = self.width() - self.floating_toggle_button.width() - 10 - filter_panel_width  # 10px from the right edge

            self.floating_toggle_button.move(x, y)
            self.floating_toggle_button.show()

    def show_filter_panel(self):
        self.filter_panel.show_panel()
        self.floating_toggle_button.set_arrow_direction("▶")
        self.position_floating_button()

    def hide_filter_panel(self):
        self.filter_panel.hide_panel()
        self.floating_toggle_button.set_arrow_direction("◀")
        self.position_floating_button()

    def apply_filters(self, id_filter, area_filter, filename_filter):
        """Apply filters based on input fields"""
        id_filter = id_filter.lower().strip()
        area_filter = area_filter.lower().strip()
        filename_filter = filename_filter.lower().strip()

        # Clear current layout
        self.clear_thumbnail_layout()

        # Filter thumbnails
        filtered_thumbnails = []
        for thumbnail in self.all_thumbnails:
            should_show = True

            # Get thumbnail data for filtering
            filename = getattr(thumbnail, 'filename', '').lower()
            thumbnail_id = getattr(thumbnail, 'id', '').lower() if hasattr(thumbnail, 'id') else ''
            thumbnail_area = getattr(thumbnail, 'area', '').lower() if hasattr(thumbnail, 'area') else ''

            # Apply filters
            if id_filter and id_filter not in thumbnail_id:
                should_show = False
            if area_filter and area_filter not in thumbnail_area:
                should_show = False
            if filename_filter and filename_filter not in filename:
                should_show = False

            if should_show:
                filtered_thumbnails.append(thumbnail)

        # Update visible thumbnails and layout
        self.visible_thumbnails = filtered_thumbnails
        self.update_thumbnail_layout()

    def clear_filters(self):
        """Clear all filters and show all thumbnails"""
        # Show all thumbnails
        self.visible_thumbnails = self.all_thumbnails.copy()
        self.update_thumbnail_layout()

    def clear_thumbnail_layout(self):
        """Remove all widgets from the thumbnail layout"""
        while self.thumbnail_layout.count():
            child = self.thumbnail_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def update_thumbnail_layout(self):
        """Update the thumbnail layout with filtered thumbnails"""
        self.clear_thumbnail_layout()

        # Add filtered thumbnails back to layout
        for i, thumbnail in enumerate(self.visible_thumbnails):
            self.thumbnail_layout.addWidget(thumbnail, i // 6, i % 6)  # 6 columns grid

    def createButtons(self, selectedImagesLayout):
        # Select Button
        self.selectButton = QPushButton("", self)
        self.selectButton.setStyleSheet("border:none")
        self.selectButton.setIcon(QIcon(SELECT_BUTTON_ICON_PATH))
        self.removeButton = QPushButton("", self)
        self.removeButton.setStyleSheet("border:none")
        self.removeButton.setIcon(QIcon(REMOVE_BUTTON_ICON_PATH))
        self.applyButton = QPushButton("", self)
        self.applyButton.setStyleSheet("border:none")
        self.applyButton.setIcon(QIcon(APPLY_BUTTON_ICON_PATH))
        self.buttonLayout = QHBoxLayout()

        # Edit Button
        # self.editButton = QPushButton("", self)
        # self.editButton.setStyleSheet("border:none")
        # You can set an icon for the edit button here, e\.g\.:
        # self.editButton.setIcon(QIcon(EDIT_BUTTON_ICON_PATH))
        # self.editButton.setText("✎")  # Simple pencil icon as text, replace wi

        selectedImagesLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.selectButton)
        self.buttonLayout.addWidget(self.removeButton)
        self.buttonLayout.addWidget(self.applyButton)
        # self.buttonLayout.addWidget(self.editButton)

        # Connect the button to the function that adds the preview label to the list
        self.selectButton.clicked.connect(self.add_preview_to_list)
        self.removeButton.clicked.connect(self.remove_preview_from_list)
        self.applyButton.clicked.connect(self.on_apply)
        # self.editButton.clicked.connect(self.onEdit)
        # Create a widget for the bottom section of the right side and set layout
        bottom_widget = QWidget(self)
        bottom_widget.setLayout(selectedImagesLayout)
        return bottom_widget

    def onEdit(self):
        pass

        # if selected_item:
        #     filename = selected_item.text()
        #     print("Selected filename onEdit:", filename)
        #     for thumb in self.all_thumbnails:
        #         print("Thumbnail filename:", getattr(thumb, 'filename', ''), "ID:", getattr(thumb, 'id', 'Unknown'))
        #         if getattr(thumb, 'filename', '') == filename:
        #             print("Selected Workpiece ID:", getattr(thumb, 'id', 'Unknown'))
        #             break

    def add_placeholders(self):
        import random
        import time

        for i in range(100):  # Increased the number of thumbnails for testing vertical scroll
            # Generate a random timestamp
            random_timestamp = time.strftime('%Y-%m-%d %H:%M:%S',
                                             time.localtime(random.randint(1609459200, 1704067200)))

            # Generate a random filename for variety
            filenames = [
                f"document_{i:03d}.pdf",
                f"image_{i:03d}.jpg",
                f"presentation_{i:03d}.pptx",
                f"spreadsheet_{i:03d}.xlsx",
                f"video_{i:03d}.mp4",
                f"archive_{i:03d}.zip"
            ]
            random_filename = random.choice(filenames)

            # Create the thumbnail widget using your custom class
            thumbnail_widget = ThumbnailWidget(
                filename=random_filename,
                pixmap=self.placeholder_pixmap,  # Use your existing placeholder pixmap
                timestamp=random_timestamp,
                parent=self
            )

            # Connect the clicked signal to your preview function
            thumbnail_widget.clicked.connect(
                lambda thumbnail_widget=thumbnail_widget, i=i, timestamp=random_timestamp, filename=random_filename: self.on_thumbnail_clicked(thumbnail_widget, i, timestamp, filename))

            # Connect the long press signal
            thumbnail_widget.long_pressed.connect(
                lambda i=i, timestamp=random_timestamp, filename=random_filename: self.on_thumbnail_long_press(i, timestamp, filename))

            # Add the thumbnail widget directly to the grid layout
            self.thumbnail_layout.addWidget(thumbnail_widget, i // 6, i % 6)  # 6 columns grid

            # Store in our lists for filtering
            self.all_thumbnails.append(thumbnail_widget)
            self.visible_thumbnails.append(thumbnail_widget)

    def create_thumbnail_widget(self):
        """Creates and returns the widget that holds the thumbnails"""
        thumbnail_widget = QWidget(self)
        thumbnail_widget.setLayout(self.thumbnail_layout)
        self.thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align thumbnails to the top
        return thumbnail_widget

    def show_preview(self, index, timestamp, filename):
        """Handles the display of the large preview of the clicked thumbnail"""
        # Display the label for the clicked thumbnail using timestamp
        self.preview_label.setText(f"{filename}")

        # Find the thumbnail widget in visible thumbnails
        thumbnail_widget = None
        for i, thumb in enumerate(self.visible_thumbnails):
            if getattr(thumb, 'filename', '') == filename:
                thumbnail_widget = thumb
                break

        if thumbnail_widget:
            # Retrieve the file name from the thumbnail widget
            file_name = thumbnail_widget.filename if hasattr(thumbnail_widget, 'filename') else "Unknown"
            print(f"File Name: {file_name}")  # Debugging statement

            # Get the pixmap of the clicked thumbnail
            pixmap = getattr(thumbnail_widget, "original_pixmap", None)
            if pixmap:
                self.update_preview_image(pixmap)

    def on_thumbnail_clicked(self, thumbnail_widget, index, timestamp, filename):
        """Handle thumbnail click events - supports both normal and selection modes"""
        if self.selection_mode:
            # In selection mode, clicking toggles selection
            self.toggle_thumbnail_selection(thumbnail_widget)
        else:
            # Normal mode, highlight thumbnail and show preview
            self.highlight_thumbnail(thumbnail_widget)
            self.show_preview(index, timestamp, filename)

    def on_thumbnail_long_press(self, index, timestamp, filename):
        """Handle long press events on thumbnails - Enter selection mode like Android"""
        print(f"Long press detected on thumbnail: {filename} (index: {index}, timestamp: {timestamp})")

        # Find the thumbnail widget
        thumbnail_widget = None
        for thumb in self.visible_thumbnails:
            if getattr(thumb, 'filename', '') == filename:
                thumbnail_widget = thumb
                break

        if thumbnail_widget:
            if not self.selection_mode:
                # Enter selection mode automatically (Android style)
                self.enter_selection_mode(thumbnail_widget)
            else:
                # If already in selection mode, toggle this thumbnail
                self.toggle_thumbnail_selection(thumbnail_widget)

    # Context menu removed - now using Android-style selection mode

    def show_thumbnail_details(self, filename):
        """Show detailed information about the thumbnail with visual workpiece representation"""
        # Find the corresponding workpiece
        workpiece = None
        thumbnail_widget = None
        
        # Find thumbnail by filename
        for thumb in self.all_thumbnails:
            if getattr(thumb, 'filename', '') == filename:
                thumbnail_widget = thumb
                break
        
        # Get workpiece ID from thumbnail
        workpiece_id = getattr(thumbnail_widget, 'workpieceId', None) if thumbnail_widget else None
        
        # Find workpiece in the workpieces list
        if workpiece_id and self.workpieces:
            for wp in self.workpieces:
                if hasattr(wp, 'workpieceId') and str(wp.workpieceId) == str(workpiece_id):
                    workpiece = wp
                    break
        
        if workpiece:
            # Show visual workpiece dialog
            try:
                from src.frontend.pl_ui.ui.windows.gallery.WorkpieceVisualizationDialog import WorkpieceVisualizationDialog
                dialog = WorkpieceVisualizationDialog(workpiece, self)
                dialog.exec()
            except Exception as e:
                print(f"Error showing workpiece visualization: {e}")
                # Fallback to text dialog
                self._show_text_details_fallback(workpiece, filename)
        else:
            # Show error message for missing workpiece
            from PyQt6.QtWidgets import QMessageBox
            from PyQt6.QtGui import QFont
            
            details = f"""Workpiece Details:

Filename: {filename}
Workpiece ID: {workpiece_id if workpiece_id else 'Not found'}

⚠️ Unable to find detailed workpiece information.
This may indicate the workpiece data is not loaded or there's a data inconsistency."""

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Workpiece Details")
            msg_box.setText(details)
            msg_box.setIcon(QMessageBox.Icon.Warning)

            # Set touch-friendly styling
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                    font-size: 16px;
                    padding: 20px;
                    min-width: 400px;
                }
                QMessageBox QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    margin: 8px;
                    min-width: 80px;
                    min-height: 40px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background-color: #106ebe;
                }
            """)

            font = QFont()
            font.setPointSize(14)
            msg_box.setFont(font)

            ok_button = msg_box.addButton("✅ OK", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def _show_text_details_fallback(self, workpiece, filename):
        """Fallback text-based details dialog if visualization fails"""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtGui import QFont
        
        details = f"""Workpiece Details:

ID: {workpiece.workpieceId}
Name: {workpiece.name}
Description: {workpiece.description}
Material: {workpiece.material}
Tool ID: {getattr(workpiece.toolID, 'value', workpiece.toolID) if hasattr(workpiece, 'toolID') else 'N/A'}
Gripper ID: {getattr(workpiece.gripperID, 'value', workpiece.gripperID) if hasattr(workpiece, 'gripperID') else 'N/A'}
Glue Type: {getattr(workpiece.glueType, 'value', workpiece.glueType) if hasattr(workpiece, 'glueType') else 'N/A'}
Program: {getattr(workpiece.program, 'value', workpiece.program) if hasattr(workpiece, 'program') else 'N/A'}
Height: {workpiece.height}
Offset: {workpiece.offset}
Contour Area: {workpiece.contourArea}
Glue Quantity: {getattr(workpiece, 'glueQty', 'N/A')}
Spray Width: {getattr(workpiece, 'sprayWidth', 'N/A')}
Nozzles: {len(workpiece.nozzles) if hasattr(workpiece, 'nozzles') and workpiece.nozzles else 0}
Spray Pattern: {len(workpiece.sprayPattern.get('Contour', [])) if hasattr(workpiece, 'sprayPattern') and isinstance(workpiece.sprayPattern, dict) else 0} contour(s), {len(workpiece.sprayPattern.get('Fill', [])) if hasattr(workpiece, 'sprayPattern') and isinstance(workpiece.sprayPattern, dict) else 0} fill(s)

⚠️ Visualization failed - showing text details."""

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Workpiece Details (Text)")
        msg_box.setText(details)
        msg_box.setIcon(QMessageBox.Icon.Information)

        # Set touch-friendly styling
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                font-size: 16px;
                padding: 20px;
                min-width: 400px;
            }
            QMessageBox QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                margin: 8px;
                min-width: 80px;
                min-height: 40px;
                font-size: 16px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #106ebe;
            }
        """)

        font = QFont()
        font.setPointSize(14)
        msg_box.setFont(font)

        ok_button = msg_box.addButton("✅ OK", QMessageBox.ButtonRole.AcceptRole)
        msg_box.exec()

    def select_thumbnail(self, thumbnail_widget, filename):
        """Select the thumbnail (example action)"""
        print(f"Selecting thumbnail: {filename}")

        # Add visual feedback for selection
        thumbnail_widget.setStyleSheet("""
            ThumbnailWidget {
                border: 3px solid #0078d4;
                border-radius: 5px;
                background-color: #e3f2fd;
                margin: 2px;
            }
        """)

        # You could also add this to a selected items list
        # self.selected_thumbnails.append(thumbnail_widget)

    def delete_thumbnail(self, thumbnail_widget, filename, workpieceId=None):
        """Delete the thumbnail and reorder remaining thumbnails"""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtGui import QFont

        # Create touch-friendly confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Delete Thumbnail')
        msg_box.setText(f'Are you sure you want to delete "{filename}"?')
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Set touch-friendly styling
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                font-size: 16px;
                padding: 20px;
            }
            QMessageBox QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 8px;
                padding: 12px 24px;
                margin: 8px;
                min-width: 80px;
                min-height: 40px;
                font-size: 16px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #0078d4;
            }
            QMessageBox QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

        # Set font for the message
        font = QFont()
        font.setPointSize(14)
        msg_box.setFont(font)

        # Add custom buttons with larger text
        yes_button = msg_box.addButton("✅ Yes, Delete", QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton("❌ Cancel", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_button)

        # Show the dialog
        msg_box.exec()
        reply = msg_box.clickedButton()

        if reply == yes_button:
            print(f"Deleting thumbnail: {filename}")

            # Get workpiece ID from parameter or thumbnail widget
            if workpieceId is None:
                workpieceId = getattr(thumbnail_widget, 'workpieceId', None)

            if workpieceId:
                print(f"Deleting workpiece with ID: {workpieceId}")
                self.controller.handleDeleteWorkpiece(workpieceId)
            else:
                print(f"Warning: No workpieceId found for thumbnail {filename}")

            # Clear highlight if this thumbnail was highlighted
            if self.highlighted_thumbnail == thumbnail_widget:
                self.highlighted_thumbnail = None

            # Remove from layout and lists
            self.thumbnail_layout.removeWidget(thumbnail_widget)
            if thumbnail_widget in self.visible_thumbnails:
                self.visible_thumbnails.remove(thumbnail_widget)
            if thumbnail_widget in self.all_thumbnails:
                self.all_thumbnails.remove(thumbnail_widget)

            # Delete the widget
            thumbnail_widget.deleteLater()

            # Reorder remaining thumbnails to fill gaps
            self.reorder_thumbnails()

    def reorder_thumbnails(self):
        """Reorder all visible thumbnails in the grid layout to fill gaps after deletion"""
        print("Reordering thumbnails to fill gaps...")

        # First, remove all thumbnails from the layout (but don't delete them)
        for thumbnail in self.visible_thumbnails:
            self.thumbnail_layout.removeWidget(thumbnail)

        # Determine the number of columns based on layout context
        # Check if we have real thumbnails (4 columns) or placeholders (6 columns)
        columns = 6  # Default to 6 columns for placeholders

        # If we have real thumbnails (self.thumbnails exists and not empty), use 4 columns
        if hasattr(self, 'thumbnails') and self.thumbnails and len(self.thumbnails) > 0:
            columns = 4
            print("Using 4 columns (real thumbnails mode)")
        else:
            print("Using 6 columns (placeholder mode)")

        # Alternative: check the first visible thumbnail to see if it has real data
        if len(self.visible_thumbnails) > 0:
            first_thumb = self.visible_thumbnails[0]
            # Check if it's a real thumbnail by looking for specific attributes
            if hasattr(first_thumb, 'filename') and not first_thumb.filename.startswith('placeholder'):
                columns = 4
                print("Detected real thumbnails, using 4 columns")

        print(f"Reordering {len(self.visible_thumbnails)} thumbnails using {columns} columns")

        # Re-add thumbnails to the layout in order, filling from top-left
        for i, thumbnail in enumerate(self.visible_thumbnails):
            row = i // columns
            col = i % columns
            self.thumbnail_layout.addWidget(thumbnail, row, col)
            print(f"Repositioned thumbnail '{getattr(thumbnail, 'filename', 'unknown')}' to position ({row}, {col})")

        print(f"Reordering complete. {len(self.visible_thumbnails)} thumbnails arranged in grid")

    def refresh_thumbnail_layout(self):
        """Public method to refresh and reorder the thumbnail layout"""
        self.reorder_thumbnails()

    # ==================== SINGLE SELECTION HIGHLIGHT METHODS ====================

    def highlight_thumbnail(self, thumbnail_widget):
        """Highlight a single thumbnail (normal single-click selection)"""
        print(f"Highlighting thumbnail: {getattr(thumbnail_widget, 'filename', 'unknown')}")

        # Clear previous highlight
        if self.highlighted_thumbnail:
            print(f"Clearing previous highlight: {getattr(self.highlighted_thumbnail, 'filename', 'unknown')}")
            self.clear_highlight(self.highlighted_thumbnail)

        # Set new highlight
        self.highlighted_thumbnail = thumbnail_widget
        self.apply_highlight_style(thumbnail_widget)

    def clear_highlight(self, thumbnail_widget):
        """Remove highlight from a thumbnail"""
        if thumbnail_widget:
            print(f"Clearing highlight from thumbnail: {getattr(thumbnail_widget, 'filename', 'unknown')}")
            # Remove the highlight overlay
            self.remove_highlight_overlay(thumbnail_widget)

    def apply_highlight_style(self, thumbnail_widget):
        """Apply highlight styling to a thumbnail (single selection)"""
        print(f"Applying highlight style to thumbnail: {getattr(thumbnail_widget, 'filename', 'unknown')}")

        # Create a highlight overlay frame
        self.create_highlight_overlay(thumbnail_widget)

    def create_highlight_overlay(self, thumbnail_widget):
        """Create a visual highlight overlay on the thumbnail"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QPalette, QColor

        # Remove any existing highlight overlay
        self.remove_highlight_overlay(thumbnail_widget)

        # Method 1: Try setting the thumbnail widget's own background
        palette = thumbnail_widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F3E8FF"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#F3E8FF"))
        thumbnail_widget.setPalette(palette)
        thumbnail_widget.setAutoFillBackground(True)

        # Method 2: Create a simple colored border overlay
        highlight_overlay = QLabel(thumbnail_widget)
        highlight_overlay.setObjectName("highlight_overlay")
        highlight_overlay.setStyleSheet("""
            QLabel#highlight_overlay {
                border: 6px solid #905BA9;
                border-radius: 10px;
                background-color: transparent;
            }
        """)

        # Position overlay to cover the entire thumbnail
        highlight_overlay.setGeometry(-3, -3, thumbnail_widget.width() + 6, thumbnail_widget.height() + 6)
        highlight_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        highlight_overlay.show()

        # Method 3: Force repaint
        thumbnail_widget.update()
        thumbnail_widget.repaint()

    def remove_highlight_overlay(self, thumbnail_widget):
        """Remove highlight overlay from thumbnail"""
        if thumbnail_widget:
            # Find and remove existing overlay
            overlay = thumbnail_widget.findChild(QLabel, "highlight_overlay")
            if overlay:
                overlay.deleteLater()

            # Reset palette to default
            thumbnail_widget.setPalette(self.palette())
            thumbnail_widget.setAutoFillBackground(False)
            thumbnail_widget.update()

    def clear_all_highlights(self):
        """Clear all single-selection highlights"""
        if self.highlighted_thumbnail:
            self.clear_highlight(self.highlighted_thumbnail)
            self.highlighted_thumbnail = None

    # ==================== MULTI-SELECTION METHODS ====================

    def enter_selection_mode(self, initial_thumbnail=None):
        """Enter multi-selection mode"""
        print("Entering multi-selection mode")
        self.selection_mode = True
        self.selected_thumbnails.clear()

        # Clear any single-selection highlight when entering multi-selection mode
        self.clear_all_highlights()

        # Select the initial thumbnail if provided
        if initial_thumbnail:
            self.selected_thumbnails.add(initial_thumbnail)
            self.apply_selection_style(initial_thumbnail, True)

        # Create and show selection action bar
        self.create_selection_action_bar()
        self.update_selection_counter()

    def exit_selection_mode(self):
        """Exit multi-selection mode"""
        print("Exiting multi-selection mode")
        self.selection_mode = False

        # Clear all selections and restore original styles
        for thumbnail in self.selected_thumbnails:
            self.apply_selection_style(thumbnail, False)
        self.selected_thumbnails.clear()

        # Hide selection action bar
        if self.selection_action_bar:
            self.selection_action_bar.hide_action_bar()

    def toggle_thumbnail_selection(self, thumbnail_widget):
        """Toggle selection state of a thumbnail"""
        if thumbnail_widget in self.selected_thumbnails:
            self.selected_thumbnails.remove(thumbnail_widget)
            self.apply_selection_style(thumbnail_widget, False)
            print(f"Deselected thumbnail: {getattr(thumbnail_widget, 'filename', 'unknown')}")
        else:
            self.selected_thumbnails.add(thumbnail_widget)
            self.apply_selection_style(thumbnail_widget, True)
            print(f"Selected thumbnail: {getattr(thumbnail_widget, 'filename', 'unknown')}")

        self.update_selection_counter()

    def apply_selection_style(self, thumbnail_widget, selected):
        """Apply or remove selection styling to a thumbnail (Android style)"""
        if selected:
            # Android-style selection with checkmark overlay
            thumbnail_widget.setStyleSheet("""
                ThumbnailWidget {
                    border: 3px solid #2196F3;
                    border-radius: 8px;
                    background-color: #E3F2FD;
                    margin: 2px;
                }
                ThumbnailWidget:hover {
                    border: 3px solid #1976D2;
                    background-color: #BBDEFB;
                }
            """)

            # Add checkmark overlay (Android style)
            self.add_selection_checkmark(thumbnail_widget)
        else:
            # Restore original style
            thumbnail_widget.setStyleSheet("""
                ThumbnailWidget {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: white;
                    margin: 2px;
                }
                ThumbnailWidget:hover {
                    border: 2px solid #0078d4;
                    background-color: #f5f5f5;
                }
            """)

            # Remove checkmark overlay
            self.remove_selection_checkmark(thumbnail_widget)

    def add_selection_checkmark(self, thumbnail_widget):
        """Add Android-style checkmark overlay to selected thumbnail"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt

        # Remove existing checkmark if any
        self.remove_selection_checkmark(thumbnail_widget)

        # Create checkmark label
        checkmark = QLabel("✓", thumbnail_widget)
        checkmark.setObjectName("selection_checkmark")
        checkmark.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                border-radius: 12px;
                padding: 4px;
                font-weight: bold;
                font-size: 16px;
            }
        """)

        # Position checkmark in top-right corner
        checkmark.resize(24, 24)
        checkmark.move(thumbnail_widget.width() - 28, 4)
        checkmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkmark.show()

    def remove_selection_checkmark(self, thumbnail_widget):
        """Remove checkmark overlay from thumbnail"""
        from PyQt6.QtWidgets import QLabel
        checkmark = thumbnail_widget.findChild(QLabel, "selection_checkmark")
        if checkmark:
            checkmark.deleteLater()

    def create_selection_action_bar(self):
        """Create Android-style action bar for multi-selection"""
        if self.selection_action_bar:
            self.selection_action_bar.show_action_bar(self)
            return

        # Create new action bar
        self.selection_action_bar = SelectionActionBar()
        self.selection_action_bar.applyStyles()

        # Connect signals
        self.selection_action_bar.exitRequested.connect(self.exit_selection_mode)
        self.selection_action_bar.showDetailsRequested.connect(self.show_single_item_details)
        self.selection_action_bar.editItemRequested.connect(self.edit_single_item)
        self.selection_action_bar.deleteRequested.connect(self.delete_selected_thumbnails)

        # Show the action bar
        self.selection_action_bar.show_action_bar(self)


    def update_selection_counter(self):
        """Update the selection counter label and action buttons"""
        if self.selection_action_bar:
            count = len(self.selected_thumbnails)
            self.selection_action_bar.update_selection_count(count)


    def show_single_item_details(self):
        """Show details for single selected item"""
        if len(self.selected_thumbnails) != 1:
            return

        thumbnail = list(self.selected_thumbnails)[0]
        filename = getattr(thumbnail, 'filename', 'Unknown')

        # Use the enhanced show_thumbnail_details method
        self.show_thumbnail_details(filename)

    def edit_single_item(self):
        """Edit single selected item"""
        if len(self.selected_thumbnails) != 1:
            return

        thumbnail = list(self.selected_thumbnails)[0]
        filename = getattr(thumbnail, 'filename', 'Unknown')
        workpieceId = getattr(thumbnail, 'workpieceId', None)
        result, workpiece = self.controller.getWorkpieceById(workpieceId)
        self.edit_requested.emit(workpieceId)
        if not result:
            # show warning dialog
            from PyQt6.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Edit Item")
            msg_box.setText(f"Cannot edit item '{filename}'. Workpiece data not found.")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()
            return

        # TODO: Implement single item edit functionality
        # For now, show a placeholder message
        from PyQt6.QtWidgets import QMessageBox

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Editing workpiece:")
        msg_box.setText(f"{workpiece}")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def select_all_thumbnails(self):
        """Select all visible thumbnails"""
        self.selected_thumbnails.clear()
        for thumbnail in self.visible_thumbnails:
            self.selected_thumbnails.add(thumbnail)
            self.apply_selection_style(thumbnail, True)

        self.update_selection_counter()
        print(f"Selected all {len(self.selected_thumbnails)} thumbnails")

    def delete_selected_thumbnails(self):
        """Delete all selected thumbnails with confirmation"""
        if len(self.selected_thumbnails) == 0:
            return

        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtGui import QFont

        count = len(self.selected_thumbnails)

        # Create touch-friendly confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Delete Multiple Thumbnails')
        msg_box.setText(f'Are you sure you want to delete {count} selected thumbnails?')
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Apply touch-friendly styling
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                font-size: 16px;
                padding: 20px;
            }
            QMessageBox QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 8px;
                padding: 12px 24px;
                margin: 8px;
                min-width: 100px;
                min-height: 40px;
                font-size: 16px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #0078d4;
            }
        """)

        font = QFont()
        font.setPointSize(14)
        msg_box.setFont(font)

        yes_button = msg_box.addButton(f"✅ Yes, Delete {count}", QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton("❌ Cancel", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_button)

        msg_box.exec()
        reply = msg_box.clickedButton()

        if reply == yes_button:
            print(f"Deleting {count} selected thumbnails")

            # Store thumbnails to delete (to avoid modifying set during iteration)
            thumbnails_to_delete = list(self.selected_thumbnails)

            for thumbnail in thumbnails_to_delete:
                # Get workpiece ID if available
                workpieceId = getattr(thumbnail, 'workpieceId', None)
                if workpieceId is None:
                    print(f"Warning: No workpieceId found for thumbnail: {getattr(thumbnail, 'filename', 'unknown')}")
                else:
                    print(f"Deleting workpiece with ID: {workpieceId}")
                    self.controller.handleDeleteWorkpiece(workpieceId)

                # Clear highlight if this thumbnail was highlighted
                if self.highlighted_thumbnail == thumbnail:
                    self.highlighted_thumbnail = None

                # Remove from layout and lists
                self.thumbnail_layout.removeWidget(thumbnail)
                if thumbnail in self.visible_thumbnails:
                    self.visible_thumbnails.remove(thumbnail)
                if thumbnail in self.all_thumbnails:
                    self.all_thumbnails.remove(thumbnail)

                # Delete the widget
                thumbnail.deleteLater()

            # Clear selection and exit selection mode
            self.exit_selection_mode()

            # Reorder remaining thumbnails
            self.reorder_thumbnails()

            print(f"Successfully deleted {count} thumbnails")

    def filter_thumbnails_by_date(self):
        """Filters thumbnails based on the selected date range."""
        print("Filtering thumbnails by date...")  # Debugging statement

        # Get the selected date range
        from_date = self.from_date_picker.date()
        to_date = self.to_date_picker.date()
        print(f"From: {from_date} To: {to_date}")

        # Apply date filtering logic here
        # This would need to be implemented based on your thumbnail data structure

    def get_thumbnail_timestamp(self, index):
        """Returns the timestamp of the thumbnail at the given index"""
        return self.timestamps[index]

    def add_preview_to_list(self):
        """Adds the preview image label to the list when the Select button is clicked"""
        if self.preview_image_label.pixmap() and self.preview_label.text():
            filename = self.preview_label.text()
            item = QListWidgetItem(filename)
            # 💡 Store the pixmap in item data
            item.setData(Qt.ItemDataRole.UserRole, self.preview_image_label.pixmap())
            self.label_list.addItem(item)

    def remove_preview_from_list(self):
        """Removes the selected preview image from the list."""
        selected_item = self.label_list.currentItem()

        if selected_item:
            row = self.label_list.row(selected_item)
            self.label_list.takeItem(row)

            # Update the preview image to the last item in the list or clear it
            if self.label_list.count() > 0:
                last_item = self.label_list.item(self.label_list.count() - 1)
                self.display_selected_image(last_item)
            else:
                self.preview_label.setText("Select a Thumbnail to Preview")
                self.preview_image_label.clear()

    def on_apply(self):
        if self.onApplyCallback is not None:
            if self.label_list.count() == 0:
                print("No items selected for apply.")
                return

            # Get first item in the list
            first_item = self.label_list.item(0)
            filename = first_item.text()
            thumbnail_pixmap = first_item.data(Qt.ItemDataRole.UserRole)

            print("First selected filename:", filename)
            if thumbnail_pixmap:
                print("Thumbnail size:", thumbnail_pixmap.size())
            else:
                print("No thumbnail found for this item.")

            # Pass both filename and thumbnail to callback
            # self.onApplyCallback(filename, thumbnail_pixmap)
            try:
                self.onApplyCallback(filename, thumbnail_pixmap)
            except TypeError:
                # Callback may accept only filename
                try:
                    self.onApplyCallback(filename)
                except Exception as e:
                    print("Error calling onApplyCallback:", e)
        else:
            print("Apply Button Pressed")

    def display_selected_image(self, item):
        """Displays the corresponding image for the clicked list item"""
        filename = item.text()
        self.preview_label.setText(f"{filename}")

        # 🔍 Get the pixmap from the item's stored data
        pixmap = item.data(Qt.ItemDataRole.UserRole)
        if pixmap:
            self.update_preview_image(pixmap)

    def update_preview_image(self, pixmap):
        """Updates the preview image with the given pixmap"""
        if pixmap:
            target_size = QSize(400, 300)  # Fixed size for preview
            scaled_pixmap = pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Handle the resizing of the window to adjust thumbnail sizes, preview image, and select button."""
        super().resizeEvent(event)

        # Move the floating arrow button to stay at the center right
        self.position_floating_button()

        # Update filter panel position if it exists and is visible
        if self.filter_panel and self.filter_panel.is_visible:
            self.filter_panel.update_position()

        # Resize the selection action bar if it exists
        if self.selection_action_bar:
            self.selection_action_bar.resize_to_parent(self.width())

        # Resize the preview image dynamically to take 50% of the right layout width
        right_layout_width = int(self.width() * 0.25)  # Ensure it's an integer for the scaled method

        # Use the last available pixmap if it exists
        if self.preview_images:
            self.update_preview_image(self.preview_images[-1])

        # Get the available width for the thumbnails section
        available_width = self.width() * 0.4  # Use 40% of the window width for thumbnails
        num_columns = 4  # Number of columns in the grid layout

        # Calculate the new thumbnail size based on available width
        thumbnail_width = (available_width - (num_columns + 1) * 10) / num_columns  # Subtracting the spacing
        self.thumbnail_size = (thumbnail_width, thumbnail_width)  # Set width and height equal for square thumbnails

        # Update the size of the thumbnail buttons
        for row in range(self.thumbnail_layout.rowCount()):
            for col in range(self.thumbnail_layout.columnCount()):
                # Get the layout item in the grid and check if it exists
                item = self.thumbnail_layout.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    if isinstance(widget, QPushButton):
                        widget.setFixedSize(QSize(*self.thumbnail_size))  # Convert tuple to QSize

        # Resize the select button dynamically
        buttonSize = int(self.width() * 0.05)  # Set the size to 5% of the window width
        self.selectButton.setIconSize(QSize(buttonSize, buttonSize))  # Adjust icon size
        self.selectButton.setFixedSize(QSize(buttonSize, buttonSize))  # Adjust button size

        self.removeButton.setIconSize(QSize(buttonSize, buttonSize))  # Adjust icon size
        self.removeButton.setFixedSize(QSize(buttonSize, buttonSize))  # Adjust button size

        self.applyButton.setIconSize(QSize(buttonSize, buttonSize))
        self.applyButton.setFixedSize(QSize(buttonSize, buttonSize))

        # self.editButton.setIconSize(QSize(buttonSize, buttonSize))
        # self.editButton.setFixedSize(QSize(buttonSize, buttonSize))

        event.accept()

    def retranslate(self):
        """Update all text labels for language changes - called automatically"""
        self.date_range_label.setText(f"{self.tr(TranslationKeys.Date.SELECT_DATE_RANGE)}:")
        self.from_label.setText(f"{self.tr(TranslationKeys.Date.FROM)}:")
        self.to_label.setText(f"{self.tr(TranslationKeys.Date.TO)}:")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    gallery_content = GalleryContent()
    gallery_content.show()
    sys.exit(app.exec())
