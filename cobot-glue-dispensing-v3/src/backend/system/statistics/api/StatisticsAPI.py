from backend.system.statistics.backend.StatsService import StatsService
from backend.system.statistics.backend.StatisticsController import Controller
from typing import Dict, Any, Optional


class PureApiV2StatisticsRequestSender:
    pass


class StatisticsAPI:
    """
    Enhanced Statistics shared with shared v2 support.
    
    Provides both local service operations and remote shared v2 request capabilities.
    Can work with or without a request sender for flexible deployment scenarios.
    """

    def __init__(self, service: StatsService, request_sender: Optional[PureApiV2StatisticsRequestSender] = None):
        """
        Initialize Statistics shared.
        
        Args:
            service: Local statistics service for data operations
            request_sender: Optional request sender for remote shared v2 operations
        """
        self.service = service
        self.controller: Controller = service.controller
        self.request_sender = request_sender

    # ============================================================================
    # LOCAL SERVICE OPERATIONS (existing functionality)
    # ============================================================================

    def get_all(self) -> Dict[str, Any]:
        """Get all statistics from local service."""
        self.service.load_all()
        return self.controller.to_dict()

    def get_generator_stats(self) -> Dict[str, Any]:
        """Get generator statistics from local service."""
        self.service.load_all()
        return self.controller.generator.to_dict()

    def get_transducer_stats(self) -> Dict[str, Any]:
        """Get transducer statistics from local service."""
        self.service.load_all()
        return self.controller.transducer.to_dict()

    def get_pumps_stats(self) -> Dict[str, Any]:
        """Get all pump statistics from local service."""
        self.service.load_all()
        return {"pumps": [p.to_dict() for p in self.controller.pumps]}

    def get_pump_stats(self, pump_id: int) -> Dict[str, Any]:
        """Get specific pump statistics from local service."""
        self.service.load_all()
        if 0 <= pump_id < len(self.controller.pumps):
            return self.controller.pumps[pump_id].to_dict()
        return {"status": "error", "error": f"Pump {pump_id} not found"}

    def get_fan_stats(self) -> Dict[str, Any]:
        """Get fan statistics from local service."""
        self.service.load_all()
        return self.controller.fan.to_dict()

    def get_loadcells_stats(self) -> Dict[str, Any]:
        """Get all loadcell statistics from local service."""
        self.service.load_all()
        return {"loadcells": [lc.to_dict() for lc in self.controller.loadcells]}

    def get_loadcell_stats(self, loadcell_id: int) -> Dict[str, Any]:
        """Get specific loadcell statistics from local service."""
        self.service.load_all()
        if 0 <= loadcell_id < len(self.controller.loadcells):
            return self.controller.loadcells[loadcell_id].to_dict()
        return {"status": "error", "error": f"Loadcell {loadcell_id} not found"}

    # ============================================================================
    # RESET OPERATIONS (existing functionality)
    # ============================================================================

    def reset_all_stats(self) -> Dict[str, Any]:
        """Reset all statistics using local service."""
        try:
            self.service.reset_generator()
            self.service.reset_transducer()
            self.service.reset_fan()
            for i in range(len(self.controller.pumps)):
                self.service.reset_pump_motor(i)
                self.service.reset_pump_belt(i)
            for i in range(len(self.controller.loadcells)):
                self.service.reset_loadcell(i)
            return {"status": "success", "message": "All statistics reset"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reset_generator(self) -> Dict[str, Any]:
        """Reset generator statistics using local service."""
        try:
            self.service.reset_generator()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reset_transducer(self) -> Dict[str, Any]:
        """Reset transducer statistics using local service."""
        try:
            self.service.reset_transducer()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reset_fan(self) -> Dict[str, Any]:
        """Reset fan statistics using local service."""
        try:
            self.service.reset_fan()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reset_pump_motor(self, pump_id: int) -> Dict[str, Any]:
        """Reset pump motor statistics using local service."""
        try:
            self.service.reset_pump_motor(pump_id)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reset_pump_belt(self, pump_id: int) -> Dict[str, Any]:
        """Reset pump belt statistics using local service."""
        try:
            self.service.reset_pump_belt(pump_id)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def reset_loadcell(self, loadcell_id: int) -> Dict[str, Any]:
        """Reset loadcell statistics using local service."""
        try:
            self.service.reset_loadcell(loadcell_id)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ============================================================================
    # REMOTE shared v2 OPERATIONS (new functionality)
    # ============================================================================

    def get_all_stats_remote(self) -> Dict[str, Any]:
        """Get all statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.get_all_stats()

    def reset_generator_remote(self) -> Dict[str, Any]:
        """Reset generator statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.reset_generator()

    def reset_transducer_remote(self) -> Dict[str, Any]:
        """Reset transducer statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.reset_transducer()

    def reset_fan_remote(self) -> Dict[str, Any]:
        """Reset fan statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.reset_fan()

    def reset_pump_motor_remote(self, pump_id: int) -> Dict[str, Any]:
        """Reset pump motor statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.reset_pump_motor(pump_id)

    def reset_pump_belt_remote(self, pump_id: int) -> Dict[str, Any]:
        """Reset pump belt statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.reset_pump_belt(pump_id)

    def reset_loadcell_remote(self, loadcell_id: int) -> Dict[str, Any]:
        """Reset loadcell statistics via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.reset_loadcell(loadcell_id)

    # ============================================================================
    # EXPORT AND REPORTING (new shared v2 functionality)
    # ============================================================================

    def export_stats_csv(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export statistics as CSV via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.export_stats_csv(filters)

    def export_stats_json(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export statistics as JSON via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.export_stats_json(filters)

    def get_daily_report(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily statistics report via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.get_daily_report(date)

    def get_weekly_report(self, week: Optional[str] = None) -> Dict[str, Any]:
        """Get weekly statistics report via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.get_weekly_report(week)

    def get_monthly_report(self, month: Optional[str] = None) -> Dict[str, Any]:
        """Get monthly statistics report via shared v2 request sender."""
        if not self.request_sender:
            return {"status": "error", "error": "No request sender configured"}
        return self.request_sender.get_monthly_report(month)

    # ============================================================================
    # HYBRID OPERATIONS (prefer remote, fallback to local)
    # ============================================================================

    def get_all_hybrid(self) -> Dict[str, Any]:
        """Get all statistics - prefer remote shared v2, fallback to local."""
        if self.request_sender:
            try:
                result = self.request_sender.get_all_stats()
                if result.get("status") != "error":
                    return result
            except Exception:
                pass
        return self.get_all()

    def reset_generator_hybrid(self) -> Dict[str, Any]:
        """Reset generator - prefer remote shared v2, fallback to local."""
        if self.request_sender:
            try:
                result = self.request_sender.reset_generator()
                if result.get("status") != "error":
                    return result
            except Exception:
                pass
        return self.reset_generator()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def set_request_sender(self, request_sender: PureApiV2StatisticsRequestSender) -> None:
        """Set or update the request sender for remote operations."""
        self.request_sender = request_sender

    def has_remote_capability(self) -> bool:
        """Check if remote shared v2 operations are available."""
        return self.request_sender is not None

    def get_capabilities(self) -> Dict[str, Any]:
        """Get shared capabilities information."""
        return {
            "local_operations": True,
            "remote_operations": self.has_remote_capability(),
            "export_operations": self.has_remote_capability(),
            "reporting_operations": self.has_remote_capability(),
            "api_version": "v2" if self.has_remote_capability() else "v1"
        }

