"""Ties the five stages together: evaluate -> gate -> prioritize ->
allocate -> reasons. In: the loaded config and an optional mode name.
Out: the full plan as one plain dict, ready to serve as JSON.
"""

from app import allocate, evaluate, gates, prioritize, reasons


def build_plan(config, mode_name=None):
    """Run the whole pipeline over the backlog and return the plan."""
    if mode_name is None:
        mode_name = config["active_mode"]
    if mode_name not in config["modes"]:
        raise ValueError(
            f"unknown mode '{mode_name}' — available: {', '.join(config['modes'])}"
        )
    weights = config["modes"][mode_name]
    gate = config["thresholds"]["readiness_gate"]
    cutoff = config["thresholds"]["score_cutoff"]

    # Stage 1 — evaluate: one priority score per task.
    scores = {}
    for task in config["tasks"]:
        scores[task["id"]] = evaluate.score_task(task, weights)

    # Stage 2 — gate. A readiness failure is final here (NOT YET), and so
    # is a score below the cutoff (LATER). A dependency failure is NOT
    # final yet: a dependency also counts as met once that task gets
    # scheduled DO NOW, which is only known during allocation. So
    # dependency-blocked tasks stay in as candidates for now.
    candidates = []
    early_verdicts = {}  # task id -> (verdict, context for the reason)
    for task in config["tasks"]:
        problem = gates.check_ready(task, config["completed"], gate)
        if problem is not None and problem[0] == "readiness":
            early_verdicts[task["id"]] = (
                "NOT YET", {"readiness": task["readiness"], "gate": gate})
        elif not gates.check_cutoff(scores[task["id"]], cutoff):
            early_verdicts[task["id"]] = ("LATER", {"cutoff": cutoff})
        else:
            candidates.append(task)

    # Stage 3 — prioritize: highest score first.
    ranked = prioritize.rank(candidates, scores)

    # Stage 4 — allocate: hand out capacity down the ranking.
    allocations, remaining = allocate.allocate(
        ranked, config["capacity"], config["completed"])

    # Stage 5 — reasons: one plain-English sentence per task.
    plan_tasks = []
    for item in allocations:
        task = item["task"]
        context = dict(item["context"])
        context["score"] = scores[task["id"]]
        context["rank"] = item["rank"]
        plan_tasks.append(
            plan_entry(task, scores[task["id"]], item["rank"], item["verdict"], context))
    for task in config["tasks"]:
        if task["id"] in early_verdicts:
            verdict, context = early_verdicts[task["id"]]
            context = dict(context)
            context["score"] = scores[task["id"]]
            plan_tasks.append(
                plan_entry(task, scores[task["id"]], None, verdict, context))

    # Show the list highest score first (equal scores keep their order).
    plan_tasks.sort(key=lambda entry: entry["priority_score"], reverse=True)

    return {
        "mode": mode_name,
        "tasks": plan_tasks,
        "remaining_capacity": remaining,
    }


def plan_entry(task, score, rank, verdict, context):
    """One task's row in the final plan."""
    return {
        "id": task["id"],
        "priority_score": round(score, 3),
        "rank": rank,
        "verdict": verdict,
        "reason": reasons.reason_for(task, verdict, context),
    }
