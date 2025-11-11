import time

import cv2
import numpy as np


def updateToolChangerStation(robotService, visionService):
    """
       Updates the tool changer station by detecting ArUco markers, validating tool-slot alignment, and
       ensuring the correct tool is placed under each slot.
       This process includes image processing, tool-slot mapping, and robot motion.

       Steps involved:
       1. **Get Tool Changer Info**:
          Retrieve the current tool changer information, including slot and tool mappings.

       2. **ArUco Marker Detection**:
          Detect ArUco markers in the workspace to identify the positions of slots and tools.

       3. **Validate Marker Presence**:
          Check if any ArUco markers are detected. If no markers are found, return an error.

       4. **Filter and Process Valid Markers**:
          Filter the detected markers to only include those corresponding to valid slot and tool IDs.

       5. **Sort Slots and Tools by Y-coordinate**:
          Sort the detected slots and tools vertically (from top to bottom) to simplify tool-slot pairing.

       6. **Map Slots to Tools**:
          For each detected slot, find the nearest tool that is correctly aligned and positioned below the slot.

       7. **Update Slot Availability**:
          If no tool is detected under a slot, mark the slot as available. If a tool is detected, mark the slot as unavailable.

       8. **Validate Slot-Tool Pairing**:
          Compare the detected tool to the expected tool for each slot. If an incorrect tool is detected, it is flagged as misplaced.

       9. **Draw Marker Information**:
          Annotate the image with the detected slots, tools, and any misplaced tools for visual inspection.

       10. **Move Robot for Tool Check**:
           Move the robot to a predefined position to perform a final tool check.

       11. **Final Tool Check**:
           After the robot has moved, detect markers again to confirm the tool present at the tool changer.
       """
    toolChanger = robotService.toolChanger

    slotToolMap = toolChanger.getSlotToolMap()

    X_TOLERANCE = 150  # Allowable X-offset between slot and tool
    slotIds = toolChanger.getSlotIds()  # Slot markers
    toolIds = toolChanger.getReservedForIds()  # Tool markers
    validIds = set(slotIds + toolIds)  # Combine slot & tool IDs into a valid set
    expected_mapping = dict(zip(slotIds, toolIds))  # Expected slot-to-tool mapping

    time.sleep(1)

    arucoCorners, arucoIds, image = visionService.detectArucoMarkers()

    if arucoIds is None or len(arucoIds) == 0:
        print("No ArUco markers detected!")
        return False, "No ArUco markers detected!"

    arucoIds = arucoIds.flatten()  # Convert to a flat list

    # Strict filtering: Only process markers in slotIds or toolIds
    validMarkers = [(id, corners) for id, corners in zip(arucoIds, arucoCorners) if id in validIds]
    filteredIds = [id for id, _ in validMarkers]  # Only valid IDs

    if not validMarkers:
        print("No valid markers detected!")
        return False, "No valid markers detected!"

    detected_slots = []
    detected_tools = []
    marker_positions = {}  # Store marker bounding boxes

    # Process only valid markers
    for marker_id, corners in validMarkers:
        center_x = np.mean(corners[0][:, 0])  # Get center X
        center_y = np.mean(corners[0][:, 1])  # Get center Y
        marker_positions[marker_id] = corners[0]  # Store full bounding box

        if marker_id in slotIds:
            detected_slots.append((marker_id, center_x, center_y))  # Store slot marker
        elif marker_id in toolIds:
            detected_tools.append((marker_id, center_x, center_y))  # Store tool marker

    # Print detected slots and tools
    print("Detected Slots:", detected_slots)
    print("Detected Tools:", detected_tools)

    # Sort by Y-coordinate (top-to-bottom)
    detected_slots.sort(key=lambda x: x[2])  # Sort slots by Y
    detected_tools.sort(key=lambda x: x[2])  # Sort tools by Y

    correct_placement = True
    detected_mapping = {}
    misplaced_tools = []  # Store misplaced tools for red bounding box

    print("\nDEBUG: Detected Slot-Tool Mapping:")
    for slot_id, slot_x, slot_y in detected_slots:
        # Find the nearest tool below the slot
        matching_tool = -1  # Default if no tool is found
        if len(detected_tools) > 0:
            tool_id = detected_tools[0][0]

        for tool_id, tool_x, tool_y in detected_tools:
            if abs(slot_x - tool_x) < X_TOLERANCE and tool_y > slot_y:  # X alignment + tool below slot
                matching_tool = tool_id
                break  # Stop after finding the first valid tool

        detected_mapping[slot_id] = matching_tool  # Store detected slot-tool pairs

        print(f"   - Slot {slot_id} в†’ Detected Tool: {matching_tool} (Expected: {expected_mapping[slot_id]})")

        # Call tool changer functions
        if matching_tool == -1:
            print(f"Setting {slot_id} as available!")
            robotService.toolChanger.setSlotAvailable(slot_id)
        else:
            robotService.toolChanger.setSlotNotAvailable(slot_id)

        print("ToolChanger: ", robotService.toolChanger.slots)

        # Validate slot-tool match (allowing -1 but NOT incorrect tools)
        expected_tool = expected_mapping.get(slot_id)
        if matching_tool != -1 and expected_tool != matching_tool:
            correct_placement = False
            print(f"ERROR: Wrong tool under slot {slot_id}: Expected {expected_tool}, Found {matching_tool}")
            misplaced_tools.append(matching_tool)  # Store misplaced tool for red box contour_editor

    if correct_placement:
        print("All tools are correctly placed (or missing but allowed)!")
    else:
        print(f"Incorrect placement detected! Mapping: {detected_mapping}")

    # Draw only valid ArUco markers on the frame
    filteredCorners = [corners for id, corners in validMarkers]  # Filtered corners for valid markers
    cv2.aruco.drawDetectedMarkers(image, filteredCorners, np.array(filteredIds, dtype=np.int32))

    # Draw red rectangles around misplaced tools
    for tool_id in misplaced_tools:
        if tool_id in marker_positions:
            corners = marker_positions[tool_id].astype(int)
            cv2.polylines(image, [corners], isClosed=True, color=(0, 0, 255), thickness=3)  # Red bounding box

    toolCheckPos = [-350, 650, 200, 180, 0, 90]
    robotService.moveToPosition(toolCheckPos, 0, 0, 100, 30)

    maxAttempts = 30

    filteredIds = []
    while maxAttempts > 0:
        arucoCorners, arucoIds, image = visionService.detectArucoMarkers(flip=True)
        if arucoIds is not None:
            image_height = image.shape[0]
            # рџ”№ Strict filtering: Only process markers in slotIds or toolIds and in the lower half of the image
            validMarkers = [(id, corners) for id, corners in zip(arucoIds, arucoCorners)
                            if id.item() in validIds and np.mean(corners[0][:, 1]) > image_height / 2]

            filteredIds = [id for id, _ in validMarkers]  # Only valid IDs

            if validMarkers:
                break
        maxAttempts -= 1

    if len(filteredIds) != 0:
        currentTool = int(arucoIds[0])
        print("Current tool in tool check: ", currentTool)
        robotService.currentGripper = currentTool
    else:
        print("No tool detected in tool check")