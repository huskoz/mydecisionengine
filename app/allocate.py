"""Stage 4 of the pipeline: allocate.
In: the ranked tasks, capacity per category, and the completed task ids.
Out: a verdict (plus details for the reason) per task, and the capacity
left over per category.
"""

from app import gates


def allocate(ranked, capacity, completed):
    """Walk the ranking top to bottom, handing out capacity."""
    remaining = dict(capacity)
    # Work that is done, or scheduled DO NOW earlier in this walk.
    # A dependency on anything in this list counts as met — the work is
    # either finished or the team is already on it this cycle.
    done_or_underway = list(completed)
    results = []

    for rank, task in enumerate(ranked, start=1):
        dep = gates.unmet_dependency(task, done_or_underway)
        if dep is not None:
            results.append({"task": task, "rank": rank, "verdict": "NOT YET",
                            "context": {"unmet_dep": dep}})
            continue

        # Which categories does this task actually use, and which of
        # those don't have enough people left?
        needed = [cat for cat, amount in task["needs"].items() if amount > 0]
        full = [cat for cat in needed if task["needs"][cat] > remaining[cat]]

        if full:
            results.append({"task": task, "rank": rank, "verdict": "QUEUED",
                            "context": {"full_categories": full}})
        else:
            for cat in needed:
                remaining[cat] -= task["needs"][cat]
            done_or_underway.append(task["id"])
            results.append({"task": task, "rank": rank, "verdict": "DO NOW",
                            "context": {"needed_categories": needed}})

    return results, remaining
