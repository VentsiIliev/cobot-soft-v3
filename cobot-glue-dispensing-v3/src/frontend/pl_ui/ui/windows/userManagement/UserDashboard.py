import sys
import qrcode
import os
from PyQt6.QtGui import QPixmap

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QComboBox, QLabel,
                             QDialog, QFormLayout, QMessageBox, QHeaderView,
                             QGroupBox, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor

# Import your existing classes (adjust paths as needed)
from modules.shared.shared.user.User import User, Role, UserField
from modules.shared.shared.user.UserService import UserService
from modules.shared.shared.user.CSVUsersRepository import CSVUsersRepository
from src.frontend.pl_ui.localization import TranslationKeys, TranslatableWidget, TranslatableDialog
from src.frontend.pl_ui.ui.widgets.ToastWidget import ToastWidget
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton


class UserTableModel:
    """Model to handle user data for the table"""

    def __init__(self, users=None):
        self.users = users or []
        self.headers = ["ID", "First Name", "Last Name", "Password", "Role", "Email"]

    def get_user_data(self, user):
        """Convert user object to list for table display"""
        try:
            # # Debug: Print user attributes
            # print(f"User object: {user}")
            # print(f"User type: {type(user)}")
            # print(f"User id: {getattr(user, 'id', 'NO ID')}")
            # print(f"User firstName: {getattr(user, 'firstName', 'NO FIRSTNAME')}")
            # print(f"User lastName: {getattr(user, 'lastName', 'NO LASTNAME')}")
            # print(f"User password: {getattr(user, 'password', 'NO PASSWORD')}")
            # print(f"User role: {getattr(user, 'role', 'NO ROLE')}")

            role_display = "Unknown"
            if hasattr(user, 'role'):
                if hasattr(user.role, 'value'):
                    role_display = user.role.value
                else:
                    role_display = str(user.role)

            data = [
                str(getattr(user, 'id', '')),
                str(getattr(user, 'firstName', '')),
                str(getattr(user, 'lastName', '')),
                "****",  # Hide password for security
                role_display,
                str(getattr(user, 'email', ''))
            ]
            # print(f"Converted user data: {data}")
            return data
        except Exception as e:
            # print(f"Error in get_user_data: {e}")
            return ["Error", "Error", "Error", "Error", "Error", "Error"]

    def update_users(self, users):
        """Update the user list"""
        self.users = users


class UserDialog(TranslatableDialog):
    """Dialog for adding/editing users"""

    def __init__(self, parent=None, user=None, title=""):
        super().__init__(auto_retranslate=False)
        self.user = user
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 350)
        self.setup_ui()
        
        # Initialize translations after UI is created
        self.init_translations()

        if user:
            self.populate_fields()

    def setup_ui(self):
        layout = QFormLayout()

        self.id_edit = FocusLineEdit(self.window())
        self.first_name_edit = FocusLineEdit(self.window())
        self.last_name_edit = FocusLineEdit(self.window())
        self.password_edit = FocusLineEdit(self.window())
        self.password_edit.setEchoMode(FocusLineEdit.EchoMode.Password)

        self.role_combo = QComboBox()
        for role in Role:
            self.role_combo.addItem(role.value, role)

        self.email_edit = FocusLineEdit(self.window())
        self.email_edit.setPlaceholderText("user@example.com")

        # Create labels without text - text will be set in retranslate()
        self.id_label = QLabel()
        self.first_name_label = QLabel()
        self.last_name_label = QLabel()
        self.password_label = QLabel()
        self.role_label = QLabel()
        self.email_label = QLabel()
        
        layout.addRow(self.id_label, self.id_edit)
        layout.addRow(self.first_name_label, self.first_name_edit)
        layout.addRow(self.last_name_label, self.last_name_edit)
        layout.addRow(self.password_label, self.password_edit)
        layout.addRow(self.role_label, self.role_combo)
        layout.addRow(self.email_label, self.email_edit)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = MaterialButton()
        self.cancel_button = MaterialButton()

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addRow(button_layout)

        self.setLayout(layout)

        # Connect signals
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def retranslate(self):
        """Update all text labels for language changes - called automatically"""
        if hasattr(self, 'id_label') and self.id_label:
            self.id_label.setText(self.tr(TranslationKeys.User.ID) + ":")
        if hasattr(self, 'first_name_label') and self.first_name_label:
            self.first_name_label.setText(self.tr(TranslationKeys.User.FIRST_NAME) + ":")
        if hasattr(self, 'last_name_label') and self.last_name_label:
            self.last_name_label.setText(self.tr(TranslationKeys.User.LAST_NAME) + ":")
        if hasattr(self, 'password_label') and self.password_label:
            self.password_label.setText(self.tr(TranslationKeys.Auth.PASSWORD) + ":")
        if hasattr(self, 'role_label') and self.role_label:
            self.role_label.setText(self.tr(TranslationKeys.User.ROLE) + ":")
        if hasattr(self, 'email_label') and self.email_label:
            self.email_label.setText(self.tr(TranslationKeys.User.EMAIL) + ":")
        if hasattr(self, 'save_button') and self.save_button:
            self.save_button.setText("Save")
        if hasattr(self, 'cancel_button') and self.cancel_button:
            self.cancel_button.setText("Cancel")

    def populate_fields(self):
        """Populate fields when editing existing user"""
        if self.user:
            self.id_edit.setText(str(self.user.id))
            self.id_edit.setReadOnly(True)  # Don't allow ID changes
            self.first_name_edit.setText(self.user.firstName)
            self.last_name_edit.setText(self.user.lastName)
            self.password_edit.setText(self.user.password)

            # Set role combo
            for i in range(self.role_combo.count()):
                if self.role_combo.itemData(i) == self.user.role:
                    self.role_combo.setCurrentIndex(i)
                    break

    def get_user_data(self):
        """Get user data from form"""
        try:
            user_id = int(self.id_edit.text().strip())
        except ValueError:
            raise ValueError("ID must be a valid number")

        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        password = self.password_edit.text().strip()
        role = self.role_combo.currentData()
        email = self.email_edit.text().strip() or None

        if not all([first_name, last_name, password]):
            raise ValueError("All fields are required")

        return {
            'id': user_id,
            'firstName': first_name,
            'lastName': last_name,
            'password': password,
            'role': role,
            'email': email
        }

    # def update_language(self):
    #     """Update all UI texts to current language"""
    #     self.id_label.setText(self.langLoader.get_message(Message.ID) + ":")
    #     self.first_name_label.setText(self.langLoader.get_message(Message.FIRST_NAME) + ":")
    #     self.last_name_label.setText(self.langLoader.get_message(Message.LAST_NAME) + ":")
    #     self.password_label.setText(self.langLoader.get_message(Message.PASSWORD) + ":")
    #     self.role_label.setText(self.langLoader.get_message(Message.ROLE) + ":")
    #
    #     self.save_button.setText(self.langLoader.get_message(Message.SAVE))
    #     self.cancel_button.setText(self.langLoader.get_message(Message.CANCEL))


class UserManagementWidget(TranslatableWidget):
    """Main widget for user management"""

    def __init__(self, csv_file_path="users.csv"):
        super().__init__(auto_retranslate=False)
        self.csv_file_path = csv_file_path
        self.setup_service()
        self.setup_ui()
        self.load_users()
        self.setup_styles()
        
        # Initialize translations after UI is created
        self.init_translations()

    def setup_service(self):
        """Initialize the user service and repository"""
        user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME,
                       UserField.PASSWORD, UserField.ROLE, UserField.EMAIL]
        self.repository = CSVUsersRepository(self.csv_file_path, user_fields, User)
        self.service = UserService(self.repository)
        self.model = UserTableModel()

    def setup_inline_user_form(self):
        """Setup the inline user form"""
        self.user_form_group = QGroupBox("Add/Edit User")
        self.user_form_layout = QFormLayout()

        # Form fields
        self.form_id_edit = FocusLineEdit(self.window())
        self.form_first_name_edit = FocusLineEdit(self.window())
        self.form_last_name_edit = FocusLineEdit(self.window())
        self.form_password_edit = FocusLineEdit(self.window())
        self.form_password_edit.setEchoMode(FocusLineEdit.EchoMode.Password)
        self.form_email_edit = FocusLineEdit(self.window())
        self.form_email_edit.setPlaceholderText("user@example.com")

        self.form_role_combo = QComboBox()
        for role in Role:
            self.form_role_combo.addItem(role.value, role)

        # Form labels
        self.form_id_label = QLabel("ID:")
        self.form_first_name_label = QLabel("First Name:")
        self.form_last_name_label = QLabel("Last Name:")
        self.form_password_label = QLabel("Password:")
        self.form_role_label = QLabel("Role:")
        self.form_email_label = QLabel("Email:")

        # Add fields to form
        self.user_form_layout.addRow(self.form_id_label, self.form_id_edit)
        self.user_form_layout.addRow(self.form_first_name_label, self.form_first_name_edit)
        self.user_form_layout.addRow(self.form_last_name_label, self.form_last_name_edit)
        self.user_form_layout.addRow(self.form_password_label, self.form_password_edit)
        self.user_form_layout.addRow(self.form_role_label, self.form_role_combo)
        self.user_form_layout.addRow(self.form_email_label, self.form_email_edit)

        # Form buttons
        form_button_layout = QHBoxLayout()
        self.form_save_button = MaterialButton("Save")
        self.form_cancel_button = MaterialButton("Cancel")

        form_button_layout.addWidget(self.form_save_button)
        form_button_layout.addWidget(self.form_cancel_button)
        self.user_form_layout.addRow(form_button_layout)

        self.user_form_group.setLayout(self.user_form_layout)
        self.main_layout.addWidget(self.user_form_group)

        # Connect form signals
        self.form_save_button.clicked.connect(self.save_user_form)
        self.form_cancel_button.clicked.connect(self.hide_user_form)

        # Initially hide the form
        self.user_form_group.hide()
        self.current_editing_user = None

    def setup_ui(self):
        """Setup the user interface"""
        self.main_layout = QVBoxLayout()

        # Title - create empty, text will be set in retranslate()
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.title_label.setFont(font)
        self.main_layout.addWidget(self.title_label)

        # Add inline user form (initially hidden)
        self.setup_inline_user_form()

        # Filter section
        self.filter_group = QGroupBox()
        self.filter_layout = QHBoxLayout()

        self.filter_by_label = QLabel()
        self.filter_layout.addWidget(self.filter_by_label)
        
        self.filter_column_combo = QComboBox()
        self.filter_layout.addWidget(self.filter_column_combo)

        self.filter_input = FocusLineEdit(self.window())
        self.filter_layout.addWidget(self.filter_input)

        self.filter_button = MaterialButton("Filter")
        self.clear_filter_button = MaterialButton("Clear")
        self.filter_layout.addWidget(self.filter_button)
        self.filter_layout.addWidget(self.clear_filter_button)

        self.filter_group.setLayout(self.filter_layout)
        self.main_layout.addWidget(self.filter_group)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "Password", "Role", "Email"])

        # Make table look better and ensure visibility
        self.header = self.table.horizontalHeader()
        self.header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(True)

        # Set minimum size to ensure table is visible
        self.table.setMinimumHeight(200)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_layout.addWidget(self.table)

        # Buttons
        self.button_group = QGroupBox("")
        self.button_layout = QHBoxLayout()

        self.add_button = MaterialButton("Add User")
        self.edit_button = MaterialButton("Edit User")
        self.delete_button = MaterialButton("Delete User")
        self.refresh_button = MaterialButton("Refresh")
        self.test_button = MaterialButton("Generate QR")

        # Style buttons
        self.buttons = [self.add_button, self.edit_button, self.delete_button, self.refresh_button,self.test_button]
        for button in self.buttons:
            button.setMinimumHeight(50)
            self.button_layout.addWidget(button)

        self.button_group.setLayout(self.button_layout)
        self.main_layout.addWidget(self.button_group)

        # Status label
        self.status_label = QLabel()
        self.main_layout.addWidget(self.status_label)

        self.setLayout(self.main_layout)

        # Connect signals
        self.add_button.clicked.connect(self.show_add_user_form)
        self.edit_button.clicked.connect(self.show_edit_user_form)
        self.delete_button.clicked.connect(self.delete_user)
        self.refresh_button.clicked.connect(self.load_users)
        self.filter_button.clicked.connect(self.apply_filter)
        self.clear_filter_button.clicked.connect(self.clear_filter)
        self.filter_input.returnPressed.connect(self.apply_filter)

        # Enable/disable edit and delete buttons based on selection
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # Test button already created above and added to layout
        self.test_button.clicked.connect(self.generateQrCode)

        # Initially disable edit and delete buttons
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def setup_styles(self):
        """Apply custom styles to the widget"""
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
            }

            QLabel {
                color: black;
            }

            QHeaderView::section {
                background-color: #f0f0f0;
                color: black;
                padding: 4px;
                border: 1px solid #d0d0d0;
            }

            QScrollBar:vertical, QScrollBar:horizontal {
                background: #e0e0e0;
            }

            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #c0c0c0;
            }

            QScrollBar::add-line, QScrollBar::sub-line {
                background: #d0d0d0;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }

            QPushButton {
                background-color: #905BA9;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #7A4D92;
            }

            QPushButton:pressed {
                background-color: #644080;
            }

            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }

            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f5f5f5;
                color: black;
            }

            QTableWidget::item:selected {
                background-color: #905BA9;
                color: white;
            }

            FocusLineEdit, QComboBox {
                background-color: white;
                color: black;
            }
        """)

    def load_users(self):
        """Load users from the repository and display in table"""
        try:
            users = self.repository.get_all()
            # print(f"Loaded {len(users)} users from repository")  # Debug
            for i, user in enumerate(users):
                print(f"User {i}: {user}")  # Debug

            self.model.update_users(users)
            self.populate_table(users)
            self.status_label.setText(f"Loaded {len(users)} users")
        except Exception as e:
            # print(f"Exception in load_users: {e}")  # Debug
            self.show_error("Error loading users")
            self.status_label.setText("Error loading users")

    def populate_table(self, users):
        """Populate the table with user data"""
        # print(f"Populating table with {len(users)} users")  # Debug

        # Clear the table first
        self.table.clearContents()
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            try:
                # print(f"Processing user {row}: {user}")  # Debug
                user_data = self.model.get_user_data(user)
                # print(f"User data for row {row}: {user_data}")  # Debug

                for col, data in enumerate(user_data):
                    item = QTableWidgetItem(str(data))
                    item.setData(Qt.ItemDataRole.UserRole, user)  # Store user object
                    # Set item flags to make it selectable and enabled
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.table.setItem(row, col, item)
                    # print(f"Set item at ({row}, {col}): {data}")  # Debug
            except Exception as e:
                print(f"Error processing user {row}: {e}")  # Debug
                continue

        # Force table refresh
        self.table.viewport().update()
        self.table.repaint()

        # print(f"Table now has {self.table.rowCount()} rows")  # Debug

        # Check if items are actually there
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    print(f"Verification - Item at ({row}, {col}): {item.text()}")
                else:
                    print(f"Verification - No item at ({row}, {col})")

    def show_add_user_form(self):
        """Show the inline form for adding a new user"""
        self.current_editing_user = None
        self.clear_user_form()
        self.form_id_edit.setReadOnly(False)
        self.user_form_group.setTitle("Add New User")
        self.user_form_group.show()

    def show_edit_user_form(self):
        """Show the inline form for editing selected user"""
        current_row = self.table.currentRow()
        if current_row < 0:
            toast = ToastWidget(self, "Please select a user to edit", 5)
            toast.show()
            return

        user = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        self.current_editing_user = user
        self.populate_user_form(user)
        self.form_id_edit.setReadOnly(True)  # Don't allow ID changes
        self.user_form_group.setTitle("Edit User")
        self.user_form_group.show()

    def hide_user_form(self):
        """Hide the user form"""
        self.user_form_group.hide()
        self.current_editing_user = None

    def clear_user_form(self):
        """Clear all form fields"""
        self.form_id_edit.clear()
        self.form_first_name_edit.clear()
        self.form_last_name_edit.clear()
        self.form_password_edit.clear()
        self.form_email_edit.clear()
        self.form_role_combo.setCurrentIndex(0)

    def populate_user_form(self, user):
        """Populate form fields with user data"""
        self.form_id_edit.setText(str(user.id))
        self.form_first_name_edit.setText(user.firstName)
        self.form_last_name_edit.setText(user.lastName)
        self.form_password_edit.setText(user.password)

        # Handle email field safely (might be NaN/float from CSV)
        email = getattr(user, 'email', '')
        if email is None or (isinstance(email, float) and str(email) == 'nan'):
            email = ''
        self.form_email_edit.setText(str(email))

        # Set role combo
        for i in range(self.form_role_combo.count()):
            if self.form_role_combo.itemData(i) == user.role:
                self.form_role_combo.setCurrentIndex(i)
                break

    def save_user_form(self):
        """Save the user form data"""
        try:
            # Get form data
            try:
                user_id = int(self.form_id_edit.text().strip())
            except ValueError:
                raise ValueError("ID must be a valid number")

            first_name = self.form_first_name_edit.text().strip()
            last_name = self.form_last_name_edit.text().strip()
            password = self.form_password_edit.text().strip()
            role = self.form_role_combo.currentData()
            email = self.form_email_edit.text().strip() or None

            if not all([first_name, last_name, password]):
                raise ValueError("All fields are required")

            user_data = {
                'id': user_id,
                'firstName': first_name,
                'lastName': last_name,
                'password': password,
                'role': role,
                'email': email
            }

            if self.current_editing_user is None:
                # Adding new user
                new_user = User(**user_data)
                if self.service.addUser(new_user):
                    self.load_users()
                    self.status_label.setText(f"{new_user.firstName} added successfully")
                    self.hide_user_form()
                else:
                    self.show_error("User already exists")
            else:
                # Editing existing user
                updated_user = User(**user_data)
                self.repository.update([updated_user])
                self.load_users()
                self.status_label.setText(f"User {updated_user.firstName} updated successfully")
                self.hide_user_form()

        except Exception as e:
            self.show_error(f"Error saving user: {str(e)}")

    def delete_user(self):
        """Delete selected user"""
        current_row = self.table.currentRow()
        if current_row < 0:
            toast = ToastWidget(self, "Please select a user to delete", 5)
            toast.show()
            return

        user = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{user.firstName} {user.lastName}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repository.delete(user.id)
                self.load_users()
                self.status_label.setText(f"User {user.firstName} deleted successfully")
            except Exception as e:
                self.show_error(f"Error deleting user: {str(e)}")

    def apply_filter(self):
        """Apply filter to the table"""
        filter_column = self.filter_column_combo.currentText()
        filter_value = self.filter_input.text().strip().lower()

        if not filter_value or filter_column == "All":
            self.load_users()
            return

        try:
            all_users = self.repository.get_all()
            filtered_users = []

            for user in all_users:
                should_include = False

                if filter_column == "ID":
                    should_include = filter_value in str(user.id).lower()
                elif filter_column == "First Name":
                    should_include = filter_value in user.firstName.lower()
                elif filter_column == "Last Name":
                    should_include = filter_value in user.lastName.lower()
                elif filter_column == "Role":
                    role_value = user.role.value if hasattr(user.role, 'value') else str(user.role)
                    should_include = filter_value in role_value.lower()

                if should_include:
                    filtered_users.append(user)

            self.populate_table(filtered_users)
            self.status_label.setText(f"Filter applied: {len(filtered_users)} users found")

        except Exception as e:
            self.show_error(f"Error applying filter: {str(e)}")

    def clear_filter(self):
        """Clear the filter and show all users"""
        self.filter_input.clear()
        self.filter_column_combo.setCurrentIndex(0)
        self.load_users()

    def on_selection_changed(self):
        """Handle table selection changes"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def show_error(self, message):
        """Show error message dialog"""
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        """Show info message dialog"""
        QMessageBox.information(self, "Information", message)

    def generateQrCode(self):
        """Generate a QR code with user ID and password"""
        current_row = self.table.currentRow()
        if current_row < 0:
            toast = ToastWidget(self, "Please select a user to generate QR code", 5)
            toast.show()
            return

        user_item = self.table.item(current_row, 0)
        user = user_item.data(Qt.ItemDataRole.UserRole)

        # Format QR content as requested
        qr_data = f"id = {user.id}\npassword = {user.password}"

        # Generate the QR code image
        qr = qrcode.make(qr_data)

        # Save temporarily to file
        temp_path = "temp_qr.png"
        qr.save(temp_path)

        # Load into QPixmap
        pixmap = QPixmap(temp_path)

        # Show in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"QR Code - {user.firstName} {user.lastName}")
        dialog.setFixedSize(400, 500)
        
        layout = QVBoxLayout()
        
        # QR Code image
        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # User info text
        info_text = QLabel(f"User: {user.firstName} {user.lastName}\nID: {user.id}")
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_text.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(info_text)
        
        # Email QR Code button
        email_button = MaterialButton("📧 Email QR Code")
        email_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        email_button.clicked.connect(lambda: self.send_access_package(user, temp_path))
        layout.addWidget(email_button)
        
        # Close button
        close_button = MaterialButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()

        # Optional: remove temp file after use
        os.remove(temp_path)

    def send_access_package(self, user,qr_image_path):
        """Send user access package via email"""

        if user.email is None:
            QMessageBox.warning(self, "No Email", "User does not have an email address.")
            return

        from src.frontend.pl_ui.utils.AccessCard import create_complete_access_package2 , PassConfig
        from src.frontend.pl_ui.utils.IconLoader import LOGO
        from modules.shared.shared.email.emailSender import EmailSenderService, get_email_template, get_default_email_config
        # Custom configuration with logo
        config = PassConfig(
            organization_name="PL Project LTD.",
            description="Machine Access Pass",
            logo_text="PL PROJECT",
            logo_image_path=LOGO
        )

        pkpass_path, google_pay_path, html_card_path = create_complete_access_package2(
            user=user,
            config=config,
            qr_code_path=qr_image_path
        )

        template = get_email_template(user_name=user.get_full_name(),
                                      message="Here is your system access package")
        sender = EmailSenderService(config=get_default_email_config())

        try:

            sender.send_email(
                subject="Your System Access Package",
                body=template,
                to_emails=[user.email],
                html=True,
                attachments=[pkpass_path,html_card_path]
            )

            # show success message
            QMessageBox.information(self, "Email Sent", f"QR code emailed to {user.email} successfully.")


        except Exception as e:
            QMessageBox.critical(self, "Email Error", f"Failed to send email: {str(e)}")

    def emailQrCode(self, user, qr_image_path):
        if user.email is None:
            QMessageBox.warning(self, "No Email", "User does not have an email address.")
            return
        """Email the QR code to the user or administrator"""
        from modules.shared.shared.email.emailSender import EmailSenderService,get_email_template,get_default_email_config
        template = get_email_template(user_name=user.get_full_name(),
                                    message="Here is your QR code for accessing the system.")
        sender = EmailSenderService(config=get_default_email_config())

        try:

            sender.send_email(
                subject="Your System QR Code",
                body=template,
                to_emails=[user.email],
                html=True,
                attachments = [qr_image_path]
            )

            # show success message
            QMessageBox.information(self, "Email Sent", f"QR code emailed to {user.email} successfully.")


        except Exception as e:
            QMessageBox.critical(self, "Email Error", f"Failed to send email: {str(e)}")

    def retranslate(self):
        """Update all UI texts for language changes - called automatically"""
        # Update title - using a basic title since USER_MANAGEMENT doesn't exist in keys
        if self.title_label:
            self.title_label.setText("User Management")

        # Update filter section - using Message enum constants that exist
        if self.filter_group:
            # Use basic string since FILTER_USERS may not be in TranslationKeys 
            self.filter_group.setTitle(self.tr(TranslationKeys.User.FILTER_USERS))
        if self.filter_by_label:
            self.filter_by_label.setText(self.tr(TranslationKeys.User.FILTER_BY) + ":")
            
        # Update filter combo - preserve current selection
        if self.filter_column_combo:
            current_index = self.filter_column_combo.currentIndex()
            self.filter_column_combo.clear()
            self.filter_column_combo.addItems([
                "All",
                self.tr(TranslationKeys.User.ID), 
                self.tr(TranslationKeys.User.FIRST_NAME),
                self.tr(TranslationKeys.User.LAST_NAME),
                self.tr(TranslationKeys.User.ROLE),
            ])
            if current_index >= 0:
                self.filter_column_combo.setCurrentIndex(current_index)

        # Update buttons
        if self.filter_button:
            self.filter_button.setText(self.tr(TranslationKeys.User.APPLY_FILTERS))
        if self.clear_filter_button:
            self.clear_filter_button.setText(self.tr(TranslationKeys.User.CLEAR_FILTERS))
        if self.add_button:
            self.add_button.setText(self.tr(TranslationKeys.User.ADD_USER))
        if self.edit_button:
            self.edit_button.setText(self.tr(TranslationKeys.User.EDIT_USER))
        if self.delete_button:
            self.delete_button.setText(self.tr(TranslationKeys.User.DELETE_USER))
        if self.refresh_button:
            self.refresh_button.setText(self.tr(TranslationKeys.Navigation.REFRESH))
        if self.test_button:
            self.test_button.setText(self.tr(TranslationKeys.User.GENERATE_QR))

        # Update placeholders
        if self.filter_input:
            self.filter_input.setPlaceholderText(self.tr(TranslationKeys.User.ENTER_FILTER_VALUE))

        # Update table headers
        if self.table:
            self.table.setHorizontalHeaderLabels([
                self.tr(TranslationKeys.User.ID),
                self.tr(TranslationKeys.User.FIRST_NAME),
                self.tr(TranslationKeys.User.LAST_NAME),
                self.tr(TranslationKeys.Auth.PASSWORD),
                self.tr(TranslationKeys.User.ROLE),
                self.tr(TranslationKeys.User.EMAIL),
            ])

        # Update status only on first initialization
        if hasattr(self, 'status_label') and self.status_label and not hasattr(self, '_initial_status_set'):
            self.status_label.setText(self.tr(TranslationKeys.Dashboard.READY))
            self._initial_status_set = True


class UserManagementWindow(QMainWindow):
    """Main window containing the user management widget"""

    def __init__(self):
        super().__init__()
        # self.setWindowTitle("User Management")
        self.setGeometry(100, 100, 800, 600)

        # Create and set central widget
        self.user_widget = UserManagementWidget()
        self.setCentralWidget(self.user_widget)


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set a light palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("white"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("black"))
    palette.setColor(QPalette.ColorRole.Base, QColor("white"))  # Text entry fields, combo boxes
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f5f5f5"))  # Alternating table rows
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("white"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("black"))
    palette.setColor(QPalette.ColorRole.Text, QColor("black"))
    palette.setColor(QPalette.ColorRole.Button, QColor("white"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("black"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("red"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#905BA9"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))

    # Apply the palette!
    app.setPalette(palette)

    window = UserManagementWindow()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
