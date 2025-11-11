import cv2

from VisionSystem.VisionSystem import VisionSystem

visionSystem= VisionSystem()

while True:
    _,frame,_=visionSystem.run()
    if frame is None:
        continue

    height, width, _ = frame.shape
    center_x, center_y = width // 2, height // 2
    color = (0, 255, 0)  # Green color in BGR
    thickness = 1
    line_length = 100
    # Draw horizontal line
    cv2.line(frame, (center_x - line_length, center_y), (center_x + line_length, center_y), color, thickness)
    # Draw vertical line
    cv2.line(frame, (center_x, center_y - line_length), (center_x, center_y + line_length), color, thickness)

    cv2.imshow("Camera with Crosshair", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break