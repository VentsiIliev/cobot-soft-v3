
"""
Workpiece Visualization Dialog
Shows a comprehensive matplotlib visualization of workpiece contours and spray patterns.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from src.frontend.pl_ui.ui.widgets.DraggableLabel import DraggableLabel

matplotlib.use('Agg')  # Use non-interactive backend
from io import BytesIO
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont


class WorkpieceVisualizationDialog(QDialog):
    """Dialog for displaying workpiece visualization"""
    
    def __init__(self, workpiece, parent=None):
        super().__init__(parent)
        self.workpiece = workpiece
        self.setWindowTitle("Workpiece Visualization")
        self.setModal(True)
        self.resize(1200, 800)
        
        # Set up the UI
        self.setup_ui()
        
        # Generate and display the visualization
        self.create_visualization()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Workpiece Visualization - ID: {getattr(self.workpiece, 'workpieceId', 'Unknown')}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Scroll area for the image
        # self.scroll_area = QScrollArea()
        # self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # # Image label
        # self.image_label = QLabel()
        # self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.image_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Use 'AsNeeded' so scrollbars remain functional for programmatic panning/gestures,
        # but hide them visually so UI stays clean.
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Hide native scrollbars visually but keep them available to adjust programmatically
        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical, QScrollBar:horizontal { background: transparent; width: 0px; height: 0px; margin: 0px; }
        """)

        # Image label that supports dragging to pan (swipe)
        self.image_label = DraggableLabel(scroll_area=self.scroll_area)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        # Ensure touch and mouse events are accepted so swipe/drag works
        self.image_label.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.image_label.setMouseTracking(True)
        self.image_label.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Make sure the scroll area viewport also accepts touch events
        self.scroll_area.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Save button
        save_btn = QPushButton("💾 Save Visualization")
        save_btn.clicked.connect(self.save_visualization)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #905BA9;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a4791;
            }
        """)
        button_layout.addWidget(save_btn)
        
        # Close button
        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def extract_points(self, contour_data):
        points = []
        if contour_data is None:
            return np.empty((0, 2))

        try:
            for point in contour_data:
                print(f"extract_points Raw point data: {point}")
                # Unwrap nested single-element containers (list/tuple/ndarray)
                while isinstance(point, (list, tuple, np.ndarray)) and len(point) == 1:
                    point = point[0]

                # Normalize to a 1-D sequence of at least two elements
                if isinstance(point, np.ndarray):
                    if point.ndim == 1 and point.size >= 2:
                        coords = point
                    else:
                        flat = np.asarray(point).reshape(-1)
                        if flat.size >= 2:
                            coords = flat[:2]
                        else:
                            continue
                elif isinstance(point, (list, tuple)):
                    if len(point) >= 2:
                        coords = np.asarray(point[:2])
                    else:
                        continue
                else:
                    # Unsupported element type (e.g. scalar)
                    continue

                try:
                    x = float(coords[0])
                    y = float(coords[1])
                    points.append([x, y])
                except (ValueError, TypeError) as e:
                    print(f"Error converting point {point}: {e}")
                    continue
        except Exception as e:
            print(f"Error processing contour data: {e}")

        return np.array(points) if points else np.empty((0, 2))
    
    def create_visualization(self):
        """Create the matplotlib visualization and convert to QPixmap"""
        try:
            # Create figure
            # fig = plt.figure(figsize=(16, 10), facecolor='white')
            fig = plt.figure(figsize=(12, 8), facecolor='white', dpi=100)
            
            # Main plot
            ax_main = plt.subplot(2, 2, (1, 2))
            
            # Extract workpiece information
            workpiece_id = getattr(self.workpiece, 'workpieceId', 'Unknown')
            name = getattr(self.workpiece, 'name', 'Unnamed')
            material = getattr(self.workpiece, 'material', 'Unknown')
            height = getattr(self.workpiece, 'height', 0)
            area = getattr(self.workpiece, 'contourArea', 0)
            
            # Extract and plot main contour
            main_contour = None
            if hasattr(self.workpiece, 'contour'):
                if isinstance(self.workpiece.contour, dict):
                    main_contour = self.workpiece.contour.get('contour', [])
                elif isinstance(self.workpiece.contour, list):
                    main_contour = self.workpiece.contour
            
            if main_contour is not None:
                main_points = self.extract_points(main_contour)
                if len(main_points) > 0:
                    try:
                        # Plot main contour (outer boundary)
                        ax_main.plot(main_points[:, 0], main_points[:, 1], 'b-', linewidth=3, 
                                    label=f'Main Contour (Area: {area:.1f})', marker='o', markersize=4)
                        
                        # Fill the main contour with light blue
                        if len(main_points) >= 3:  # Need at least 3 points for fill
                            ax_main.fill(main_points[:, 0], main_points[:, 1], 'lightblue', alpha=0.3)
                    except Exception as e:
                        print(f"Error plotting main contour: {e}")
                        # Just plot points without fill if there's an error
                        ax_main.scatter(main_points[:, 0], main_points[:, 1], color='blue', s=50, 
                                      label=f'Main Contour Points (Area: {area:.1f})')
            
            # Extract and plot spray patterns
            spray_patterns = []
            if hasattr(self.workpiece, 'sprayPattern') and isinstance(self.workpiece.sprayPattern, dict):
                contour_patterns = self.workpiece.sprayPattern.get('Contour', [])
                fill_patterns = self.workpiece.sprayPattern.get('Fill', [])
                spray_patterns = contour_patterns + fill_patterns
            
            colors = ['red', 'green', 'orange', 'purple', 'brown', 'cyan', 'magenta']
            
            for i, pattern in enumerate(spray_patterns[:7]):  # Limit to 7 patterns
                if isinstance(pattern, dict) and pattern.get('contour') is not None:
                    spray_points = self.extract_points(pattern['contour'])
                    if len(spray_points) > 0:
                        color = colors[i % len(colors)]
                        
                        # Plot spray pattern as thick line
                        ax_main.plot(spray_points[:, 0], spray_points[:, 1], 
                                    color=color, linewidth=4, alpha=0.8,
                                    label=f'Spray Pattern {i+1}', marker='s', markersize=6)
                        
                        # Add arrows to show spray direction
                        if len(spray_points) >= 2:
                            for j in range(min(len(spray_points) - 1, 10)):  # Limit arrows
                                start = spray_points[j]
                                end = spray_points[j + 1]
                                dx = float(end[0] - start[0])
                                dy = float(end[1] - start[1])
                                if abs(dx) > 0.1 or abs(dy) > 0.1:  # Avoid zero-length arrows
                                    try:
                                        ax_main.arrow(float(start[0]), float(start[1]), dx*0.7, dy*0.7, 
                                                    head_width=8, head_length=10, fc=color, ec=color, alpha=0.6)
                                    except Exception as e:
                                        print(f"Arrow drawing error: {e}")
                                        continue
            
            # Set main plot properties
            ax_main.set_xlabel('X Coordinate (pixels)', fontsize=12)
            ax_main.set_ylabel('Y Coordinate (pixels)', fontsize=12)
            ax_main.set_title(f'Workpiece Visualization\nID: {workpiece_id} | Name: "{name}" | Material: {material}',
                              fontsize=14, fontweight='bold')
            ax_main.grid(True, alpha=0.3)
            # Place legend outside the main axes to avoid overlapping the drawing
            ax_main.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), borderaxespad=0, fontsize=10, framealpha=0.9)
            ax_main.set_aspect('equal')
            
            # Invert Y-axis to match image coordinates
            ax_main.invert_yaxis()
            
            # Detail view subplot
            ax_detail = plt.subplot(2, 2, 3)
            
            # Plot spray patterns in detail
            for i, pattern in enumerate(spray_patterns[:5]):  # Limit to 5 for detail view
                if isinstance(pattern, dict) and pattern.get('contour') is not None:
                    spray_points = self.extract_points(pattern['contour'])
                    if len(spray_points) > 0:
                        color = colors[i % len(colors)]
                        
                        ax_detail.plot(spray_points[:, 0], spray_points[:, 1], 
                                      color=color, linewidth=3, marker='o', markersize=8,
                                      label=f'Pattern {i+1}: {len(spray_points)} points')
            
            ax_detail.set_title('Spray Patterns Detail', fontsize=12, fontweight='bold')
            ax_detail.grid(True, alpha=0.3)
            ax_detail.legend()
            ax_detail.set_aspect('equal')
            ax_detail.invert_yaxis()
            
            # Information panel
            ax_info = plt.subplot(2, 2, 4)
            ax_info.axis('off')
            
            # Compile workpiece information
            glue_type = getattr(self.workpiece.glueType, 'value', getattr(self.workpiece, 'glueType', 'Unknown')) if hasattr(self.workpiece, 'glueType') else 'Unknown'
            tool_id = getattr(self.workpiece.toolID, 'value', getattr(self.workpiece, 'toolID', 'N/A')) if hasattr(self.workpiece, 'toolID') else 'N/A'
            program = getattr(self.workpiece.program, 'value', getattr(self.workpiece, 'program', 'N/A')) if hasattr(self.workpiece, 'program') else 'N/A'
            
            info_text = f"""
                WORKPIECE INFORMATION
                ═══════════════════════
                
                ID: {workpiece_id}
                Name: {name if name else 'Unnamed'}
                Description: {getattr(self.workpiece, 'description', 'None')}
                
                GEOMETRY
                ─────────────────
                • Area: {area:.1f} sq pixels
                • Height: {height} mm
                • Offset: {getattr(self.workpiece, 'offset', 'N/A')}
                
                SPRAY CONFIGURATION
                ─────────────────────
                • Glue Type: {glue_type}
                • Tool ID: {tool_id}
                • Program: {program}
                • Material: {material}
                
                SPRAY PATTERNS
                ──────────────
                • Total patterns: {len(spray_patterns)}
                """
            
            # Add spray pattern details
            for i, pattern in enumerate(spray_patterns[:3]):  # Limit to 3 for space
                if isinstance(pattern, dict) and pattern.get('contour') is not None:
                    spray_points = self.extract_points(pattern['contour'])
                    if len(spray_points) > 0:
                        settings = pattern.get('settings', {})
                        spray_height = settings.get('Spraying Height', 'N/A')
                        fan_speed = settings.get('Fan Speed', 'N/A')
                        
                        info_text += f"""
                                    Pattern {i+1}:
                                      • Points: {len(spray_points)}
                                      • Height: {spray_height} mm
                                      • Fan Speed: {fan_speed}%
                                    """
            
            ax_info.text(0.05, 0.95, info_text, transform=ax_info.transAxes, 
                        fontsize=10, verticalalignment='top', fontfamily='monospace',
                        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
            
            # plt.tight_layout()
            plt.tight_layout(rect=[0, 0, 0.82, 1])
            
            # Convert to QPixmap
            self.figure = fig
            self.display_figure(fig)
            
        except Exception as e:
            # Show error message if visualization fails
            error_text = f"Error creating visualization:\n{str(e)}"
            self.image_label.setText(error_text)
            self.image_label.setStyleSheet("color: red; padding: 20px; font-size: 14px;")
            print(f"Visualization error: {e}")
            import traceback
            traceback.print_exc()
    
    def display_figure(self, fig):
        """Convert matplotlib figure to QPixmap and display it"""
        # Save figure to BytesIO
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        
        # Create QPixmap from bytes
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        
        # Display in label
        self.image_label.setPixmap(pixmap)
        
        # Close the figure to free memory
        plt.close(fig)
        
        buf.close()
    
    def save_visualization(self):
        """Save the visualization to a file"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            default_name = f"workpiece_{getattr(self.workpiece, 'workpieceId', 'unknown')}_visualization.png"
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Workpiece Visualization",
                default_name,
                "PNG Image (*.png);;PDF Document (*.pdf);;All Files (*)"
            )
            
            if file_path:
                # Get the pixmap from the label and save it
                pixmap = self.image_label.pixmap()
                if pixmap:
                    pixmap.save(file_path)
                    print(f"Visualization saved to: {file_path}")
                
        except Exception as e:
            print(f"Error saving visualization: {e}")


if __name__ == "__main__":
    # Test the dialog with dummy data
    import sys
    from PyQt6.QtWidgets import QApplication
    
    class DummyWorkpiece:
        def __init__(self):
            self.workpieceId = "TEST001"
            self.name = "Test Workpiece"
            self.material = "Aluminum"
            self.height = 5.0
            self.contourArea = 1250.5
            self.contour = [[[100, 100]], [[200, 100]], [[200, 200]], [[100, 200]], [[100, 100]]]
    
    app = QApplication(sys.argv)
    
    dummy_workpiece = DummyWorkpiece()
    dialog = WorkpieceVisualizationDialog(dummy_workpiece)
    dialog.exec()
    
    sys.exit(app.exec())