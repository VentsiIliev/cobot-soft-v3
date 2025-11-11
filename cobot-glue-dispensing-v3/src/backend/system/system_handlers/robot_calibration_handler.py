import threading

from src.backend.system.robot.calibration.newRobotCalibUsingTopLeftCornersOfArucoMarkers import CalibrationPipeline

def calibrate_robot(application):
        # required_ids = [0,8,15,66,74,81,132,140,147,198,206,213,264,272,279]
        # required_ids = [0, 14, 28, 43, 57, 71, 86, 100, 115, 129, 143, 158, 172, 186, 201, 215, 229, 244, 258, 267, 272,
        #                 315, 330]
        required_ids = [0,1, 2,3,4,5, 6,8]
        # required_ids = list(range(0, 247))
        # required_ids = set(range(0, 247, 2))
        # required_ids = [0, 165, 313, 8, 173, 272, 15,150,329]
        # required_ids = [0, 8, 15, 165, 173, 180, 272, 313, 329]
        robot_calib_pipeline = CalibrationPipeline(system=application.visionService,
                                                   robot_service=application.robotService,
                                                   required_ids=required_ids,
                                                   debug=False,
                                                   step_by_step=False,
                                                   live_visualization=False)

        # robot_calib_pipeline.run()
        application.visionService.drawContours = False
        threading.Thread(target=robot_calib_pipeline.run, daemon=True).start()
        message = "Calibration started in background thread"
        image = None
        return True, message, image
