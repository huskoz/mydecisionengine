# Build Priority Engine

A small, deterministic backend that decides what a game dev team should work
on next. Every task in the backlog is scored, gated, ranked, and given a share
of the team's capacity, ending in one of four verdicts — **DO NOW**,
**QUEUED**, **NOT YET**, or **LATER** — plus a plain-English reason. Same
input, same output, every time: all behaviour comes from the numbers in
`config.yaml`, never from the code.

## Install

```bash
pip install -r requirements.txt
```

(If your system Python refuses, make a virtual env first:
`python3 -m venv .venv && source .venv/bin/activate`.)

## Run the API

```bash
uvicorn app.api:app --reload
```

| Endpoint | What it does |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /tasks` | all tasks with their raw config values |
| `POST /evaluate` | one task's signals in, its priority score out |
| `GET /plan` | **the main one** — the full pipeline over the whole backlog |
| `GET /plan?mode=demo_crunch` | same plan, different weight profile |

Examples:

```bash
curl http://127.0.0.1:8000/plan
```

```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"player_impact": 4, "low_effort": 4, "unblocks_work": 2.5, "rework_risk": 1, "relevance": 5}'
```

## Run the CLI

```bash
python -m app.cli
```

Try a different mode:

```bash
python -m app.cli --mode demo_crunch
```

## Run the tests

```bash
python -m pytest
```

## How the decision works

Each task flows through five stages:

1. **evaluate** — `priority_score = Σ(signal value × weight)` using the active
   mode's weights.
2. **gate** — readiness below `readiness_gate` → **NOT YET**; score below
   `score_cutoff` → **LATER**.
3. **prioritize** — everyone left is ranked, highest score first.
4. **allocate** — walk the ranking top to bottom: if every category a task
   needs still has people free, it's **DO NOW** and the people are subtracted;
   if a needed category is empty, it's **QUEUED**.
5. **reasons** — each verdict becomes one fixed plain-English sentence built
   from the numbers.

One rule worth knowing: a dependency counts as met when the task it points to
is in the `completed` list **or was just scheduled DO NOW higher up the same
ranking** (the team is already on it). That's why `add_ui` — which depends on
`finish_art_music` — comes out QUEUED on capacity rather than
dependency-blocked: its dependency is already underway this cycle.

## How to change the model

**Everything tunable lives in `config.yaml`.** The Python never hard-codes a
weight, threshold, capacity number, or task. The API re-reads the file on
every request, so you don't even need to restart the server — edit, save,
refresh.

**Change a weight** — make quick wins matter more in the default mode:

```yaml
modes:
  long_term_quality:
    low_effort: 0.30   # was 0.15
```

**Change capacity** — the team hired another artist:

```yaml
capacity:
  art: 3   # was 2
```

**Add a task** — append it to `tasks:` with all five signals, a readiness,
its dependencies, and its needs:

```yaml
  - id: fix_boss_hitbox
    signals:
      player_impact: 4.5
      low_effort: 2
      unblocks_work: 1.5
      rework_risk: 1
      relevance: 5
    readiness: 4
    depends_on: []
    needs:
      programming: 1
      music: 0
      art: 0
      gameplay: 1
```

**Mark work as done** — add its id to `completed` and remove it from
`tasks`, and everything that depended on it unblocks:

```yaml
completed: [finish_art_music]
```

**Switch the default mode** — `active_mode: demo_crunch`.
