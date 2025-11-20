from core.services.robot_service.impl.base_robot_service import RobotService


def clean_nozzle(robot_service:RobotService):
    pos1, pos2 = robot_service.robot_config.getNozzleCleanPointsParsed()
    config = robot_service.robot_config.getNozzleCleanConfig()

    def move_to_nozzle_clean_point(robot_service, point):
        robot_service.robot.move_cartesian(position=point,
                                     vel=30,
                                     acc=10,
                                     tool=robot_service.robot_config.robot_tool,
                                     user=robot_service.robot_config.robot_user, )

        robot_service._waitForRobotToReachPosition(point, 1, 0)
        return 0

    move_to_nozzle_clean_point(robot_service, pos1)
    iterations = config.iterations
    print(f"Starting nozzle cleaning with {iterations} iterations.")
    while iterations > 0:
        move_to_nozzle_clean_point(robot_service,pos2)
        move_to_nozzle_clean_point(robot_service, pos1)

        iterations-=1

    move_to_nozzle_clean_point(robot_service,pos2)

    robot_service.move_to_calibration_position()
    robot_service._waitForRobotToReachPosition(robot_service.robot_config.getCalibrationPositionParsed(),1,0)
    ret = 0
    return ret



