"""
Pure shared v2 Statistics Request Handler.

This handler ONLY works with proper shared v2 requests and endpoints.
NO legacy compatibility, NO string-based actions, NO manual parsing.

ONLY accepts:
- V2Request objects with proper resource URLs
- HTTP method validation  
- URL-based routing using endpoint definitions
"""

from typing import Any, Dict, Optional, Tuple
import json
import re

from modules.shared.v2.Request import Request as V2Request
from modules.shared.v2.Response import Response as V2Response
from modules.shared.v2.constants.ApiEndpoints import ApiEndpoints, EndpointGroups, HttpMethod
from src.backend.system.statistics.api.StatisticsAPI import StatisticsAPI


class PureApiV2StatisticsHandler:
    """
    Pure shared v2 Statistics Request Handler.
    
    STRICT REQUIREMENTS:
    - ONLY accepts V2Request objects
    - ONLY routes based on resource URLs  
    - ONLY supports defined shared v2 endpoints
    - ONLY validates HTTP methods
    - NO legacy compatibility whatsoever
    
    This ensures complete shared v2 compliance and consistency.
    """

    def __init__(self, stats_api: StatisticsAPI):
        """Initialize with StatisticsAPI instance."""
        self.stats_api = stats_api
        self._build_endpoint_registry()

    def _build_endpoint_registry(self):
        """Build registry of valid shared v2 endpoints with their handlers."""
        self.endpoint_registry = {}
        
        # Only register statistics endpoints from shared v2 definitions
        for endpoint in EndpointGroups.STATISTICS:
            self.endpoint_registry[endpoint.path] = {
                'endpoint': endpoint,
                'handler': self._get_handler_for_endpoint(endpoint),
                'method': endpoint.method,
                'requires_auth': endpoint.requires_auth,
                'rate_limited': endpoint.rate_limited
            }

    def _get_handler_for_endpoint(self, endpoint):
        """Map endpoint to handler method based on URL pattern."""
        path = endpoint.path
        
        # Map endpoints to handler methods by URL pattern
        handler_mapping = {
            '/api/v2/stats/all': self._handle_get_all_stats,
            '/api/v2/stats/generator': self._handle_get_generator_stats,
            '/api/v2/stats/transducer': self._handle_get_transducer_stats,
            '/api/v2/stats/pumps': self._handle_get_pumps_stats,
            '/api/v2/stats/pumps/{pump_id}': self._handle_get_pump_stats,
            '/api/v2/stats/fan': self._handle_get_fan_stats,
            '/api/v2/stats/loadcells': self._handle_get_loadcells_stats,
            '/api/v2/stats/loadcells/{loadcell_id}': self._handle_get_loadcell_stats,
            '/api/v2/stats/reset/all': self._handle_reset_all_stats,
            '/api/v2/stats/reset/generator': self._handle_reset_generator,
            '/api/v2/stats/reset/transducer': self._handle_reset_transducer,
            '/api/v2/stats/reset/fan': self._handle_reset_fan,
            '/api/v2/stats/reset/pumps/{pump_id}/motor': self._handle_reset_pump_motor,
            '/api/v2/stats/reset/pumps/{pump_id}/belt': self._handle_reset_pump_belt,
            '/api/v2/stats/reset/loadcells/{loadcell_id}': self._handle_reset_loadcell,
            '/api/v2/stats/export/csv': self._handle_export_csv,
            '/api/v2/stats/export/json': self._handle_export_json,
            '/api/v2/stats/reports/daily': self._handle_daily_report,
            '/api/v2/stats/reports/weekly': self._handle_weekly_report,
            '/api/v2/stats/reports/monthly': self._handle_monthly_report,
        }
        
        return handler_mapping.get(path)

    def handle(self, request: Any) -> Dict[str, Any]:
        """
        Handle ONLY pure shared v2 requests.
        
        Args:
            request: MUST be a V2Request object
            
        Returns:
            Dict response following V2Response format
            
        Raises:
            ValueError: If request is not a proper V2Request
        """
        # STRICT: Only accept V2Request objects
        if not isinstance(request, V2Request):
            return self._error_response(
                "Invalid request type. Only V2Request objects are supported.",
                {"received_type": str(type(request)), "expected_type": "V2Request"}
            )
        
        # STRICT: Must have resource URL
        if not request.resource:
            return self._error_response(
                "Missing resource URL. Pure shared v2 requires proper endpoint URLs.",
                {"resource": request.resource}
            )
        
        # STRICT: Must have HTTP method
        if not request.req_type:
            return self._error_response(
                "Missing HTTP method. Pure shared v2 requires proper HTTP methods.",
                {"req_type": request.req_type}
            )
        
        try:
            # Resolve endpoint and extract parameters
            endpoint_info, url_params = self._resolve_endpoint(request)
            
            if not endpoint_info:
                return self._error_response(
                    f"Unknown shared v2 endpoint: {request.resource}",
                    {
                        "resource": request.resource,
                        "supported_endpoints": list(self.endpoint_registry.keys())[:10]  # Show first 10
                    }
                )
            
            # Validate HTTP method
            if not self._validate_http_method(request, endpoint_info['endpoint']):
                return self._error_response(
                    f"Invalid HTTP method for endpoint",
                    {
                        "resource": request.resource,
                        "provided_method": request.req_type,
                        "expected_method": endpoint_info['endpoint'].method.value
                    }
                )
            
            # Get handler
            handler = endpoint_info['handler']
            if not handler:
                return self._error_response(
                    f"No handler implemented for endpoint: {request.resource}",
                    {"endpoint": request.resource}
                )
            
            # Execute handler
            return handler(request, url_params)
            
        except Exception as e:
            return self._error_response(
                f"Request processing failed: {str(e)}",
                {"exception": str(e), "resource": request.resource}
            )

    def _resolve_endpoint(self, request: V2Request) -> Tuple[Optional[Dict], Dict[str, Any]]:
        """
        Resolve V2Request to endpoint registry entry and extract URL parameters.
        
        ONLY uses resource URL for routing - no legacy action support.
        """
        resource_url = request.resource
        
        # Try exact match first
        if resource_url in self.endpoint_registry:
            return self.endpoint_registry[resource_url], {}
        
        # Try parameterized endpoint matching
        for template_url, endpoint_info in self.endpoint_registry.items():
            if '{' in template_url:
                url_params = self._extract_url_parameters(template_url, resource_url)
                if url_params is not None:
                    return endpoint_info, url_params
        
        return None, {}

    def _extract_url_parameters(self, template_url: str, actual_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract parameters from URL using template pattern.
        
        Examples:
            template: "/api/v2/stats/pumps/{pump_id}"
            actual: "/api/v2/stats/pumps/5" 
            result: {"pump_id": 5}
            
            template: "/api/v2/stats/reset/pumps/{pump_id}/motor"
            actual: "/api/v2/stats/reset/pumps/3/motor"
            result: {"pump_id": 3}
        """
        # Convert template to regex with named groups
        pattern = re.escape(template_url)
        pattern = pattern.replace(r'\{pump_id\}', r'(?P<pump_id>\d+)')
        pattern = pattern.replace(r'\{loadcell_id\}', r'(?P<loadcell_id>\d+)')
        pattern = f'^{pattern}$'
        
        match = re.match(pattern, actual_url)
        if match:
            params = match.groupdict()
            # Convert numeric strings to integers
            for key, value in params.items():
                if value.isdigit():
                    params[key] = int(value)
            return params
        return None

    def _validate_http_method(self, request: V2Request, endpoint) -> bool:
        """Validate that the HTTP method matches the endpoint definition."""
        try:
            provided_method = HttpMethod(request.req_type.upper())
            return provided_method == endpoint.method
        except ValueError:
            return False

    def _success_response(self, data: Any = None, message: str = None) -> Dict[str, Any]:
        """Create standardized V2 success response."""
        response = V2Response(
            status="success", 
            data=data, 
            message=message
        )
        return response.to_dict()

    def _error_response(self, message: str, error_details: Dict = None) -> Dict[str, Any]:
        """Create standardized V2 error response."""
        response = V2Response(
            status="error", 
            message=message, 
            error=error_details or {}
        )
        return response.to_dict()

    # ============================================================================
    # PURE shared v2 HANDLER METHODS
    # ============================================================================
    # Each handler method corresponds to exactly one shared v2 endpoint

    def _handle_get_all_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/all"""
        try:
            result = self.stats_api.get_all()
            return self._success_response(result, "Retrieved all statistics")
        except Exception as e:
            return self._error_response(f"Failed to retrieve all statistics: {str(e)}")

    def _handle_get_generator_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/generator"""
        try:
            result = self.stats_api.get_generator_stats()
            return self._success_response(result, "Retrieved generator statistics")
        except Exception as e:
            return self._error_response(f"Failed to retrieve generator statistics: {str(e)}")

    def _handle_get_transducer_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/transducer"""
        try:
            result = self.stats_api.get_transducer_stats()
            return self._success_response(result, "Retrieved transducer statistics")
        except Exception as e:
            return self._error_response(f"Failed to retrieve transducer statistics: {str(e)}")

    def _handle_get_pumps_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/pumps"""
        try:
            result = self.stats_api.get_pumps_stats()
            return self._success_response(result, "Retrieved all pump statistics")
        except Exception as e:
            return self._error_response(f"Failed to retrieve pump statistics: {str(e)}")

    def _handle_get_pump_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/pumps/{pump_id}"""
        try:
            pump_id = params.get("pump_id")
            if pump_id is None:
                return self._error_response(
                    "Missing pump_id in URL path",
                    {"expected_format": "/api/v2/stats/pumps/{pump_id}"}
                )
            
            result = self.stats_api.get_pump_stats(pump_id)
            return self._success_response(result, f"Retrieved statistics for pump {pump_id}")
        except Exception as e:
            return self._error_response(f"Failed to retrieve pump {params.get('pump_id', '?')} statistics: {str(e)}")

    def _handle_get_fan_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/fan"""
        try:
            result = self.stats_api.get_fan_stats()
            return self._success_response(result, "Retrieved fan statistics")
        except Exception as e:
            return self._error_response(f"Failed to retrieve fan statistics: {str(e)}")

    def _handle_get_loadcells_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/loadcells"""
        try:
            result = self.stats_api.get_loadcells_stats()
            return self._success_response(result, "Retrieved all loadcell statistics")
        except Exception as e:
            return self._error_response(f"Failed to retrieve loadcell statistics: {str(e)}")

    def _handle_get_loadcell_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/loadcells/{loadcell_id}"""
        try:
            loadcell_id = params.get("loadcell_id")
            if loadcell_id is None:
                return self._error_response(
                    "Missing loadcell_id in URL path",
                    {"expected_format": "/api/v2/stats/loadcells/{loadcell_id}"}
                )
            
            result = self.stats_api.get_loadcell_stats(loadcell_id)
            return self._success_response(result, f"Retrieved statistics for loadcell {loadcell_id}")
        except Exception as e:
            return self._error_response(f"Failed to retrieve loadcell {params.get('loadcell_id', '?')} statistics: {str(e)}")

    def _handle_reset_all_stats(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/all"""
        try:
            result = self.stats_api.reset_all_stats()
            return self._success_response(result, "Reset all statistics")
        except Exception as e:
            return self._error_response(f"Failed to reset all statistics: {str(e)}")

    def _handle_reset_generator(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/generator"""
        try:
            result = self.stats_api.reset_generator()
            return self._success_response(result, "Reset generator statistics")
        except Exception as e:
            return self._error_response(f"Failed to reset generator statistics: {str(e)}")

    def _handle_reset_transducer(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/transducer"""
        try:
            result = self.stats_api.reset_transducer()
            return self._success_response(result, "Reset transducer statistics")
        except Exception as e:
            return self._error_response(f"Failed to reset transducer statistics: {str(e)}")

    def _handle_reset_fan(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/fan"""
        try:
            result = self.stats_api.reset_fan()
            return self._success_response(result, "Reset fan statistics")
        except Exception as e:
            return self._error_response(f"Failed to reset fan statistics: {str(e)}")

    def _handle_reset_pump_motor(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/pumps/{pump_id}/motor"""
        try:
            pump_id = params.get("pump_id")
            if pump_id is None:
                return self._error_response(
                    "Missing pump_id in URL path",
                    {"expected_format": "/api/v2/stats/reset/pumps/{pump_id}/motor"}
                )
            
            result = self.stats_api.reset_pump_motor(pump_id)
            return self._success_response(result, f"Reset motor statistics for pump {pump_id}")
        except Exception as e:
            return self._error_response(f"Failed to reset pump {params.get('pump_id', '?')} motor statistics: {str(e)}")

    def _handle_reset_pump_belt(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/pumps/{pump_id}/belt"""
        try:
            pump_id = params.get("pump_id")
            if pump_id is None:
                return self._error_response(
                    "Missing pump_id in URL path",
                    {"expected_format": "/api/v2/stats/reset/pumps/{pump_id}/belt"}
                )
            
            result = self.stats_api.reset_pump_belt(pump_id)
            return self._success_response(result, f"Reset belt statistics for pump {pump_id}")
        except Exception as e:
            return self._error_response(f"Failed to reset pump {params.get('pump_id', '?')} belt statistics: {str(e)}")

    def _handle_reset_loadcell(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/reset/loadcells/{loadcell_id}"""
        try:
            loadcell_id = params.get("loadcell_id")
            if loadcell_id is None:
                return self._error_response(
                    "Missing loadcell_id in URL path",
                    {"expected_format": "/api/v2/stats/reset/loadcells/{loadcell_id}"}
                )
            
            result = self.stats_api.reset_loadcell(loadcell_id)
            return self._success_response(result, f"Reset statistics for loadcell {loadcell_id}")
        except Exception as e:
            return self._error_response(f"Failed to reset loadcell {params.get('loadcell_id', '?')} statistics: {str(e)}")

    def _handle_export_csv(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/export/csv"""
        try:
            filters = request.data or {}
            result = self.stats_api.export_stats_csv(filters)
            return self._success_response(result, "Exported statistics as CSV")
        except Exception as e:
            return self._error_response(f"Failed to export statistics as CSV: {str(e)}")

    def _handle_export_json(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/v2/stats/export/json"""
        try:
            filters = request.data or {}
            result = self.stats_api.export_stats_json(filters)
            return self._success_response(result, "Exported statistics as JSON")
        except Exception as e:
            return self._error_response(f"Failed to export statistics as JSON: {str(e)}")

    def _handle_daily_report(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/reports/daily"""
        try:
            date = request.data.get("date") if request.data else None
            result = self.stats_api.get_daily_report(date)
            return self._success_response(result, f"Retrieved daily report for {date or 'today'}")
        except Exception as e:
            return self._error_response(f"Failed to get daily report: {str(e)}")

    def _handle_weekly_report(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/reports/weekly"""
        try:
            week = request.data.get("week") if request.data else None
            result = self.stats_api.get_weekly_report(week)
            return self._success_response(result, f"Retrieved weekly report for {week or 'this week'}")
        except Exception as e:
            return self._error_response(f"Failed to get weekly report: {str(e)}")

    def _handle_monthly_report(self, request: V2Request, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /api/v2/stats/reports/monthly"""
        try:
            month = request.data.get("month") if request.data else None
            result = self.stats_api.get_monthly_report(month)
            return self._success_response(result, f"Retrieved monthly report for {month or 'this month'}")
        except Exception as e:
            return self._error_response(f"Failed to get monthly report: {str(e)}")

    # ============================================================================
    # PURE shared v2 UTILITIES
    # ============================================================================

    def get_api_info(self) -> Dict[str, Any]:
        """Get information about this pure shared v2 handler."""
        return {
            "handler_type": "PureApiV2StatisticsHandler",
            "api_version": "v2",
            "strict_mode": True,
            "legacy_support": False,
            "supported_endpoints": len(self.endpoint_registry),
            "endpoint_list": list(self.endpoint_registry.keys()),
            "requirements": {
                "request_type": "V2Request only",
                "routing_method": "Resource URL only",
                "http_method_validation": True,
                "parameter_extraction": "URL path only"
            }
        }

    def validate_request_format(self, request: Any) -> Dict[str, Any]:
        """Validate if a request meets pure shared v2 requirements."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not isinstance(request, V2Request):
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Invalid request type: {type(request)}. Must be V2Request.")
        
        if hasattr(request, 'resource') and not request.resource:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Missing resource URL. Pure shared v2 requires proper endpoint URLs.")
        
        if hasattr(request, 'req_type') and not request.req_type:
            validation_result["is_valid"] = False
            validation_result["errors"].append("Missing HTTP method. Pure shared v2 requires proper HTTP methods.")
        
        if hasattr(request, 'action') and request.action:
            validation_result["warnings"].append("Action field is ignored in pure shared v2 mode. Only resource URL is used for routing.")
        
        return validation_result