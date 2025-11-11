# python
from typing import Any, Dict, TypeVar, Type
from pydantic import BaseModel, Field
import time

T = TypeVar("T", bound="BaseStatisticDataModel")

class BaseStatisticDataModel(BaseModel):
    model_config = {"frozen": False}  # allow mutation

    name: str
    value: float
    unit: str
    start_time: float = Field(default_factory=time.time)

    def increment(self, amount: float = 1.0) -> None:
        if self.value <= 0 and amount > 0:
            self.start_time = time.time()
        self.value = float(self.value) + float(amount)

    def decrement(self, amount: float = 1.0) -> None:
        self.value = max(0.0, float(self.value) - float(amount))

    def reset(self) -> None:
        self.value = 0.0
        self.start_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls.model_validate(data)  # type: ignore[return-value]



# -----------------------------
# GENERATOR
# -----------------------------
class GeneratorStats(BaseStatisticDataModel):
    toggle_count: int = 0
    total_on_seconds: float = 0.0
    last_on_time: float | None = None

    def toggle(self, on: bool) -> None:
        self.toggle_count += 1
        if on:
            # starting
            self.last_on_time = time.time()
        else:
            # stopping
            if self.last_on_time:
                self.total_on_seconds += time.time() - self.last_on_time
                self.last_on_time = None

    def reset(self) -> None:
        super().reset()
        self.toggle_count = 0
        self.total_on_seconds = 0.0
        self.last_on_time = None


# -----------------------------
# TRANSDUCER
# -----------------------------
class TransducerStats(BaseStatisticDataModel):
    toggle_count: int = 0
    total_on_seconds: float = 0.0
    last_on_time: float | None = None

    def toggle(self, on: bool) -> None:
        self.toggle_count += 1
        if on:
            self.last_on_time = time.time()
        else:
            if self.last_on_time:
                self.total_on_seconds += time.time() - self.last_on_time
                self.last_on_time = None

    def reset(self) -> None:
        super().reset()
        self.toggle_count = 0
        self.total_on_seconds = 0.0
        self.last_on_time = None


# -----------------------------
# PUMP
# -----------------------------
class PumpStats(BaseStatisticDataModel):
    # Tracking times
    motor_start_time: float = Field(default_factory=time.time)
    belt_start_time: float = Field(default_factory=time.time)

    # Glue quantities
    motor_glue_qty: float = 0.0
    belt_glue_qty: float = 0.0

    # On/off tracking
    toggle_count: int = 0
    total_on_seconds: float = 0.0
    last_on_time: float | None = None

    def pump_glue(self, qty: float) -> None:
        """Register that the pump has pumped a quantity of glue."""
        self.motor_glue_qty += qty
        self.belt_glue_qty += qty
        self.value += qty  # keep base.value as 'total glue pumped' if you want

    def toggle(self, on: bool) -> None:
        """Track pump ON/OFF state changes."""
        self.toggle_count += 1
        if on:
            self.last_on_time = time.time()
        else:
            if self.last_on_time:
                self.total_on_seconds += time.time() - self.last_on_time
                self.last_on_time = None

    def reset_motor(self) -> None:
        """Reset motor-related stats when motor is replaced."""
        self.motor_start_time = time.time()
        self.motor_glue_qty = 0.0

    def reset_belt(self) -> None:
        """Reset belt-related stats when belt is replaced."""
        self.belt_start_time = time.time()
        self.belt_glue_qty = 0.0

    def reset(self) -> None:
        """Full reset (pump replaced entirely)."""
        super().reset()
        self.motor_start_time = time.time()
        self.belt_start_time = time.time()
        self.motor_glue_qty = 0.0
        self.belt_glue_qty = 0.0
        self.toggle_count = 0
        self.total_on_seconds = 0.0
        self.last_on_time = None


# -----------------------------
# FAN
# -----------------------------

class FanStats(BaseStatisticDataModel):
    toggle_count: int = 0
    total_on_seconds: float = 0.0
    last_on_time: float | None = None
    fan_start_time: float = Field(default_factory=time.time)

    def toggle(self, on: bool) -> None:
        """Track fan ON/OFF state changes."""
        self.toggle_count += 1
        if on:
            # turned ON
            self.last_on_time = time.time()
        else:
            # turned OFF
            if self.last_on_time:
                self.total_on_seconds += time.time() - self.last_on_time
                self.last_on_time = None

    def reset(self) -> None:
        """Reset all statistics when fan is replaced."""
        super().reset()
        self.toggle_count = 0
        self.total_on_seconds = 0.0
        self.last_on_time = None
        self.fan_start_time = time.time()

# -----------------------------
# LOADCELL
# -----------------------------

class LoadCellStats(BaseStatisticDataModel):
    loadcell_start_time: float = Field(default_factory=time.time)
    last_weight: float = 0.0

    def update_weight(self, weight: float) -> None:
        """Update the last measured weight."""
        self.last_weight = weight
        self.value = weight  # optional: keep base.value = current weight

    def reset(self) -> None:
        """Reset stats when loadcell is replaced."""
        super().reset()
        self.loadcell_start_time = time.time()
        self.last_weight = 0.0

