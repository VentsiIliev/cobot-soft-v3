"""
* File: FileSelector.py
* Author: ILV
* Comments: This file contains the main function of the project.
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
* 070524     ILV         Initial release
* -----------------------------------------------------------------
*
"""


from enum import Enum

import cv2
import mediapipe as mp
import math


class Modes(Enum):
    LIVE_STREAM = "LIVE_STREAM"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class HandDetector:
    """
        A class to detect hands in a video frame using MediaPipe Hands.

        Attributes:
            mode (Modes): Whether to treat the input images as a batch of static and possibly unrelated images, or a stream of images where the hand presence and positioning is more predictable. Default is False.
            maxHands (int): Maximum number of hands to detect. Default is 2.
            detectionCon (float): Minimum confidence value ([0.0, 1.0]) for hand detection to be considered successful. Default is 1.
            trackCon (float): Minimum confidence value ([0.0, 1.0]) for the hand landmarks to be considered tracked successfully. Default is 0.5.
    """

    def __init__(self, mode=Modes.LIVE_STREAM, maxHands=1, detectionCon=1, trackCon=0.5):  # constructor
        self.results = None
        self.lmList = None
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mpHands = mp.solutions.hands  # initializing hands module for the instance
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.detectionCon,
                                        self.trackCon)  # object for Hands for a particular instance
        self.mpDraw = mp.solutions.drawing_utils  # object for Drawing
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, image, draw=True):
        """
            Finds hands in an image.

            Args:
                image: The image in which to detect hands.
                draw (bool): Whether to draw the detection results on the image.

            Returns:
                The image with or without drawings.
        """
        imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # converting to RGB bcoz hand recognition works only on RGB image
        self.results = self.hands.process(imgRGB)  # processing the RGB image
        if self.results.multi_hand_landmarks:  # gives x,y,z of every landmark or if no hand than NONE
            for handLms in self.results.multi_hand_landmarks:  # each hand landmarks in results
                if draw:
                    self.mpDraw.draw_landmarks(image, handLms,
                                               self.mpHands.HAND_CONNECTIONS)  # joining points on our hand
        return image

    def findPosition(self, img, handNo=0, draw=True):
        """
            Finds the position of hand landmarks in an image.

            Args:
                img: The image from which to find the positions.
                handNo (int): The index of the hand to find positions for (in case of multiple hands detected).
                draw (bool): Whether to draw circles at each landmark position.

            Returns:
                A tuple containing a list of all landmark positions (with each position being a list of [id, x, y])
                and a bounding box around the detected hand in the format (xmin, ymin, xmax, ymax).
        """
        xList = []
        yList = []
        zList = []
        bbox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:  # gives x,y,z of every landmark
            myHand = self.results.multi_hand_landmarks[handNo]  # Gives result for particular hand
            for id, lm in enumerate(myHand.landmark):  # gives id and lm(x,y,z)
                h, w, c = img.shape  # getting h,w for converting decimals x,y into pixels
                cx, cy, cz = int(lm.x * w), int(lm.y * h), int(lm.z * w)  # pixels coordinates for landmarks
                # print(id, cx, cy)
                xList.append(cx)
                yList.append(cy)
                zList.append(cz)
                self.lmList.append([id, cx, cy, cz])
                # if draw:
                #     cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax

            if draw:
                cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20), (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)

        return self.lmList, bbox

    def fingersUp(self):
        """
                Определя дали пръстът е изправен (отворен) или сгънат (затворен).

                Връща:
                    Списък с булеви стойности, където всяка стойност представлява отворен (1) или затворен (0) пръст:
                    - Първият елемент отговаря на показалеца.
                    - Вторият елемент отговаря на средния пръст.
                    - Третият елемент отговаря на пръстът "халка".
                    - Четвъртият елемент отговаря на малкия пръст.
                    - Петият елемент отговаря на палеца.
                """
        fingers = []  # Storing final result

        # Detecting thumb
        thumb_angle = self.calculateAngle(self.lmList[self.tipIds[0]], self.lmList[self.tipIds[0] - 2],
                                          self.lmList[self.tipIds[0] - 4])
        if thumb_angle > 160:  # Adjust this threshold as needed
            fingers.append(1)  # Thumb is open
        else:
            fingers.append(0)  # Thumb is closed

        # Detecting fingers
        for id in range(1, 5):  # Checking fingers 1 to 4
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)  # Finger is open
            else:
                fingers.append(0)  # Finger is closed

        return fingers

    def isThumbOpen(self):
        """
           Determines if the thumb is open.

           Returns:
               True if the thumb is considered open, False otherwise.
       """
        thumb_angle = self.calculateAngle(self.lmList[self.tipIds[0]], self.lmList[self.tipIds[0] - 2],
                                          self.lmList[self.tipIds[0] - 4])
        return thumb_angle > 160  # Adjust this threshold as needed

    def isFingerOpen(self, finger_id):
        """
           Determines if a specified finger is open.

           Args:
               finger_id (int): The index of the finger to check.

           Returns:
               True if the finger is considered open, False otherwise.
       """
        finger_tip = self.lmList[finger_id]
        finger_base = self.lmList[finger_id - 1]
        return finger_tip[2] < finger_base[2]  # Check if finger tip is above finger base

    def calculateAngle(self, point1, point2, point3):
        """
            Calculates the angle between three points.

            Args:
                point1: The first point.
                point2: The second point, which acts as the vertex of the angle.
                point3: The third point.

            Returns:
                The angle in degrees between the three points.
        """
        angle_radians = math.atan2(point3[1] - point2[1], point3[0] - point2[0]) - math.atan2(point1[1] - point2[1],
                                                                                              point1[0] - point2[0])
        angle_degrees = math.degrees(angle_radians)
        return abs(angle_degrees)

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):  # finding distance between two points p1 & p2
        """
            Finds the distance between two points on the hand.

            Args:
                p1, p2: The indices of the points to measure the distance between.
                img: The image on which the measurement is to be drawn.
                draw (bool): Whether to draw the measurement on the image.
                r (int): The radius of the circles to be drawn at points p1 and p2.
                t (int): The thickness of the line to be drawn between points p1 and p2.

            Returns:
                A tuple containing the distance between the points, the image, and the coordinates of the points.
        """
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]  # getting x,y of p1
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]  # getting x,y of p2
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # getting centre point

        if draw:  # contour_editor line and circles on the points
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]
