"""The HTTP layer: a small FastAPI app exposing the pipeline.
Reads config.yaml fresh on every request, so YAML edits show up on the
next request without restarting the server.
"""

from fastapi import FastAPI, HTTPException

from app.config_loader import load_config
from app.evaluate import score_task
from app.pipeline import build_plan

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
