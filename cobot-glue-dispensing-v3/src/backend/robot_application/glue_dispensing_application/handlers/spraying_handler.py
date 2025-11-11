import cv2

def start_spraying(application,workpieces,debug):
    generator = application.workpiece_to_spray_paths_generator
    generated_paths = generator.generate_robot_paths(workpieces, debug)
    # ✅ Send all paths to robot
    if generated_paths:
        publish_robot_trajectory(application)
        application.move_to_spray_capture_position()
        start_path_execution(application,generated_paths)
    else:
        print("No valid paths generated")

    return True, ""


def publish_robot_trajectory(application):
    # Publish trajectory image and start message
    # To start the trajectory visualization on the UI
    # on the dashboard
    frame = application.visionService.captureImage()
    frame = cv2.resize(frame, (800, 450))
    application.message_publisher.publish_trajectory_image(frame)
    application.message_publisher.publish_trajectory_start()

def start_path_execution(application,paths):
    print(f"In spraying handler, paths to spray: {len(paths)}")
    print(f"Spray on: {application.settingsManager.glue_settings.get_spray_on()}")
    application.glue_dispensing_operation.traceContours(paths,
                                           spray_on=application.settingsManager.glue_settings.get_spray_on())

