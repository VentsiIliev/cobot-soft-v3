import numpy as np

from modules.shared.shared.Contour import Contour
from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from src.backend.system.utils import utils
from src.backend.system.utils.contours import flatten_and_convert_to_list

class WorkpieceToSprayPathsGenerator:
    def __init__(self, application):
        self.application = application

    def generate_robot_paths(self, workpieces, debug=False):
        print(f"generate_robot_paths called with {len(workpieces)} workpieces")
        generate_paths = []
        for workpiece_i, workpiece in enumerate(workpieces):
            sprayPatternContour = workpiece.get_spray_pattern_contours()
            sprayPatternFill = workpiece.get_spray_pattern_fills()
            workpiece_height = workpiece.height

            # this orientation is computed for pixel coordinates
            # which might introduce error when the robot orientation is different from the camera orientation
            # for fix this we need to calculate the orientation after transforming the points to robot coordinates
            # orientation = orientations[workpiece_i]
            # print("Orientation before transform: ", orientation)
            # calculate orientation based on transformed points
            contour_data = workpiece.contour["contour"]
            contour_points = contour_data.reshape(-1, 2).tolist()
            robot_points = (contour_points)
            robot_points_contour_obj = Contour(contour_points=np.array(robot_points))
            orientation = robot_points_contour_obj.getOrientation()

            # ✅ Check if spray pattern exists and has data
            has_spray_contours = sprayPatternContour and len(sprayPatternContour) > 0
            has_spray_fills = sprayPatternFill and len(sprayPatternFill) > 0

            # --- CASE 1: No spray pattern, fall back to outer contour ---
            if not has_spray_contours and not has_spray_fills:
                main_contour_path = self.handle_workpiece_main_contour( workpiece, robot_points, workpiece_height, orientation)
                generate_paths.append(main_contour_path)
                continue
            # --- CASE 2 & 3: Process spray contours and fills using unified handler ---
            if has_spray_contours:
                contour_paths = self.handle_workpiece_paths( sprayPatternContour, workpiece_height, orientation, debug,
                                       label="CONTOUR")
                for path in contour_paths:
                    generate_paths.append(path)

            if has_spray_fills:
                fill_paths = self.handle_workpiece_paths(sprayPatternFill, workpiece_height, orientation, debug, label="FILL")
                for path in fill_paths:
                    generate_paths.append(path)

        return generate_paths

    def handle_workpiece_main_contour(self,match,robot_points,workpiece_height,orientation=0):
        # Get main contour data
        if isinstance(match.contour, dict) and "contour" in match.contour:
            contour_data = match.contour["contour"]
            main_settings = match.contour.get("settings", {})
        else:
            contour_data = match.contour
            main_settings = {}

        # Convert to list format if numpy array
        if isinstance(contour_data, np.ndarray):
            contour_points = contour_data.reshape(-1, 2).tolist()
        else:
            contour_points = flatten_and_convert_to_list(contour_data)

        # Close contour if not already closed
        if contour_points and contour_points[0] != contour_points[-1]:
            contour_points.append(contour_points[0])

        # Convert to robot path format with Z, RX, RY, RZ
        robot_path = self.convert_to_robot_path(robot_points, main_settings, workpiece_height, orientation)

        return (robot_path, main_settings)

    def handle_workpiece_paths(self, entries, workpiece_height, orientation=0, debug=False, label="TRANSFORMATION"):
        paths = []
        for entry in entries:
            # --- Validate contour existence and content ---
            contour_data = entry.get("contour", None)

            # Handle None or empty arrays/lists robustly
            if contour_data is None:
                if debug:
                    print(f"⚠️ Skipping {label} entry: contour is None -> {entry}")
                continue

            # --- Validate settings existence ---
            settings = entry.get("settings", {})
            if not settings:
                if debug:
                    print(f"⚠️ Skipping {label} entry: missing or empty settings -> {entry}")
                continue

            # --- Process the valid entry ---
            robot_path = self.contour_to_robot_path(contour_data,settings,workpiece_height,orientation)
            paths.append((robot_path, settings))
        return paths

    def convert_to_robot_path(self, points_2d, settings, workpiece_height, orientation=0):
        """Convert 2D points to robot path format [x, y, z, rx, ry, rz]"""

        COMPUTE_ANGLE_BASED_ON_WIDTH = False
        FOLLOW_WORKPIECE_ORIENTATION = False

        robot_path = []
        # orientation = 0
        print("Settings in _convert_to_robot_path: ", settings)
        # Extract settings with defaults
        spray_height = float(settings.get(GlueSettingKey.SPRAYING_HEIGHT.value))
        rz_angle = float(settings.get(GlueSettingKey.RZ_ANGLE.value))

        if COMPUTE_ANGLE_BASED_ON_WIDTH:
            spray_width = float(settings.get(GlueSettingKey.SPRAY_WIDTH.value))
            from src.backend.system.utils.calculateAngleBasedOnWidth import get_angle_from_width, SPRAY_ALONG_X
            rz_angle = get_angle_from_width(desired_width=spray_width, transducer_magnitude=25,
                                            spray_along_axis=SPRAY_ALONG_X)

        if FOLLOW_WORKPIECE_ORIENTATION:
            rz_angle = rz_angle + orientation

        safety_min_z = self.application.robotService.robot_config.safety_limits.z_min

        print("safety_min_z ->", type(safety_min_z), safety_min_z)
        print("spray_height ->", type(spray_height), spray_height)
        print("workpiece_height ->", type(workpiece_height), workpiece_height)
        z_height = safety_min_z + spray_height + int(workpiece_height)
        print("z_height: ", z_height)

        for i, point in enumerate(points_2d):
            if len(point) >= 2:
                robot_point = [
                    float(point[0]),  # x
                    float(point[1]),  # y
                    z_height,  # z
                    180.0,  # rx (standard orientation)
                    0.0,  # ry
                    rz_angle  # rz
                ]
                robot_path.append(robot_point)

        return robot_path


    def contour_to_robot_path(self,contour,settings,workpiece_height,orientation):
        pts = flatten_and_convert_to_list(contour)
        robot_points = self.transform_to_robot_coordinates( pts)
        robot_path = self.convert_to_robot_path( robot_points, settings, workpiece_height, orientation)
        return robot_path

    def transform_to_robot_coordinates(self, points):
        """Transform 2D points from camera coordinates to robot coordinates with transducer offset applied at rz=0"""
        if not points:
            return []

        # Convert to numpy array for transformation
        np_points = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
        print("Points before transformation: ", np_points)

        # Apply camera to robot transformation with transducer offset correction
        # Offset is applied at rz=0 since rotation will be handled later in robot path generation
        # The offset parameters can be configured via settings or hardcoded based on hardware specs
        transformed = utils.applyTransformation(
            cameraToRobotMatrix=self.application.visionService.cameraToRobotMatrix,
            contours=np_points,
            apply_transducer_offset=True,  # Enable transducer offset correction
            x_offset=self.application.get_transducer_offsets()[0],  # X offset in mm (configure based on your transducer)
            y_offset=self.application.get_transducer_offsets()[1],
            dynamic_offsets_config=self.application.get_dynamic_offsets_config()
            # Y offset in mm (configure based on your transducer)
        )
        print("Transformed points: ", transformed)

        # Convert back to list format
        result = []
        for point in transformed:
            # Flatten nested point structure
            while isinstance(point, (list, tuple, np.ndarray)) and len(point) == 1:
                point = point[0]
            if len(point) >= 2:
                result.append([float(point[0]), float(point[1])])

        return result
