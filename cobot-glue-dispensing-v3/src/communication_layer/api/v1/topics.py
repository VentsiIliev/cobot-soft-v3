"""
Centralized Topic Definitions

This module provides a single source of truth for all message broker topics
used throughout the application. This prevents typos, makes refactoring easier,
and provides better organization.

Usage:
    from modules.shared.v1.topics import SystemTopics, RobotTopics
    
    # Subscribe to system state updates
    broker.subscribe(SystemTopics.APPLICATION_STATE, callback)
    
    # Publish robot service state
    broker.publish(RobotTopics.SERVICE_STATE, state)
"""

from enum import Enum


class TopicCategory:
    """Base class for topic category definitions"""
    
    @classmethod
    def all_topics(cls) -> list[str]:
        """Get all topic values for this category"""
        return [getattr(cls, attr) for attr in dir(cls) 
                if not attr.startswith('_') and not callable(getattr(cls, attr))]


class SystemTopics(TopicCategory):
    """System-level topics for application state and coordination"""
    
    # Application state management
    SYSTEM_STATE = "system/state"
    SYSTEM_MODE_CHANGE = "system/mode-change"
    CURRENT_PROCESS = "system/current-process"
    # Glue process state
    OPERATION_STATE = "application/operation/state"
    APPLICATION_STATE = "application/state"


class RobotTopics(TopicCategory):
    """Robot service and control topics"""
    
    # Robot service state
    SERVICE_STATE = "robot-service/state"
    
    # Robot trajectory and movement
    TRAJECTORY_START = "robot/trajectory/start"
    TRAJECTORY_STOP = "robot/trajectory/stop" 
    TRAJECTORY_BREAK = "robot/trajectory/break"
    TRAJECTORY_UPDATE_IMAGE = "robot/trajectory/updateImage"
    TRAJECTORY_POINT = "robot/trajectory/point"

    # Robot calibration -> feedback topics for the calibration process
    # they do not start stop the calibration but provide feedback
    ROBOT_CALIBRATION_LOG = "robot/calibration/log"
    ROBOT_CALIBRATION_START = "robot/calibration/start"
    ROBOT_CALIBRATION_STOP = "robot/calibration/stop"
    ROBOT_CALIBRATION_IMAGE = "robot/calibration/image"
    ROBOT_STATE = "robot/state" # example message -> {"state": self.robotState,"position": self.position, "speed": self.velocity, "accel": self.acceleration}


class VisionTopics(TopicCategory):
    """Vision system and camera topics"""
    
    # Vision service state
    SERVICE_STATE = "vision-service/state"
    LATEST_IMAGE = "vision-system/latest-image"
    CALIBRATION_IMAGE_CAPTURED = "vision-system/calibration-image-captured"
    # Camera and image processing
    BRIGHTNESS_REGION = "vision-system/brightness-region"
    THRESHOLD_REGION = "vision-system/threshold"
    CALIBRATION_FEEDBACK = "vision-system/calibration-feedback"
    THRESHOLD_IMAGE = "vision-system/threshold-image"
    AUTO_BRIGHTNESS = "vision-system/auto-brightness"
    AUTO_BRIGHTNESS_START = "vison-auto-brightness"
    AUTO_BRIGHTNESS_STOP = "vison-auto-brightness"
    TRANSFORM_TO_CAMERA_POINT = "vision-system/transform-to-camera-point"



class GlueTopics(TopicCategory):
    """Glue dispensing specific topics"""
    # Glue meter values
    GLUE_METER_1_VALUE = "GlueMeter_1/VALUE"
    GLUE_METER_2_VALUE = "GlueMeter_2/VALUE" 
    GLUE_METER_3_VALUE = "GlueMeter_3/VALUE"
    PROCESS_STATE = "glue-process/state"
    GLUE_DISPENSING_LOG = "glue-dispensing/log"

class UITopics(TopicCategory):
    """User interface specific topics"""
    # Language and localization
    LANGUAGE_CHANGED = "Language"



# ========== Topic Registry ==========

class TopicRegistry:
    """Central registry for all application topics"""
    
    # All topic categories
    CATEGORIES = {
        'system': SystemTopics,
        'robot': RobotTopics, 
        'vision': VisionTopics,
        'glue': GlueTopics,
        'ui': UITopics
    }
    
    @classmethod
    def get_all_topics(cls) -> dict[str, list[str]]:
        """Get all topics organized by category"""
        return {category: topic_class.all_topics() 
                for category, topic_class in cls.CATEGORIES.items()}
    
    @classmethod
    def find_topic(cls, topic_name: str) -> tuple[str, str] | None:
        """Find which category a topic belongs to"""
        for category, topic_class in cls.CATEGORIES.items():
            if topic_name in topic_class.all_topics():
                return category, topic_class.__name__
        return None
    
    @classmethod
    def validate_topic(cls, topic_name: str) -> bool:
        """Validate if a topic is registered"""
        return cls.find_topic(topic_name) is not None
    
    @classmethod
    def list_topics_by_pattern(cls, pattern: str) -> list[str]:
        """Find topics matching a pattern"""
        all_topics = []
        for topic_class in cls.CATEGORIES.values():
            all_topics.extend(topic_class.all_topics())
        
        return [topic for topic in all_topics if pattern.lower() in topic.lower()]

# ========== Utility Functions ==========

def get_topic_info(topic_name: str) -> dict[str, str]:
    """Get detailed information about a topic"""
    result = TopicRegistry.find_topic(topic_name)
    if result:
        category, class_name = result
        return {
            "topic": topic_name,
            "category": category,
            "class": class_name,
        }
    else:
        return {
            "topic": topic_name,
            "category": "unknown",
            "class": "unknown",
        }


def print_all_topics():
    """Print all registered topics organized by category"""
    print("🔗 Registered Message Broker Topics")
    print("=" * 50)
    
    for category, topics in TopicRegistry.get_all_topics().items():
        print(f"\n📁 {category.upper()} TOPICS:")
        for topic in topics:
            info = get_topic_info(topic)
            print(f"  • {info['topic']}  (Class: {info['class']})")


# ========== Example Usage ==========

if __name__ == "__main__":
    print_all_topics()
    
    # Example validation
    print(f"\nTopic validation:")
    print(f"  ✅ Valid: {TopicRegistry.validate_topic(SystemTopics.SYSTEM_STATE)}")
    print(f"  ❌ Invalid: {TopicRegistry.validate_topic('invalid/topic')}")
    
    # Example search
    print(f"\nTopics containing 'state':")
    for topic in TopicRegistry.list_topics_by_pattern('state'):
        print(f"  • {topic}")