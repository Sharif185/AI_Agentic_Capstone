"""Validate all log files under logs/.

Checks:
  1. Every line is valid JSON.
  2. Every event has the required fields (timestamp, session_id, event_type, data).
  3. Every required event type appears at least once somewhere in logs/.

Exits 0 if all checks pass, 1 otherwise.
"""
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src"
for _p in (_REPO_ROOT, _SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

LOG_DIR = _REPO_ROOT / "logs"
REQUIRED_LAYERS = {
    "model_call", "rag_retrieval", "tool_call",
    "approval", "agent_iteration", "guardrail_trigger",
}
REQUIRED_FIELDS = {"timestamp", "session_id", "event_type", "data"}


def main():
    if not LOG_DIR.exists():
        print(f"FAIL: no logs directory at {LOG_DIR}")
        return 1

    files = sorted(LOG_DIR.rglob("*.log"))
    if not files:
        print(f"FAIL: no .log files under {LOG_DIR}")
        return 1

    print(f"Scanning {len(files)} log file(s) under {LOG_DIR}\n")

    total_lines = 0
    invalid = 0
    missing_fields = 0
    seen_layers = set()

    for f in files:
        file_ok = True
        with open(f, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                total_lines += 1
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"  [FAIL] {f.name}:{lineno} invalid JSON: {e}")
                    invalid += 1
                    file_ok = False
                    continue

                missing = REQUIRED_FIELDS - event.keys()
                if missing:
                    print(f"  [FAIL] {f.name}:{lineno} missing fields: {sorted(missing)}")
                    missing_fields += 1
                    file_ok = False
                    continue

                seen_layers.add(event.get("event_type"))

        if file_ok:
            print(f"  [OK]   {f.relative_to(_REPO_ROOT)}")

    print()
    print(f"Total events scanned: {total_lines}")
    print(f"Invalid JSON lines:   {invalid}")
    print(f"Missing required fields: {missing_fields}")
    print()
    print("Layers seen:")
    for layer in sorted(seen_layers):
        marker = "[required]" if layer in REQUIRED_LAYERS else "[bonus]"
        print(f"  + {layer}  {marker}")

    missing_layers = REQUIRED_LAYERS - seen_layers
    print()
    if missing_layers:
        print(f"Missing required layers: {sorted(missing_layers)}")
    else:
        print("All 6 required layers present.")

    ok = invalid == 0 and missing_fields == 0 and not missing_layers
    print()
    print("RESULT:", "SUCCESS" if ok else "FAILURE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())