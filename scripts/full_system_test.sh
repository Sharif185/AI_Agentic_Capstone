#!/usr/bin/env bash
# scripts/full_system_test.sh
# Full system test for Week 8. Produces evidence in evidence/week8/.
set -euo pipefail

EVIDENCE="evidence/week8"
mkdir -p "$EVIDENCE"

echo "=== 1/5: UNIT TESTS ==="
python -m unittest discover -s tests -v 2>&1 | tee "$EVIDENCE/unit-tests.txt"

echo
echo "=== 2/5: GUARDRAIL ACCEPTANCE ==="
python scripts/guardrail_acceptance.py 2>&1 | tee "$EVIDENCE/guardrail-acceptance.txt"

echo
echo "=== 3/5: FULL EVALUATION (34 scenarios) ==="
python evaluation/run_evaluation.py 2>&1 | tee "$EVIDENCE/evaluation.txt"

echo
echo "=== 4/5: DEMO SCENARIOS ==="
python demo/run_demo.py --fast 2>&1 | tee "$EVIDENCE/demo-scenarios.txt"

echo
echo "=== 5/5: LOG INTEGRITY ==="
python scripts/check_log_integrity.py 2>&1 | tee "$EVIDENCE/log-integrity.txt"

echo
echo "ALL SUITES COMPLETE — review $EVIDENCE/"