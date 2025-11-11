# import numpy as np
#
# from system.utils.custom_logging import log_if_enabled
#
#
# def saveWorkAreaPoints(self, data):
#     """
#     Saves the work area points captured by the camera service.
#     Supports both legacy format (list of points) and new format (dict with area_type and corners).
#     """
#
#     print(f"In  VisionSystem.saveWorkAreaPoints with data: {data}")
#
#     if data is None or len(data) == 0:
#         return False, "No data provided to save"
#
#     try:
#         # Handle new format with area type
#         if isinstance(data, dict) and 'area_type' in data and 'corners' in data:
#             area_type = data['area_type']
#             points = data['corners']
#
#             if area_type not in ['pickup', 'spray']:
#                 return False, f"Invalid area_type: {area_type}. Must be 'pickup' or 'spray'"
#
#             if points is None or len(points) == 0:
#                 return False, f"No points provided for {area_type} area"
#
#             points_array = np.array(points, dtype=np.float32)
#
#             # Save to area-specific file
#             if area_type == 'pickup':
#                 np.save(PICKUP_AREA_POINTS_PATH, points_array)
#                 self.pickupAreaPoints = points_array
#                 message = f"Pickup area points saved successfully"
#                 log_if_enabled(enabled=ENABLE_LOGGING,
#                                logger=vision_system_logger,
#                                level=LoggingLevel.INFO,
#                                message=f"Saved pickup area points to {PICKUP_AREA_POINTS_PATH}",
#                                broadcast_to_ui=False)
#             else:  # spray
#                 np.save(SPRAY_AREA_POINTS_PATH, points_array)
#                 log_if_enabled(enabled=ENABLE_LOGGING,
#                                logger=vision_system_logger,
#                                level=LoggingLevel.INFO,
#                                message=f"Saved spray area points to {PICKUP_AREA_POINTS_PATH}",
#                                broadcast_to_ui=False)
#                 self.sprayAreaPoints = points_array
#                 message = f"Spray area points saved successfully"
#
#             # Also save to legacy path for backward compatibility if this is the first area saved
#             if not hasattr(self, 'workAreaPoints') or self.workAreaPoints is None:
#                 np.save(WORK_AREA_POINTS_PATH, points_array)
#                 self.workAreaPoints = points_array
#                 self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
#                 log_if_enabled(enabled=ENABLE_LOGGING,
#                                logger=vision_system_logger,
#                                level=LoggingLevel.INFO,
#                                message=f"Also saved to legacy work area points at {WORK_AREA_POINTS_PATH}",
#                                broadcast_to_ui=False)
#
#             return True, message
#
#         # Handle legacy format (list of points)
#         else:
#             points = data
#             points_array = np.array(points, dtype=np.float32)
#             np.save(WORK_AREA_POINTS_PATH, points_array)
#             self.workAreaPoints = points_array
#             self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
#             log_if_enabled(enabled=ENABLE_LOGGING,
#                            logger=vision_system_logger,
#                            level=LoggingLevel.INFO,
#                            message=f"Work area points saved successfully (legacy format)",
#                            broadcast_to_ui=False)
#             return True, "Work area points saved successfully (legacy format)"
#
#     except Exception as e:
#         log_if_enabled(enabled=ENABLE_LOGGING,
#                        logger=vision_system_logger,
#                        level=LoggingLevel.INFO,
#                        message=f"Error saving work area points: {str(e)}",
#                        broadcast_to_ui=False)
#         return False, f"Error saving work area points: {str(e)}"