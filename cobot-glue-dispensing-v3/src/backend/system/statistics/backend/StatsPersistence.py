import os
import json
import time
from typing import Any, Dict, Optional

class StatsPersistence:
    def __init__(self, storage_folder: str):
        self.storage_folder = storage_folder
        os.makedirs(self.storage_folder, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        return os.path.join(self.storage_folder, f"{key}.json")

    def save(self, key: str, data: Dict[str, Any]) -> None:
        file_path = self._get_file_path(key)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def load(self, key: str, default_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            # file missing → create with default
            if default_data is None:
                default_data = {"name": key, "value": 0.0, "unit": "s", "start_time": time.time()}
            self.save(key, default_data)
            return default_data
        with open(file_path, "r") as f:
            return json.load(f)
