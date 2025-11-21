import time

from core.operation_state_management import OperationResult


def handle_contour_matching_mode(application,nesting,debug)->OperationResult:

    if nesting:
        result = application.start_nesting(debug)
        if result.success is False:
            return result

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
        return OperationResult(success=False, message=Message.NO_WORKPIECE_DETECTED)

    return application.start_spraying(matches,debug)


