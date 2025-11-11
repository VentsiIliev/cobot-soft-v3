# from enum import Enum
#
# import numpy as np
# from shared.shared.workpiece.Workpiece import BaseWorkpiece
# from shared.shared.interfaces.JsonSerializable import JsonSerializable
# from shared.shared.workpiece.Workpiece import WorkpieceField
# from system.tools.enums.Program import Program
# from system.tools.enums.ToolID import ToolID
# from system.tools.GlueCell import GlueType
# from system.tools.enums.Gripper import Gripper
#
# from typing import List
#
# class PathType(Enum):
#     CONTOUR = "Contour"
#     FILL = "Fill"
#
# class PathSegment:
#     def __init__(self,points,settings):
#         self.points = points
#         self.settings = settings
#
#     def __repr__(self):
#         return f"PathSegment(points={self.points}, settings={self.settings})"
#
# class Path:
#     def __init__(self,segments:List['PathSegment'],path_type:PathType):
#         self.segments = segments
#         self.path_type = path_type
#
# class SprayPattern:
#     """Holds both contour and fill paths — strict, no isinstance guessing."""
#     def __init__(self, spray_contour: List['Path'], spray_fill: List['Path']):
#         if not isinstance(spray_contour, list) or not all(isinstance(p, Path) for p in spray_contour):
#             raise TypeError("spray_contour must be a list of Path objects")
#         if not isinstance(spray_fill, list) or not all(isinstance(p, Path) for p in spray_fill):
#             raise TypeError("spray_fill must be a list of Path objects")
#         self.spray_contour = spray_contour
#         self.spray_fill = spray_fill
#         self.spray_patterns = self.spray_contour + self.spray_fill
#
#     def __repr__(self):
#         return f"SprayPattern(contour={len(self.spray_contour)}, fill={len(self.spray_fill)})"
#
#     @classmethod
#     def from_dict(cls, data: dict) -> "SprayPattern":
#         """Strict deserialization from dict -> SprayPattern."""
#         if not isinstance(data, dict):
#             raise TypeError(f"Expected dict for SprayPattern, got {type(data)}")
#
#         def dict_to_segment(seg_dict):
#             if not isinstance(seg_dict, dict):
#                 raise TypeError(f"Expected dict for segment, got {type(seg_dict)}")
#             points = np.array(seg_dict["points"], dtype=np.float32)
#             settings = dict(seg_dict.get("settings", {}))
#             return PathSegment(points, settings)
#
#         def dict_to_path(path_dict):
#             if not isinstance(path_dict, dict):
#                 raise TypeError(f"Expected dict for path, got {type(path_dict)}")
#             path_type = PathType(path_dict["type"])
#             segments = [dict_to_segment(s) for s in path_dict["segments"]]
#             return Path(segments, path_type)
#
#         contour_data = data.get("Contour", [])
#         fill_data = data.get("Fill", [])
#         return cls(
#             spray_contour=[dict_to_path(p) for p in contour_data],
#             spray_fill=[dict_to_path(p) for p in fill_data],
#         )
#
#     def to_dict(self) -> dict:
#         """Strict serialization to dict."""
#         def segment_to_dict(seg: PathSegment):
#             return {"points": np.array(seg.points).tolist(), "settings": dict(seg.settings)}
#
#         def path_to_dict(path: Path):
#             return {
#                 "type": path.path_type.value,
#                 "segments": [segment_to_dict(s) for s in path.segments]
#             }
#
#         return {
#             "Contour": [path_to_dict(p) for p in self.spray_contour],
#             "Fill": [path_to_dict(p) for p in self.spray_fill],
#         }
#
# class WorkpieceDto:
#     def __init__(self):
#
#
#
# class Workpiece(BaseWorkpiece, JsonSerializable):
#     def __init__(self, workpieceId, name, description, toolID, gripperID, glueType,
#                  program, material, contour, offset, height, nozzles, contourArea,
#                  glueQty, sprayWidth, pickupPoint, sprayPattern=None):
#
#         self.workpieceId = workpieceId
#         self.name = name
#         self.description = description
#         self.toolID = toolID
#         self.gripperID = gripperID
#         self.glueType = glueType
#         self.program = program
#         self.material = material
#         self.contour = contour
#         self.offset = offset
#         self.height = height
#         self.contourArea = contourArea
#         self.nozzles = nozzles
#         self.glueQty = glueQty
#         self.sprayWidth = sprayWidth
#         self.pickupPoint = pickupPoint
#
#         # ✅ If sprayPattern is not already a SprayPattern object, construct one
#         if not isinstance(sprayPattern, SprayPattern):
#             raise TypeError("Workpiece.sprayPattern must be a SprayPattern instance")
#         self.sprayPattern = sprayPattern
#
#     """ HELPERS FOR PATH EXTRACTION """
#
#     def get_paths_by_type(self, path_type: PathType) -> List[Path]:
#         """Return all paths of a given type (Contour or Fill)."""
#         return [p for p in self.sprayPattern.spray_patterns if p.path_type == path_type]
#
#     def get_contour_paths(self) -> List[Path]:
#         return self.get_paths_by_type(PathType.CONTOUR)
#
#     def get_fill_paths(self) -> List[Path]:
#         return self.get_paths_by_type(PathType.FILL)
#
#     """ JSON SERIALIZATION / DESERIALIZATION """
#
#     @staticmethod
#     def serialize(workpiece):
#         """
#         Serialize a Workpiece object (including PathSegment/Path/SprayPattern)
#         into a pure-Python dict ready for JSON storage.
#         Assumes workpiece and nested types are valid.
#         """
#
#         def segment_to_dict(seg: PathSegment):
#             return {
#                 "points": seg.points.tolist(),
#                 "settings": dict(seg.settings)
#             }
#
#         def path_to_dict(path: Path):
#             return {
#                 "type": path.path_type.value,
#                 "segments": [segment_to_dict(s) for s in path.segments]
#             }
#
#         def spray_pattern_to_dict(pattern: SprayPattern):
#             # assumes spray_contour/fill are lists of Path
#             return {
#                 "Contour": [path_to_dict(p) for p in pattern.spray_contour],
#                 "Fill": [path_to_dict(p) for p in pattern.spray_fill],
#             }
#
#         def convert_contour(contour):
#             # assume either ndarray, list of ndarrays, or dicts with 'contour'
#             if isinstance(contour, np.ndarray):
#                 return contour.tolist()
#             if isinstance(contour, dict):
#                 return {
#                     "contour": contour["contour"].tolist(),
#                     "settings": dict(contour.get("settings", {}))
#                 }
#             # plain list of points or list of dicts
#             return [convert_contour(c) for c in contour] if contour else []
#
#         return {
#             WorkpieceField.WORKPIECE_ID.value: workpiece.workpieceId,
#             WorkpieceField.NAME.value: workpiece.name,
#             WorkpieceField.DESCRIPTION.value: workpiece.description,
#             WorkpieceField.TOOL_ID.value: workpiece.toolID.value,
#             WorkpieceField.GRIPPER_ID.value: workpiece.gripperID.value,
#             WorkpieceField.GLUE_TYPE.value: workpiece.glueType.value,
#             WorkpieceField.PROGRAM.value: workpiece.program.value,
#             WorkpieceField.MATERIAL.value: workpiece.material,
#             WorkpieceField.CONTOUR.value: convert_contour(workpiece.contour),
#             WorkpieceField.OFFSET.value: workpiece.offset,
#             WorkpieceField.HEIGHT.value: workpiece.height,
#             WorkpieceField.GLUE_QTY.value: workpiece.glueQty,
#             WorkpieceField.SPRAY_WIDTH.value: workpiece.sprayWidth,
#             WorkpieceField.PICKUP_POINT.value: workpiece.pickupPoint,
#             WorkpieceField.SPRAY_PATTERN.value: spray_pattern_to_dict(workpiece.sprayPattern),
#             WorkpieceField.CONTOUR_AREA.value: workpiece.contourArea,
#             WorkpieceField.NOZZLES.value: workpiece.nozzles
#         }
#
#     @staticmethod
#     def deserialize(data):
#         """
#         Deserialize a Workpiece dictionary (typically loaded from JSON)
#         into a fully structured Workpiece object with PathSegment, Path,
#         and SprayPattern instances.
#         """
#
#         def to_numpy(points):
#             """Convert list of points → numpy array (Nx2)."""
#             arr = np.array(points, dtype=float)
#             if arr.ndim == 1:
#                 arr = arr.reshape(-1, 2)
#             return arr
#
#         def dict_to_segment(seg_dict: dict) -> PathSegment:
#             return PathSegment(
#                 points=to_numpy(seg_dict["points"]),
#                 settings=dict(seg_dict.get("settings", {}))
#             )
#
#         def dict_to_path(path_dict: dict) -> Path:
#             path_type = PathType(path_dict["type"])
#             segments = [dict_to_segment(s) for s in path_dict["segments"]]
#             return Path(segments, path_type)
#
#         def dict_to_spray_pattern(sp_dict: dict) -> SprayPattern:
#             """Convert dict -> SprayPattern (expects {'Contour': [...], 'Fill': [...]})"""
#             contour_paths = [dict_to_path(p) for p in sp_dict.get("Contour", [])]
#             fill_paths = [dict_to_path(p) for p in sp_dict.get("Fill", [])]
#             return SprayPattern(contour_paths, fill_paths)
#
#         def convert_contour(obj):
#             """Convert contour data to consistent numpy/list structure."""
#             if isinstance(obj, dict):  # {"contour": [[...]], "settings": {...}}
#                 return {
#                     "contour": np.array(obj["contour"], dtype=float),
#                     "settings": dict(obj.get("settings", {}))
#                 }
#             if isinstance(obj, list):
#                 # list of points or list of dicts
#                 if len(obj) == 0:
#                     return np.empty((0, 2))
#                 if isinstance(obj[0], (list, tuple)):
#                     return np.array(obj, dtype=float)
#                 if isinstance(obj[0], dict):
#                     return [convert_contour(o) for o in obj]
#             return obj
#
#         contour = convert_contour(data["contour"])
#         spray_pattern = dict_to_spray_pattern(data["sprayPattern"])
#
#         return Workpiece(
#             workpieceId=data["workpieceId"],
#             name=data.get("name", ""),
#             description=data.get("description", ""),
#             toolID=data["toolID"],
#             gripperID=data["gripperID"],
#             glueType=data["glueType"],
#             program=data["program"],
#             material=data.get("material", ""),
#             contour=contour,
#             offset=data.get("offset", 0.0),
#             height=data.get("height", 0.0),
#             nozzles=data.get("nozzles", []),
#             contourArea=data.get("contourArea", 0.0),
#             glueQty=data.get("glueQty", 0.0),
#             sprayWidth=data.get("sprayWidth", 0.0),
#             pickupPoint=data.get("pickupPoint", [0, 0]),
#             sprayPattern=spray_pattern
#         )
#
#     def toDict(self):
#         """
#                 Convert the Workpiece object into a dictionary representation.
#
#                 Returns:
#                     dict: A dictionary containing the Workpiece's properties, suitable for serialization or storage.
#                 """
#         return {
#             WorkpieceField.WORKPIECE_ID.value: self.workpieceId,
#             WorkpieceField.NAME.value: self.name,
#             WorkpieceField.DESCRIPTION.value: self.description,
#             WorkpieceField.TOOL_ID.value: self.toolID.value,
#             WorkpieceField.GRIPPER_ID.value: self.gripperID.value,
#             WorkpieceField.GLUE_TYPE.value: self.glueType.value,
#             WorkpieceField.PROGRAM.value: self.program.value,
#             WorkpieceField.MATERIAL.value: self.material,
#             WorkpieceField.CONTOUR.value: self.contour,
#             WorkpieceField.OFFSET.value: self.offset,
#             WorkpieceField.HEIGHT.value: self.height,
#             WorkpieceField.GLUE_QTY.value: self.glueQty,
#             WorkpieceField.SPRAY_WIDTH.value: self.sprayWidth,
#             WorkpieceField.PICKUP_POINT.value: self.pickupPoint,
#             WorkpieceField.SPRAY_PATTERN.value: self.sprayPattern,
#             WorkpieceField.CONTOUR_AREA.value: self.contourArea,
#             WorkpieceField.NOZZLES.value: self.nozzles
#
#         }
#
#     @staticmethod
#     def fromDict(data: dict) -> "Workpiece":
#         """
#         Deserialize a dictionary into a Workpiece object, restoring
#         nested PathSegment / Path / SprayPattern structures.
#         """
#
#         def dict_to_segment(seg_dict):
#             """Convert dict → PathSegment."""
#             return PathSegment(
#                 points=np.array(seg_dict["points"], dtype=np.float32),
#                 settings=seg_dict.get("settings", {})
#             )
#
#         def dict_to_path(path_dict):
#             """Convert dict → Path."""
#             path_type = PathType(path_dict["type"])
#             segments = [dict_to_segment(s) for s in path_dict["segments"]]
#             return Path(segments, path_type)
#
#         # ✅ Use SprayPattern.from_dict — single entry point for all legacy formats
#         spray_pattern = SprayPattern.from_dict(
#             data[WorkpieceField.SPRAY_PATTERN.value]
#         )
#
#         # ✅ Convert contour directly to numpy if it’s list-based
#         contour = data.get(WorkpieceField.CONTOUR.value)
#         if isinstance(contour, list):
#             contour = np.array(contour, dtype=np.float32)
#
#         # ✅ Build Workpiece — no isinstance checks, assume valid data
#         return Workpiece(
#             workpieceId=data[WorkpieceField.WORKPIECE_ID.value],
#             name=data[WorkpieceField.NAME.value],
#             description=data[WorkpieceField.DESCRIPTION.value],
#             toolID=ToolID(data[WorkpieceField.TOOL_ID.value]),
#             gripperID=Gripper(data[WorkpieceField.GRIPPER_ID.value]),
#             glueType=GlueType(data[WorkpieceField.GLUE_TYPE.value]),
#             program=Program(data[WorkpieceField.PROGRAM.value]),
#             material=data[WorkpieceField.MATERIAL.value],
#             contour=contour,
#             offset=data[WorkpieceField.OFFSET.value],
#             height=data[WorkpieceField.HEIGHT.value],
#             pickupPoint=data[WorkpieceField.PICKUP_POINT.value],
#             nozzles=data.get(WorkpieceField.NOZZLES.value, []),
#             contourArea=data[WorkpieceField.CONTOUR_AREA.value],
#             glueQty=data[WorkpieceField.GLUE_QTY.value],
#             sprayWidth=data[WorkpieceField.SPRAY_WIDTH.value],
#             sprayPattern=spray_pattern
#         )
#
#
# if __name__ == "__main__":
#     # Original
#     seg = PathSegment([[0, 0], [10, 0]], {"speed": "100"})
#     path = Path([seg], PathType.CONTOUR)
#     pattern = SprayPattern([path])
#
#     wp = Workpiece("1", "Test", "Desc", ToolID.Tool0, Gripper.DOUBLE,
#                    GlueType.TypeA, Program.TRACE, "Steel",
#                    contour=[[0, 0], [1, 1]], offset=0, height=5,
#                    nozzles=[], contourArea=1.0, glueQty=5,
#                    sprayWidth=2, pickupPoint=[0, 0], sprayPattern=pattern)
#
#     # Serialize
#     serialized = Workpiece.serialize(wp)
#
#     # Deserialize
#     restored = Workpiece.fromDict(serialized)
#
#     print(restored.sprayPattern.spray_patterns[0].segments[0].points)
#     print(restored.sprayPattern.spray_patterns[0].segments[0].settings)
#
