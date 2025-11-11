from tkinter import filedialog, messagebox

from .DxfConverter import DxfConverter


def upload():
    dxf_file = filedialog.askopenfilename(
        title="Select DXF File",
        filetypes=(("DXF files", "*.dxf"), ("All files", "*.*"))
    )
    if not dxf_file:
        return None, None  # User cancelled the file picker

    try:
        processor = DxfConverter(dxf_file, mode='json')
        contourJSON, scaledContours = processor.process()

        return contourJSON, scaledContours
        # show teach dialog
        # teachDialog = TeachDialogDxf(self.root,scaledContours)
        # print('result', scaledContours)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        messagebox.showerror("File Not Found", f"The file {dxf_file} was not found.")
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")