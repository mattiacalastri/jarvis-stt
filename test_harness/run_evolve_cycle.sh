#!/usr/bin/env bash
# Jarvis Voice — ciclo evolutivo completo
# 1. Esegue tutti gli scenari
# 2. Analizza failures ricorrenti (3x → cicatrice draft locale)
# 3. Notifica via voice_briefing se passed/total cambia
#
# Pensato per LaunchAgent notturno (es. 03:00) o manuale.
set -euo pipefail

ROOT="$HOME/projects/jarvis-stt/test_harness"
PY=/opt/homebrew/bin/python3.10

cd "$ROOT"

# Snapshot precedente (per delta detection)
PREV_PASSED=0
LATEST_RUN=$(ls -t runs/*.json 2>/dev/null | head -1)
if [ -n "$LATEST_RUN" ]; then
    PREV_PASSED=$($PY -c "import json; print(json.load(open('$LATEST_RUN')).get('passed',0))")
fi

# Run + evolve
"$PY" harness.py

# Confronta con run precedente
NEW_RUN=$(ls -t runs/*.json | head -1)
NEW_PASSED=$($PY -c "import json; print(json.load(open('$NEW_RUN')).get('passed',0))")
NEW_TOTAL=$($PY -c "import json; print(json.load(open('$NEW_RUN')).get('total',0))")

# Se è cambiato qualcosa, opzionalmente notifica (non hard-coded — solo se voice_briefing è disponibile)
DELTA=$((NEW_PASSED - PREV_PASSED))
if [ "$DELTA" -lt 0 ] && [ -x "$HOME/scripts/voice_briefing.py" ]; then
    "$PY" "$HOME/scripts/voice_briefing.py" \
        "Signore, regressione nei test voice. Passati ${NEW_PASSED} su ${NEW_TOTAL}, perso ${DELTA}." \
        --no-send 2>/dev/null || true
fi

echo "[evolve-cycle] passed=$NEW_PASSED/$NEW_TOTAL delta=$DELTA"
