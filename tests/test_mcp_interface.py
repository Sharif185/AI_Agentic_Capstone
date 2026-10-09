import os
import sys
 
# Make `src` importable when running `python tests/test_mcp_interface.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from src.interfaces.mcp_interface import StudentSupportInterface
 
EXPECTED_CAPABILITIES = {
    "query_support", "get_course_info", "create_ticket", "check_ticket_status"
}
 
interface = StudentSupportInterface()
results = []
created_ticket_id = None
 
 
def record(name, passed, detail=""):
    results.append(passed)
    print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f"  -> {detail}" if detail else ""))
 
 
# 1. List capabilities
try:
    listing = interface.list_capabilities()
    # ASSUMPTION: {"version": "...", "capabilities": {...}} - adjust if Noah's differs
    caps = listing.get("capabilities", {})
    record("1. List capabilities",
           bool(listing.get("version")) and set(caps) == EXPECTED_CAPABILITIES,
           f"version={listing.get('version')}, caps={sorted(caps)}")
except Exception as e:
    record("1. List capabilities", False, str(e))
 
# 2. get_course_info
try:
    r = interface.invoke("get_course_info",
                         {"course_code": "BSE4104", "info_type": "prerequisites"})
    record("2. get_course_info", r.get("success") is True, str(r)[:120])
except Exception as e:
    record("2. get_course_info", False, str(e))
 
# 3. query_support
try:
    # ASSUMPTION: input key is "query"
    r = interface.invoke("query_support",
                         {"query": "When is the registration deadline?"})
    ok = r.get("success") is True and bool(r.get("response")) and "sources" in r
    record("3. query_support", ok, str(r)[:120])
except Exception as e:
    record("3. query_support", False, str(e))
 
# 4. create_ticket
try:
    r = interface.invoke("create_ticket", {
        "student_name": "MCP Test Student",
        "issue_summary": "Automated MCP interface test ticket",
    })
    created_ticket_id = r.get("ticket_id")
    record("4. create_ticket", r.get("success") is True and bool(created_ticket_id),
           f"ticket_id={created_ticket_id}")
except Exception as e:
    record("4. create_ticket", False, str(e))
 
# 5. check_ticket_status (uses the ticket from test 4)
try:
    if not created_ticket_id:
        record("5. check_ticket_status", False, "skipped: test 4 produced no ticket_id")
    else:
        r = interface.invoke("check_ticket_status", {"ticket_id": created_ticket_id})
        record("5. check_ticket_status",
               r.get("success") is True and "status" in r,
               f"status={r.get('status')}")
except Exception as e:
    record("5. check_ticket_status", False, str(e))
 
# 6. Invalid capability
try:
    r = interface.invoke("does_not_exist", {})
    record("6. Invalid capability",
           r.get("success") is False and r.get("error_code") == "NOT_FOUND",
           f"error_code={r.get('error_code')}")
except Exception as e:
    record("6. Invalid capability", False, str(e))
 
# 7. Missing required input
try:
    r = interface.invoke("get_course_info", {})  # course_code missing
    record("7. Missing required input",
           r.get("success") is False and r.get("error_code") == "INVALID_INPUT",
           f"error_code={r.get('error_code')}")
except Exception as e:
    record("7. Missing required input", False, str(e))
 
print(f"\n{sum(results)}/{len(results)} tests passed")
sys.exit(0 if all(results) else 1)