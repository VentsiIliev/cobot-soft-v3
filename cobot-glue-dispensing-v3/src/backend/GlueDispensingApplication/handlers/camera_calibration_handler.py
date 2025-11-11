def calibrate_camera(application):
    application.robotService.moveToCalibrationPosition()
    application.robotService._waitForRobotToReachPosition(application.robotService.robot_config.getCalibrationPositionParsed(), 1,
                                                   delay=0)
    application.visionService.setRawMode(True)
    result = application.visionService.calibrateCamera()
    application.visionService.setRawMode(False)
    return result