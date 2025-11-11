import time

import cv2
import numpy as np
from VisionSystem.VisionSystem import VisionSystem
from GlueDispensingApplication.robot.RobotConfig import *
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
from GlueDispensingApplication.robot.RobotService import RobotService
from GlueDispensingApplication.settings.SettingsService import SettingsService

class DebugDraw:
    def __init__(self):
        # drawing settings
        self.marker_color = (0, 255, 0)  # Green
        self.marker_radius = 6
        self.text_color = (0, 255, 0)  # Green
        self.text_scale = 0.7
        self.text_thickness = 2
        self.text_font = cv2.FONT_HERSHEY_SIMPLEX
        self.text_offset = 10  # Offset for text position relative to marker center
        self.text_position = (self.marker_radius + self.text_offset, self.marker_radius + self.text_offset)
        self.image_center_color = (255, 0, 0)  # Blue
        self.image_center_radius = 4
        self.circle_thickness = -1

    def draw_marker_center(self, frame, marker_id,marker_centers):
        """Draw marker center on frame"""
        if marker_id in marker_centers:
            center_px = marker_centers[marker_id]
            cv2.circle(frame, center_px, self.marker_radius, self.marker_color, self.circle_thickness)
            cv2.putText(frame, f"ID {marker_id}", (center_px[0] + self.text_offset, center_px[1]),
                        self.text_font, self.text_scale, self.text_color, self.text_thickness)
            return True
        return False

    def draw_image_center(self, frame):
        """Draw image center on frame"""
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        image_center_px = (
            frame_width // 2,
            frame_height // 2
        )

        cv2.circle(frame, image_center_px, self.image_center_radius, self.image_center_color, 10)
        

class CalibrationPipeline:
    def __init__(self, required_ids=None,debug=False, step_by_step=False):
        # --- STATES ---
        self.debug = debug
        self.step_by_step = step_by_step
        if self.debug:
            self.debug_draw = DebugDraw()

        self.states = {
            "INITIALIZING": 0,
            "LOOKING_FOR_CHESSBOARD": 1,
            "CHESSBOARD_FOUND": 2,
            "ALIGN_TO_CHESSBOARD_CENTER": 3,
            "LOOKING_FOR_ARUCO_MARKERS": 4,
            "ALL_ARUCO_FOUND": 5,
            "COMPUTE_OFFSETS": 6,
            "ALIGN_ROBOT": 7,
            "DONE": 8
        }
        self.current_state = self.states["INITIALIZING"]

        # --- Vision system ---
        self.system = VisionSystem()
        self.system.camera_settings.set_draw_contours(False)

        # --- Settings Service ---
        settingsService = SettingsService()
        robot_config = settingsService.load_robot_config()

        # --- Robot ---
        self.robot = RobotWrapper(robot_config.robot_ip)
        self.settings_service = SettingsService()
        self.robot_service = RobotService(self.robot, self.settings_service,None)
        self.robot_service.moveToCalibrationPosition()

        self.chessboard_size = (
            self.system.camera_settings.get_chessboard_width(),
            self.system.camera_settings.get_chessboard_height()
        )
        self.square_size_mm = self.system.camera_settings.get_square_size_mm()
        self.bottom_left_chessboard_corner_px = None
        self.chessboard_center_px = None

        # ArUco requirements
        self.required_ids = set(required_ids if required_ids is not None else [])
        self.detected_ids = set()
        self.marker_centers = {}
        self.markers_offsets_mm = {}
        self.current_marker_id = 0

        self.Z_current = self.robot_service.getCurrentPosition()[2]
        print("Z_current:", self.Z_current)
        self.Z_target = 300  # desired height
        self.ppm_scale = self.Z_current / self.Z_target

        self.marker_centers_mm = {}
        self.robot_positions_for_calibration = {}

        self.PPM = None

        print(f"Looking for chessboard with size: {self.chessboard_size}")
        
        if self.step_by_step:
            print("Step-by-step mode enabled. Press SPACE to continue to next state after completion.")

    # --- Utils ---
    def wait_for_spacebar(self, state_name):
        """Wait for spacebar press to continue to next state in step-by-step mode"""
        if not self.step_by_step:
            return
            
        print(f"State '{state_name}' completed. Press SPACE to continue...")
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space bar
                print("Continuing to next state...")
                break
            elif key == ord('q'):
                print("Exiting...")
                cv2.destroyAllWindows()
                exit()
    def compute_ppm_from_corners(self, corners_refined):
        """Compute pixels-per-mm from chessboard corners"""
        cols, rows = self.chessboard_size
        horiz, vert = [], []
        # corners_refined has shape (n_corners, 1, 2), so we need to access [i, 0]
        for r in range(rows):  # horizontal neighbors
            base = r * cols
            for c in range(cols - 1):
                i1 = base + c
                i2 = base + c + 1
                pt1 = corners_refined[i1, 0]  # Extract (x, y) coordinates
                pt2 = corners_refined[i2, 0]  # Extract (x, y) coordinates
                horiz.append(np.linalg.norm(pt2 - pt1))

        for r in range(rows - 1):  # vertical neighbors
            for c in range(cols):
                i1 = r * cols + c
                i2 = (r + 1) * cols + c
                pt1 = corners_refined[i1, 0]  # Extract (x, y) coordinates
                pt2 = corners_refined[i2, 0]  # Extract (x, y) coordinates
                vert.append(np.linalg.norm(pt2 - pt1))

        all_d = np.array(horiz + vert, dtype=np.float32)
        if all_d.size == 0:
            return None

        avg_square_px = float(np.mean(all_d))
        ppm = avg_square_px / float(self.square_size_mm)
        print(f"PPM calculation debug: avg_square_px={avg_square_px:.3f}, square_size_mm={self.square_size_mm:.2f}, ppm={ppm:.3f}")
        return ppm

    def find_chessboard_and_compute_ppm(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

        if ret:
            print(f"Found chessboard! Detected {len(corners)} corners")
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), criteria
            )

            # --- Store bottom-left corner of chessboard in pixels ---
            cols, rows = self.chessboard_size
            self.bottom_left_chessboard_corner_px = corners_refined[(rows - 1) * cols, 0]  # (x, y)
            print(f"Bottom-left chessboard corner (px): {self.bottom_left_chessboard_corner_px}")
            
            # Draw bottom-left corner marker
            bottom_left_px = tuple(self.bottom_left_chessboard_corner_px.astype(int))
            cv2.circle(frame, bottom_left_px, 8, (0, 0, 255), -1)  # Red circle
            cv2.putText(frame, "BL", (bottom_left_px[0] + 10, bottom_left_px[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            
            # --- Compute chessboard center ---
            print(f"Chessboard dimensions: {rows} rows x {cols} cols")
            print(f"Row parity: {'even' if rows % 2 == 0 else 'odd'}, Col parity: {'even' if cols % 2 == 0 else 'odd'}")
            
            # For even-dimensioned chessboards, calculate center as average of 4 central corners
            if rows % 2 == 0 and cols % 2 == 0:
                print("Using 4-corner averaging method for even dimensions")
                # Even dimensions - use 4 central corners
                center_row1 = rows // 2 - 1
                center_row2 = rows // 2
                center_col1 = cols // 2 - 1
                center_col2 = cols // 2
                
                # Get the 4 central corner indices
                idx1 = center_row1 * cols + center_col1  # top-left of center
                idx2 = center_row1 * cols + center_col2  # top-right of center
                idx3 = center_row2 * cols + center_col1  # bottom-left of center
                idx4 = center_row2 * cols + center_col2  # bottom-right of center
                
                print(f"Central corner indices: {idx1}, {idx2}, {idx3}, {idx4}")
                
                # Average the 4 central corners
                center_x = (corners_refined[idx1, 0, 0] + corners_refined[idx2, 0, 0] + 
                           corners_refined[idx3, 0, 0] + corners_refined[idx4, 0, 0]) / 4.0
                center_y = (corners_refined[idx1, 0, 1] + corners_refined[idx2, 0, 1] + 
                           corners_refined[idx3, 0, 1] + corners_refined[idx4, 0, 1]) / 4.0
                
                self.chessboard_center_px = (float(center_x), float(center_y))
            else:
                print("Using single center corner method for odd dimensions")
                # Odd dimensions - use single center corner
                center_row = rows // 2
                center_col = cols // 2
                center_corner_index = center_row * cols + center_col
                
                print(f"Center corner: row {center_row}, col {center_col}, index {center_corner_index}")
                
                self.chessboard_center_px = (
                    float(corners_refined[center_corner_index, 0, 0]),  # x coordinate
                    float(corners_refined[center_corner_index, 0, 1])   # y coordinate
                )
            print(f"Chessboard center (px): {self.chessboard_center_px}")
            if self.debug:
                self.debug_draw.draw_image_center(frame)

            ppm = self.compute_ppm_from_corners(corners_refined)

            cv2.drawChessboardCorners(frame, self.chessboard_size, corners_refined, ret)
            return True, ppm
        else:
            cv2.putText(frame, "No chessboard detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.bottom_left_chessboard_corner_px = None
            return False, None

    def find_required_aruco_markers(self, frame):

        arucoCorners, arucoIds, image = self.system.detectArucoMarkers(frame)

        if arucoIds is not None:
            print(f"Detected {len(arucoIds)} ArUco markers")
            print(f"Marker IDs: {arucoIds.flatten()}")

            for i, marker_id in enumerate(arucoIds.flatten()):
                if marker_id in self.required_ids:
                    self.detected_ids.add(marker_id)
                    center = tuple(np.mean(arucoCorners[i][0], axis=0).astype(int))
                    self.marker_centers[marker_id] = center

                    # Draw center on frame
                    cv2.circle(frame, center, 5, (0, 255, 0), -1)
                    cv2.putText(frame, f"ID {marker_id}", (center[0] + 10, center[1]),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            print(f"Currently have: {self.detected_ids}")
            print(f"Still missing: {self.required_ids - self.detected_ids}")

            all_found = self.required_ids.issubset(self.detected_ids)
            if all_found:
                print("🎯 All required ArUco markers found!")
            return frame, all_found

        return frame, False

    def detect_specific_marker(self, marker_id, skip_frames_after_motion=True, skip_frames=5):
        marker_found = False
        arucoCorners = []
        arucoIds = []
        new_frame = None
        while not marker_found:
            _, new_frame, _ = self.system.run()

            if skip_frames_after_motion is True and skip_frames > 0:
                skip_frames -= 1
                continue

            arucoCorners, arucoIds, image = self.system.detectArucoMarkers(new_frame)
            print(f"Detection loop for specific marker {marker_id}")
            print(
                f"Detected {len(arucoIds)} ArUco markers at new pose ID: {arucoIds if arucoIds is not None else 'None'}")
            if arucoIds is not None and marker_id in arucoIds:
                marker_found = True

        return arucoCorners, arucoIds,new_frame

    def update_marker_centers(self, marker_id,corners,ids):
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id != marker_id:
                continue
            # update marker center in pixels
            center_px = tuple(np.mean(corners[i][0], axis=0).astype(int))
            self.marker_centers[marker_id] = center_px

            # Convert to mm relative to bottom-left of chessboard
            x_mm = (center_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.PPM
            y_mm = (self.bottom_left_chessboard_corner_px[1] - center_px[1]) / self.PPM

            # update marker center in mm
            self.marker_centers_mm[marker_id] = (x_mm, y_mm)
            print(f"Updated marker {marker_id} position in mm: {self.marker_centers_mm[marker_id]}")

    # --- Main loop ---
    def run(self):
        while True:
            _, frame, _ = self.system.run()
            state_name = [name for name, value in self.states.items() if value == self.current_state][0]
            print(f"Current state: {state_name} ({self.current_state})")
            if self.current_state == self.states["INITIALIZING"]:
                if frame is None:
                    continue
                else:
                    print("System initialized ✅")
                    self.current_state = self.states["LOOKING_FOR_CHESSBOARD"]

            elif self.current_state == self.states["LOOKING_FOR_CHESSBOARD"]:
                found, ppm = self.find_chessboard_and_compute_ppm(frame)
                if found:
                    self.PPM = ppm
                    print(f"✅ PPM computed: {self.PPM:.3f} px/mm")
                    
                    # Wait for stability before saving debug image
                    print("Stabilizing before saving chessboard image...")
                    time.sleep(2)
                    
                    # Flush camera buffer and capture stable frame
                    for _ in range(5):
                        self.system.run()
                    _, stable_frame, _ = self.system.run()
                    
                    if stable_frame is not None:
                        cv2.imwrite("chessboard_detected.png", stable_frame)
                        print("Saved stable chessboard_detected.png")
                    else:
                        cv2.imwrite("chessboard_detected.png", frame)
                        print("Saved chessboard_detected.png (fallback)")


                    self.current_state = self.states["CHESSBOARD_FOUND"]

            elif self.current_state == self.states["CHESSBOARD_FOUND"]:
                cv2.putText(frame, f"PPM calibrated: {self.PPM:.3f} px/mm",
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # self.current_state = self.states["ALIGN_TO_CHESSBOARD_CENTER"]
                self.current_state = self.states["LOOKING_FOR_ARUCO_MARKERS"]

            elif self.current_state == self.states["ALIGN_TO_CHESSBOARD_CENTER"]:
                # Calculate offset between image center and chessboard center
                image_center_px = (
                    self.system.camera_settings.get_camera_width() // 2,
                    self.system.camera_settings.get_camera_height() // 2
                )

                print(f"Image center (px): {image_center_px}")
                print(f"Chessboard center (px): {self.chessboard_center_px}")
                print(f"Camera width: {self.system.camera_settings.get_camera_width()}")
                print(f"Camera height: {self.system.camera_settings.get_camera_height()}")
                print(f"Current PPM: {self.PPM:.3f} px/mm")

                # Calculate offset in pixels
                offset_x_px = self.chessboard_center_px[0] - image_center_px[0]
                offset_y_px = self.chessboard_center_px[1] - image_center_px[1]
                
                print(f"Offset in pixels: X={offset_x_px:.2f}px, Y={offset_y_px:.2f}px")
                
                # Convert to mm using PPM
                offset_x_mm = offset_x_px / self.PPM
                offset_y_mm = offset_y_px / self.PPM
                
                print(f"Chessboard center offset from image center: X={offset_x_mm:.2f}mm, Y={offset_y_mm:.2f}mm")
                
                # Draw image center
                self.debug_draw.draw_image_center(frame)
                
                # Draw chessboard center
                chessboard_center_int = (int(self.chessboard_center_px[0]), int(self.chessboard_center_px[1]))
                cv2.circle(frame, chessboard_center_int, 10, (255, 255, 0), -1)  # Yellow circle
                cv2.putText(frame, "CB Center", (chessboard_center_int[0] + 15, chessboard_center_int[1] - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Wait for stability before saving debug image
                print("Stabilizing before saving alignment image...")
                time.sleep(2)
                
                # Flush camera buffer and capture stable frame
                for _ in range(5):
                    self.system.run()
                _, stable_frame, _ = self.system.run()
                
                if stable_frame is not None:
                    cv2.imwrite("alignment_before_move.png", stable_frame)
                    print("Saved stable alignment_before_move.png")
                else:
                    cv2.imwrite("alignment_before_move.png", frame)
                    print("Saved alignment_before_move.png (fallback)")
                
                # Move robot to align chessboard center with image center
                current_pose = self.robot_service.getCurrentPosition()
                x, y, z, rx, ry, rz = current_pose
                
                print(f"Current robot pose: {current_pose}")
                
                x_new = x + offset_x_mm
                y_new = y - offset_y_mm  # Y-axis is inverted in image coordinates
                new_position = [x_new, y_new, z, rx, ry, rz]
                
                print(f"Aligning robot to center chessboard at image center: {new_position}")
                print(f"Robot movement: X+={offset_x_mm:.2f}mm, Y-={offset_y_mm:.2f}mm")
                
                self.robot_service.moveToPosition(position=new_position,
                                                  tool=self.robot_service.robot_config.robot_tool,
                                                  workpiece=self.robot_service.robot_config.robot_user,
                                                  velocity=20,
                                                  acceleration=30,
                                                  waitToReachPosition=True)

                self.robot_service._waitForRobotToReachPosition(new_position,threshold = 1,delay=9,timeout=30)

                print("Robot reached the new position.")

                time.sleep(2)  # Allow some time for stabilization

                print("Robot alignment movement completed")

                self.current_state = self.states["LOOKING_FOR_ARUCO_MARKERS"]
                # self.current_state = self.states["DONE"]


            elif self.current_state == self.states["LOOKING_FOR_ARUCO_MARKERS"]:

                if self.debug:
                    self.debug_draw.draw_image_center(frame)

                # Wait for stability before detecting markers
                print("Ensuring camera stability before marker detection...")
                time.sleep(2)
                
                # Flush camera buffer and get stable frame
                for _ in range(5):
                    self.system.run()
                _, stable_frame, _ = self.system.run()
                
                if stable_frame is not None:
                    frame, all_found = self.find_required_aruco_markers(stable_frame)
                else:
                    frame, all_found = self.find_required_aruco_markers(frame)
                    
                if all_found:

                    self.current_state = self.states["ALL_ARUCO_FOUND"]

            elif self.current_state == self.states["ALL_ARUCO_FOUND"]:
                cv2.putText(frame, "All required ArUco markers found !", (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                self.marker_centers_mm = {}

                # Draw marker centers and convert to mm relative to bottom-left of chessboard

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    bottom_left_px = self.bottom_left_chessboard_corner_px  # use detected bottom-left corner

                    for marker_id, center_px in self.marker_centers.items():
                        # Draw in pixels

                        if self.debug and self.debug_draw:
                            self.debug_draw.draw_marker_center(frame, marker_id,self.marker_centers)

                        # Convert to mm relative to bottom-left
                        x_mm = (center_px[0] - bottom_left_px[0]) / self.PPM
                        y_mm = (bottom_left_px[1] - center_px[1]) / self.PPM  # y relative to bottom-left

                        self.marker_centers_mm[marker_id] = (x_mm, y_mm)

                print("Marker centers in mm relative to bottom-left:")

                for marker_id, center_mm in self.marker_centers_mm.items():
                    print(f"ID {marker_id}: {center_mm}")

                self.current_state = self.states["COMPUTE_OFFSETS"]

            elif self.current_state == self.states["COMPUTE_OFFSETS"]:

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    # Image center in pixels
                    image_center_px = (self.system.camera_settings.get_camera_width() // 2, self.system.camera_settings.get_camera_height() // 2)


                    # Convert image center to mm relative to bottom-left of chessboard
                    center_x_mm = (image_center_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.PPM
                    center_y_mm = (self.bottom_left_chessboard_corner_px[1] - image_center_px[1]) / self.PPM
                    print(f"Image center in mm relative to bottom-left: ({center_x_mm:.2f}, {center_y_mm:.2f})")

                    # Calculate offsets for all markers relative to image center
                    for marker_id, marker_mm in self.marker_centers_mm.items():
                        offset_x = marker_mm[0] - center_x_mm
                        offset_y = marker_mm[1] - center_y_mm
                        print(
                            f"Marker {marker_id}: position in mm = {marker_mm}, offset from image center = (X={offset_x:.2f}, Y={offset_y:.2f})")
                        self.markers_offsets_mm[marker_id] = (offset_x, offset_y)

                    self.current_state = self.states["ALIGN_ROBOT"]


            elif self.current_state == self.states["ALIGN_ROBOT"]:
                marker_id = self.current_marker_id

                # (1) Precomputed offset from calibration pose to marker
                calib_to_marker = self.markers_offsets_mm.get(marker_id, (0, 0))

                # (2) Current robot pose
                current_pose = self.robot_service.getCurrentPosition()
                x, y, z, rx, ry, rz = current_pose

                # (3) Calibration pose
                # calib_pose = CALIBRATION_POS
                calib_pose = self.robot_service.robot_config.getCalibrationPositionParsed()
                cx, cy, cz, crx, cry, crz = calib_pose

                # (4) Compute delta: calibration -> current
                calib_to_current = (x - cx, y - cy)

                # (5) Compute current -> marker
                current_to_marker = (
                    calib_to_marker[0] - calib_to_current[0],
                    calib_to_marker[1] - calib_to_current[1]
                )

                # (6) Apply correction at current pose
                x_new = x + current_to_marker[0]
                y_new = y + current_to_marker[1]
                z_new = self.Z_target
                new_position = [x_new, y_new, z_new, rx, ry, rz]

                # Capture "before alignment" image showing current marker position
                print(f"Capturing before-alignment image for marker {marker_id}...")
                time.sleep(1)  # Brief stability
                for _ in range(5):
                    self.system.run()
                _, before_frame, _ = self.system.run()
                
                if before_frame is not None:
                    # Draw current marker and image center on before frame
                    if marker_id in self.marker_centers:
                        center = self.marker_centers[marker_id]
                        cv2.circle(before_frame, center, 8, (0, 255, 0), -1)
                        cv2.putText(before_frame, f"ID {marker_id}", (center[0] + 10, center[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Draw image center
                    if self.debug and self.debug_draw:
                        self.debug_draw.draw_image_center(before_frame)
                    
                    cv2.imwrite(f"before_align_{marker_id}.png", before_frame)
                    print(f"Saved before_align_{marker_id}.png")

                print(f"Moving robot from current pose to marker {marker_id}: {new_position}")

                self.robot_service.moveToPosition(position=new_position,
                                                  tool=self.robot_service.robot_config.robot_tool,
                                                  workpiece=self.robot_service.robot_config.robot_user,
                                                  velocity=20,
                                                  acceleration=30,
                                                  waitToReachPosition=True)


                # Wait for robot and camera stability after movement
                print(f"Waiting for robot stability after moving to marker {marker_id}...")
                time.sleep(1)
                
                # Flush camera buffer before detecting specific marker
                print(f"Flushing camera buffer before detecting marker {marker_id}...")
                for _ in range(10):
                    self.system.run()

                # --- Re-detect marker at new height with enhanced stability ---
                arucoCorners,arucoIds,_ = self.detect_specific_marker(marker_id, skip_frames_after_motion=True, skip_frames=15)

                self.update_marker_centers(marker_id,arucoCorners,arucoIds)

                if self.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    bottom_left_px = self.bottom_left_chessboard_corner_px  # use detected bottom-left corner

                    # if self.debug_draw:
                    #     self.debug_draw.draw_marker_center(frame, marker_id, self.marker_centers)


                if marker_id in self.marker_centers_mm:
                    new_marker_px = self.marker_centers[marker_id]
                    # Compute new offset relative to image center
                    image_center_px = (
                        self.system.camera_settings.get_camera_width() // 2,
                        self.system.camera_settings.get_camera_height() // 2
                    )

                    if self.debug:
                        self.debug_draw.draw_image_center(frame)

                    newPpm = self.PPM * self.ppm_scale
                    print(f"New PPM at Z={self.Z_target}mm: {newPpm:.3f} px/mm")

                    # Calculate new offsets in pixels
                    new_offset_X_px= new_marker_px[0] - image_center_px[0]
                    new_offset_Y_px= new_marker_px[1] - image_center_px[1]

                    # Convert offsets to mm
                    new_offset_x_mm = new_offset_X_px/newPpm
                    new_offset_y_mm = new_offset_Y_px/newPpm

                    # Capture "before secondary alignment" image
                    print(f"Capturing before-secondary-alignment image for marker {marker_id}...")
                    time.sleep(1)  # Brief stability
                    for _ in range(5):
                        self.system.run()
                    _, before_secondary_frame, _ = self.system.run()
                    
                    if before_secondary_frame is not None:
                        # Draw marker and image center on before secondary frame
                        cv2.circle(before_secondary_frame, tuple(new_marker_px), 8, (0, 255, 0), -1)
                        cv2.putText(before_secondary_frame, f"ID {marker_id}", (new_marker_px[0] + 10, new_marker_px[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        # Draw image center
                        if self.debug and self.debug_draw:
                            self.debug_draw.draw_image_center(before_secondary_frame)
                        
                        # Show offset values on image
                        cv2.putText(before_secondary_frame, f"Offset: {new_offset_x_mm:.1f},{new_offset_y_mm:.1f}mm", 
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
                        cv2.imwrite(f"before_secondary_align_{marker_id}.png", before_secondary_frame)
                        print(f"Saved before_secondary_align_{marker_id}.png")

                    # Update robot position with new offsets
                    new_current_pose = self.robot_service.getCurrentPosition()
                    x,y,z,rx,ry,rz = new_current_pose
                    x+= new_offset_x_mm
                    y+= -new_offset_y_mm
                    new_current_pose = [x,y,z,rx,ry,rz]

                    print(f"Secondary alignment movement: X+={new_offset_x_mm:.2f}mm, Y-={new_offset_y_mm:.2f}mm")

                    self.robot_service.moveToPosition(position=new_current_pose,
                                                      tool=self.robot_service.robot_config.robot_tool,
                                                      workpiece=self.robot_service.robot_config.robot_user,
                                                      velocity=20,
                                                      acceleration=30,
                                                      waitToReachPosition=True)

                    # Wait for stability after secondary alignment
                    print(f"Waiting for stability after secondary alignment...")
                    time.sleep(3)
                    
                    # Enhanced detection with multiple attempts for after-secondary image
                    print(f"Re-detecting marker {marker_id} after secondary alignment...")
                    final_center = None
                    attempts = 0
                    max_attempts = 20
                    
                    while final_center is None and attempts < max_attempts:
                        attempts += 1
                        _, after_secondary_frame, _ = self.system.run()
                        
                        if after_secondary_frame is not None:
                            # Re-detect marker to get final position
                            final_corners, final_ids, _ = self.system.detectArucoMarkers(after_secondary_frame)
                            
                            if final_ids is not None and marker_id in final_ids.flatten():
                                for i, mid in enumerate(final_ids.flatten()):
                                    if mid == marker_id:
                                        final_center = tuple(np.mean(final_corners[i][0], axis=0).astype(int))
                                        print(f"Final marker {marker_id} detected at: {final_center} after {attempts} attempts")
                                        break
                                break
                            else:
                                if attempts % 5 == 0:
                                    print(f"Attempt {attempts}: Marker {marker_id} not detected, retrying...")
                    
                    if after_secondary_frame is not None and final_center is not None:
                        # Draw final marker position
                        cv2.circle(after_secondary_frame, final_center, 8, (0, 255, 0), -1)
                        cv2.putText(after_secondary_frame, f"ID {marker_id}", (final_center[0] + 10, final_center[1]),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        # Calculate final error
                        final_error_x = final_center[0] - image_center_px[0]
                        final_error_y = final_center[1] - image_center_px[1]
                        final_error = np.sqrt(final_error_x**2 + final_error_y**2)
                        
                        print(f"Final alignment result: Center at {final_center}, Error: {final_error:.1f}px")
                        cv2.putText(after_secondary_frame, f"Final Error: {final_error:.1f}px", 
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
                        # Draw image center
                        if self.debug and self.debug_draw:
                            self.debug_draw.draw_image_center(after_secondary_frame)
                        
                        cv2.imwrite(f"after_secondary_align_{marker_id}.png", after_secondary_frame)
                        print(f"Saved after_secondary_align_{marker_id}.png")
                        
                        # Verify alignment quality
                        if final_error < 5.0:
                            print(f"✅ Excellent alignment! Error < 5px")
                        elif final_error < 10.0:
                            print(f"✅ Good alignment! Error < 10px")
                        else:
                            print(f"⚠️  Alignment may need improvement. Error: {final_error:.1f}px")
                    else:
                        print(f"❌ Failed to detect marker {marker_id} after secondary alignment!")
                        if after_secondary_frame is not None:
                            # Save frame even without marker detection for debugging
                            if self.debug and self.debug_draw:
                                self.debug_draw.draw_image_center(after_secondary_frame)
                            cv2.putText(after_secondary_frame, "MARKER NOT DETECTED", 
                                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            cv2.imwrite(f"after_secondary_align_{marker_id}_FAILED.png", after_secondary_frame)
                            print(f"Saved after_secondary_align_{marker_id}_FAILED.png for debugging")


                    print(f"New marker {marker_id} offset from image center at Z={self.Z_target}mm: "
                          f"X={new_offset_x_mm:.2f}, Y={new_offset_y_mm:.2f}")

                    # Draw marker 4 on the frame
                    # if self.debug_draw:
                    #     self.debug_draw.draw_marker_center(frame, marker_id, self.marker_centers)


                    self.current_state= self.states["DONE"]
                else:

                    print(f"Marker {marker_id} not detected at new pose.")
            elif self.current_state == self.states["DONE"]:
                marker_id = self.current_marker_id

                # Wait for robot stability after final alignment
                print("Waiting for robot stability after final alignment...")
                time.sleep(3)
                
                # FOR DEBUGGING AND VALIDATION ONLY REDETECT THE MARKER AND SHOW IT`S CENTER
                arucoCorners, arucoIds,frame = self.detect_specific_marker(marker_id,skip_frames_after_motion=True, skip_frames=10)

                self.update_marker_centers(marker_id, arucoCorners, arucoIds)

                if self.debug and self.debug_draw:
                    self.debug_draw.draw_marker_center(frame, marker_id, self.marker_centers)
                    self.debug_draw.draw_image_center(frame)

                # Capture additional stable frame for saving
                print("Capturing stable frame for final image...")
                for _ in range(5):
                    self.system.run()
                _, final_stable_frame, _ = self.system.run()
                
                if final_stable_frame is not None:
                    if self.debug and self.debug_draw:
                        self.debug_draw.draw_marker_center(final_stable_frame, marker_id, self.marker_centers)
                        self.debug_draw.draw_image_center(final_stable_frame)
                    cv2.imwrite(f"aligned_center_marker_{self.current_marker_id}.png", final_stable_frame)
                    print(f"Saved stable aligned_center_marker_{self.current_marker_id}.png")
                else:
                    cv2.imwrite(f"aligned_center_marker_{self.current_marker_id}.png", frame)
                    print(f"Saved aligned_center_marker_{self.current_marker_id}.png (fallback)")

                cv2.putText(frame, "Calibration complete! Press 'q' to exit.", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Get robot position after alignment and store it for calibration
                current_robot_position = self.robot_service.getCurrentPosition()
                self.robot_positions_for_calibration[marker_id] = current_robot_position
                print(f"Robot position for marker {marker_id} after alignment: {current_robot_position}")

                if self.current_marker_id < len(self.required_ids) - 1:
                    self.current_marker_id += 1
                    self.current_state = self.states["ALIGN_ROBOT"]
                else:
                    print("All markers processed. Calibration complete!")
                    self.current_state = self.states["DONE"]
                    break

            if frame is not None:
                cv2.imshow("Calibration State Machine", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    pipeline = CalibrationPipeline(required_ids=[0, 1, 2, 3, 4, 5, 6],
                                   debug=True, step_by_step=True)
    pipeline.run()
