import json
import sys
import os
 
def view_trace(trace_file):
    """Pretty-print a trace file."""
    with open(trace_file) as f:
        trace = json.load(f)
    
    print("=" * 70)
    print(f"TRACE: {trace['trace_id']}")
    print("=" * 70)
    print(f"Goal: {trace['goal']}")
    print(f"Started: {trace['started_at']}")
    print(f"Completed: {trace['completed_at']}")
    print(f"Stop reason: {trace['stop_reason']}")
    print()
    
    print(f"ITERATIONS ({len(trace['iterations'])})")
    print("-" * 70)
    for it in trace["iterations"]:
        print(f"\n[Iteration {it.get('iteration', '?')}] {it['action'].upper()}")
        data = it.get("data", {})
        print(f"  {json.dumps(data, indent=2)[:500]}")
    
    print(f"\nTOOL CALLS ({len(trace['tool_calls'])})")
    print("-" * 70)
    for tc in trace["tool_calls"]:
        print(f"\n  Tool: {tc['tool']}")
        print(f"  Args: {tc['arguments']}")
        print(f"  Result: {str(tc['result'])[:200]}")
    
    print(f"\nRAG CALLS ({len(trace['rag_calls'])})")
    print("-" * 70)
    for rc in trace["rag_calls"]:
        print(f"\n  Query: {rc['query']}")
        print(f"  Results: {rc['num_results']}")
        print(f"  Sources: {rc['sources']}")
    
    print(f"\nFINAL RESPONSE")
    print("-" * 70)
    print(trace["final_response"])
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_trace.py <trace_file>")
        sys.exit(1)
    view_trace(sys.argv[1])
