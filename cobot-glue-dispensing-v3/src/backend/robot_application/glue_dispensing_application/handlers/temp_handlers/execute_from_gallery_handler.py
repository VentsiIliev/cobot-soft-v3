import numpy as np

from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from src.backend.system.utils import utils


def execute_from_gallery(application,workpiece,z_offset_for_calibration_pattern):
    def flatten_point(p):
        """Flattens nested point lists like [[[x, y]]] -> [x, y]"""
        while isinstance(p, (list, tuple)) and len(p) == 1:
            p = p[0]
        return p

    # print("Handling execute from gallery: ", workpiece)
    robotPaths = []

    # Process both Contour and Fill patterns if available
    for pattern_type in ["Contour", "Fill"]:
        sprayPatternsList = workpiece.sprayPattern.get(pattern_type, [])
        if not sprayPatternsList:
            print(f"No {pattern_type} patterns found, skipping...")
            continue

        print(f"Processing {pattern_type} patterns: {len(sprayPatternsList)} patterns found")

        for pattern in sprayPatternsList:
            contour_arr = pattern.get("contour", [])
            fill_arr = pattern.get("fill", [])
            contour_arr_settings = pattern.get("settings", {})

            # Sanitize and convert points to float
            points = []

            for p in contour_arr:
                coords = p[0] if isinstance(p[0], (list, tuple, np.ndarray)) else p
                # Ensure coords[0] and coords[1] are scalars
                x = float(coords[0])
                y = float(coords[1])

                points.append([x, y])

            if points:
                print(f"=== HANDLEEXECUTEFROMGALLERY {pattern_type} TRANSFORMATION DEBUG ===")
                print(f"Input points type: {type(points)}")
                print(f"Input points sample: {points[:3] if len(points) > 3 else points}")

                # Prepare points for OpenCV: shape (N, 1, 2)
                np_points = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
                print(f"After np.array reshape: shape={np_points.shape}, dtype={np_points.dtype}")
                print(f"np_points sample: {np_points[:3] if len(np_points) > 3 else np_points}")

                # Transform to robot coordinates
                # print(f"Camera to robot matrix: {self.visionService.cameraToRobotMatrix}")
                transformed = utils.applyTransformation(application.visionService.cameraToRobotMatrix, np_points,
                                                        x_offset=application.get_transducer_offsets()[0],
                                                        y_offset=application.get_transducer_offsets()[1],
                                                        dynamic_offsets_config=application.get_dynamic_offsets_config())
                # print(f"After transformation: type={type(transformed)}, shape={transformed.shape if hasattr(transformed, 'shape') else 'no shape'}")
                # print(f"Transformed sample: {transformed[:3] if len(transformed) > 3 else transformed}")

                finalContour = []
                for i, point in enumerate(transformed):
                    # print(f"Processing point {i}: {point}")
                    point = flatten_point(point)
                    # print(f"After flatten_point: {point}")
                    x = float(point[0])
                    y = float(point[1])
                    # print(f"Final x,y: {x}, {y}")

                    z_str = str(contour_arr_settings.get(GlueSettingKey.SPRAYING_HEIGHT.value, 250)).replace(",",
                                                                                                             "")
                    z = float(z_str)
                    z = application.robotService.robot_config.safety_limits.z_min + z
                    # print(f"z_min + z = {self.robotService.robot_config.safety_limits.z_min} + {z} = {z}")
                    rx = 180
                    ry = 0
                    rz = float(contour_arr_settings.get(GlueSettingKey.RZ_ANGLE.value, 0))

                    newPoint = [x, y, z, rx, ry, rz]
                    finalContour.append(newPoint)

                robotPaths.append([finalContour, contour_arr_settings])
                print(f"Added {pattern_type} path with {len(finalContour)} points")

    application.robotService.moveToCalibrationPosition(z_offset=z_offset_for_calibration_pattern)
    # self.robotService.cleanNozzle()
    application.robotService.moveToCalibrationPosition(z_offset=z_offset_for_calibration_pattern)
    # self.robotService._waitForRobotToReachPosition(self.robotService.calibrationPosition, 1, delay=0)
    # print(f"    handleExecuteFromGallery: paths to trace: {robotPaths}")
    application.glue_dispensing_operation.traceContours(robotPaths, spray_on=application.settingsManager.glue_settings.get_spray_on())
    # print("Paths to trace: ", robotPaths)