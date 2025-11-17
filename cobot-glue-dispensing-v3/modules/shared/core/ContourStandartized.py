import cv2
import numpy as np


class Contour:
    def __init__(self, contour_points):
        """
        Standardizes and stores contour points in shape (N, 2), dtype=float32.
        Accepts lists, (N,2), (N,1,2), or any OpenCV contour format.
        """
        contour_points = np.asarray(contour_points, dtype=np.float32)
        if contour_points.ndim == 3 and contour_points.shape[1] == 1:
            contour_points = contour_points[:, 0, :]
        self.contour_points = contour_points.reshape(-1, 2)

    # --- Accessors ---
    def get(self):
        """Return the standardized contour points (N,2)."""
        return self.contour_points

    def as_cv(self):
        """Return the contour in OpenCV's (N,1,2) format."""
        return self.contour_points.reshape(-1, 1, 2)

    # --- Geometry and properties ---
    def getArea(self):
        return cv2.contourArea(self.as_cv())

    def getBbox(self):
        return cv2.boundingRect(self.as_cv())

    def getMinAreaRect(self):
        return cv2.minAreaRect(self.as_cv())

    def getMoments(self):
        return cv2.moments(self.as_cv())

    def getPerimeter(self):
        return cv2.arcLength(self.as_cv(), True)

    def getCentroid(self):
        M = self.getMoments()
        if M["m00"] == 0:
            x, y, w, h = self.getBbox()
            if w > 0 and h > 0:
                return (int(x + w / 2), int(y + h / 2))
            elif len(self.contour_points):
                return tuple(map(int, self.contour_points[0]))
            else:
                return (0, 0)
        return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

    def getConvexHull(self):
        return cv2.convexHull(self.as_cv())

    def getOrientation(self):
        M = self.getMoments()
        if abs(M["mu20"]) < 1e-10:
            return 0
        angle = 0.5 * np.arctan2(2 * M["mu11"], M["mu20"] - M["mu02"])
        return np.degrees(angle)

    # --- Comparison ---
    def match(self, other):
        if isinstance(other, Contour):
            other = other.as_cv()
        return cv2.matchShapes(self.as_cv(), other, 1, 0.0)

    # --- Transformations ---
    def translate(self, dx, dy):
        self.contour_points += np.array([dx, dy], dtype=np.float32)

    def scale(self, factor):
        self.contour_points *= factor

    def rotate(self, angle_deg, pivot):
        angle_rad = np.radians(angle_deg)
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        p = np.asarray(pivot, dtype=np.float32)
        pts = self.contour_points - p
        R = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float32)
        self.contour_points = pts @ R.T + p

    def simplify(self, epsilon_factor=0.01):
        peri = self.getPerimeter()
        epsilon = epsilon_factor * peri
        simplified = cv2.approxPolyDP(self.as_cv(), epsilon, True)
        self.contour_points = simplified.reshape(-1, 2).astype(np.float32)
        return self.contour_points

    # --- Convexity ---
    def getConvexityDefects(self):
        contour = self.as_cv().astype(np.int32)
        hull = cv2.convexHull(contour, returnPoints=False)
        if hull is None or len(hull) < 3:
            return False, None
        defects = cv2.convexityDefects(contour, hull)
        return (defects is not None), defects

    # --- Morphological shrinking ---
    def shrink(self, offset_x, offset_y):
        x, y, w, h = self.getBbox()
        mask = np.zeros((h + 2 * offset_y, w + 2 * offset_x), dtype=np.uint8)
        shifted = self.contour_points - [x - offset_x, y - offset_y]
        cv2.fillPoly(mask, [shifted.astype(np.int32)], 255)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * offset_x, 2 * offset_y))
        eroded = cv2.erode(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            new_c = contours[0].reshape(-1, 2) + [x - offset_x, y - offset_y]
            self.contour_points = new_c.astype(np.float32)

    # --- Drawing ---
    def draw(self, frame, color=(0, 255, 0), thickness=2):
        cv2.drawContours(frame, [self.as_cv().astype(np.int32)], -1, color, thickness)


if __name__ == "__main__":
    import cv2
    import numpy as np


    # --- Helper function ---
    def ttest_contour(name, pts):
        print(f"\n🟢 Testing: {name}")
        c = Contour(pts)
        print("  shape:", c.get().shape, "| dtype:", c.get().dtype)
        print("  area:", round(c.getArea(), 2))
        print("  centroid:", c.getCentroid())
        print("  orientation:", round(c.getOrientation(), 2))
        return c


    # --- 1️⃣ Simple rectangle as list of tuples (unordered) ---
    rect_pts = [(10, 10), (110, 10), (110, 60), (10, 60)]
    ttest_contour("Rectangle (list of tuples)", rect_pts)

    # --- 2️⃣ NumPy array (N,2) shape ---
    np_rect = np.array(rect_pts, dtype=np.float32)
    ttest_contour("Rectangle (numpy (N,2))", np_rect)

    # --- 3️⃣ OpenCV contour format (N,1,2) ---
    cv_rect = np_rect.reshape(-1, 1, 2)
    ttest_contour("Rectangle (OpenCV (N,1,2))", cv_rect)

    # --- 4️⃣ Irregular polygon ---
    poly_pts = np.array([[50, 50], [150, 70], [130, 150], [70, 130]], dtype=np.float32)
    ttest_contour("Polygon", poly_pts)

    # --- 5️⃣ Circle (approximated using cv2.ellipse2Poly) ---
    circle_pts = cv2.ellipse2Poly((100, 100), (50, 50), 0, 0, 360, 15)
    ttest_contour("Circle (ellipse2Poly)", circle_pts)

    # --- 6️⃣ Star shape (non-convex polygon) ---
    star_pts = np.array([[100, 20], [120, 80], [180, 80], [130, 120],
                         [150, 180], [100, 140], [50, 180], [70, 120],
                         [20, 80], [80, 80]], dtype=np.float32)
    ttest_contour("Star shape", star_pts)

    # --- 7️⃣ Random noisy points (simulate raw contour from cv2.findContours) ---
    random_pts = (np.random.rand(10, 1, 2) * 100).astype(np.float32)
    ttest_contour("Random (N,1,2)", random_pts)

    # --- 8️⃣ Degenerate: Single point ---
    single_pt = np.array([[50, 50]], dtype=np.float32)
    ttest_contour("Single point", single_pt)

    # --- 9️⃣ Degenerate: Empty contour ---
    empty = np.empty((0, 2), dtype=np.float32)
    ttest_contour("Empty contour", empty)

