"""The terminal view: prints the same plan as GET /plan, as an aligned
table. Run `python -m app.cli`, or `python -m app.cli --mode demo_crunch`
to try another weight profile.
"""

import argparse

from app.config_loader import load_config
from app.pipeline import build_plan


def main():
    parser = argparse.ArgumentParser(description="Print the build plan as a table.")
    parser.add_argument("--mode",
                        help="weight profile to use (default: active_mode from config.yaml)")
    args = parser.parse_args()

    config = load_config()
    try:
        plan = build_plan(config, args.mode)
    except ValueError as error:
        raise SystemExit(f"error: {error}")

    print(f"Build Priority Engine — mode: {plan['mode']}")
    print()

    headers = ["RANK", "TASK", "SCORE", "VERDICT", "REASON"]
    rows = []
    for task in plan["tasks"]:
        rank = "-" if task["rank"] is None else str(task["rank"])
        rows.append([rank, task["id"], str(task["priority_score"]),
                     task["verdict"], task["reason"]])

    # Make every column as wide as its widest cell, then print aligned.
    widths = []
    for column in range(len(headers)):
        cells = [headers[column]] + [row[column] for row in rows]
        widths.append(max(len(cell) for cell in cells))

    def print_row(cells):
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)))

    print_row(headers)
    print_row(["-" * width for width in widths])
    for row in rows:
        print_row(row)

    print()
    leftovers = plan["remaining_capacity"]
    print("Remaining capacity: "
          + "  ".join(f"{category}={amount}" for category, amount in leftovers.items()))


if __name__ == "__main__":
    main()
