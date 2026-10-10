"""
MCP Interface Tests — Week 6

Tests the StudentSupportInterface exposing 4 capabilities with proper
input validation, error codes, and consistent output shapes.

Author: Louis (AI Engineering Lead)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from interfaces.mcp_interface import StudentSupportInterface


def run_tests():
    """Run all MCP interface tests."""
    print("=" * 60)
    print("Week 6 MCP Interface Tests")
    print("=" * 60)
    print()

    interface = StudentSupportInterface()
    results = []

    # ------------------------------------------------------------------
    # TEST 1: List Capabilities
    # ------------------------------------------------------------------
    print("TEST 1: List capabilities")
    try:
        caps = interface.list_capabilities()
        assert "version" in caps, "Missing 'version' in list_capabilities"
        assert caps["version"] == "1.0", f"Wrong version: {caps['version']}"
        assert "capabilities" in caps, "Missing 'capabilities' key"

        cap_names = list(caps["capabilities"].keys())
        expected = ["query_support", "get_course_info", "create_ticket", "check_ticket_status"]
        assert set(cap_names) == set(expected), f"Capability list mismatch: {cap_names}"

        print(f"✅ PASS: Version {caps['version']}, {len(cap_names)} capabilities listed")
        results.append({"test": "list_capabilities", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "list_capabilities", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 2: get_course_info — Success
    # ------------------------------------------------------------------
    print("TEST 2: get_course_info — valid course")
    try:
        result = interface.invoke("get_course_info", {"course_code": "BSE4104", "info_type": "all"})
        assert result.get("success") is True, f"Expected success=True, got {result}"
        assert "course_code" in result, "Missing course_code in response"
        assert result["course_code"] == "BSE4104", f"Wrong course_code: {result['course_code']}"
        print(f"✅ PASS: Course BSE4104 retrieved successfully")
        results.append({"test": "get_course_info_success", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "get_course_info_success", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 3: get_course_info — Not Found
    # ------------------------------------------------------------------
    print("TEST 3: get_course_info — unknown course")
    try:
        result = interface.invoke("get_course_info", {"course_code": "XYZ999"})
        assert result.get("success") is False, "Expected success=False for unknown course"
        assert result.get("error_code") == "NOT_FOUND", f"Wrong error_code: {result.get('error_code')}"
        print(f"✅ PASS: Unknown course returns NOT_FOUND")
        results.append({"test": "get_course_info_not_found", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "get_course_info_not_found", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 4: check_ticket_status — Not Found (no ticket created yet)
    # ------------------------------------------------------------------
    print("TEST 4: check_ticket_status — ticket not found")
    try:
        result = interface.invoke("check_ticket_status", {"ticket_id": "TICKET-9999"})
        assert result.get("success") is False, "Expected success=False for non-existent ticket"
        assert result.get("error_code") == "NOT_FOUND", f"Wrong error_code: {result.get('error_code')}"
        print(f"✅ PASS: Non-existent ticket returns NOT_FOUND")
        results.append({"test": "check_ticket_status_not_found", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "check_ticket_status_not_found", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 5: Invalid Capability
    # ------------------------------------------------------------------
    print("TEST 5: invoke — invalid capability")
    try:
        result = interface.invoke("nonexistent_capability", {})
        assert result.get("success") is False, "Expected success=False for invalid capability"
        assert result.get("error_code") == "NOT_FOUND", f"Wrong error_code: {result.get('error_code')}"
        assert "Unknown capability" in result.get("error", ""), "Error message should mention unknown capability"
        print(f"✅ PASS: Invalid capability returns NOT_FOUND")
        results.append({"test": "invalid_capability", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "invalid_capability", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 6: get_course_info — Missing Required Input
    # ------------------------------------------------------------------
    print("TEST 6: get_course_info — missing course_code")
    try:
        result = interface.invoke("get_course_info", {})  # missing course_code
        assert result.get("success") is False, "Expected success=False for missing input"
        assert result.get("error_code") == "INVALID_INPUT", f"Wrong error_code: {result.get('error_code')}"
        print(f"✅ PASS: Missing required input returns INVALID_INPUT")
        results.append({"test": "missing_required_input", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "missing_required_input", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # TEST 7: Output Consistency — All Responses Have 'success'
    # ------------------------------------------------------------------
    print("TEST 7: Output consistency — all responses have 'success' key")
    try:
        r1 = interface.invoke("get_course_info", {"course_code": "BSE4104"})
        r2 = interface.invoke("check_ticket_status", {"ticket_id": "TICKET-9999"})
        r3 = interface.invoke("invalid_cap", {})

        assert "success" in r1, "Response 1 missing 'success'"
        assert "success" in r2, "Response 2 missing 'success'"
        assert "success" in r3, "Response 3 missing 'success'"

        # Failure responses must have error and error_code
        assert "error" in r2 and "error_code" in r2, "Failure response missing error/error_code"
        assert "error" in r3 and "error_code" in r3, "Failure response missing error/error_code"

        print(f"✅ PASS: All responses consistent (success + error/error_code structure)")
        results.append({"test": "output_consistency", "status": "PASS"})
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        results.append({"test": "output_consistency", "status": "FAIL", "error": str(e)})
    print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    print(f"Total: {len(results)} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()

    return passed == len(results)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
