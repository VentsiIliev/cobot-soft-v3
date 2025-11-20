from dataclasses import dataclass

import cv2

from core.base_robot_application import ApplicationState
# from modules.VisionSystem.VisionSystem import VisionSystemState
from core.system_state_management import ServiceState

@dataclass
class CreateWorkpieceData:
    estimatedHeight: float
    contourArea: float
    workpiece_contour: list
    scaleFactor: float
    image: object
    message: str
    originalContours: list


@dataclass
class CrateWorkpieceResult:
    success: bool
    message: str
    data: object

    def to_dict(self):
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data
        }

class CreateWorkpieceHandler:
    def __init__(self, application):
        self.application = application
        self.workpiece_step = 1

    def create_workpiece(self) -> CrateWorkpieceResult:
        if self.workpiece_step == 1:
            result = self.create_workpiece_step_1()
            if result.success:
                self.workpiece_step = 2

            return result

        elif self.workpiece_step == 2:
            result = self.create_workpiece_step_2()
            if result.success:
                self.workpiece_step = 2

            return result
        else:
            raise ValueError(f"Invalid workpiece creation step: {self.workpiece_step}")

    def create_workpiece_step_1(self)->CrateWorkpieceResult:
        # if robot service is not in idle state, return error
        if self.application.state_manager.state != ApplicationState.IDLE:
            return CrateWorkpieceResult(success=False, message="Application not in IDLE state", data=None)

        ret = self.application.move_to_spray_capture_position()
        if ret != 0:
            return CrateWorkpieceResult(success=False, message="Failed to move to spray capture position", data=None)

        return CrateWorkpieceResult(success=True, message="", data=None)

    def create_workpiece_step_2(self) -> CrateWorkpieceResult:
        # if robot service is not in idle state, return error
        if self.application.state_manager.state != ApplicationState.IDLE:
            return CrateWorkpieceResult(success=False, message="Application not in IDLE state", data=None)

        # if vision service is not running, return error
        if self.application.state_manager.visonServiceState != ServiceState.IDLE:
            return CrateWorkpieceResult(success=False, message="Vision service not in RUNNING state", data=None)
        self.create_workpiece_step_1()
        # Store original contours for later use
        originalContours = self.application.visionService.contours

        externalContour = []
        if originalContours is not None and len(originalContours) > 0:
            contour = originalContours[0]
            contourArea = cv2.contourArea(contour)
            externalContour = contour
        else:
            # No contours found - set defaults and prepare for manual editing
            originalContours = []
            contour = []
            centroid = [0, 0]
            contourArea = 0

        # Capture image for workpiece creation
        createWpImage = self.application.visionService.captureImage()

        estimatedHeight = self.measure_workpiece_height()

        # Set default values (height measurement is currently disabled)
        scaleFactor = 1


        # Set message based on whether contours were found automatically
        if originalContours is not None and len(originalContours) > 0:
            message = "Workpiece created successfully"
        else:
            message = "No contours found - opening contour editor for manual setup"

        # Prepare return data
        data = CreateWorkpieceData(
            estimatedHeight=estimatedHeight,
            contourArea=contourArea,
            workpiece_contour=externalContour,
            scaleFactor=scaleFactor,
            image=createWpImage,
            message=message,
            originalContours=originalContours
        )


        # Always return True to allow contour editor to open, even if no contours found
        return CrateWorkpieceResult(success=True, message=message, data=data)

    def measure_workpiece_height(self):
        return 40  # Default height in mm
        """
                HEIGHT MEASUREMENT SECTION (DISABLED)

                The commented-out section below was used for height measuring using the laser line.

                This code snippet was designed to:
                1. Turn on the laser
                2. Capture the current position of the robot
                3. Use the camera to get the current image and calculate the TCP to image center offsets
                4. Move the robot to a specific position for height measurement
                5. Capture a new image at the height measurement point
                6. Estimate the height by measuring the captured image
                7. Turn off the laser
                8. Return the robot to its start position after height measurement

                # laserController = Laser()
                # laserController.turnOn()
                #
                # initialX = self.robotService.startPosition[0]
                # initialY = self.robotService.startPosition[1]
                # image = self.visionService.captureImage()
                #
                # cameraToRobotMatrix = self.visionService.getCameraToRobotMatrix()
                # imageCenter = (image.shape[1] // 2, image.shape[0] // 2)
                # offsets = Teaching.calculateTcpToImageCenterOffsets(
                #     imageCenter, initialX, initialY, cameraToRobotMatrix
                # )
                #
                # position = [centroid[0], centroid[1] + offsets[1], 300, 180, 0, 0]
                # self.robotService.moveToPosition(
                #     position, 0, 0, 100, 30, waitToReachPosition=True
                # )
                #
                # time.sleep(1)
                #
                # # Capture new frame from the height measurement point
                # newFrame = self.visionService.captureImage()
                # estimatedHeight = self.measureHeight(newFrame, maxAttempts=10, debug=False)
                # laserController.turnOff()
                # self.robotService.moveToStartPosition()
                """