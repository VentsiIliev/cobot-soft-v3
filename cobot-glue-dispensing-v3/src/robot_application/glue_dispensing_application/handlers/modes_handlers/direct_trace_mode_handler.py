import time

from robot_application.glue_dispensing_application.handlers.spraying_handler import publish_robot_trajectory, \
    start_path_execution
from frontend.pl_ui.contour_editor.widgets.SegmentSettingsWidget import default_settings

def handle_direct_tracing_mode(application):
    # from src.frontend.pl_ui.contour_editor.widgets.SegmentSettingsWidget import default_settings

    # application.clean_nozzle()
    application.move_to_spray_capture_position()
    application.message_publisher.publish_brightness_region(region="spray")
    # ✅ Direct contour tracing without matching
    time.sleep(2)

    newContours = application.visionService.contours
    if newContours is None:
        return False, "No contours found"

    # Transform contours to robot coordinates and convert to proper format
    paths = []
    generator = application.workpiece_to_spray_paths_generator
    for contour in newContours:
        robot_path = generator.contour_to_robot_path( contour, default_settings, 0, 0)
        paths.append((robot_path, default_settings))
        print(f"Final path points No Contour Matching: {len(robot_path)}")

    if paths:
        publish_robot_trajectory(application)
        application.move_to_spray_capture_position()
        start_path_execution(application,paths)

    return True,""