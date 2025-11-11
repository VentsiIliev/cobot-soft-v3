from src.backend.system.statistics.backend.StatiscticModel import (
     GeneratorStats, TransducerStats, PumpStats, FanStats, LoadCellStats
)
from src.backend.system.statistics.backend.StatisticsController import Controller
from src.backend.system.statistics.backend.StatsPersistence import StatsPersistence
import time

class StatsService:
    def __init__(self, controller: Controller, persistence: StatsPersistence):
        self.controller = controller
        self.persistence = persistence

    # -------------------------
    # GENERATOR
    # -------------------------
    def toggle_generator(self, on: bool):
        self.controller.generator.toggle(on)
        self.persistence.save("generator", self.controller.generator.to_dict())

    def reset_generator(self):
        self.controller.generator.reset()
        self.persistence.save("generator", self.controller.generator.to_dict())

    # -------------------------
    # TRANSDUCER
    # -------------------------
    def toggle_transducer(self, on: bool):
        self.controller.transducer.toggle(on)
        self.persistence.save("transducer", self.controller.transducer.to_dict())

    def reset_transducer(self):
        self.controller.transducer.reset()
        self.persistence.save("transducer", self.controller.transducer.to_dict())

    # -------------------------
    # PUMPS
    # -------------------------
    def toggle_pump(self, index: int, on: bool):
        pump: PumpStats = self.controller.pumps[index]
        pump.toggle(on)
        self.persistence.save(f"pump_{index+1}", pump.to_dict())

    def pump_glue(self, index: int, qty: float):
        pump: PumpStats = self.controller.pumps[index]
        pump.pump_glue(qty)
        self.persistence.save(f"pump_{index+1}", pump.to_dict())

    def reset_pump_motor(self, index: int):
        pump: PumpStats = self.controller.pumps[index]
        pump.reset_motor()
        self.persistence.save(f"pump_{index+1}", pump.to_dict())

    def reset_pump_belt(self, index: int):
        pump: PumpStats = self.controller.pumps[index]
        pump.reset_belt()
        self.persistence.save(f"pump_{index+1}", pump.to_dict())

    def reset_pump(self, index: int):
        pump: PumpStats = self.controller.pumps[index]
        pump.reset()
        self.persistence.save(f"pump_{index+1}", pump.to_dict())

    # -------------------------
    # FAN
    # -------------------------
    def toggle_fan(self, on: bool):
        fan: FanStats = self.controller.fan
        fan.toggle(on)
        self.persistence.save("fan", fan.to_dict())

    def reset_fan(self):
        fan: FanStats = self.controller.fan
        fan.reset()
        self.persistence.save("fan", fan.to_dict())

    # -------------------------
    # LOADCELLS
    # -------------------------
    def update_loadcell(self, index: int, weight: float):
        lc: LoadCellStats = self.controller.loadcells[index]
        lc.update_weight(weight)
        self.persistence.save(f"loadcell_{index+1}", lc.to_dict())

    def reset_loadcell(self, index: int):
        lc: LoadCellStats = self.controller.loadcells[index]
        lc.reset()
        self.persistence.save(f"loadcell_{index+1}", lc.to_dict())

    # -------------------------
    # FULL SAVE/LOAD
    # -------------------------
    def save_all(self):
        self.persistence.save("generator", self.controller.generator.to_dict())
        self.persistence.save("transducer", self.controller.transducer.to_dict())
        for i, pump in enumerate(self.controller.pumps, start=1):
            self.persistence.save(f"pump_{i}", pump.to_dict())
        self.persistence.save("fan", self.controller.fan.to_dict())
        for i, lc in enumerate(self.controller.loadcells, start=1):
            self.persistence.save(f"loadcell_{i}", lc.to_dict())

    def load_all(self):
        # Generator
        self.controller.generator = GeneratorStats.from_dict(
            self.persistence.load("generator", default_data={
                "name": "generator_on_seconds", "value": 0.0, "unit": "s", "start_time": time.time()
            })
        )

        # Transducer
        self.controller.transducer = TransducerStats.from_dict(
            self.persistence.load("transducer", default_data={
                "name": "transducer_on_seconds", "value": 0.0, "unit": "s", "start_time": time.time()
            })
        )

        # Pumps
        for i, pump in enumerate(self.controller.pumps, start=1):
            self.controller.pumps[i - 1] = PumpStats.from_dict(
                self.persistence.load(f"pump_{i}", default_data={
                    "name": f"pump_{i}_stats",
                    "value": 0.0,
                    "unit": "ml",
                    "start_time": time.time(),
                    "motor_glue_qty": 0.0,
                    "belt_glue_qty": 0.0,
                    "motor_start_time": time.time(),
                    "belt_start_time": time.time(),
                    "toggle_count": 0,
                    "total_on_seconds": 0.0,
                    "last_on_time": None
                })
            )

        # Fan
        self.controller.fan = FanStats.from_dict(
            self.persistence.load("fan", default_data={
                "name": "fan_on_seconds", "value": 0.0, "unit": "s",
                "start_time": time.time(), "toggle_count": 0, "total_on_seconds": 0.0, "last_on_time": None
            })
        )

        # Loadcells
        for i, lc in enumerate(self.controller.loadcells, start=1):
            self.controller.loadcells[i - 1] = LoadCellStats.from_dict(
                self.persistence.load(f"loadcell_{i}", default_data={
                    "name": f"loadcell_{i}_stats",
                    "value": 0.0,
                    "unit": "kg",
                    "start_time": time.time(),
                    "loadcell_start_time": time.time(),
                    "last_weight": 0.0
                })
            )

