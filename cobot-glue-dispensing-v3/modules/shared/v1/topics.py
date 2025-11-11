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
    APPLICATION_STATE = "system/state"
    APPLICATION_INFO = "system/application"
    
    # System health and monitoring
    SYSTEM_HEALTH = "system/health"
    SYSTEM_METRICS = "system/metrics"
    SYSTEM_ERRORS = "system/errors"


class RobotTopics(TopicCategory):
    """Robot service and control topics"""
    
    # Robot service state
    SERVICE_STATE = "robot-service/state"
    
    # Robot trajectory and movement
    TRAJECTORY_START = "robot/trajectory/start"
    TRAJECTORY_STOP = "robot/trajectory/stop" 
    TRAJECTORY_BREAK = "robot/trajectory/break"
    TRAJECTORY_UPDATE_IMAGE = "robot/trajectory/updateImage"
    
    # Robot status and monitoring
    ROBOT_POSITION = "robot/position"
    ROBOT_STATUS = "robot/status"


class VisionTopics(TopicCategory):
    """Vision system and camera topics"""
    
    # Vision service state
    SERVICE_STATE = "vision-service/state"
    
    # Camera and image processing
    BRIGHTNESS_REGION = "vision-system/brightness-region"
    THRESHOLD_REGION = "vision-system/threshold"
    CAMERA_FEED = "vision-system/camera-feed"
    
    # Image processing results
    CONTOUR_DETECTION = "vision-system/contour-detection"
    ARUCO_DETECTION = "vision-system/aruco-detection"


class GlueTopics(TopicCategory):
    """Glue dispensing specific topics"""
    
    # Glue application control
    MODE_CHANGE = "glue-spray-app/mode"
    NOZZLE_CONTROL = "glue-app/nozzle"
    
    # Glue process monitoring
    GLUE_LEVEL = "glue-app/level"
    GLUE_PRESSURE = "glue-app/pressure"
    GLUE_TEMPERATURE = "glue-app/temperature"


class WorkpieceTopics(TopicCategory):
    """Workpiece management topics"""
    
    # Workpiece operations
    WORKPIECE_LOADED = "workpiece/loaded"
    WORKPIECE_PROCESSED = "workpiece/processed"
    WORKPIECE_VALIDATION = "workpiece/validation"
    
    # Workpiece data updates
    WORKPIECE_CREATED = "workpiece/created"
    WORKPIECE_UPDATED = "workpiece/updated"
    WORKPIECE_DELETED = "workpiece/deleted"


class SettingsTopics(TopicCategory):
    """Settings and configuration topics"""
    
    # Settings updates
    ROBOT_SETTINGS = "settings/robot"
    CAMERA_SETTINGS = "settings/camera" 
    GLUE_SETTINGS = "settings/glue"
    
    # Configuration changes
    CONFIG_UPDATED = "settings/config-updated"
    CONFIG_VALIDATED = "settings/config-validated"


class UITopics(TopicCategory):
    """User interface specific topics"""
    
    # Dashboard updates
    DASHBOARD_UPDATE = "ui/dashboard/update"
    
    # User interactions
    USER_ACTION = "ui/user-action"
    BUTTON_CLICKED = "ui/button-clicked"
    
    # Notifications
    TOAST_MESSAGE = "ui/toast"
    ERROR_DIALOG = "ui/error-dialog"


# ========== Topic Registry ==========

class TopicRegistry:
    """Central registry for all application topics"""
    
    # All topic categories
    CATEGORIES = {
        'system': SystemTopics,
        'robot': RobotTopics, 
        'vision': VisionTopics,
        'glue': GlueTopics,
        'workpiece': WorkpieceTopics,
        'settings': SettingsTopics,
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


# ========== Backwards Compatibility ==========

class LegacyTopics:
    """Mapping of old topic names to new standardized names"""
    
    LEGACY_MAPPING = {
        # Old -> New mappings for migration
        "system/state": SystemTopics.APPLICATION_STATE,
        "robot-service/state": RobotTopics.SERVICE_STATE,
        "vision-system/brightness-region": VisionTopics.BRIGHTNESS_REGION,
        "robot/trajectory/updateImage": RobotTopics.TRAJECTORY_UPDATE_IMAGE,
    }
    
    @classmethod
    def migrate_topic(cls, old_topic: str) -> str:
        """Get the new topic name for a legacy topic"""
        return cls.LEGACY_MAPPING.get(old_topic, old_topic)
    
    @classmethod
    def is_legacy_topic(cls, topic: str) -> bool:
        """Check if a topic is a legacy topic that should be migrated"""
        return topic in cls.LEGACY_MAPPING


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
            "is_legacy": LegacyTopics.is_legacy_topic(topic_name)
        }
    else:
        return {
            "topic": topic_name,
            "category": "unknown",
            "class": "unknown", 
            "is_legacy": LegacyTopics.is_legacy_topic(topic_name),
            "suggested_migration": LegacyTopics.migrate_topic(topic_name)
        }


def print_all_topics():
    """Print all registered topics organized by category"""
    print("🔗 Registered Message Broker Topics")
    print("=" * 50)
    
    for category, topics in TopicRegistry.get_all_topics().items():
        print(f"\n📁 {category.upper()} TOPICS:")
        for topic in topics:
            info = get_topic_info(topic)
            legacy_note = " (Legacy)" if info["is_legacy"] else ""
            print(f"  • {topic}{legacy_note}")


# ========== Example Usage ==========

if __name__ == "__main__":
    print_all_topics()
    
    # Example validation
    print(f"\nTopic validation:")
    print(f"  ✅ Valid: {TopicRegistry.validate_topic(SystemTopics.APPLICATION_STATE)}")
    print(f"  ❌ Invalid: {TopicRegistry.validate_topic('invalid/topic')}")
    
    # Example search
    print(f"\nTopics containing 'state':")
    for topic in TopicRegistry.list_topics_by_pattern('state'):
        print(f"  • {topic}")