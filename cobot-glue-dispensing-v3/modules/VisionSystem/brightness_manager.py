import numpy as np

from libs.plvision.PLVision.PID.BrightnessController import BrightnessController


class BrightnessManager:
    def __init__(self, vision_system):
        self.brightnessAdjustment = 0
        self.adjustment = None
        self.vision_system = vision_system
        self.brightnessController = BrightnessController(
            Kp=self.vision_system.camera_settings.get_brightness_kp(),
            Ki=self.vision_system.camera_settings.get_brightness_ki(),
            Kd=self.vision_system.camera_settings.get_brightness_kd(),
            setPoint=self.vision_system.camera_settings.get_target_brightness()
        )


    def auto_brightness_control_off(self):
        self.vision_system.camera_settings.set_brightness_auto(False)


    def auto_brightness_control_on(self):
        self.vision_system.camera_settings.set_brightness_auto(True)


    def on_brighteness_toggle(self, mode):
        if mode == "start":
            self.vision_system.camera_settings.set_brightness_auto(True)
        elif mode == "stop":
            self.vision_system.camera_settings.set_brightness_auto(False)
        else:
            print(f"Invalid mode")

    def get_area_by_threshold(self):
        if self.vision_system.threshold_by_area == "pickup":
            print(
                f"Using pickup area for brightness adjustment with thresh = {self.vision_system.camera_settings.get_threshold_pickup_area()}")
            return self.vision_system.getPickupAreaPoints()
        elif self.vision_system.threshold_by_area == "spray":
            print(f"Using spray area for brightness adjustment with thresh = {self.vision_system.camera_settings.get_threshold()}")
            return self.vision_system.getSprayAreaPoints()

    #
    # def adjustBrightness(self, frame):
    #     """
    #     Adjusts the brightness of a frame.
    #     """
    #     # Get spray area points for brightness calculation
    #     area = self.get_area_by_threshold()
    #     adjustedFrame = self.brightnessController.adjustBrightness(frame, self.adjustment, area)
    #     currentBrightness = self.brightnessController.calculateBrightness(adjustedFrame, area)
    #     self.adjustment = self.brightnessController.compute(currentBrightness)
    #     adjustedFrame = self.brightnessController.adjustBrightness(frame, self.adjustment, area)
    #     return adjustedFrame

    def adjust_brightness(self):
        area_p1, area_p2, area_p3, area_p4 = (940, 612), (1004, 614), (1004, 662), (940, 660)
        area = np.array([area_p1, area_p2, area_p3, area_p4], dtype=np.float32)
        adjusted_frame = self.brightnessController.adjustBrightness(self.vision_system.image, self.brightnessAdjustment,area)
        current_brightness = self.brightnessController.calculateBrightness(adjusted_frame,area)
        self.brightnessAdjustment = self.brightnessController.compute(current_brightness)
        adjusted_frame = self.brightnessController.adjustBrightness(self.vision_system.image, self.brightnessAdjustment)
        self.vision_system.image = adjusted_frame