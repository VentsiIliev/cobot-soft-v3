import cv2
import numpy as np

from VisionSystem.VisionSystem import VisionSystem

#
# image_path = "/home/plp/cobot-soft-v2.1/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/calib.io_charuco_900x600_21x33_25_18_DICT_4X4_page-0001.jpg"  # Use a valid image file
# board = cv2.imread(image_path)
# #resise to 1280x720
# board = cv2.resize(board, (1280, 720))
# if board is None:
#     print(f"Failed to load image: {image_path}")
# else:
#     print(f"Loaded image: {image_path} with shape {board.shape}")

# required_ids_list = [0,8,15,66,74,81,132,140,147,198,206,213,264,272,279]
# required_ids = set(range(0, 346))
# required_ids = set(range(0, 247))
required_ids = set(range(0, 247, 2))

# required_ids_list = [0, 14, 28, 43, 57, 71, 86, 100, 115, 129, 143, 158, 172, 186, 201, 215, 229, 244, 258, 272, 287,
#                      301, 315, 330, 345]
# required_ids = set(required_ids_list)
detected_ids = set()
marker_centers = {}
system = VisionSystem()
print(f"Vision System initialized.")


def find_required_aruco_markers(frame):
    arucoCorners, arucoIds, image = system.detectArucoMarkers(image=frame)

    if arucoIds is not None:

        for i, marker_id in enumerate(arucoIds.flatten()):
            if marker_id in required_ids:
                detected_ids.add(marker_id)
                center = tuple(np.mean(arucoCorners[i][0], axis=0).astype(int))
                marker_centers[marker_id] = center

                # Draw center on frame
                # cv2.circle(frame, center, 5, (0, 255, 0), -1)
                # cv2.putText(frame, f"ID {marker_id}", (center[0] + 10, center[1]),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        all_found = required_ids.issubset(detected_ids)
        if not all_found:
            missing = required_ids - detected_ids
            print(f"Missing marker IDs: {sorted(missing)}")

        return frame, all_found

    return frame, False


while True:
    _, image, _ = system.run()


    if image is None:
        print("No image!")
        continue

    frame, all_found = find_required_aruco_markers(image)
    display_image = frame.copy()
    if marker_centers and len(marker_centers) > 0:
        for marker_id, center in marker_centers.items():  # print(f"Detected {len(arucoIds) if arucoIds is not None else 0} ArUco markers")
            # cv2.circle(display_image, center, 5, (0, 255, 0), -1)
            cv2.putText(display_image, f"{marker_id}", (center[0], center[1]),
                        # # Draw marker IDs if markers are detected
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 2)
    # if arucoIds is not None and len(arucoIds) > 0:
    #     for i, marker_id in enumerate(arucoIds):
    #         # Get the corner coordinates
    #         corners = arucoCorners[i][0]
    #         # Calculate center of the marker
    #         center = corners.mean(axis=0).astype(int)
    #         # Draw the marker ID at the center
    #         cv2.putText(display_image, str(marker_id[0]), tuple(center),
    #                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Board", display_image)
    key = cv2.waitKey(1000) & 0xFF
    if key == ord('q'):
        break
cv2.destroyAllWindows()


