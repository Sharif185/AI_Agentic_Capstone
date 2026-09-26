class ApprovalController:
    """Manages human approval for high-impact tools."""
    
    def __init__(self, auto_approve=False, interactive=True):
        self.auto_approve = auto_approve
        self.interactive = interactive
        self.approval_log = []
    
    def request_approval(self, tool_name, arguments):
        """
        Request human approval for a tool call.
        
        Returns:
            bool: True if approved, False otherwise
        """
        # Auto-approve mode (for testing)
        if self.auto_approve:
            self.approval_log.append({
                "tool": tool_name,
                "arguments": arguments,
                "approved": True,
                "mode": "auto"
            })
            return True
        
        # Interactive mode
        if self.interactive:
            print("\n" + "=" * 60)
            print("HUMAN APPROVAL REQUIRED")
            print("=" * 60)
            print(f"Tool: {tool_name}")
            print(f"Arguments: {arguments}")
            print("-" * 60)
            response = input("Approve this action? (y/n): ").strip().lower()
            approved = response == "y"
            
            self.approval_log.append({
                "tool": tool_name,
                "arguments": arguments,
                "approved": approved,
                "mode": "interactive"
            })
            return approved
        
        # Non-interactive: default deny
        self.approval_log.append({
            "tool": tool_name,
            "arguments": arguments,
            "approved": False,
            "mode": "denied_non_interactive"
        })
        return False
    
    def get_log(self):
        """Return the approval log."""
        return self.approval_log