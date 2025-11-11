# import datetime
# import json
# import os
# import numpy as np
# from system.model.Workpiece import Workpiece
# from system.model.enums.Program import Program
# from system.model.enums.ToolID import ToolID
#
#
# class WorkPieceRepository():
#     DATE_FORMAT = "%Y-%m-%d"
#     TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"
#     BASE_DIR = "system/storage/workpieces"
#     WORKPIECE_FILE_SUFFIX = "_workpiece.json"
#
#     def __init__(self):
#         self.data = self.loadData()
#         # print("data", self.data)
#
#     def saveWorkpiece(self, workpieces: Workpiece):
#
#         # Get today's date and timestamp
#         today_date = datetime.datetime.now().strftime(self.DATE_FORMAT)
#         timestamp = datetime.datetime.now().strftime(self.TIMESTAMP_FORMAT)
#
#         # Full path based on today's date
#         date_dir = os.path.join(self.BASE_DIR, today_date)
#         timestamp_dir = os.path.join(date_dir, timestamp)
#
#         # Check if the folder for today's date exists, if not, create it
#         if not os.path.exists(date_dir):
#             os.makedirs(date_dir)
#
#         # Create the folder with the timestamp if it doesn't exist
#         os.makedirs(timestamp_dir, exist_ok=True)
#
#         # Serialize the workpieces
#         serialized_data = json.dumps(self.serialize(workpieces), indent=4)
#
#         # Define the file path
#         file_path = os.path.join(timestamp_dir, f"{timestamp}{self.WORKPIECE_FILE_SUFFIX}")
#
#         try:
#             # Save the workpieces to the file
#             with open(file_path, 'w') as file:
#                 file.write(serialized_data)
#             self.data.append(workpieces)
#             print(f"Workpiece saved to {file_path}")
#         except Exception as e:
#             raise Exception(e)
#             # print(f"Error saving workpieces: {e}")
#
#     def serialize(self, workpieces):
#         """
#         Serialize the Workpiece object to a dictionary that can be converted to JSON.
#         Ensure numpy arrays (such as contours) are converted to lists for JSON serialization.
#         """
#
#         def convert_ndarray_to_list(obj):
#             """Helper function to convert ndarrays and lists of ndarrays to lists."""
#             if isinstance(obj, np.ndarray):
#                 return obj.tolist()  # Convert ndarray to list
#             elif isinstance(obj, list):
#                 return [convert_ndarray_to_list(item) for item in obj]  # Recursively convert elements in a list
#             return obj
#
#         # Apply the conversion for contour (list of ndarrays)
#         contour_list = convert_ndarray_to_list(workpieces.contour)
#
#         return {
#             "id": workpieces.workpieceId,
#             "description": workpieces.description,
#             "name": workpieces.name,
#             "toolId": workpieces.toolID.name,
#             "glueType": workpieces.glueType.value,
#             "program": workpieces.program.value,
#             "material": workpieces.material,
#             "contour": contour_list,  # Ensure contours are properly serialized as lists
#             "offset": workpieces.offset,
#             "height": workpieces.height,
#             "nozzles": workpieces.nozzles,
#             "sprayPattern": workpieces.sprayPattern,
#             "area": workpieces.contourArea,
#
#         }
#
#     def deserialize(self, data):
#         """
#         Deserialize a dictionary back into a Workpiece object.
#         """
#
#         def convert_list_to_ndarray(obj):
#             """Convert lists to numpy arrays with the correct shape."""
#             if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], list):
#                 arr = np.array(obj, dtype=np.float32)  # Convert list to NumPy array
#                 if arr.ndim == 2 and arr.shape[1] == 2:  # Ensure correct shape
#                     return arr.reshape(-1, 1, 2)  # Reshape to (N, 1, 2)
#                 return arr
#             return obj
#
#         def reshapeSprayPattern(obj):
#             """Convert lists to numpy arrays with the correct shape."""
#             if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], list):
#                 # Flatten the list if it has unnecessary nesting
#                 flat_obj = [point[0] if isinstance(point[0], list) else point for point in obj]
#
#                 arr = np.array(flat_obj, dtype=np.float32)  # Convert list to NumPy array
#                 if arr.ndim == 2 and arr.shape[1] == 2:  # Ensure correct shape
#                     return arr.reshape(-1, 1, 2)  # Reshape to (N, 1, 2)
#                 return arr
#             return obj
#
#         # Deserialize fields
#         contour = convert_list_to_ndarray(data['contour'])
#         toolID = ToolID[data['toolId']]
#         spray_pattern = reshapeSprayPattern(data['sprayPattern'])
#         return Workpiece(
#             workpieceId=data['id'],
#             name=data['name'],
#             description=data['description'],
#             toolID=toolID,
#             glueType=data['glueType'],
#             program=Program(data['program']),
#             material=data['material'],
#             contour=contour,  # Properly formatted contour
#             offset=data['offset'],
#             height=data['height'],
#             nozzles=data['nozzles'],
#             sprayPattern=spray_pattern,
#             contourArea=data['area']
#         )
#
#     def loadData(self):
#         """
#         Recursively iterates over all directories inside 'storage/workpieces', deserializes all JSON files,
#         and returns a list of Workpiece objects.
#         """
#         workpieces = []
#
#         # Check if the base directory exists
#         if not os.path.exists(self.BASE_DIR):
#             print(f"Directory {self.BASE_DIR} does not exist.")
#             return workpieces
#
#         # Walk through all subdirectories and files
#         for root, _, files in os.walk(self.BASE_DIR):
#             for file in files:
#                 if file.endswith(self.WORKPIECE_FILE_SUFFIX):  # Ensure we only process workpieces JSON files
#                     file_path = os.path.join(root, file)
#                     try:
#                         with open(file_path, 'r') as f:
#                             data = json.load(f)  # Load JSON data
#                             print("Data: ", data)
#                             workpieces = self.deserialize(data)  # Deserialize into Workpiece
#                             workpieces.append(workpieces)
#                     except Exception as e:
#                         print(f"Error loading workpieces from {file_path}: {e}")
#                         raise Exception(f"Error loading workpieces.{e}")
#         return workpieces
