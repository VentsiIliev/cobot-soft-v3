import cv2
import numpy as np
import os
import requests
from datetime import datetime

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
LEFT_URL = "http://192.168.222.225:5000/image/left"
RIGHT_URL = "http://192.168.222.225:5000/image/right"

SAVE_DIR_LEFT = "calibration_images/left"
SAVE_DIR_RIGHT = "calibration_images/right"

# Create folders if not exist
os.makedirs(SAVE_DIR_LEFT, exist_ok=True)
os.makedirs(SAVE_DIR_RIGHT, exist_ok=True)

# -------------------------------------------------------------
# HELPER FUNCTION
# -------------------------------------------------------------
def get_image(url):
    """Fetch image from a URL and decode it into OpenCV format."""
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        else:
            print(f"[WARN] Failed to get image from {url}, status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Could not connect to {url}: {e}")
        return None

# -------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------
img_counter = 0
print("[INFO] Press 's' to save stereo image pair | Press 'q' to quit")

while True:
    left_img = get_image(LEFT_URL)
    right_img = get_image(RIGHT_URL)

    if left_img is None or right_img is None:
        print("[WARN] Could not retrieve images. Retrying...")
        continue

    # Ensure same dimensions
    if left_img.shape != right_img.shape:
        right_img = cv2.resize(right_img, (left_img.shape[1], left_img.shape[0]))

    # Concatenate side-by-side for display
    stereo_pair = np.hstack((left_img, right_img))
    cv2.imshow("Stereo Camera Feed [Left | Right]", stereo_pair)

    key = cv2.waitKey(1) & 0xFF

    # Save stereo pair
    if key == ord('s'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        left_path = os.path.join(SAVE_DIR_LEFT, f"left_{timestamp}.png")
        right_path = os.path.join(SAVE_DIR_RIGHT, f"right_{timestamp}.png")

        cv2.imwrite(left_path, left_img)
        cv2.imwrite(right_path, right_img)

        img_counter += 1
        print(f"[INFO] Saved image pair #{img_counter}:")
        print(f"   {left_path}")
        print(f"   {right_path}")

    # Quit
    elif key == ord('q'):
        print("[INFO] Exiting capture loop.")
        break

cv2.destroyAllWindows()
