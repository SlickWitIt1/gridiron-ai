#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -d src/ui || ! -f src/desktop_app.py ]]; then
  echo "ERROR: Run this script from the FantasyDraftSimulator project root."
  exit 1
fi

ROOT_PY=(
  ai.py availability_engine.py config.py decision_engine.py desktop_app.py
  draft_assistant.py draft_board.py draft_engine.py draft_pick.py draft_pulse.py
  draft_session_store.py draft_slot_analyzer.py draft_state.py league.py
  lineup_optimizer.py live_draft.py loader.py market.py monte_carlo.py player.py
  player_scorer.py preferences.py projection.py projection_loader.py
  recommendation.py recommendation_engine.py recommendation_score.py
  roster_evaluator.py simulation.py simulator.py team.py wait_analyzer.py
)

for file in "${ROOT_PY[@]}"; do
  if [[ -e "$file" ]]; then
    git rm -f -- "$file"
  fi
done

if [[ -d ui ]]; then
  git rm -r -f -- ui
fi

rm -rf __pycache__ src/__pycache__ src/ui/__pycache__ __MACOSX
find . -name .DS_Store -delete

echo
echo "Duplicate root code removed."
echo "Next run: python3 tests/smoke_test.py"
echo "Then inspect: git status"
