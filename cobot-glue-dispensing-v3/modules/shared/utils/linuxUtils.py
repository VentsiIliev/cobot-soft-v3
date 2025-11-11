import logging
import platform
import re
import subprocess

# -----------------------------
# Logging Setup
# -----------------------------
logging.basicConfig(
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console only, no file
    ]
)

SUDO_PASS = "plp"
# SUDO_PASS = "123"


def find_ch341_uart_port():
    try:
        result = subprocess.run(
            ["sudo", "-S", "dmesg"], input=SUDO_PASS + "\n", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    except subprocess.SubprocessError as e:
        logging.error("Failed to execute dmesg command: %s", e)
        return None

        # Regex to match known USB-to-serial drivers and extract ttyUSB device number
    pattern = r'(ch341-uart|FTDI|pl2303|cp210x|usbserial).*?ttyUSB(\d+)'

    lines = result.stdout.splitlines()
    lines.reverse()  # Most recent logs first

    for line in lines:
        if "now attached to ttyUSB" in line:
            logging.info("Inspecting line: %s", line)
            match = re.search(pattern, line)
            if match:
                device = f"/dev/ttyUSB{match.group(2)}"
                logging.info("Detected UART USB device: %s", device)
                return device

    return None

def get_modbus_port():
    # return "/dev/ttyS1"
    if platform.system() == "Windows":
        return "COM5"  # Adjust as necessary
    else:  # Assuming Linux
        port = find_ch341_uart_port()
        if port:
            # print("Port found:", port)
            return port
        else:
            return " "



def list_video_devices_v4l2():
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE, text=True)
        output = result.stdout

        devices = {}
        lines = output.splitlines()
        current_device = None

        for line in lines:
            if line.strip() == "":
                continue
            if not line.startswith('\t'):
                # This is a device name line
                current_device = line.strip(':')
                devices[current_device] = []
            else:
                # This is a /dev/videoX or /dev/mediaX line
                path = line.strip()
                devices[current_device].append(path)

        return devices
    except Exception as e:
        logging.error("Failed to list video devices: %s", e)
        return {}

# # Example usage:
# devices = list_video_devices_v4l2()
# for name, paths in devices.items():
#     print(f"Device: {name}")
#     for path in paths:
#         print(f"  - {path}")

print(get_modbus_port())