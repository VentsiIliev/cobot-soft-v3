import time
import random


class DummyGlueSprayingApplication:
    def __init__(self):
        self.state = None
        self.robotService = self  # To satisfy ErrorState moveToStartPosition()

        # Control simulation outcomes
        # Options: "success", "failure", "error", or "random"
        self.simulation_mode = "success"

    def _simulate(self, success_msg, failure_msg="Operation failed"):
        """Helper to simulate different outcomes based on simulation_mode."""
        time.sleep(0.2)

        if self.simulation_mode == "success":
            return success_msg
        elif self.simulation_mode == "failure":
            return failure_msg
        elif self.simulation_mode == "error":
            raise Exception(f"{failure_msg} (simulated error)")
        elif self.simulation_mode == "random":
            if random.choice([True, False]):
                return success_msg
            else:
                raise Exception(f"{failure_msg} (random error)")
        else:
            return success_msg  # default fallback

    def start(self, contourMatching=True):
        print(f"[Dummy] Executing start with contourMatching={contourMatching}")
        return self._simulate("Start OK", "Start failed")

    def calibrateRobot(self):
        print("[Dummy] Calibrating robot...")
        return self._simulate("Calibration OK", "Calibration failed")

    def calibrateCamera(self):
        print("[Dummy] Calibrating camera...")
        return self._simulate("Camera Calibration OK", "Camera calibration failed")

    def createWorkpiece(self):
        print("[Dummy] Creating workpiece...")
        return self._simulate("Workpiece created", "Workpiece creation failed")

    def measureHeight(self):
        print("[Dummy] Measuring height...")
        return self._simulate("Height measured", "Height measurement failed")

    def updateToolChangerStation(self):
        print("[Dummy] Updating tool changer...")
        return self._simulate("Tool changer updated", "Tool changer update failed")

    def handleBelt(self):
        print("[Dummy] Handling belt...")
        return self._simulate("Belt handled", "Belt handling failed")

    def testRun(self):
        print("[Dummy] Running test...")
        return self._simulate("Test run OK", "Test run failed")

    def handleExecuteFromGallery(self):
        print("[Dummy] Executing from gallery...")
        return self._simulate("Gallery execution OK", "Gallery execution failed")

    def moveToStartPosition(self):
        print("[Dummy] Robot moved to safe start position")
