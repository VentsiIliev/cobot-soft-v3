import math

import cv2
import numpy as np


def calculate_distance_between_points(pointA_3D, pointB_3D):
    """
    Calculate Euclidean distance between two points.

    Args:
        pointA: First point as (x, y)
        pointB: Second point as (x, y)

    Returns:
        float: Euclidean distance
    """
    distance = math.sqrt(
        (pointA_3D[0] - pointB_3D[0]) ** 2 +
        (pointA_3D[1] - pointB_3D[1]) ** 2 +
        (pointA_3D[2] - pointB_3D[2]) ** 2
    )

    return distance

def calculate_velocity(pointA_3D, pointB_3D, time_delta):
    """
    Calculate velocity between two 3D points given a time delta.

    Args:
        pointA_3D: First point as (x, y, z)
        pointB_3D: Second point as (x, y, z)
        time_delta: Time difference in seconds

    Returns:
        float: Velocity
    """
    distance = calculate_distance_between_points(pointA_3D, pointB_3D)
    if time_delta <= 0:
        return 0.0
    velocity = distance / time_delta
    return velocity

def calculate_acceleration(velocity_initial, velocity_final, time_delta,use_dt=False):
    """
    Calculate acceleration given initial and final velocities and time delta.

    Args:
        velocity_initial: Initial velocity
        velocity_final: Final velocity
        time_delta: Time difference in seconds

    Returns:
        float: Acceleration
    """
    if use_dt:
        if time_delta <= 0:
            return 0.0
        acceleration = (velocity_final - velocity_initial) / time_delta

    else:
        acceleration = velocity_final - velocity_initial

    return acceleration