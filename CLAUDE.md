# NFL Game Predictor

## Critical Rules
- Never modify features/build.py or features/definitions.py
  during the autoresearch experiment loop — only models/train.py
- All rolling features require .shift(1) — no exceptions
- Leakage tests in features/tests/test_leakage.py must pass
  before any model training
- Temporal split is hardcoded: train 2005-2022, val 2023,
  holdout 2024 — never shuffle

## Planning Files
Read .planning/REQUIREMENTS.md and .planning/ROADMAP.md
at the start of each session.

## Experiment Loop
- experiments.jsonl is append-only — never delete entries
- program.md lives at models/program.md
- 5 experiment maximum per session before stopping to review

## Data Rules
- Team abbreviations must use the constants mapping in data/sources.py
  (OAK→LV, SD→LAC, STL→LA, WSH→WAS) — never inline string replacements
- Never use result, home_score, or away_score as model features
