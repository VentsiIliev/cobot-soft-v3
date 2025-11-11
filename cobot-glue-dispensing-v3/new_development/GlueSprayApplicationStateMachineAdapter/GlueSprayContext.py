from typing import Dict, Any

from new_development.StateMachineFramework.v2 import BaseContext


class GlueSprayContext(BaseContext):
    """Extended context for glue spray application"""

    def __init__(self, original_application):
        super().__init__()
        self.original_app = original_application
        self.current_operation = None
        self.operation_params = {}
        self.safety_checks_enabled = True

    def get_robot_status(self) -> Dict[str, Any]:
        """Get current robot status"""
        try:
            # Access robot through original application
            return {
                'connected': hasattr(self.original_app, 'robotService') and self.original_app.robotService,
                'position': 'unknown',  # Could get actual position
                'status': 'ready'
            }
        except Exception as e:
            return {'connected': False, 'error': str(e)}

    def is_safe_to_operate(self) -> bool:
        """Check if it's safe to perform operations"""
        if not self.safety_checks_enabled:
            return True

        robot_status = self.get_robot_status()
        return robot_status.get('connected', False)