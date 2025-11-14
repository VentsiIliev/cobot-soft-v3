from robot_application.glue_dispensing_application.tools.enums.Gripper import Gripper


class ToolChanger():

    """
      A class to manage the tool-changing process for a robotic arm or similar system.

    This class handles the management of tool slots, checking whether they are available or occupied,
    and provides functionalities for setting the availability status, retrieving tool positions,
    and managing reserved tools.
    """

    STATUS_AVAILABLE = -1
    STATUS_OCCUPIED = 0

    def __init__(self):
        """
               Initializes the ToolChanger with predefined slots and their occupancy status.

               The slots are defined with their positions and reserved tools (e.g., Gripper types).
               The available slots are marked as available (-1), and occupied slots are marked as occupied (0).

               Example of slot structure:
                   - slot 10: Reserved for Gripper.SINGLE and occupied
                   - slot 11: Reserved for Gripper.MOCK and available
                   - slot 12: Reserved for Gripper.MOCK2 and available
                   - slot 14: Reserved for Gripper.DOUBLE and occupied
               """
        # Initialize slots with position and occupancy status (0: empty, 1: occupied)
        # THE POSITIONS ARE NOT USE ANYMORE, BUT THEY ARE STILL HERE FOR COMPATIBILITY
        self.slots = {
            10: {"position": [], "occupied": self.STATUS_AVAILABLE,"reservedFor": Gripper.BELT},
            11: {"position": [], "occupied": self.STATUS_AVAILABLE,"reservedFor": Gripper.SINGLE},
            12: {"position": [], "occupied": self.STATUS_AVAILABLE,"reservedFor": Gripper.DOUBLE},
            13: {"position": [], "occupied": self.STATUS_AVAILABLE,"reservedFor": Gripper.MOCK3},
            14: {"position": [], "occupied": self.STATUS_AVAILABLE,"reservedFor": Gripper.MOCK4},
        }

    def getSlotPosition(self, slotId):
        """
               Returns the position of the specified slot.

               Args:
                   slotId (int): The ID of the slot whose position is to be retrieved.

               Returns:
                   list: A list representing the position of the specified slot, including [x, y, z, rotation, etc.].
               """
        return self.slots[slotId]["position"]

    def _setSlotOccupied(self, slotId, status):
        """
               Sets the occupancy status of the specified slot.

               Args:
                   slotId (int): The ID of the slot whose occupancy status is to be updated.
                   status (int): The status to set. Use -1 for available or 0 for occupied.

               Raises:
                   ValueError: If the slotId is not valid or the status is not -1 or 0.
               """
        # print("Slot ID: ", slotId)
        # print("Status: ", status)
        """Sets the slot as occupied (1) or empty (0)."""
        if slotId in self.slots and status in [-1, 0]:
            self.slots[slotId]["occupied"] = status
        else:
            raise ValueError("Invalid slot ID or status. Use -1 or 0.")

    def setSlotNotAvailable(self, slotId):
        """
        Marks the specified slot as occupied.

        Args:
            slotId (int): The ID of the slot to mark as occupied.
        """
        self._setSlotOccupied(slotId, self.STATUS_OCCUPIED)

    def setSlotAvailable(self, slotId):
        """
        Marks the specified slot as available.

        Args:
            slotId (int): The ID of the slot to mark as available.
        """
        self._setSlotOccupied(slotId, self.STATUS_AVAILABLE)

    def isSlotOccupied(self, slotId):
        """
              Checks if the specified slot is occupied.

              Args:
                  slotId (int): The ID of the slot to check.

              Returns:
                  bool: True if the slot is occupied, False if it is available.
              """
        print("Slot ID: ", slotId)
        occupied = self.slots[slotId]["occupied"] == self.STATUS_OCCUPIED
        print("Occupied: ", occupied)
        return occupied

    def getOccupiedSlots(self):
        """
        Returns a list of all occupied slot IDs.

        Returns:
            list: A list of slot IDs that are currently occupied.
        """
        return [slot for slot, data in self.slots.items() if data["occupied"] == self.STATUS_OCCUPIED]

    def getEmptySlots(self):
        """
        Returns a list of all empty slot IDs.

        Returns:
            list: A list of slot IDs that are currently available.
        """
        return [slot for slot, data in self.slots.items() if data["occupied"] == self.STATUS_AVAILABLE]

    def getReservedFor(self,slotId):
        """
              Returns the tool reserved for the specified slot.

              Args:
                  slotId (int): The ID of the slot.

              Returns:
                  Gripper: The Gripper instance reserved for the slot, or None if not reserved.
              """
        return self.slots[slotId]["reservedFor"]

    def isSlotReserved(self,slotId):
        """
             Checks if the specified slot is reserved for a tool.

             Args:
                 slotId (int): The ID of the slot.

             Returns:
                 bool: True if the slot is reserved for a tool, False otherwise.
             """
        return self.slots[slotId]["reservedFor"] != None

    def getSlotToolMap(self):
        """
        Returns a map representing the Aruco marker IDs for each slot and its corresponding tool.

        Returns:
            dict: A dictionary mapping slot IDs to tool marker IDs.
        """
        map = {
            10: 0,
            11: 1,
            12: 2,
            13: 3,
            14: 4
        }
        return map

    def getSlotIds(self):
        """
               Returns a list of all slot IDs.

               Returns:
                   list: A list of all slot IDs.
               """
        return list(self.slots.keys())

    def getReservedForIds(self):
        """
              Returns a list of all tool IDs reserved for slots.

              Returns:
                  list: A list of tool IDs reserved for slots, as integers.
              """
        return [int(data["reservedFor"].value) for slot, data in self.slots.items()]

    def getSlotIdByGrippedId(self, gripperId: int):
        print("getSlotIdByGrippedId Gripper ID: ", gripperId)
        for slot, data in self.slots.items():
            if int(data["reservedFor"].value) == gripperId:
                return slot

        print(f"Can not find slot for gripper {gripperId} gripper type = {type(gripperId)}:")

        return None

    # def getGripperPickupPositions_0(self):
    #     """
    #           Returns the slot ID reserved for a specific gripper ID.
    #
    #           Args:
    #               gripperId (int): The ID of the gripper whose reserved slot is to be retrieved.
    #
    #           Returns:
    #               int: The slot ID reserved for the specified gripper, or None if not found.
    #           """
    #     slot_0_pos_0 = SLOT_0_PICKUP_0
    #     slot_0_pos_1 = SLOT_0_PICKUP_1  # before pick up
    #     slot_0_pos_2 = SLOT_0_PICKUP_2  # pick up pos
    #     slot_0_pos_3 = SLOT_0_PICKUP_3  # pick up pos
    #     return [slot_0_pos_0,slot_0_pos_1,slot_0_pos_2,slot_0_pos_3]
    #
    # def getGripperDropoffPositions_0(self):
    #     """
    #           Returns the slot ID reserved for a specific gripper ID.
    #
    #           Args:
    #               gripperId (int): The ID of the gripper whose reserved slot is to be retrieved.
    #
    #           Returns:
    #               int: The slot ID reserved for the specified gripper, or None if not found.
    #           """
    #
    #     slot_0_pos_1 = SLOT_0_DROPOFF_1  # pick up pos
    #     slot_0_pos_2 = SLOT_0_DROPOFF_2  # pick up pos
    #     slot_0_pos_3 = SLOT_0_DROPOFF_3  # before pick up
    #     slot_0_pos_4 = SLOT_0_DROPOFF_4  # before pick up
    #
    #     return [slot_0_pos_1,slot_0_pos_2,slot_0_pos_3, slot_0_pos_4]
    #
    # def getGripperPickupPositions_1(self):
    #     """
    #           Returns the slot ID reserved for a specific gripper ID.
    #
    #           Args:
    #               gripperId (int): The ID of the gripper whose reserved slot is to be retrieved.
    #
    #           Returns:
    #               int: The slot ID reserved for the specified gripper, or None if not found.
    #           """
    #     slot_1_pos_0 = SLOT_1_PICKUP_0
    #     slot_1_pos_1 = SLOT_1_PICKUP_1
    #     slot_1_pos_2 = SLOT_1_PICKUP_2  # pick up
    #     return [slot_1_pos_0, slot_1_pos_1, slot_1_pos_2]
    #
    # def getGripperDropoffPositions_1(self):
    #     """
    #           Returns the slot ID reserved for a specific gripper ID.
    #
    #           Args:
    #               gripperId (int): The ID of the gripper whose reserved slot is to be retrieved.
    #
    #           Returns:
    #               int: The slot ID reserved for the specified gripper, or None if not found.
    #           """
    #
    #     slot_1_pos_1 = SLOT_1_DROPOFF_1
    #     slot_1_pos_2 = SLOT_1_DROPOFF_2  # pick up pos
    #     slot_1_pos_3 = SLOT_1_DROPOFF_3  # before pick up
    #     return [slot_1_pos_1, slot_1_pos_2, slot_1_pos_3]
    #
    # def getGripperPickupPositions_2(self):
    #     raise ValueError("Not implemented yet.")
    #
    # def getGripperDropoffPositions_2(self):
    #     raise ValueError("Not implemented yet.")
    #
    # def getGripperPickupPositions_4(self):
    #     raise ValueError("Not implemented yet.")
    #
    # def getGripperDropoffPositions_4(self):
    #     raise ValueError("Not implemented yet.")



if __name__ == "__main__":
    toolChanger = ToolChanger()
    print("Tool Changer initialized with slots:")
    for slotId, data in toolChanger.slots.items():
        print(f"Slot {slotId}: Position {data['position']}, Occupied: {data['occupied']}, Reserved For: {data['reservedFor']}")

    # Example usage
    print("Is slot 10 occupied?", toolChanger.isSlotOccupied(10))
    print("Available slots:", toolChanger.getEmptySlots())
    print("Occupied slots:", toolChanger.getOccupiedSlots())

    print("Slot tool map:", toolChanger.getSlotToolMap())
    print("Slot IDs:", toolChanger.getSlotIds())
    print("Reserved for IDs:", toolChanger.getReservedForIds())
    print("Slot ID for Gripper SINGLE:", toolChanger.getSlotIdByGrippedId(Gripper.SINGLE.value))
    print("Slot position for slot 10:", toolChanger.getSlotPosition(10))
    print("Is slot 11 reserved?", toolChanger.isSlotReserved(11))
    print("Reserved for slot 12:", toolChanger.getReservedFor(12))
    print("Setting slot 11 to available.")
    toolChanger.setSlotAvailable(11)
    print("Is slot 11 occupied now?", toolChanger.isSlotOccupied(11))
    print("Setting slot 11 to occupied.")
    toolChanger.setSlotNotAvailable(11)
    print("Is slot 11 occupied now?", toolChanger.isSlotOccupied(11))

