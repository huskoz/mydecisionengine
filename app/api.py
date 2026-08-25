"""The HTTP layer: a small FastAPI app exposing the pipeline.
Reads config.yaml fresh on every request, so YAML edits show up on the
next request without restarting the server.
"""
import yaml
import os
from fastapi import FastAPI, HTTPException
from starlette.staticfiles import StaticFiles

from app.config_loader import load_config, CONFIG_PATH
from app.evaluate import score_task
from app.pipeline import build_plan
from app.schemas import Task

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
STATIC_DIRECTORY = os.path.join(CURRENT_DIRECTORY, "static")


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

# to do, i will add a new function
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

@app.post("/tasks")

def add_task(new_task: Task):
    """Simple function for adding a new task."""
    # This function will:
    # load the current configuration - DONE
    # verify is the task does not already exist to prevent duplicates - DONE
    # append the new task and save the file

    config = load_config()
    for i in config["tasks"]:
        if new_task.id == i["id"]:
            raise HTTPException(status_code=400, detail=f"task with id {new_task.id} already exists")

    task_dict = new_task.model_dump()
    config['tasks'].append(task_dict)

    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    return {"status": "success", "message": f"Task '{new_task.id}' added successfully"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    """Removes a task from the config.yaml file."""
    config = load_config()

    initial_count = len(config["tasks"])

    config["tasks"] = [task for task in config["tasks"] if task["id"] != task_id]

    if len(config["tasks"]) == initial_count:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    with open(CONFIG_PATH, "w") as file:
        yaml.safe_dump(config, file, sort_keys=False)

    return {"status": "success", "message": f"Task '{task_id}' DELETED SUCCESSFULLY."}


@app.put("/tasks/{task_id}")
def modify_task(task_id: str, updated_task: Task):
    """Simple function for modifying a task."""
    config = load_config()

    for index, task in enumerate(config["tasks"]):
        if task["id"] == task_id:
            if updated_task.id != task_id:
                raise HTTPException(status_code=400, detail="Cannot change the task ID.")

            config["tasks"][index] = updated_task.model_dump()

            with open(CONFIG_PATH, "w") as file:
                yaml.safe_dump(config, file, sort_keys=False)

            return {"status": "success", "message": f"Task '{task_id}' UPDATED SUCCESSFULLY."}

    raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

app.mount('/', StaticFiles(directory=STATIC_DIRECTORY, html=True), name='static')