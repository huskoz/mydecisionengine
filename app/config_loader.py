"""Loads config.yaml and checks it has everything the pipeline needs.
In: the path to the YAML file. Out: one plain dict with the modes,
thresholds, capacity, completed list, and task backlog.
"""

from pathlib import Path

import yaml

# config.yaml sits in the project root, one folder above this package.
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

REQUIRED_KEYS = ["active_mode", "modes", "thresholds", "capacity", "completed", "tasks"]
REQUIRED_TASK_KEYS = ["id", "signals", "readiness", "depends_on", "needs"]
REQUIRED_THRESHOLDS = ["readiness_gate", "score_cutoff"]


def load_config(path=CONFIG_PATH):
    """Read the YAML file, complain loudly if anything is missing."""
    with open(path) as file:
        config = yaml.safe_load(file)

    for key in REQUIRED_KEYS:
        if key not in config:
            raise ValueError(f"config.yaml is missing '{key}'")

    for key in REQUIRED_THRESHOLDS:
        if key not in config["thresholds"]:
            raise ValueError(f"config.yaml thresholds are missing '{key}'")

    if config["active_mode"] not in config["modes"]:
        raise ValueError(
            f"active_mode '{config['active_mode']}' is not one of the modes: "
            f"{', '.join(config['modes'])}"
        )

    for task in config["tasks"]:
        for key in REQUIRED_TASK_KEYS:
            if key not in task:
                raise ValueError(f"task '{task.get('id', '?')}' is missing '{key}'")

        for category in task["needs"]:
            if category not in config["capacity"]:
                raise ValueError(
                    f"task '{task['id']}' needs unknown category '{category}'"
                )

        # Every signal a mode weighs must have a value on every task.
        for mode_name, weights in config["modes"].items():
            for signal in weights:
                if signal not in task["signals"]:
                    raise ValueError(
                        f"task '{task['id']}' has no value for signal '{signal}' "
                        f"(used by mode '{mode_name}')"
                    )

    return config
