# python
import json
import os
import datetime
from enum import Enum

STATISTICS_PATH = os.path.join(os.path.dirname(__file__), "storage", "statistics.json")
STARTED_AT_KEY = "started_at"

class StatisticKey(Enum):
    GENERATOR_ON_SECONDS = "generator_on_seconds"
    PUMP_ON_SECONDS = "pump_on_seconds"
    PUMP_RPM = "pump_rpm"

class Statistics:
    """Class to manage statistics."""
    _stats = None

    @staticmethod
    def _now_iso():
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    @staticmethod
    def get_statistics():
        """Read and return statistics as a dict."""
        if not os.path.exists(STATISTICS_PATH):
            return {}
        with open(STATISTICS_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    @staticmethod
    def _default_stats():
        """Return the canonical zeroed structure for statistics."""
        return {
            STARTED_AT_KEY: Statistics._now_iso(),
            StatisticKey.GENERATOR_ON_SECONDS.value: 0,
            StatisticKey.PUMP_ON_SECONDS.value: {},  # keyed by pump id
            StatisticKey.PUMP_RPM.value: {}          # keyed by pump id
        }

    @staticmethod
    def resetAllToZero():
        """Reset all statistics values to 0, including nested dicts, and update start time."""
        Statistics._ensure_stats_loaded()

        def zero_values(d):
            for key, value in list(d.items()):
                if isinstance(value, dict):
                    zero_values(value)
                else:
                    # only numeric/stat values should be zeroed; preserve non-numeric keys if any
                    try:
                        d[key] = 0
                    except Exception:
                        d[key] = 0

        # If no meaningful stats exist, replace with defaults
        if not Statistics._stats or all(k == STARTED_AT_KEY for k in Statistics._stats.keys()):
            Statistics._stats = Statistics._default_stats()
        else:
            zero_values(Statistics._stats)
            # ensure canonical keys exist
            for k, v in Statistics._default_stats().items():
                if k not in Statistics._stats:
                    Statistics._stats[k] = v if isinstance(v, dict) else 0

            # update started_at to now
            Statistics._stats[STARTED_AT_KEY] = Statistics._now_iso()

        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def update_statistics(new_stats):
        """Update statistics.json with new values."""
        os.makedirs(os.path.dirname(STATISTICS_PATH), exist_ok=True)
        with open(STATISTICS_PATH, "w") as f:
            json.dump(new_stats, f, indent=2)

    @staticmethod
    def _ensure_stats_loaded():
        if Statistics._stats is None:
            Statistics._stats = Statistics.get_statistics() or {}
            # ensure started_at exists
            if STARTED_AT_KEY not in Statistics._stats or not Statistics._stats.get(STARTED_AT_KEY):
                Statistics._stats[STARTED_AT_KEY] = Statistics._now_iso()
                Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def clearAll():
        """Clear all statistics and set a new start time and zeroed structure."""
        Statistics._stats = Statistics._default_stats()
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def _set_by_key(key, value):
        """Set a statistic value by key."""
        Statistics._ensure_stats_loaded()
        Statistics._stats[key] = value
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def _getByKey(key):
        """Get a statistic value by key."""
        Statistics._ensure_stats_loaded()
        return Statistics._stats.get(key, None)

    # START TIME accessor
    @staticmethod
    def getStartedAt():
        """Return the ISO timestamp when statistics collection started (string)."""
        Statistics._ensure_stats_loaded()
        return Statistics._stats.get(STARTED_AT_KEY)

    # GENERATOR ON SECONDS methods
    @staticmethod
    def getGeneratorOnSeconds():
        """Get the total seconds the generator has been on."""
        return Statistics._getByKey(StatisticKey.GENERATOR_ON_SECONDS.value)

    @staticmethod
    def setGeneratorOnSeconds(seconds):
        """Set the total seconds the generator has been on."""
        Statistics._set_by_key(StatisticKey.GENERATOR_ON_SECONDS.value, seconds)

    @staticmethod
    def flatten_stats(stats):
        """Flatten nested dicts in statistics"""
        flat = {}
        for key, value in stats.items():
            if isinstance(value, dict):
                for subkey, subval in value.items():
                    flat[f"{key}_{subkey}"] = subval
            else:
                flat[key] = value
        return flat

    @staticmethod
    def incrementGeneratorOnSeconds(seconds):
        """Increment the total seconds the generator has been on."""
        current_seconds = Statistics.getGeneratorOnSeconds() or 0
        Statistics.setGeneratorOnSeconds(current_seconds + seconds)

    # PUMP ON TIME methods
    @staticmethod
    def getPumpOnTimeById(pump_id):
        """Get the total seconds a specific pump has been on."""
        return Statistics._getByKey(f"{StatisticKey.PUMP_ON_SECONDS.value}_{pump_id}") or \
               (Statistics._getByKey(StatisticKey.PUMP_ON_SECONDS.value) or {}).get(str(pump_id))

    @staticmethod
    def setPumpOnTimeById(pump_id, seconds):
        """Set the total seconds a specific pump has been on."""
        # ensure nested dict exists
        Statistics._ensure_stats_loaded()
        pumps = Statistics._stats.setdefault(StatisticKey.PUMP_ON_SECONDS.value, {})
        pumps[str(pump_id)] = seconds
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def incrementPumpOnTimeById(pump_id, seconds):
        """Increment the total seconds a specific pump has been on."""
        current_seconds = Statistics.getPumpOnTimeById(pump_id) or 0
        Statistics.setPumpOnTimeById(pump_id, current_seconds + seconds)

    # PUMP RPM methods
    @staticmethod
    def getPumpRpmById(pump_id):
        """Get the RPM of a specific pump."""
        return Statistics._getByKey(f"{StatisticKey.PUMP_RPM.value}_{pump_id}") or \
               (Statistics._getByKey(StatisticKey.PUMP_RPM.value) or {}).get(str(pump_id))

    @staticmethod
    def setPumpRpmById(pump_id, rpm):
        """Set the RPM of a specific pump."""
        Statistics._ensure_stats_loaded()
        rpms = Statistics._stats.setdefault(StatisticKey.PUMP_RPM.value, {})
        rpms[str(pump_id)] = rpm
        Statistics.update_statistics(Statistics._stats)

    @staticmethod
    def incrementPumpRpmById(pump_id, rpm):
        """Increment the RPM of a specific pump."""
        current_rpm = Statistics.getPumpRpmById(pump_id) or 0
        Statistics.setPumpRpmById(pump_id, current_rpm + rpm)



# python
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import QTimer, Qt
from src.backend.system.Statistics import Statistics


class StatisticsViewer(QMainWindow):
    def __init__(self, refresh_interval_ms: int = 2000):
        super().__init__()
        self.setWindowTitle("Glue Dispensing - Statistics Viewer")
        self.resize(600, 400)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        # Header with started_at and buttons
        header_layout = QHBoxLayout()
        self.started_label = QLabel("Started at: -")
        self.started_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        header_layout.addWidget(self.started_label)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_stats)
        header_layout.addWidget(self.refresh_btn)

        self.reset_btn = QPushButton("Reset (clear & restart)")
        self.reset_btn.clicked.connect(self.reset_stats)
        header_layout.addWidget(self.reset_btn)

        layout.addLayout(header_layout)

        # Table for stats (key / value)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Auto-refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_stats)
        if refresh_interval_ms > 0:
            self.timer.start(refresh_interval_ms)

        self.load_stats()

    def load_stats(self):
        # Use the Statistics shared to read current values
        try:
            Statistics._ensure_stats_loaded()
        except Exception:
            # If the module shared changed, fall back to get_statistics
            pass

        stats = {}
        try:
            stats = Statistics.get_statistics() or {}
        except Exception:
            # fallback: try to access internal copy
            try:
                stats = Statistics._stats or {}
            except Exception:
                stats = {}

        # Ensure started_at is present via accessor when available
        try:
            started = Statistics.getStartedAt()
            if started:
                stats["started_at"] = started
        except Exception:
            # if not available, keep whatever is in stats
            pass

        # flatten nested structures if the helper exists
        try:
            flat = Statistics.flatten_stats(stats)
        except Exception:
            # naive flatten
            flat = {}
            for k, v in stats.items():
                if isinstance(v, dict):
                    for sk, sv in v.items():
                        flat[f"{k}_{sk}"] = sv
                else:
                    flat[k] = v

        # sort keys for stable display
        items = sorted(flat.items(), key=lambda x: x[0])

        self.table.setRowCount(len(items))
        for row, (k, v) in enumerate(items):
            key_item = QTableWidgetItem(str(k))
            key_item.setFlags(key_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            val_item = QTableWidgetItem(str(v))
            val_item.setFlags(val_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, key_item)
            self.table.setItem(row, 1, val_item)

        # update started label
        started_text = flat.get("started_at", "-")
        self.started_label.setText(f"Started at: {started_text}")

    def reset_stats(self):
        # Call the Statistics clearAll or resetAllToZero if available
        try:
            Statistics.clearAll()
        except Exception:
            try:
                Statistics.resetAllToZero()
            except Exception:
                # as last resort, write minimal structure
                try:
                    Statistics.update_statistics({ "started_at": Statistics._now_iso() })
                except Exception:
                    pass
        self.load_stats()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = StatisticsViewer(refresh_interval_ms=2000)
    viewer.show()
    sys.exit(app.exec())
