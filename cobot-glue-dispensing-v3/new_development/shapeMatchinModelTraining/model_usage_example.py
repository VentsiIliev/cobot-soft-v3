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
import os
from modelManager import load_latest_model, predict_similarity
from featuresExtraction import compute_enhanced_features

# ===============================================================
# Global variables
# ===============================================================
target_contour = None
target_features = None
target_image = None
model = None
window_name = "Contour Matcher"


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

    print("🚀 Starting real-time contour matcher...")
    model = load_latest_model(
        save_dir="/home/plp/cobot-soft-v2.1.3/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/new_development/saved_models"
    )

    system = VisionSystem()
    cv2.namedWindow(window_name)

    while True:
        contours, frame, _ = system.run()
        if frame is None:
            continue

        display = frame.copy()

        # Attach callback each frame with both frame and contours
        cv2.setMouseCallback(window_name, select_contour, (frame, contours))

        # Show target overlay and predictions
        if target_contour is not None:
            # Draw the selected contour in green
            # cv2.drawContours(display, [target_contour], -1, (0, 255, 0), 2)

            if target_features is None:
                target_features = compute_enhanced_features(target_contour, target_contour)

            for cnt in contours:
                if cnt is target_contour or cv2.contourArea(cnt) < 100:
                    continue
                try:
                    
                    result, confidence, _ = predict_similarity(model, target_contour, cnt)

                    # 🔵 BLUE for match, 🔴 RED for non-match
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


if __name__ == "__main__":
    main()
