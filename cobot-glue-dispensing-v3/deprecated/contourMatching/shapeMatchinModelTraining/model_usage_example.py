#!/usr/bin/env python3
"""
Real-time contour matching demo using a pre-trained contour similarity model.

Features:
- Opens live camera feed
- Finds contours in real-time
- Click on any contour to set it as the target
- Continuously compares new contours to the target
- Draws matches in BLUE, non-matches in RED
"""

import cv2
import numpy as np

from GlueDispensingApplication.contourMatching.shapeMatchinModelTraining.modelManager import load_latest_model, predict_similarity
from GlueDispensingApplication.contourMatching.shapeMatchinModelTraining.featuresExtraction import compute_enhanced_features
from GlueDispensingApplication.workpiece.WorkpieceController import WorkpieceController
from API.shared.workpiece.WorkpieceService import WorkpieceService
from GlueDispensingApplication.workpiece.Workpiece import Workpiece

# ===============================================================
# Global variables
# ===============================================================
target_contour = None
target_features = None
target_image = None
model = None
window_name = "Contour Matcher"
import os
import sys
def ensure_project_root_contains(pkg_dir='system'):
    p = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.isdir(os.path.join(p, pkg_dir)):
            if p not in sys.path:
                sys.path.insert(0, p)
            try:
                os.chdir(p)
            except Exception:
                pass
            return
        parent = os.path.dirname(p)
        if parent == p:
            return
        p = parent

ensure_project_root_contains()


# ===============================================================
# Mouse click callback (fixed)
# ===============================================================
def select_contour(event, x, y, flags, param):
    global target_contour, target_image, target_features

    frame, contours = param  # we pass both frame and contours together

    if event == cv2.EVENT_LBUTTONDOWN:
        for cnt in contours:
            if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                target_contour = cnt
                target_image = frame.copy()
                # cv2.drawContours(target_image, [cnt], -1, (0, 255, 0), 2)
                target_features = None  # reset cached features
                print("🎯 Target contour selected!")
                return  # stop after first match


# ===============================================================
# Main live function
# ===============================================================


def main():
    from VisionSystem.VisionSystem import VisionSystem
    global model, target_contour, target_features

    MATCH_WORKPIECES = True

    workpieces = []
    if MATCH_WORKPIECES:
        wp_service = WorkpieceService()
        workpieces = wp_service.loadAllWorkpieces()

    print("🚀 Starting real-time contour matcher...")
    model = load_latest_model(
        save_dir="/home/plp/cobot-soft-v2.1.3/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/GlueDispensingApplication/contourMatching/saved_models"
    )

    system = VisionSystem()
    cv2.namedWindow(window_name)

    while True:
        contours, frame, _ = system.run()
        if frame is None:
            continue

        display = frame.copy()

        # Attach callback each frame with both frame and contours
        if MATCH_WORKPIECES:
            matches,uncertain,non_matches = match_workpiece(workpieces, contours)
            print(f"Found {len(matches)} matches with workpieces")
            if len(matches) > 0:
                for wp, cnt, result, confidence in matches:
                    color = (0,255, 0)
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(display, f"{wp.workpieceId}:{confidence:.2f}", (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if len(uncertain) > 0:
                for wp, cnt, result, confidence in uncertain:
                    color = (0, 255, 255)
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(display, f":{confidence:.2f}", (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if len(non_matches) > 0:
                for cnt in non_matches:
                    color = (0, 0, 255)
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                    # cv2.putText(display, f":{confidence:.2f}", (x, y - 5),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        else:
            cv2.setMouseCallback(window_name, select_contour, (frame, contours))

            # Show target overlay and predictions
            if target_contour is not None:


                if target_features is None:
                    target_features = compute_enhanced_features(target_contour, target_contour)
                for cnt in contours:
                    if cnt is target_contour or cv2.contourArea(cnt) < 100:
                        continue
                    try:

                        result, confidence, _ = predict_similarity(model, target_contour, cnt)

                        if result == "SAME":
                            result = 1
                            #color green
                            color = (0, 255, 0)
                        elif result == "UNCERTAIN":
                            result = -1
                            #color yellow
                            color = (0, 255, 255)
                        else:
                            # color red
                            color = (0, 0, 255)
                            result = 0

                        # print(f"Contour compared: Result={result}, Confidence={confidence:.2f},Color={color}")
                        x, y, w, h = cv2.boundingRect(cnt)
                        cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(display, f"{confidence}", (x, y - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    except Exception as e:
                        print(f"⚠️ Comparison error: {e}")

        cv2.imshow(window_name, display)
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            target_contour = None
            print("🔁 Reset target contour")

    # No cap, so no release needed for VisionSystem
    cv2.destroyAllWindows()


def match_workpiece(workpieces_list: list[Workpiece], contours: list[np.ndarray]):
    # if model is None:
    model = load_latest_model(
        save_dir="/home/plp/cobot-soft-v2.1.3/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/GlueDispensingApplication/contourMatching/saved_models"
    )
    matches = []
    uncertain = []
    non_matches = []

    # Make a copy of the list to safely remove contours
    remaining_contours = contours.copy()

    contour_index = 0
    while contour_index < len(remaining_contours):
        cnt = remaining_contours[contour_index]
        matched = False
        uncertain_for_this_cnt = False

        for wp in workpieces_list:
            try:
                wp_contour = wp.get_main_contour()
                result, confidence, _ = predict_similarity(model, wp_contour, cnt)

                if result == "SAME":
                    matches.append((wp, cnt, result, confidence))
                    wp.contour = cnt  # Update the workpiece's contour
                    matched = True
                    break  # stop at first match
                elif result == "UNCERTAIN":
                    uncertain_for_this_cnt = True
                    uncertain.append((wp, cnt, result, confidence))

            except Exception as e:
                print(f"⚠️ Comparison error: {e}")

        if not matched and not uncertain_for_this_cnt:
            # Only add to non_matches if it did not match any workpiece
            non_matches.append(cnt)

        # Remove the contour after processing, matched or not
        remaining_contours.pop(contour_index)
        # No increment needed because we just popped the current index

    return matches, uncertain, non_matches



if __name__ == "__main__":
    main()
