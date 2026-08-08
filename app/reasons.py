"""Stage 5 of the pipeline: reasons.
Turns each verdict plus a few numbers into one fixed plain-English
sentence. Same numbers in, same sentence out — never random, never vague.
"""


def reason_for(task, verdict, context):
    """Build the reason sentence for one task's verdict.
    `context` is a small dict holding whichever numbers the template
    needs (score, rank, categories, unmet dependency, readiness...)."""
    if verdict == "DO NOW":
        categories = ", ".join(context["needed_categories"])
        return (f"DO NOW — ranked #{context['rank']}, score {pretty_score(context['score'])}, "
                f"ready, capacity available in {categories}.")

    if verdict == "QUEUED":
        categories = ", ".join(context["full_categories"])
        return (f"QUEUED — ready and high priority (score {pretty_score(context['score'])}), "
                f"but {categories} capacity is full this cycle.")

    if verdict == "NOT YET":
        if "unmet_dep" in context:
            return f"NOT YET — blocked: {context['unmet_dep']} not complete"
        return f"NOT YET — readiness {context['readiness']} below gate {context['gate']}."

    if verdict == "LATER":
        return (f"LATER — score {pretty_score(context['score'])} is below the cutoff "
                f"{context['cutoff']}; not worth doing yet.")

    raise ValueError(f"unknown verdict: {verdict}")


def pretty_score(score):
    """Round to 3 decimals and drop trailing zeros, e.g. 4.35 or 3.975."""
    return f"{round(score, 3):g}"
