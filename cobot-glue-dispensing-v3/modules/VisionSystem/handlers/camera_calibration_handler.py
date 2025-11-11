from src.backend.GlueDispensingApplication.utils.custom_logging import log_if_enabled, LoggingLevel
from modules.VisionSystem.calibration.cameraCalibration.CameraCalibrationService import CameraCalibrationService


def capture_calibration_image(vision_system,log_enabled,logger):
    if vision_system.rawImage is None:
        log_if_enabled(enabled=log_enabled,
                       logger=logger,
                       level=LoggingLevel.WARNING,
                       message=f"No rawImage image captured for calibration",
                       broadcast_to_ui=False)
        return False, "No rawImage image captured for calibration"

    vision_system.calibrationImages.append(vision_system.rawImage)
    vision_system.message_publisher.publishLatestImage(vision_system.rawImage)
    log_if_enabled(enabled=log_enabled,
                   logger=logger,
                   level=LoggingLevel.INFO,
                   message=f"Calibration image captured successfully",
                   broadcast_to_ui=False)
    return True, "Calibration image captured successfully"

def calibrate_camera(vision_system,log_enabled,logger) -> tuple[bool, str]:
    """
    Calibrates the camera using the CameraCalibrationService.
    """
    enableContourDrawingAfterCalibration = vision_system.camera_settings.get_draw_contours()
    if vision_system.camera_settings.get_draw_contours():
        vision_system.camera_settings.set_draw_contours(False)

    cameraCalibrationService = CameraCalibrationService(
        chessboardWidth=vision_system.camera_settings.get_chessboard_width(),
        chessboardHeight=vision_system.camera_settings.get_chessboard_height(),
        squareSizeMM=vision_system.camera_settings.get_square_size_mm(),
        skipFrames=vision_system.camera_settings.get_calibration_skip_frames(),
        message_publisher = vision_system.message_publisher,
    )

    cameraCalibrationService.calibrationImages = vision_system.calibrationImages

    result, calibrationData, perspectiveMatrix, message = cameraCalibrationService.run(vision_system.rawImage)

    # Clear calibration images after each calibration attempt (success or failure)
    vision_system.calibrationImages.clear()
    log_if_enabled(enabled=log_enabled,
                   logger=logger,
                   level=LoggingLevel.INFO,
                   message=f"Cleared {len(vision_system.calibrationImages)} calibration images from memory",
                   broadcast_to_ui=False)

    if result:
        vision_system.cameraMatrix = calibrationData[1]
        vision_system.cameraDist = calibrationData[0]
        vision_system.perspectiveMatrix = perspectiveMatrix

        # Reload calibration data to ensure we're using the latest files
        vision_system.data_manager.loadCameraCalibrationData()
        vision_system.data_manager.loadPerspectiveMatrix()
        vision_system.data_manager.loadCameraToRobotMatrix()

        # Update system calibration status
        if vision_system.data_manager.cameraData is not None and vision_system.data_manager.cameraToRobotMatrix is not None:
            vision_system.isSystemCalibrated = True
            log_if_enabled(enabled=log_enabled,
                           logger=logger,
                           level=LoggingLevel.INFO,
                           message=f"Camera calibration completed and system recalibrated",
                           broadcast_to_ui=False)
    else:
        log_if_enabled(enabled=log_enabled,
                       logger=logger,
                       level=LoggingLevel.INFO,
                       message=f"[{vision_system.__class__.__name__}] Calibration failed",
                       broadcast_to_ui=False)

    if enableContourDrawingAfterCalibration:
        vision_system.camera_settings.set_draw_contours(True)
    return result, message
