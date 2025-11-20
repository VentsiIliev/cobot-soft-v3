import threading
from typing import Optional, Tuple


from modules.shared.tools.ToolChanger import ToolChanger


class ToolManager:
    """
    Manages gripper/tool pickup and drop-off in a decoupled way.
    RobotService delegates tool operations to this manager.
    """

    def __init__(self, tool_changer: ToolChanger, robot_service):
        self.tool_changer = tool_changer
        self.robot_service = robot_service
        self.current_gripper: Optional[int] = None
        self._lock = threading.Lock()
        self.tools = {}

    def add_tool(self,name,tool):
        self.tools[name] = tool

    def pickup_gripper(self, gripper_id: int) -> Tuple[bool, Optional[str]]:
        """Pick up a gripper/tool from its slot."""
        with self._lock:
            if self.current_gripper == gripper_id:
                return False, f"Gripper {gripper_id} is already picked"

            slot_id = self.tool_changer.getSlotIdByGrippedId(gripper_id)
            self.tool_changer.setSlotAvailable(slot_id)

            positions, config = self._get_pickup_positions_and_config(gripper_id)
            if positions is None or config is None:
                return False, f"Unsupported gripper ID: {gripper_id}"

            try:
                for pos in positions:
                    self.robot_service.robot.moveL(
                        position=pos,
                        tool=self.robot_service.robot_config.robot_tool,
                        user=self.robot_service.robot_config.robot_user,
                        vel=config.velocity,
                        acc=config.acceleration,
                        blendR=1
                    )
            except Exception as e:
                import traceback
                traceback.print_exc()
                return False, str(e)

            self.robot_service.moveToStartPosition()
            self.current_gripper = gripper_id
            return True, None

    def drop_off_gripper(self, gripper_id: int) -> Tuple[bool, Optional[str]]:
        """Drop the currently held gripper/tool into its slot."""
        with self._lock:
            if self.current_gripper != gripper_id:
                return False, f"Gripper {gripper_id} is not currently held"

            slot_id = self.tool_changer.getSlotIdByGrippedId(gripper_id)
            if self.tool_changer.isSlotOccupied(slot_id):
                return False, f"Slot {slot_id} is already occupied"

            self.tool_changer.setSlotNotAvailable(slot_id)

            positions, config = self._get_dropoff_positions_and_config(gripper_id)
            if positions is None or config is None:
                return False, f"Unsupported gripper ID: {gripper_id}"

            try:
                for pos in positions:
                    self.robot_service.robot.moveL(
                        position=pos,
                        tool=self.robot_service.robot_config.robot_tool,
                        user=self.robot_service.robot_config.robot_user,
                        vel=config.velocity,
                        acc=config.acceleration,
                        blendR=1
                    )
            except Exception as e:
                import traceback
                traceback.print_exc()
                return False, str(e)

            self.current_gripper = None
            return True, None

    # ----------------------
    # Helper methods
    # ----------------------
    def _get_pickup_positions_and_config(self, gripper_id):
        """Return the pickup positions and configuration for a given gripper."""
        cfg = None
        positions = None
        rcfg = self.robot_service.robot_config

        if gripper_id == 0:
            cfg = rcfg.getSlot0PickupConfig()
            positions = rcfg.getSlot0PickupPointsParsed()
        elif gripper_id == 1:
            cfg = rcfg.getSlot1PickupConfig()
            positions = rcfg.getSlot1PickupPointsParsed()
        elif gripper_id == 4:
            cfg = rcfg.getSlot4PickupConfig()
            positions = rcfg.getSlot4PickupPointsParsed()
        return positions, cfg

    def _get_dropoff_positions_and_config(self, gripper_id):
        """Return the dropoff positions and configuration for a given gripper."""
        cfg = None
        positions = None
        rcfg = self.robot_service.robot_config

        if gripper_id == 0:
            cfg = rcfg.getSlot0DropoffConfig()
            positions = rcfg.getSlot0DropoffPointsParsed()
        elif gripper_id == 1:
            cfg = rcfg.getSlot1DropoffConfig()
            positions = rcfg.getSlot1DropoffPointsParsed()
        elif gripper_id == 4:
            cfg = rcfg.getSlot4DropoffConfig()
            positions = rcfg.getSlot4DropoffPointsParsed()
        return positions, cfg