
import time
from enum import Enum, auto

import cv2
import numpy as np

from backend.system.utils.custom_logging import log_warning_message
from modules.VisionSystem.data_loading import CAMERA_TO_ROBOT_MATRIX_PATH
from modules.robot.calibration import metrics, visualizer
from modules.robot.calibration.CalibrationVision import CalibrationVision
from modules.robot.calibration.axis_mapping import auto_calibrate_image_to_robot_mapping
from modules.robot.calibration.config_helpers import RobotCalibrationEventsConfig, RobotCalibrationConfig, \
    AdaptiveMovementConfig
from modules.robot.calibration.debug import DebugDraw
from modules.robot.calibration.logging import get_log_timing_summary, construct_chessboard_state_log_message, \
    construct_aruco_state_log_message, construct_compute_offsets_log_message, construct_align_robot_log_message, \
    construct_iterative_alignment_log_message, construct_calibration_completion_log_message
from modules.robot.calibration.robot_controller import CalibrationRobotController
from modules.robot.calibration.states.initializing import handle_initializing_state
from modules.robot.calibration.states.robot_calibration_states import RobotCalibrationStates
from backend.system.utils.custom_logging import LoggingLevel, log_if_enabled, \
    setup_logger, log_debug_message, log_info_message, log_error_message, LoggerContext

ENABLE_LOGGING = True

robot_calibration_logger = setup_logger("RobotCalibrationService") if ENABLE_LOGGING else None






class RobotCalibrationContext:
    def __init__(self):
        pass

class RobotCalibrationPipeline:
    def __init__(self, config:RobotCalibrationConfig,
                 adaptive_movement_config: AdaptiveMovementConfig = None,
                 events_config:RobotCalibrationEventsConfig=None):


        self.image_to_robot_mapping = None
        self.alignment_threshold_mm = adaptive_movement_config.target_error_mm

        if events_config is not None:
            self.broker = events_config.broker
            self.BROADCAST_TOPIC = events_config.calibration_log_topic
            self.CALIBRATION_START_TOPIC = events_config.calibration_start_topic
            self.CALIBRATION_STOP_TOPIC = events_config.calibration_stop_topic
            self.CALIBRATION_IMAGE_TOPIC = events_config.calibration_image_topic
            self.broadcast_events = True
        else:
            self.broadcast_events = False

        self.logger_context = LoggerContext(ENABLE_LOGGING,robot_calibration_logger,self.broadcast_events,self.BROADCAST_TOPIC)

        self.debug = config.debug
        self.step_by_step = config.step_by_step
        self.system = config.vision_system
        self.system.camera_settings.set_draw_contours(False)
        self.chessboard_size = (
            self.system.camera_settings.get_chessboard_width(),
            self.system.camera_settings.get_chessboard_height()
        )
        self.square_size_mm = self.system.camera_settings.get_square_size_mm()

        self.calibration_robot_controller = CalibrationRobotController(config.robot_service,
                                                                       adaptive_movement_config,
                                                                       self.logger_context)
        self.calibration_robot_controller.move_to_calibration_position()

        self.debug_draw = DebugDraw()

        self.current_state = RobotCalibrationStates.INITIALIZING
        time.sleep(2)

        self.bottom_left_chessboard_corner_px = None
        self.chessboard_center_px = None

        # ArUco requirements
        self.required_ids = set(config.required_ids)

        self.markers_offsets_mm = {}
        self.current_marker_id = 0

        self.Z_current = self.calibration_robot_controller.get_current_z_value()
        log_info_message(self.logger_context,message=f"Z_current: {self.Z_current}")

        self.Z_target = config.z_target  # desired height
        self.ppm_scale = self.Z_current / self.Z_target

        self.robot_positions_for_calibration = {}
        self.camera_points_for_homography = {}

        # Iterative alignment tracking
        self.iteration_count = 0
        self.max_iterations = 50
        
        # Optimization parameters
        
        self.min_camera_flush = 5  # Reduce camera buffer flushing
        self.fast_iteration_wait = 1  # Shorter wait time for iterations
        self.max_acceptable_calibration_error =1

        # Live visualization
        self.live_visualization = config.live_visualization  # Enable live camera feed
        self.show_debug_info = True  # Show state and error info on feed
        
        # Timing and performance tracking
        self.state_timings = {}  # Track time spent in each state
        self.current_state_start_time = None
        self.total_calibration_start_time = None

        self.calibration_vision = CalibrationVision(self.system,
                                                    self.chessboard_size,
                                                    self.square_size_mm,
                                                    self.required_ids,
                                                    self.logger_context,
                                                    self.debug_draw,
                                                    self.debug)

        log_info_message(self.logger_context,message = f"Looking for chessboard with size: {self.chessboard_size}")

    def get_current_state_name(self):
        return self.current_state.name

    def draw_live_overlay(self, frame, current_error_mm=None):
        """Draw comprehensive live visualization overlay"""
        if not self.live_visualization:
            return frame

        # Get current state name
        state_name = self.get_current_state_name()

        # Draw image center (always visible)
        if hasattr(self, 'debug_draw'):
            self.debug_draw.draw_image_center(frame)

        # Draw progress bar
        progress = (self.current_marker_id / len(self.required_ids)) * 100 if self.required_ids else 0
        visualizer.draw_progress_bar(frame, progress)
        visualizer.draw_status_text(frame,state_name)

        # Current marker info
        if hasattr(self, 'current_marker_id') and self.required_ids:
            required_ids_list = sorted(list(self.required_ids))
            if self.current_marker_id < len(required_ids_list):
                current_marker = required_ids_list[self.current_marker_id]
                visualizer.draw_current_marker_info(frame,current_marker, self.current_marker_id, required_ids_list)

        # Iteration info (during iterative alignment)
        if self.current_state == RobotCalibrationStates.ITERATE_ALIGNMENT:
            visualizer.draw_iteration_info(frame,self.iteration_count,self.max_iterations)

            if current_error_mm is not None:
                visualizer.draw_current_error_mm(frame,current_error_mm, self.alignment_threshold_mm)


        visualizer.draw_progress_text(frame,progress)
        return frame

    def show_live_feed(self, frame, current_error_mm=None, window_name="Calibration Live Feed", draw_overlay=True,broadcast_image=False):
        """Show live camera feed with overlays"""

        if broadcast_image:
            self.broker.publish(self.CALIBRATION_IMAGE_TOPIC, frame)

        if not self.live_visualization:
            return False

        # Detect markers in current frame for live display
        current_markers = {}
        arucoCorners, arucoIds, _ = self.system.detectArucoMarkers(image=frame)

        if arucoIds is not None:
            for i, marker_id in enumerate(np.array(arucoIds).flatten()):
                # Only process markers that are in required_ids
                if marker_id in self.required_ids:
                    # Get top-left corner (first corner) of the ArUco marker
                    top_left_corner = tuple(arucoCorners[i][0][0].astype(int))
                    current_markers[marker_id] = top_left_corner

        # Add overlays with current frame markers
        if draw_overlay:
            display_frame = self.draw_live_overlay(frame.copy(), current_error_mm, current_markers)
        else:
            display_frame = frame.copy()
        # Show frame
        cv2.imshow(window_name, display_frame)

        # Check for exit key
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            log_debug_message(self.logger_context, "Live feed stopped by user (q pressed)")

            return True  # Signal to exit
        elif key == ord('s'):
            # Save current frame
            cv2.imwrite(f"live_capture_{time.time():.0f}.png", display_frame)

        elif key == ord('p'):
            # Pause/resume

            cv2.waitKey(0)

        return False  # Continue

    def start_state_timer(self, state_name):
        """Start timing for a state"""
        if self.current_state_start_time is not None:
            # End previous state
            self.end_state_timer()
        
        self.current_state_start_time = time.time()
        log_debug_message(self.logger_context, f"⏱️ Starting timer for state: {state_name}")

    def end_state_timer(self):
        """End timing for current state"""
        if self.current_state_start_time is None:
            return
            
        state_duration = time.time() - self.current_state_start_time
        state_name = self.get_current_state_name()
        
        # Store timing
        if state_name not in self.state_timings:
            self.state_timings[state_name] = []
        self.state_timings[state_name].append(state_duration)
        log_debug_message(self.logger_context, f"⏱️ State '{state_name}' completed in {state_duration:.3f} seconds")

        self.current_state_start_time = None
    
    def log_timing_summary(self):
        """Log comprehensive timing summary for bottleneck analysis"""
        if not self.state_timings:
            return
        summary = get_log_timing_summary(self.state_timings)
        log_debug_message(self.logger_context,summary)

    def flush_camera_buffer(self):
        # Flush camera buffer and get stable frame
        for _ in range(self.min_camera_flush):
            self.system.getLatestFrame()

    def run(self):
        try:
            log_debug_message(self.logger_context,f"=== STARTING CALIBRATION RUN METHOD ===")
            log_debug_message(self.logger_context,f"Required IDs: {self.required_ids}")

            if self.broadcast_events:
                self.broker.publish(self.CALIBRATION_START_TOPIC,"")
            # Start total calibration timer
            self.total_calibration_start_time = time.time()
        except Exception as e:
            print(f"ERROR in run method initialization: {e}")
            import traceback
            traceback.print_exc()
            raise

        while True:
            log_if_enabled(ENABLE_LOGGING, robot_calibration_logger, LoggingLevel.INFO,
                           "--- Calibration Pipeline State Machine ---",
                           broadcast_to_ui=self.broadcast_events, topic=self.BROADCAST_TOPIC)
            init_frame= self.system.getLatestFrame()
            log_if_enabled(ENABLE_LOGGING, robot_calibration_logger, LoggingLevel.INFO,
                           f"Current state:({self.current_state})",
                           broadcast_to_ui=self.broadcast_events, topic=self.BROADCAST_TOPIC)
            
            # Start timer for current state
            self.start_state_timer(self.current_state)
            
            if self.current_state == RobotCalibrationStates.INITIALIZING:
                result = handle_initializing_state(init_frame,self.logger_context)
                if not result.success:
                    continue

                self.current_state = result.next_state

            elif self.current_state == RobotCalibrationStates.AXIS_MAPPING:
                print(f"Performing axis mapping...")
                image_to_robot_mapping = auto_calibrate_image_to_robot_mapping(self.system,
                                                                               self.calibration_vision,
                                                                               self.calibration_robot_controller)
                self.image_to_robot_mapping = image_to_robot_mapping
                self.calibration_robot_controller.move_to_calibration_position()
                time.sleep(1)

                self.current_state = RobotCalibrationStates.LOOKING_FOR_CHESSBOARD

            elif self.current_state == RobotCalibrationStates.LOOKING_FOR_CHESSBOARD:
                chessboard_frame = None

                while chessboard_frame is None:
                    chessboard_frame = self.system.getLatestFrame()

                # found, ppm = self.find_chessboard_and_compute_ppm(chessboard_frame)
                # found, ppm,self.bottom_left_chessboard_corner_px = self.calibration_vision.find_chessboard_and_compute_ppm(chessboard_frame)
                result = self.calibration_vision.find_chessboard_and_compute_ppm(chessboard_frame)
                found = result.found
                ppm = result.ppm
                self.bottom_left_chessboard_corner_px = result.bottom_left_px
                message = construct_chessboard_state_log_message(
                    found=found,
                    ppm=ppm if found else None,
                    bottom_left_corner=self.bottom_left_chessboard_corner_px,
                    chessboard_center=self.chessboard_center_px,
                    debug_enabled=self.debug and self.debug_draw is not None
                )

                log_debug_message(self.logger_context,message)

                if found:
                    self.calibration_vision.PPM = ppm
                    # Draw the bottom-left corner
                    if self.bottom_left_chessboard_corner_px is not None:
                        bottom_left_px = tuple(self.bottom_left_chessboard_corner_px.astype(int))
                        cv2.circle(chessboard_frame, bottom_left_px, 8, (0, 0, 255), -1)  # Red circle
                        cv2.putText(chessboard_frame, "BL", (bottom_left_px[0] + 10, bottom_left_px[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                    # Draw the chessboard center
                    if self.chessboard_center_px is not None:
                        chessboard_center_int = (int(self.chessboard_center_px[0]), int(self.chessboard_center_px[1]))
                        cv2.circle(chessboard_frame, chessboard_center_int, 2, (255, 255, 0), -1)  # Yellow circle
                        cv2.putText(chessboard_frame, "CB Center",
                                    (chessboard_center_int[0] + 15, chessboard_center_int[1] - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)


                    # Draw image center
                    if self.debug and self.debug_draw:
                        self.debug_draw.draw_image_center(chessboard_frame)

                    cv2.imwrite("new_development/NewCalibrationMethod/chessboard_frame.png", chessboard_frame)
                    self.current_state = RobotCalibrationStates.CHESSBOARD_FOUND

            elif self.current_state == RobotCalibrationStates.CHESSBOARD_FOUND:
                log_debug_message(self.logger_context,f"CHESSBOARD FOUND at {self.chessboard_center_px}, aligning to center...")

                self.current_state = RobotCalibrationStates.LOOKING_FOR_ARUCO_MARKERS

            elif self.current_state == RobotCalibrationStates.LOOKING_FOR_ARUCO_MARKERS:

                self.flush_camera_buffer()

                # Capture frame for ArUco detection
                all_aruco_detection_frame = None
                while all_aruco_detection_frame is None:
                    log_debug_message(self.logger_context,"Capturing frame for ArUco detection...")

                    all_aruco_detection_frame = self.system.getLatestFrame()
                self.show_live_feed(all_aruco_detection_frame, 0, broadcast_image=self.broadcast_events)
                result = self.calibration_vision.find_required_aruco_markers(all_aruco_detection_frame)
                frame= result.frame
                all_found = result.found
                # save the aruco detection frame
                cv2.imwrite("new_development/NewCalibrationMethod/aruco_detection_frame.png", frame)
                if all_found:
                    self.current_state = RobotCalibrationStates.ALL_ARUCO_FOUND

            elif self.current_state == RobotCalibrationStates.ALL_ARUCO_FOUND:
                self.camera_points_for_homography = self.calibration_vision.marker_top_left_corners.copy()
                # marker_top_left_corners_mm will be computed below

                if self.calibration_vision.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    bottom_left_px = self.bottom_left_chessboard_corner_px  # use detected bottom-left corner

                    for marker_id, top_left_corner_px in self.calibration_vision.marker_top_left_corners.items():
                        # Convert to mm relative to bottom-left
                        x_mm = (top_left_corner_px[0] - bottom_left_px[0]) / self.calibration_vision.PPM
                        y_mm = (top_left_corner_px[1]-bottom_left_px[1]) / self.calibration_vision.PPM
                        # y_mm = (bottom_left_px[1] - top_left_corner_px[1]) / self.calibration_vision.PPM  # y relative to bottom-left


                        self.calibration_vision.marker_top_left_corners_mm[marker_id] = (x_mm, y_mm)

                # Build unified log message
                message = construct_aruco_state_log_message(
                    detected_ids=self.calibration_vision.detected_ids,
                    marker_top_left_corners_px=self.calibration_vision.marker_top_left_corners,
                    marker_top_left_corners_mm=self.calibration_vision.marker_top_left_corners_mm,
                    ppm=self.calibration_vision.PPM,
                    bottom_left_corner_px=self.bottom_left_chessboard_corner_px
                )

                log_debug_message(self.logger_context,message)


                self.current_state = RobotCalibrationStates.COMPUTE_OFFSETS

            elif self.current_state == RobotCalibrationStates.COMPUTE_OFFSETS:

                if self.calibration_vision.PPM is not None and self.bottom_left_chessboard_corner_px is not None:
                    # Image center in pixels
                    image_center_px = (self.system.camera_settings.get_camera_width() // 2,
                                       self.system.camera_settings.get_camera_height() // 2)

                    # Convert image center to mm relative to bottom-left of chessboard
                    center_x_mm = (image_center_px[0] - self.bottom_left_chessboard_corner_px[0]) / self.calibration_vision.PPM
                    center_y_mm = (image_center_px[1] - self.bottom_left_chessboard_corner_px[1]) / self.calibration_vision.PPM
                    # center_y_mm = (self.bottom_left_chessboard_corner_px[1] - image_center_px[1]) / self.calibration_vision.PPM

                    # Calculate offsets for all markers relative to image center
                    for marker_id, marker_mm in self.calibration_vision.marker_top_left_corners_mm.items():
                        offset_x = marker_mm[0] - center_x_mm
                        offset_y = marker_mm[1] - center_y_mm
                        # Store robot-space offsets
                        print("[CENTER_MM]", center_x_mm, center_y_mm)
                        print("[OFFSET_MM] marker", marker_id, ":", offset_x, offset_y)

                        self.markers_offsets_mm[marker_id] = (offset_x, offset_y)

                    # Build unified message
                    message = construct_compute_offsets_log_message(
                        ppm=self.calibration_vision.PPM,
                        bottom_left_corner_px=self.bottom_left_chessboard_corner_px,
                        image_center_px=image_center_px,
                        marker_top_left_corners_mm=self.calibration_vision.marker_top_left_corners_mm,
                        markers_offsets_mm=self.markers_offsets_mm,
                    )
                    log_debug_message(self.logger_context,message)

                    self.current_state = RobotCalibrationStates.ALIGN_ROBOT

            elif self.current_state == RobotCalibrationStates.ALIGN_ROBOT:
                required_ids_list = sorted(list(self.required_ids))
                marker_id = required_ids_list[self.current_marker_id]
                self.iteration_count = 0

                calib_to_marker = self.markers_offsets_mm.get(marker_id, (0, 0))
                # apply mapping to calib_to_marker
                calib_to_marker_mapped = self.image_to_robot_mapping.map(
                    calib_to_marker[0],
                    calib_to_marker[1]
                )
                calib_to_marker = calib_to_marker_mapped

                print(f"calib_to_marker for ID {marker_id}: {calib_to_marker}")
                current_pose = self.calibration_robot_controller.get_current_position()
                print(f"current_pose: {current_pose}")
                calib_pose = self.calibration_robot_controller.get_calibration_position()
                print(f"calib_pose: {calib_pose}")
                retry_attempted = False

                # Compute new target position
                x, y, z, rx, ry, rz = current_pose
                cx, cy, cz, crx, cry, crz = calib_pose

                calib_to_current = (x - cx, y - cy)
                print(f"calib_to_current: {calib_to_current}")
                # Map image offsets to robot space
                x_offset_before_mapping = calib_to_marker[0] - calib_to_current[0]
                y_offset_before_mapping = calib_to_marker[1] - calib_to_current[1]
                print(f"Before mapping: X {x_offset_before_mapping}, Y {y_offset_before_mapping}")
                # mapped_x_mm, mapped_y_mm = self.image_to_robot_mapping.map(
                #     x_offset_before_mapping,
                #     y_offset_before_mapping
                # )
                # print("After mapping:", mapped_x_mm, mapped_y_mm)
                # current_to_marker = (mapped_x_mm, mapped_y_mm)

                current_to_marker = (
                    calib_to_marker[0] - calib_to_current[0],
                    calib_to_marker[1] - calib_to_current[1]
                )

                x_new = x + current_to_marker[0]
                y_new = y + current_to_marker[1]

                z_new = self.Z_target
                new_position = [x_new, y_new, z_new, rx, ry, rz]


                # Move to position
                result = self.calibration_robot_controller.move_to_position(new_position, blocking=True)

                # Retry if failed
                if result != 0:
                    retry_attempted = True
                    if len(self.robot_positions_for_calibration) != 0:
                        self.calibration_robot_controller.move_to_position(self.robot_positions_for_calibration[0], blocking=False)

                    result = self.calibration_robot_controller.move_to_position(new_position, blocking=True)

                    if result != 0:
                        self.current_state = RobotCalibrationStates.ERROR

                # Create structured summary
                message = construct_align_robot_log_message(
                    marker_id=marker_id,
                    calib_to_marker=calib_to_marker,
                    current_pose=current_pose,
                    calib_pose=calib_pose,
                    z_target=self.Z_target,
                    result=result,
                    retry_attempted=retry_attempted,

                )

                log_debug_message(self.logger_context,message)

                if self.current_state != RobotCalibrationStates.ERROR:
                    time.sleep(1)
                    self.current_state = RobotCalibrationStates.ITERATE_ALIGNMENT

            elif self.current_state == RobotCalibrationStates.ITERATE_ALIGNMENT:

                required_ids_list = sorted(list(self.required_ids))
                marker_id = required_ids_list[self.current_marker_id]
                self.iteration_count += 1

                if self.iteration_count > self.max_iterations:
                    self.current_state = RobotCalibrationStates.DONE
                    continue

                # Capture frame
                capture_start = time.time()
                iteration_image = None
                attempt = 0

                while iteration_image is None:
                    attempt += 1
                    iteration_image = self.system.getLatestFrame()

                capture_time = time.time() - capture_start
                # Detect marker
                detection_start = time.time()

                result = self.calibration_vision.detect_specific_marker(iteration_image, marker_id)
                marker_found = result.found
                arucoCorners = result.aruco_corners
                arucoIds = result.aruco_ids

                detection_time = time.time() - detection_start

                if not marker_found:
                    log_debug_message(self.logger_context,f"Marker {marker_id} not found during iteration {self.iteration_count}!")
                    continue

                # Process and compute error
                processing_start = time.time()
                self.calibration_vision.update_marker_top_left_corners(marker_id, arucoCorners, arucoIds)
                image_center_px = (
                    self.system.camera_settings.get_camera_width() // 2,
                    self.system.camera_settings.get_camera_height() // 2
                )

                marker_top_left_px = self.calibration_vision.marker_top_left_corners[marker_id]
                offset_x_px = marker_top_left_px[0] - image_center_px[0]
                offset_y_px = marker_top_left_px[1] - image_center_px[1]
                current_error_px = np.sqrt(offset_x_px ** 2 + offset_y_px ** 2)
                newPpm = self.calibration_vision.PPM * self.ppm_scale
                current_error_mm = current_error_px / newPpm
                offset_x_mm = offset_x_px / newPpm
                offset_y_mm = offset_y_px / newPpm

                processing_time = time.time() - processing_start
                alignment_success = current_error_mm <= self.alignment_threshold_mm
                movement_time = stability_time = None

                result = None

                if alignment_success:
                    # Store pose
                    start_time = time.time()
                    while time.time() - start_time < 1.0:
                        current_pose = self.calibration_robot_controller.get_current_position()
                        time.sleep(0.05)

                    self.robot_positions_for_calibration[marker_id] = current_pose
                    self.debug_draw.draw_image_center(iteration_image)
                    self.show_live_feed(iteration_image, current_error_mm, broadcast_image=self.broadcast_events)
                    self.current_state = RobotCalibrationStates.DONE

                else:
                    # Compute next move
                    mapped_x_mm, mapped_y_mm = self.image_to_robot_mapping.map(offset_x_mm, offset_y_mm)
                    log_debug_message(
                        self.logger_context,
                        f"Marker {marker_id} offsets: image_mm=({offset_x_mm:.2f},{offset_y_mm:.2f}) -> mapped_robot_mm=({mapped_x_mm:.2f},{mapped_y_mm:.2f})"
                    )
                    iterative_position = self.calibration_robot_controller.get_iterative_align_position(current_error_mm, mapped_x_mm, mapped_y_mm,self.alignment_threshold_mm)
                    # iterative_position = self.calibration_robot_controller.get_iterative_align_position(current_error_mm, offset_x_mm, offset_y_mm,self.alignment_threshold_mm)
                    movement_start = time.time()
                    result = self.calibration_robot_controller.move_to_position(iterative_position, blocking=True)
                    movement_time = time.time() - movement_start

                    # Stability wait
                    stability_start = time.time()
                    time.sleep(self.fast_iteration_wait)
                    stability_time = time.time() - stability_start
                    self.debug_draw.draw_image_center(iteration_image)
                    self.show_live_feed(iteration_image, current_error_mm, broadcast_image=self.broadcast_events)

                # ✅ Structured summary log

                message = construct_iterative_alignment_log_message(
                    marker_id=marker_id,
                    iteration=self.iteration_count,
                    max_iterations=self.max_iterations,
                    capture_time=capture_time,
                    detection_time=detection_time,
                    processing_time=processing_time,
                    movement_time=movement_time,
                    stability_time=stability_time,
                    current_error_mm=current_error_mm,
                    current_error_px=current_error_px,
                    offset_mm=(offset_x_mm, offset_y_mm),
                    threshold_mm=self.alignment_threshold_mm,
                    alignment_success=alignment_success,
                    result=result

                )
                log_debug_message(self.logger_context,message)

            elif self.current_state == RobotCalibrationStates.DONE:
                if self.current_marker_id < len(self.required_ids) - 1:
                    self.current_marker_id += 1
                    self.current_state = RobotCalibrationStates.ALIGN_ROBOT
                else:
                    log_debug_message(self.logger_context,"All markers processed, proceeding to homography computation...")
                    self.current_state = RobotCalibrationStates.DONE
                    break

            elif self.current_state == RobotCalibrationStates.ERROR:
                log_error_message(self.logger_context,message = "An error occurred during calibration. Exiting...")

                break

        log_debug_message(self.logger_context,"--- Calibration Process Complete ---")

        # Sort by marker ID
        sorted_robot_items = sorted(self.robot_positions_for_calibration.items(), key=lambda x: x[0])
        sorted_camera_items = sorted(self.camera_points_for_homography.items(), key=lambda x: x[0])

        # Prepare corresponding points in sorted order
        robot_positions = [pos[:2] for _, pos in sorted_robot_items]
        camera_points = [pt for _, pt in sorted_camera_items]

        # Compute homography
        src_pts = np.array(camera_points, dtype=np.float32)
        dst_pts = np.array(robot_positions, dtype=np.float32)
        H_camera_center, status = cv2.findHomography(src_pts, dst_pts)

        # Test and validate
        average_error_camera_center, _ = metrics.test_calibration(
            H_camera_center, src_pts, dst_pts, self.logger_context,"transformation_to_camera_center"
        )

        if average_error_camera_center <= 1:
            np.save(CAMERA_TO_ROBOT_MATRIX_PATH, H_camera_center)
            log_info_message(self.logger_context, message=f"Saved homography matrix to {CAMERA_TO_ROBOT_MATRIX_PATH}")
        else:
            log_warning_message(self.logger_context, message="High reprojection error — recalibration suggested")


        # End final state timer
        self.end_state_timer()
        total_calibration_time = time.time() - self.total_calibration_start_time

        # ✅ Structured final log
        completion_log = construct_calibration_completion_log_message(
            sorted_robot_items=sorted_robot_items,
            sorted_camera_items=sorted_camera_items,
            H_camera_center=H_camera_center,
            status=status,
            average_error_camera_center=average_error_camera_center,
            matrix_path=CAMERA_TO_ROBOT_MATRIX_PATH,
            total_calibration_time=total_calibration_time
        )
        
        log_debug_message(self.logger_context,completion_log)
        # Log detailed timing analysis for bottleneck identification
        self.log_timing_summary()

        if self.broadcast_events:
            self.broker.publish(self.CALIBRATION_STOP_TOPIC,"")
        return


