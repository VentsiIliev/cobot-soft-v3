# from typing import Any, Dict
# import json
#
# from backend.system.statistics.api.StatisticsAPI import StatisticsAPI
#
#
#
# class StatisticsRequestHandler:
#     """Handle incoming requests (legacy dicts or shared v2 Request) for statistics.
#
#     The handler accepts:
#       - shared.v2.Request instances
#       - dicts with keys {"type","action","resource","data"}
#       - JSON strings representing the above
#
#     It returns an shared.v2.Response (can be converted to dict by caller).
#     """
#
#     def __init__(self, api: StatisticsAPI):
#         self.api = api
#
#     def _normalize(self, message: Any) -> V2Request:
#         """Normalize input into a V2Request instance."""
#         if isinstance(message, V2Request):
#             return message
#         if isinstance(message, dict):
#             return V2Request.from_dict(message)
#         if isinstance(message, str):
#             try:
#                 obj = json.loads(message)
#                 return V2Request.from_dict(obj)
#             except Exception:
#                 raise ValueError("Invalid JSON request string")
#         raise ValueError("Unsupported message type for StatisticsRequestHandler")
#
#     def handle(self, message: Any) -> Dict[str, Any]:
#         """Handle the incoming message and return a normalized dict response."""
#         try:
#             req = self._normalize(message)
#         except Exception as e:
#             return V2Response(status="failure", message=str(e), error={"exception": str(e)}).to_dict()
#
#         action = (req.action or "").lower()
#         data = req.data or {}
#
#         try:
#             if action == "get_all" or action == "get" or action == "stats/get_all":
#                 result = self.api.get_all()
#                 return V2Response(status="success", data=result).to_dict()
#
#             if action == "reset_generator":
#                 res = self.api.reset_generator()
#                 return V2Response(status=res.get("status", "success")).to_dict()
#
#             if action == "reset_transducer":
#                 res = self.api.reset_transducer()
#                 return V2Response(status=res.get("status", "success")).to_dict()
#
#             if action == "reset_fan":
#                 res = self.api.reset_fan()
#                 return V2Response(status=res.get("status", "success")).to_dict()
#
#             if action in ("reset_pump_motor", "reset_pump"):
#                 idx = int(data.get("idx", 0))
#                 res = self.api.reset_pump_motor(idx)
#                 return V2Response(status=res.get("status", "success")).to_dict()
#
#             if action == "reset_pump_belt":
#                 idx = int(data.get("idx", 0))
#                 res = self.api.reset_pump_belt(idx)
#                 return V2Response(status=res.get("status", "success")).to_dict()
#
#             if action == "reset_loadcell":
#                 idx = int(data.get("idx", 0))
#                 res = self.api.reset_loadcell(idx)
#                 return V2Response(status=res.get("status", "success")).to_dict()
#
#             # Unknown action
#             return V2Response(status="failure", message=f"Unknown action: {req.action}", error={}).to_dict()
#
#         except Exception as e:
#             return V2Response(status="failure", message="Exception while handling request", error={"exception": str(e)}).to_dict()
#
# # End of file
