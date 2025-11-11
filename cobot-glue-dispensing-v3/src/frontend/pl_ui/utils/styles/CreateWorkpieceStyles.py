def getStyles():
    styles= """
            /* === Main Form Container === */
            CreateWorkpieceForm, QWidget#CreateWorkpieceForm {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 2px solid #905BA9;  /* keep or change */
            }

            /* === Line Edit Styling === */
            FocusLineEdit, QLineEdit {
                background: #F7F3FA;
                border: 1.5px solid #D3D3D3;   /* neutral grey */
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 16px;
                color: #3A2C4A;
            }

            FocusLineEdit:focus, QLineEdit:focus {
                border: 1.5px solid #3A2C4A;   /* dark grey instead of orange */
                outline: none;
            }

            /* === ComboBox Styling === */
            QComboBox {
                background: #F7F3FA; /* match FocusLineEdit */
                border: 1.5px solid #D3D3D3;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 16px;
                color: #3A2C4A;
                min-height: 40px;
            }
            QComboBox:focus, QComboBox:pressed {
                border: 1.5px solid #3A2C4A; /* same focus border as line edit */
                outline: none;
            }
            QComboBox:hover {
                background: #F7F3FA;
                border: 1.5px solid #C8C8C8;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 36px;
                border-left: none;
            }
            QComboBox::down-arrow {
                image: none; /* keep native arrow or use icon if desired */
                width: 12px;
                height: 12px;
            }

            /* Popup list (QAbstractItemView / QListView) styling - ensure colors apply */
            QComboBox QAbstractItemView,
            QComboBox QListView,
            QComboBox QAbstractItemView::item,
            QListView {
                background: #FFFFFF; /* popup white to contrast against highlighted items */
                color: #000000;
                selection-background-color: #e0f7fa;
                selection-color: #000000;
            }

            QComboBox QAbstractItemView::item {
                padding: 6px 8px;
            }

            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover,
            QComboBox QListView::item:selected,
            QComboBox QListView::item:hover {
                background: #e0f7fa; /* highlight */
                color: #000000; /* text color on hover/selection */
            }

            /* ensure popup view paints background */
            QComboBox QAbstractItemView {
                outline: none;
                border: 1px solid #e6e6e6;
            }

            /* Ensure drop-down subcontrol doesn't draw its own border so overall border matches QLineEdit */
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                color: #3A2C4A;
            }
        """

    return styles

def get_input_field_styles():
    styles = """
            background: #F7F3FA;
            border: 1.5px solid #D3D3D3;
            border-radius: 8px;
            padding: 6px 10px;
            color: #3A2C4A;
        """

    return styles

def get_popup_view_styles():
    styles =     """
                QListView { background: #ffffff; color: #000000; }
                QListView::item { padding: 6px 8px; }
                QListView::item:selected, QListView::item:hover { background: #e0f7fa; color: #000000; }
                """

    return styles