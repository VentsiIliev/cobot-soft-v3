from typing import Dict, Any, List
from backend.system.statistics.backend.StatiscticModel import GeneratorStats, TransducerStats, PumpStats, FanStats, LoadCellStats


class Controller:
    def __init__(self) -> None:
        self.generator = GeneratorStats(name="generator_on_seconds", value=0.0, unit="s")
        self.transducer = TransducerStats(name="transducer_on_seconds", value=0.0, unit="s")
        self.pumps: List[PumpStats] = [PumpStats(name=f"pump_{i+1}_stats", value=0.0, unit="ml") for i in range(4)]
        self.fan = FanStats(name="fan_on_seconds", value=0.0, unit="s")
        self.loadcells: List[LoadCellStats] = [LoadCellStats(name=f"loadcell_{i+1}_stats", value=0.0, unit="kg") for i in range(4)]

    # -------------------------
    # Serialization helpers
    # -------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generator": self.generator.to_dict(),
            "transducer": self.transducer.to_dict(),
            "pumps": [p.to_dict() for p in self.pumps],
            "fan": self.fan.to_dict(),
            "loadcells": [lc.to_dict() for lc in self.loadcells],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Controller":
        c = cls()
        c.generator = GeneratorStats.from_dict(data["generator"])
        c.transducer = TransducerStats.from_dict(data["transducer"])
        c.pumps = [PumpStats.from_dict(d) for d in data["pumps"]]
        c.fan = FanStats.from_dict(data["fan"])
        c.loadcells = [LoadCellStats.from_dict(d) for d in data["loadcells"]]
        return c
