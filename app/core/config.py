import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "config.json"

def read_config() -> dict:
    """
    Reads the configuration from the config file.

    Returns:
        dict: The configuration data.
    """
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"excluded_directories": []}

def update_config(config_data: dict):
    """
    Updates the configuration in the config file.

    Args:
        config_data (dict): The new configuration data.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)
