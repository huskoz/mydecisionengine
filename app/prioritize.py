"""Stage 3 of the pipeline: prioritize.
In: the tasks that passed both gates, plus everyone's scores.
Out: the same tasks ordered highest score first.
"""


def rank(tasks, scores):
    """Sort by score, best first. Tied scores keep their config.yaml
    order because Python's sort is stable."""
    return sorted(tasks, key=lambda task: scores[task["id"]], reverse=True)
