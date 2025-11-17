import time


def handle_contour_matching_mode(application,nesting,debug):

    if nesting:
        nesting_result, nesting_message = application.start_nesting(debug)
        if nesting_result is False:
            return nesting_result, nesting_message

    # application.clean_nozzle()
    application.move_to_spray_capture_position()
    application.message_publisher.publish_brightness_region(region="spray")

    workpieces = application.get_workpieces()
    time.sleep(2)  # wait for camera to stabilize
    new_contours = application.visionService.contours
    result,matches = application.workpiece_matcher.perform_matching(workpieces,new_contours,debug)
    print(f"perform_matching result: {result} matches: {matches}")
    if not result:
        from modules.shared.localization.enums.Message import Message
        return False, Message.NO_WORKPIECE_DETECTED

    result,message = application.start_spraying(matches,debug)

    return result, message

