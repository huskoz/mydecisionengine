"""Stage 1 of the pipeline: evaluate.
In: one task and the active mode's weights. Out: the task's priority
score — each signal value times its weight, all added up.
"""


def score_task(task, weights):
    """priority_score = sum of (signal value x that signal's weight)."""
    score = 0.0
    for signal_name, weight in weights.items():
        score += task["signals"][signal_name] * weight
    return score
