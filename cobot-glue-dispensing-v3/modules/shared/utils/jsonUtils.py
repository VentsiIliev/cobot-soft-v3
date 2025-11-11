import json
from typing import Dict, Any, Optional


def load_json_file(file_path: str, default_return: Any = None, debug: bool = False) -> Any:
    """
    Generic utility function to load JSON data from a file.

    Args:
        file_path (str): Path to the JSON file to load
        default_return (Any): Value to return if loading fails (default: None)
        debug (bool): Whether to print debug information (default: False)

    Returns:
        Any: The loaded JSON data, or default_return if loading fails

    Example:
        # Load settings with empty dict as fallback
        settings = load_json_file('settings.json', {})

        # Load config with debug output
        config = load_json_file('config.json', {}, debug=True)

        # Load data with custom fallback
        data = load_json_file('data.json', [])
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if debug:
                print(f"Successfully loaded data from {file_path}:", data)
            return data
    except FileNotFoundError:
        if debug:
            print(f"File not found: {file_path}")
        return default_return
    except json.JSONDecodeError as e:
        if debug:
            print(f"Invalid JSON in {file_path}: {e}")
        return default_return
    except Exception as e:
        if debug:
            print(f"Failed to load {file_path}: {e}")
        return default_return


