from deprecated.pl_gui.gallery.GalleryContent import ThumbnailWidget
import os
import time
import threading
import cv2
import numpy as np
from matplotlib import pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from PyQt6.QtGui import QPixmap, QImage

class DXFThumbnailLoader:
    def __init__(self, dxf_directory=None, thumbnail_size=(800, 600)):
        self.dxf_directory = dxf_directory
        self.thumbnail_size = thumbnail_size
        self.thumbnail_widgets = []  # Store loaded thumbnail widgets
        self.thread = None

    def set_directory(self, dxf_directory):
        """Set the directory to load DXF files from."""
        self.dxf_directory = dxf_directory

    def load(self):
        """Start the loading process."""
        if not self.dxf_directory:
            raise ValueError("DXF directory is not set.")
        self.thumbnail_widgets = []  # Clear previous thumbnails
        self.thread = threading.Thread(target=self.run)
        self.thread.start()



    def dxf_to_png(self, doc, dpi=300):
        """Convert DXF document to PNG using matplotlib backend"""
        try:
            # Create matplotlib backend
            fig = plt.figure(figsize=(4, 3))
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            backend = MatplotlibBackend(ax)

            # Create frontend and draw
            frontend = Frontend(ctx, backend)
            frontend.draw_layout(doc.modelspace(), finalize=True)

            import io
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            print(f"Error converting DXF to PNG: {e}")
            return None

    def run(self):
        """Load all DXF files and create thumbnail widgets."""
        if not os.path.exists(self.dxf_directory):
            print(f"DXF directory does not exist: {self.dxf_directory}")
            return []

        dxf_files = [f for f in os.listdir(self.dxf_directory) if f.lower().endswith('.dxf')]

        for filename in dxf_files:
            dxf_file_path = os.path.join(self.dxf_directory, filename)
            try:
                # Get file modification time for timestamp
                file_stat = os.stat(dxf_file_path)
                timestamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(file_stat.st_mtime))

                # Load and convert DXF
                doc = ezdxf.readfile(dxf_file_path)
                png_data = self.dxf_to_png(doc, dpi=72)

                if png_data:
                    # Convert to OpenCV image
                    img = cv2.imdecode(np.frombuffer(png_data, np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        # Create thumbnail
                        thumbnail = cv2.resize(img, self.thumbnail_size, interpolation=cv2.INTER_AREA)
                        height, width, channel = thumbnail.shape
                        bytes_per_line = 3 * width
                        q_img = QImage(thumbnail.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
                        pixmap = QPixmap.fromImage(q_img)

                        # Create thumbnail widget and store it
                        thumbnail_widget = ThumbnailWidget(filename, pixmap, timestamp)
                        self.thumbnail_widgets.append(thumbnail_widget)

            except Exception as e:
                print(f"Error loading {dxf_file_path}: {e}")

        return self.thumbnail_widgets

    def get_thumbnails(self):
        """Return the list of loaded thumbnail widgets."""
        if self.thread:
            self.thread.join()  # Ensure the thread has finished
        return self.thumbnail_widgets
