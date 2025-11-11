"""
* File: CNC.py
* Author: AtD
* Comments: This file contains CNC functionality for CNC Software.
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
* 070524     AtD         Initial release
* -----------------------------------------------------------------
*
"""
import os
import sys
import threading

import cv2  # Import OpenCV
import linuxcnc
import numpy as np  # Import numpy
from PLVision.Contouring import *


def GenerateGCode(contours, hierarchy, offset_x=0, offset_y=0):
    min_contour_area = 100  # Set your minimum contour area
    contours = [cnt for cnt, h in zip(contours, hierarchy[0]) if cv2.contourArea(cnt) > min_contour_area and h[3] == -1]
    f = open("storage/image.ngc", "w")
    f.write("G90\n")
    f.write("G64 P2\n")
    for contour in contours:
        epsilon = 0.001 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        for i in range(len(approx)):
            x1 = approx[i - 1][0][0] * 5.5 + offset_x
            y1 = approx[i - 1][0][1] * 6 + offset_y
            x2 = approx[i][0][0] * 5.5 + offset_x
            y2 = approx[i][0][1] * 6 + offset_y
            if i == 1:
                f.write("M3\n")
            f.write("G1 X" + str(max(1, x2 / 10 + 215)) + " Y" + str(max(1, y2 / 10 + 162)) + " F110000\n")
            if i == len(approx) - 1:
                f.write("M5\n")
    f.write("G1 X0 Y0 F20000\n")
    f.write("M2\n")
    f.close()


def PowerOnMachine():  # This function powers on the machine
    os.system("sudo halcmd setp halui.machine.on false")
    os.system("sudo halcmd setp halui.machine.off false")
    os.system("sudo halcmd setp halui.machine.on true")


def PowerOffMachine():  # This function powers off the machine
    os.system("sudo halcmd setp halui.machine.off false")
    os.system("sudo halcmd setp halui.machine.on false")
    os.system("sudo halcmd setp halui.machine.off true")


def HomeMachine():  # This function homes the machine
    os.system("sudo halcmd setp halui.home-all false")  # Set the mode to auto
    os.system("sudo halcmd setp halui.mode.joint false")  # Set the mode to joint
    os.system("sudo halcmd setp halui.mode.auto false")  # Set the mode to auto
    os.system("sudo halcmd setp halui.mode.mdi false")  # Set the mode to MDI
    os.system("sudo halcmd setp halui.mode.joint true")  # Set the mode to joint
    os.system("sudo halcmd setp halui.home-all true")  # Set the mode to auto
    os.system("sudo halcmd setp halui.mode.joint false")  # Set the mode to joint


def run_program(gcode_file):
    c = linuxcnc.command()
    c.program_open(gcode_file)
    os.system("sudo halcmd setp halui.program.run 1")
    os.system("sudo halcmd setp halui.program.run 0")


def headexecution():
    while True:
        # check for halui.spindle.0.runs-forward
        spindle_runs_forward = os.popen("halcmd getp halui.spindle.0.runs-forward").read().strip()
        if spindle_runs_forward == 'TRUE':
            os.system("halcmd setp mb2hal.00.uwMode.float 1")
            os.system("halcmd setp mb2hal.00.uwCommand.float 16")
            os.system("halcmd setp mb2hal.01.uwMode.float 1")
            os.system("halcmd setp mb2hal.01.uwCommand.float 16")
            os.system("halcmd setp mb2hal.02.uwMode.float 1")
            os.system("halcmd setp mb2hal.02.uwCommand.float 16")
            os.system("halcmd setp mb2hal.03.uwMode.float 1")
            os.system("halcmd setp mb2hal.03.uwCommand.float 16")
        else:
            os.system("halcmd setp mb2hal.00.uwMode.float 1")
            os.system("halcmd setp mb2hal.00.uwCommand.float 0")
            os.system("halcmd setp mb2hal.01.uwMode.float 1")
            os.system("halcmd setp mb2hal.01.uwCommand.float 0")
            os.system("halcmd setp mb2hal.02.uwMode.float 1")
            os.system("halcmd setp mb2hal.02.uwCommand.float 0")
            os.system("halcmd setp mb2hal.03.uwMode.float 1")
            os.system("halcmd setp mb2hal.03.uwCommand.float 0")


def RunGCode():  # This function runs the gcode program
    try:  # Try to run the gcode program
        run_program("/home/cnc/Desktop/LinuxCNC/storage/image.ngc")  # Run the gcode program
        threading.Thread(target=headexecution).start()
    except linuxcnc.error as detail:  # Check for errors
        print("Error", detail)  # Print the error


def StopGCode():  # This function stops the gcode program
    os.system("sudo halcmd setp halui.program.stop false")  # Set the mode to auto
    os.system("sudo halcmd setp halui.program.stop true")  # Set the mode to auto


def ServiceMove():  # This function moves the machine to the service position
    os.system("sudo halcmd setp halui.mode.auto false")  # Set the mode to auto
    os.system("sudo halcmd setp halui.mode.joint false")  # Set the mode to joint
    os.system("sudo halcmd setp halui.mode.mdi false")  # Set the mode to auto
    os.system("sudo halcmd setp halui.mode.mdi true")  # Set the mode to auto
    os.system("axis-remote --mdi 'G1 X300 Y500 F20000'")  # Move the machine to the service position
    os.system("sudo halcmd setp halui.mode.mdi false")  # Set the mode to auto


def MDIMode():  # This function sets the machine to MDI mode
    os.system("sudo halcmd setp halui.mode.auto false")  # Set the mode to auto
    os.system("sudo halcmd setp halui.mode.mdi false")  # Set the mode to MDI
    os.system("sudo halcmd setp halui.mode.mdi true")  # Set the mode to MDI


def MoveUp():  # This function moves the machine up
    os.system("sudo halcmd setp halui.axis.x.plus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 0")
    os.system("sudo halcmd setp halui.axis.y.plus 0")
    os.system("sudo halcmd setp halui.axis.y.minus 1")


def MoveDown():  # This function moves the machine down
    os.system("sudo halcmd setp halui.axis.x.plus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 0")
    os.system("sudo halcmd setp halui.axis.y.minus 0")
    os.system("sudo halcmd setp halui.axis.y.plus 1")


def MoveLeft():  # This function moves the machine left
    os.system("sudo halcmd setp halui.axis.x.plus 0")
    os.system("sudo halcmd setp halui.axis.y.minus 0")
    os.system("sudo halcmd setp halui.axis.y.plus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 1")


def MoveRight():  # This function moves the machine right
    os.system("sudo halcmd setp halui.axis.x.minus 0")
    os.system("sudo halcmd setp halui.axis.y.plus 0")
    os.system("sudo halcmd setp halui.axis.y.minus 0")
    os.system("sudo halcmd setp halui.axis.x.plus 1")


def MoveDiagonalUpLeft():  # This function moves the machine diagonally up and left
    os.system("sudo halcmd setp halui.axis.x.plus 0")
    os.system("sudo halcmd setp halui.axis.y.plus 0")
    os.system("sudo halcmd setp halui.axis.y.minus 1")
    os.system("sudo halcmd setp halui.axis.x.minus 1")


def MoveDiagonalUpRight():  # This function moves the machine diagonally up and right
    os.system("sudo halcmd setp halui.axis.y.plus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 0")
    os.system("sudo halcmd setp halui.axis.x.plus 1")
    os.system("sudo halcmd setp halui.axis.y.minus 1")


def MoveDiagonalDownLeft():  # This function moves the machine diagonally down and left
    os.system("sudo halcmd setp halui.axis.y.minus 0")
    os.system("sudo halcmd setp halui.axis.x.plus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 1")
    os.system("sudo halcmd setp halui.axis.y.plus 1")


def MoveDiagonalDownRight():  # This function moves the machine diagonally down and right
    os.system("sudo halcmd setp halui.axis.y.minus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 0")
    os.system("sudo halcmd setp halui.axis.x.plus 1")
    os.system("sudo halcmd setp halui.axis.y.plus 1")


def StopMove():  # This function stops the machine
    os.system("sudo halcmd setp halui.axis.x.plus 0")
    os.system("sudo halcmd setp halui.axis.x.minus 0")
    os.system("sudo halcmd setp halui.axis.y.plus 0")
    os.system("sudo halcmd setp halui.axis.y.minus 0")


def Status():  # This function gets the status of the machine
    try:  # Try to get the status
        s = linuxcnc.stat()  # create a connection to the status channel
        s.poll()  # get current values
    except linuxcnc.error as detail:  # Check for errors
        print()  # Print a blank line
        var = "error", detail  # Set the variable
        sys.exit(1)  # Exit the program
    for x in dir(s):  # Loop through the attributes of the status
        if not x.startswith("_"):  # Check for errors
            print()  # Print a blank line
            x, getattr(s, x)  # Print the attribute
