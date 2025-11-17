import ezdxf
from ezdxf import bbox
import numpy as np
from ezdxf.entities import Spline
import matplotlib.pyplot as plt
import math
import numpy as np

from modules.shared.core.dxf.DXFCoordinateConverter import DXFCoordinateConverter

# SCALE_X = 1280 / 900 # 1.422
# SCALE_Y = 720 / 600 # 1.2

class DXFPathExtractor:
    """
    Extracts path data (lines, polylines, circles, arcs, splines) from specified layers of a DXF file.

    This class supports visualization, OpenCV-style contour conversion, and saving the modified DXF with an added border.

    Attributes:
        filename (str): Path to the input DXF file.
        wp_layer (str): Layer name for the external workpieces boundary.
        contour_layer (str): Layer name for spray/contour paths.
        fill_layer (str): Layer name for fill paths.
        target_size (tuple): Size of the border rectangle (width, height).
        wpCnt (list): List of extracted workpieces contours.
        contourCnt (list): List of extracted contour/spray paths.
        fillCnt (list): List of extracted fill paths.
    """
    def __init__(self, filename, wp_layer="External", contour_layer="Contour",fillLayer = "Fill", target_size=(900, 600)):

        """
        Initializes the DXFPathExtractor.

        Args:
            filename (str): Path to the DXF file to be processed.
            wp_layer (str): Name of the layer containing the workpieces boundary.
            contour_layer (str): Name of the layer containing contour/spray lines.
            fillLayer (str): Name of the layer containing fill geometry.
            target_size (tuple): Width and height of the added border rectangle.
        """
        self.filename = filename
        self.wp_layer = wp_layer
        self.contour_layer = contour_layer
        self.fill_layer = fillLayer
        self.target_layers = [wp_layer, contour_layer,fillLayer]
        self.target_size = target_size
        self.wpCnt = []
        self.contourCnt = []
        self.fillCnt = []

        self._load_dxf()
        self._add_border()
        self._extract_paths()

    def _load_dxf(self):
        """
           Loads the DXF file and retrieves the modelspace (drawing canvas).
           """
        self.doc = ezdxf.readfile(self.filename)
        self.msp = self.doc.modelspace()

    def _add_border(self):
        """
            Calculates the center of the existing drawing and adds a rectangle border around it.
            """
        cache = bbox.Cache()
        first_bbox = bbox.extents(self.msp, cache=cache)
        if first_bbox:
            cx = (first_bbox.extmin.x + first_bbox.extmax.x) / 2
            cy = (first_bbox.extmin.y + first_bbox.extmax.y) / 2
            self._draw_rectangle(cx, cy, self.target_size[0], self.target_size[1])

    def _spline_to_points(self, spline, segments=100):
        """Convert a spline to a series of points by sampling at regular intervals."""
        if not isinstance(spline, Spline):
            return []

        # Use fit_points to get the spline's points
        points = spline.fit_points  # This returns the points used to fit the spline

        # If you want to sample additional points in between, you might use the 'get_points' method if it's available or manually interpolate along the spline
        return [(pt[0], pt[1]) for pt in points]



    def _draw_rectangle(self, cx, cy, width, height):
        """
        Draws a rectangle centered at (cx, cy) with specified width and height.

        Args:
            cx (float): Center x-coordinate.
            cy (float): Center y-coordinate.
            width (float): Width of the rectangle.
            height (float): Height of the rectangle.
        """
        hw = width / 2
        hh = height / 2
        bl = (cx - hw, cy - hh)
        br = (cx + hw, cy - hh)
        tr = (cx + hw, cy + hh)
        tl = (cx - hw, cy + hh)

        self.msp.add_lwpolyline(
            points=[bl, br, tr, tl, bl],
            close=True,
            dxfattribs={'layer': 'border'}
        )

    def _circle_to_points(self, center, radius, segments=36):
        return [
            (
                center[0] + radius * math.cos(2 * math.pi * i / segments),
                center[1] + radius * math.sin(2 * math.pi * i / segments),
            )
            for i in range(segments)
        ]

    def _arc_to_points(self, center, radius, start_angle, end_angle, segments=36):
        """Convert an arc to a series of points."""
        if start_angle > end_angle:
            end_angle += 360  # Handle arcs that cross the 0-degree line

        angles = np.linspace(math.radians(start_angle), math.radians(end_angle), segments)
        return [
            (
                center[0] + radius * math.cos(angle),
                center[1] + radius * math.sin(angle),
            )
            for angle in angles
        ]

    def _extract_paths(self):
        for entity in self.msp:
            if entity.dxf.layer not in self.target_layers:
                continue
            layer = self.doc.layers.get(entity.dxf.layer)
            layer_color = layer.color if layer else None
            print(f"Entity Type: {entity.dxftype()}, Layer: {entity.dxf.layer}, Color: {layer_color}")

            # Set the current list based on the layer type
            if entity.dxf.layer == self.wp_layer:
                current_list = self.wpCnt
            elif entity.dxf.layer == self.contour_layer:
                current_list = self.contourCnt
            elif entity.dxf.layer == self.fill_layer:
                current_list = self.fillCnt
            else:
                continue  # This shouldn't happen, but is a safe fallback

            # Process the entities accordingly
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                current_list.append([(start.x, start.y), (end.x, end.y)])

            elif entity.dxftype() == 'LWPOLYLINE':
                points = [(pt[0], pt[1]) for pt in entity.get_points()]
                closed = entity.closed
                print("Should be closed?", closed)
                if closed:
                    points.append(points[0])  # Close the polyline if it is closed
                current_list.append(points)  # Add the closed polyline as a separate shape

            elif entity.dxftype() == 'CIRCLE':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                circle_pts = self._circle_to_points(center, radius)
                circle_pts.append(circle_pts[0])  # Close the circle
                current_list.append(circle_pts)  # Add the circle as a separate shape

            elif entity.dxftype() == 'ARC':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                arc_pts = self._arc_to_points(center, radius, start_angle, end_angle)
                current_list.append(arc_pts)  # Add the arc as a separate shape

            # For other types (POLYLINE, ELLIPSE, SPLINE), you can extend further
            elif entity.dxftype() == "POLYLINE":
                print("POLYLINE not implemented")

            elif entity.dxftype() == "ELLIPSE":
                print("ELLIPSE not implemented")

            elif entity.dxftype() == "SPLINE":

                spline_points = self._spline_to_points(entity)

                current_list.append(spline_points)


    def get_paths(self):
        return self.wpCnt, self.contourCnt, self.fillCnt

    def get_opencv_contours(self):
        def to_opencv_contour(path):
            if not path or not all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in path):
                print("⚠️ Skipping invalid path:", path)
                return None

            # if path[0] != path[-1]:
            #     path = path + [path[0]]

            return np.array(path, dtype=np.float32).reshape(-1, 1, 2)

        # Convert main workpieces contour (single contour)
        wp_contour = to_opencv_contour(self.wpCnt)

        # Convert each path in contourCnt and fillCnt to an OpenCV-style contour
        contour_contours = []
        for path in self.contourCnt:
            contour = to_opencv_contour(path)
            if contour is not None:
                contour_contours.append(contour)

        fill_contours = []
        for path in self.fillCnt:
            contour = to_opencv_contour(path)
            if contour is not None:
                fill_contours.append(contour)

        return wp_contour, contour_contours, fill_contours


    def save_dxf(self, output_file="modified.dxf"):
        self.doc.saveas(output_file)

    def plot(self):
        def extract_xy(coords):
            x_vals = [p[0] for p in coords]
            y_vals = [p[1] for p in coords]
            return x_vals, y_vals

        aci_to_rgb = {
            10: "#FF0000",  # Red - External Layer
            130: "#00FFFF",  # Cyan - Contour Layer
            90: '#00FF00'  # Green - Fill Layer
        }

        plt.figure(figsize=(10, 8))

        # Plot workpieces paths
        for path in self.wpCnt:
            layer = self.doc.layers.get(self.wp_layer)
            color_index = layer.color if layer else None
            color = aci_to_rgb.get(color_index, "blue")  # Default to blue if color not found
            x_wp, y_wp = extract_xy(path)
            plt.plot(x_wp, y_wp, label=f"Workpiece ({self.wp_layer})", color=color)

        # Plot spray pattern paths
        for path in self.contourCnt:
            layer = self.doc.layers.get(self.contour_layer)
            color_index = layer.color if layer else None
            color = aci_to_rgb.get(color_index, "red")  # Default to red if color not found
            x_sp, y_sp = extract_xy(path)
            plt.plot(x_sp, y_sp, label=f"Contour ({self.contour_layer})", color=color)

        # Plot fill paths
        for path in self.fillCnt:
            layer = self.doc.layers.get(self.fill_layer)
            color_index = layer.color if layer else None
            color = aci_to_rgb.get(color_index, "#FFA500")  # Default to orange for fill
            x_fill, y_fill = extract_xy(path)
            plt.plot(x_fill, y_fill, label=f"Fill ({self.fill_layer})", color=color)

        plt.axis("equal")
        plt.title("DXF Paths with Layer Colors")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend()
        plt.grid(True)
        plt.show()

# ---------------------------
# Entry point for CLI usage
# ---------------------------
if __name__ == "__main__":
    # dxf_file = "rectTest.dxf"  # Change as needed
    dxf_file = "CustomPartSplines.dxf"  # Change as needed
    extractor = DXFPathExtractor(dxf_file)

    # wp, contour,fill = extractor.get_paths()
    wp, contour,fill = extractor.get_opencv_contours()
    print("✅ Workpiece Points:", wp)
    print("len = ",len(wp))
    print("✅ Contour Pattern Points:", contour)
    print("len = ",len(contour))
    print("✅ Fill Points:", fill)
    print("len = ",len(fill))
    extractor.plot()
    extractor.save_dxf("plate_with_border.dxf")
