"""
* File: DxfConverter.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
* 061124     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import json
import socket
import cv2
import ezdxf
from ezdxf import bbox
from ezdxf.addons.drawing import matplotlib


class ServerSender:
    """
    Handles the transmission of image and JSON data to a remote server over specified ports.

    Attributes:
        server_ip (str): IP address of the server to connect.
        port_png (int): Port number for sending PNG images.
        port_json (int): Port number for sending JSON files.
    """

    def __init__(self, server_ip="192.168.222.74", port_png=8888, port_json=9999):
        """
        Initializes the server sender with IP and port configurations.

        Args:
            server_ip (str): IP address of the server to connect to.
            port_png (int): Port for sending PNG images.
            port_json (int): Port for sending JSON files.
        """
        self.server_ip = server_ip
        self.port_png = port_png
        self.port_json = port_json

    def send_png_to_server(self, image):
        """
        Encodes an image to PNG format and sends it to the server.

        Args:
            image (numpy.ndarray): Image to be sent as a PNG.

        Raises:
            Exception: If image encoding fails or connection issues occur.
        """
        ret, png_image = cv2.imencode('.png', image)
        if not ret:
            raise Exception("Error converting image to PNG format")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_ip, self.port_png))
            print(f"Connected to {self.server_ip}:{self.port_png}")
            sock.sendall(png_image.tobytes())
            print(f"PNG image sent to {self.server_ip}")

    def send_json_to_server(self, filename):
        """
        Sends a JSON file to the server over the designated JSON port.

        Args:
            filename (str): Path to the JSON file to be sent.

        Raises:
            Exception: If file reading or connection issues occur.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_ip, self.port_json))
                print(f"Connected to {self.server_ip}:{self.port_json}")

                with open(filename, 'rb') as f:
                    sock.sendall(f.read())
                    print(f"File '{filename}' sent to {self.server_ip}")

        except Exception as e:
            raise e


class ImageProcessor:
    """
    Processes DXF files to extract image data, detect contours, scale, and send data to the server.

    Attributes:
        dxf_file (str): Path to the DXF file to process.
        server_sender (ServerSender): Server sender instance for sending data.
        dpi (int): DPI for the PNG image rendering.
        target_size_mm (tuple): Target size in millimeters.
        target_size_px (tuple): Target size in pixels.
        mode (str): Operation mode ('png' or 'json').
        resized_cropped (numpy.ndarray): Processed, resized, and cropped image.
        scaleX (float): Scaling factor along the X axis.
        scaleY (float): Scaling factor along the Y axis.
        original_shape (tuple): Original shape of the rendered image.
    """

    def __init__(self, dxf_file, server_sender, dpi=146, target_size_mm=(700, 350), target_size_px=(1280, 720),
                 mode='png'):
        """
        Initializes the ImageProcessor with necessary configurations and loads the DXF file.

        Args:
            dxf_file (str): Path to the DXF file.
            server_sender (ServerSender): Instance of ServerSender for sending data.
            dpi (int): DPI setting for image rendering.
            target_size_mm (tuple): Target dimensions in millimeters.
            target_size_px (tuple): Target dimensions in pixels.
            mode (str): Processing mode ('png' or 'json').
        """
        self.dxf_file = dxf_file
        self.png_file = dxf_file.replace('.dxf', '.png')
        self.server_sender = server_sender
        self.dpi = dpi
        self.target_size_mm = target_size_mm
        self.target_size_px = target_size_px
        self.mode = mode
        self.resized_cropped = None
        self.scaleX = None
        self.scaleY = None
        self.original_shape = None

        # Load and process DXF file
        self.doc = ezdxf.readfile(dxf_file)
        self.msp = self.doc.modelspace()
        self.cache = bbox.Cache()
        self.first_bbox = bbox.extents(self.msp, cache=self.cache)

    def scale_contours(self, contours):
        """
        Scales the contours based on computed scale factors.

        Args:
            contours (list): List of contours to scale.

        Returns:
            list: Scaled and translated contours.
        """
        scaled_translated_contours = []
        for contour in contours:
            scaled_contour = []
            for point in contour:
                x = int(point[0][0] * self.scaleX)
                y = int(point[0][1] * self.scaleY)
                scaled_contour.append([[x, y]])
            scaled_translated_contours.append(scaled_contour)

        return scaled_translated_contours

    def contours_to_json_file(self, contours, json_file_name):
        """
        Saves contours data to a JSON file.

        Args:
            contours (list): Contours to save.
            json_file_name (str): Path to the output JSON file.
        """
        contours_json = [
            [point for point in contour] for contour in contours
        ]
        print("Contour JSON: ", contours_json)
        with open(json_file_name, 'w') as json_file:
            json.dump(contours_json, json_file)

    def detect_contours(self, image):
        """
        Detects contours in a grayscale image using thresholding.

        Args:
            image (numpy.ndarray): Input image for contour detection.

        Returns:
            list: Detected contours.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 80, 255, 0)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def draw_rectangle(self, center_x, center_y, width, height):
        """
        Draws a rectangle in the DXF file based on center and dimensions.

        Args:
            center_x (float): X-coordinate of the rectangle center.
            center_y (float): Y-coordinate of the rectangle center.
            width (float): Width of the rectangle.
            height (float): Height of the rectangle.
        """
        half_width = width / 2
        half_height = height / 2

        bottom_left = (center_x - half_width, center_y - half_height)
        bottom_right = (center_x + half_width, center_y - half_height)
        top_right = (center_x + half_width, center_y + half_height)
        top_left = (center_x - half_width, center_y + half_height)

        self.msp.add_lwpolyline(
            points=[bottom_left, bottom_right, top_right, top_left, bottom_left],
            close=True,
            dxfattribs={'layer': '0'}
        )

    def process_dxf(self):
        """
        Processes the DXF file to draw a rectangle and renders it as a PNG image.

        Returns:
            numpy.ndarray: Rendered image of the DXF content.
        """
        if self.first_bbox:
            center_x = (self.first_bbox.extmin.x + self.first_bbox.extmax.x) / 2
            center_y = (self.first_bbox.extmin.y + self.first_bbox.extmax.y) / 2
            self.draw_rectangle(center_x, center_y, 706, 350)

            matplotlib.qsave(self.doc.modelspace(), self.png_file, dpi=self.dpi)
            img = cv2.imread(self.png_file)
            self.original_shape = img.shape
            print(self.original_shape)
            return img
        return None

    def crop_and_resize(self, img):
        """
        Crops the largest contour from the image and resizes it to the original image shape.

        Args:
            img (numpy.ndarray): Input image to crop and resize.
        """
        contours = self.detect_contours(img)
        if contours:
            sorted_contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[0])
            large_contour = sorted_contours[0]

            x, y, w, h = cv2.boundingRect(large_contour)
            cropped = img[y:y + h, x:x + w]

            resized_cropped = cv2.resize(cropped, (self.original_shape[1], self.original_shape[0]))
            self.resized_cropped = resized_cropped
        else:
            print("No contours found.")

    def set_scale_factors(self):
        """
        Computes scale factors based on target and original image size in pixels and millimeters.
        """
        targetPpmX = self.target_size_px[0] / self.target_size_mm[0]
        targetPpmY = self.target_size_px[1] / self.target_size_mm[1]
        currentPpmX = self.original_shape[1] / self.target_size_mm[0]
        currentPpmY = self.original_shape[0] / self.target_size_mm[1]
        self.scaleX = targetPpmX / currentPpmX
        self.scaleY = targetPpmY / currentPpmY

    def handle_contours(self):
        """
        Processes contours, scales them, and writes them to a JSON file.

        Returns:
            str: Name of the output JSON file with contour data.
        """
        newContours = self.detect_contours(self.resized_cropped)
        scaledContours = self.scale_contours(newContours)
        self.contours_to_json_file(scaledContours, 'contours.json')
        return 'contours.json'

    def handle_png(self):
        """
        Resizes the processed image based on scale factors and returns it.

        Returns:
            numpy.ndarray: Resized image ready for sending as PNG.
        """
        if isinstance(self.resized_cropped, cv2.UMat):
            self.resized_cropped = self.resized_cropped.get()

        new_width = int(self.resized_cropped.shape[1] * self.scaleX)
        new_height = int(self.resized_cropped.shape[0] * self.scaleY)
        resized_scaled = cv2.resize(self.resized_cropped, (new_width, new_height))
        return resized_scaled

    def process(self):
        """
        Main method for processing the DXF file and handling the mode-specific output (PNG or JSON).

        Returns:
            str or numpy.ndarray: Resulting image or JSON file path, depending on the mode.

        Raises:
            Exception: If DXF processing fails.
            ValueError: If mode is invalid.
        """
        img = self.process_dxf()
        if img is None:
            raise Exception("DXF file processing failed.")

        self.crop_and_resize(img)
        self.set_scale_factors()

        if self.resized_cropped is not None:
            if self.mode == 'json':
                return self.handle_contours()
            elif self.mode == 'png':
                return self.handle_png()
            else:
                raise ValueError("Invalid mode. Use 'json' or 'png'.")


# Usage
dxf_file = 'storage/Uplatnenie2mm.dxf'
server_sender = ServerSender(server_ip="192.168.222.74")
processor = ImageProcessor(dxf_file, server_sender, mode='json')
result = processor.process()
# server_sender.send_png_to_server(result)
server_sender.send_json_to_server(result)
