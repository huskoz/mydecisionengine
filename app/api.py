"""The HTTP layer: a small FastAPI app exposing the pipeline.
Reads config.yaml fresh on every request, so YAML edits show up on the
next request without restarting the server.
"""
import yaml
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from app.config_loader import load_config, CONFIG_PATH
from app.evaluate import score_task
from app.pipeline import build_plan
from app.schemas import Task
import os
from fastapi.staticfiles import StaticFiles

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "static")

app = FastAPI(title="Build Priority Engine")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def all_tasks():
    """Every task exactly as written in config.yaml."""
    return load_config()["tasks"]


@app.post("/evaluate")
def evaluate_one(signals: dict[str, float], mode: str | None = None):
    """The evaluate stage alone: one task's signals in, its score out."""
    config = load_config()
    mode = pick_mode(config, mode)
    weights = config["modes"][mode]

    missing = [name for name in weights if name not in signals]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"missing signals: {', '.join(missing)}")

    score = score_task({"signals": signals}, weights)
    return {"mode": mode, "priority_score": round(score, 3)}


@app.get("/plan")
def plan(mode: str | None = None):
    """The main endpoint: run the whole pipeline on the backlog."""
    config = load_config()
    mode = pick_mode(config, mode)
    return build_plan(config, mode)


def pick_mode(config, mode):
    """Fall back to the config's active mode; reject unknown mode names."""
    if mode is None:
        return config["active_mode"]
    if mode not in config["modes"]:
        raise HTTPException(status_code=400,
                            detail=f"unknown mode '{mode}'; available: {', '.join(config['modes'])}")
    return mode

#session 2
@app.post("/tasks")
def add_task(new_task: Task):
    """Adds a new task to the config.yaml file."""
    config = load_config()

    # 1. Prevent duplicate task IDs
    for task in config["tasks"]:
        if task["id"] == new_task.id:
            raise HTTPException(
                status_code=400,
                detail=f"Task with id '{new_task.id}' already exists."
            )

    # 2. Append the new task (convert Pydantic object to a standard dictionary)
    # Using model_dump() for Pydantic v2 (or dict() if he is on older Pydantic v1)
    task_dict = new_task.model_dump()
    config["tasks"].append(task_dict)

    # 3. Write the updated config back to the YAML file
    with open(CONFIG_PATH, "w") as file:
        yaml.safe_dump(config, file, sort_keys=False)

    return {"status": "success", "message": f"Task '{new_task.id}' CREATED SUCCESSFULLY"}

# session 3
@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    """Removes a task from the config.yaml file."""
    config = load_config()

    # Check how many tasks we started with
    initial_count = len(config["tasks"])

    # Keep only the tasks that do NOT match the task_id
    config["tasks"] = [task for task in config["tasks"] if task["id"] != task_id]

    # If the count hasn't changed, the task wasn't there
    if len(config["tasks"]) == initial_count:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    # Save the updated list back to the file
    with open(CONFIG_PATH, "w") as file:
        yaml.safe_dump(config, file, sort_keys=False)

    return {"status": "success", "message": f"Task '{task_id}' DELETED SUCCESSFULLY."}


@app.put("/tasks/{task_id}")
def update_task(task_id: str, updated_task: Task):
    """Completely replaces an existing task."""
    config = load_config()

    for index, task in enumerate(config["tasks"]):
        if task["id"] == task_id:
            # Prevent the user from accidentally changing the ID in the payload
            if updated_task.id != task_id:
                raise HTTPException(status_code=400, detail="Cannot change the task ID.")

            # Replace the old dictionary with the new one
            config["tasks"][index] = updated_task.model_dump()

            with open(CONFIG_PATH, "w") as file:
                yaml.safe_dump(config, file, sort_keys=False)

            return {"status": "success", "message": f"Task '{task_id}' UPDATED SUCCESSFULLY."}

    raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found - PUT ENDPOINT.")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


