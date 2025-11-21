def calibrate_camera(application):
    application.robotService.move_to_calibration_position()
    application.robotService._waitForRobotToReachPosition(application.robotService.robot_config.getCalibrationPositionParsed(), 1, delay=0)
    application.visionService.setRawMode(True)
    result = application.visionService.calibrate_camera()
    application.visionService.setRawMode(False)
    return result