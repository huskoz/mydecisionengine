"""Stage 2 of the pipeline: the two gates.
The readiness gate asks "can we even start this?" (readiness high enough,
dependencies done). The score cutoff asks "is it worth doing yet?".
"""


def check_ready(task, completed, gate):
    """The readiness gate.

    A task is ready when its readiness meets the gate AND every task it
    depends on is in `completed`. Returns None when the task is ready,
    otherwise a pair naming the first problem found:
    ("readiness", <value>) or ("dependency", <task id>).
    """
    if task["readiness"] < gate:
        return ("readiness", task["readiness"])
    dep = unmet_dependency(task, completed)
    if dep is not None:
        return ("dependency", dep)
    return None


def unmet_dependency(task, completed):
    """Return the first depends_on entry not in `completed`, or None."""
    for dep in task["depends_on"]:
        if dep not in completed:
            return dep
    return None


def check_cutoff(score, cutoff):
    """The score cutoff. True when the score is high enough to act on."""
    return score >= cutoff
