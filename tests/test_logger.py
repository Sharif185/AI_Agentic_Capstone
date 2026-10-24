import json
import tempfile
import unittest
from pathlib import Path

from src.observability.logger import AgentLogger


class TestAgentLogger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logger = AgentLogger(log_dir=self.tmp.name, session_id="TEST-SESSION")

    def tearDown(self):
        # Required on Windows: FileHandler holds an open file lock until
        # close() is called, which prevents TemporaryDirectory from being
        # removed. Without this, teardown raises PermissionError [WinError 32].
        self.logger.close()
        self.tmp.cleanup()

    def _read_lines(self):
        with open(self.logger.log_file, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    # ------------------------------------------------------------------ #
    # Six layers / JSON Lines shape
    # ------------------------------------------------------------------ #
    def test_all_six_layers_emit_valid_jsonl(self):
        self.logger.log_model_call("m", "p", "r", 1, 2, 3.0)
        self.logger.log_rag_retrieval("q", 1, ["doc1"], 5.0)
        self.logger.log_tool_call("get_course_info", {"code": "BSE4104"}, True, "ok", 4.0)
        self.logger.log_approval("create_support_ticket", {}, True, "auto")
        self.logger.log_agent_iteration(1, "plan", {"x": 1})
        self.logger.log_guardrail_trigger("input", "bad", "injection", decision="refuse")
        events = self._read_lines()
        self.assertEqual(len(events), 6)
        for e in events:
            self.assertIn("timestamp", e)
            self.assertIn("session_id", e)
            self.assertIn("event_type", e)
            self.assertIn("data", e)

    # ------------------------------------------------------------------ #
    # Instance isolation
    # ------------------------------------------------------------------ #
    def test_second_logger_same_session_does_not_affect_first(self):
        # Each AgentLogger owns its own handlers. Creating a second instance
        # with the same session_id must not disturb the first instance's
        # handlers, and the first instance must still write afterwards.
        before = len(self.logger._logger.handlers)
        other = AgentLogger(log_dir=self.tmp.name, session_id="TEST-SESSION")
        try:
            self.assertEqual(len(self.logger._logger.handlers), before)
            self.logger.log_error("E", "still-works")
            events = self._read_lines()
            self.assertTrue(
                any(e.get("event_type") == "error" for e in events),
                "first logger must still emit after a second instance is created",
            )
        finally:
            other.close()

    # ------------------------------------------------------------------ #
    # Privacy / redaction
    # ------------------------------------------------------------------ #
    def test_sensitive_keys_redacted(self):
        self.logger.log_tool_call("x", {"password": "hunter2", "api_key": "abc"}, True)
        line = self._read_lines()[0]
        self.assertEqual(line["data"]["arguments"]["password"], "<redacted>")
        self.assertEqual(line["data"]["arguments"]["api_key"], "<redacted>")

    # ------------------------------------------------------------------ #
    # Summary / filter / file output
    # ------------------------------------------------------------------ #
    def test_summary_and_filter(self):
        self.logger.log_error("E", "boom")
        self.logger.log_error("E", "boom2")
        self.assertEqual(self.logger.get_summary()["by_type"]["error"], 2)
        self.assertEqual(len(self.logger.get_events("error")), 2)

    def test_save_summary_writes_file(self):
        self.logger.log_error("E", "boom")
        path = self.logger.save_summary()
        self.assertTrue(Path(path).exists())
        with open(path) as f:
            payload = json.load(f)
        self.assertEqual(payload["total_events"], 1)

    # ------------------------------------------------------------------ #
    # Lifecycle (new — matches the close() contract on AgentLogger)
    # ------------------------------------------------------------------ #
    def test_close_is_idempotent(self):
        self.logger.log_error("E", "boom")
        self.logger.close()
        # A second close must not raise.
        self.logger.close()
        # Events captured before close are still readable.
        self.assertGreaterEqual(len(self.logger.get_events()), 1)

    def test_context_manager_closes_handlers(self):
        with AgentLogger(log_dir=self.tmp.name, session_id="CTX-TEST") as ctx_logger:
            ctx_logger.log_error("E", "inside-with")
            self.assertTrue(ctx_logger.log_file.exists())
        # After the with-block, the logger is closed. The file is flushable
        # and the handle is released.
        with open(ctx_logger.log_file, encoding="utf-8") as f:
            lines = [ln for ln in f if ln.strip()]
        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()