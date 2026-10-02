class ApprovalController:
    """
    Gatekeeper for any tool with requires_approval = True.

    Default behaviour: prompt the human at the terminal (CLI demo).
    For automated tests, pass a `decision_fn(tool_name, arguments) -> bool`
    so approval can be simulated without blocking on stdin — this is the
    ONLY supported way to bypass the interactive prompt, and it still goes
    through this same approve() method, so ToolExecutor's enforcement
    doesn't change either way.
    """

    def __init__(self, decision_fn=None):
        self._decision_fn = decision_fn

    def approve(self, tool_name: str, arguments: dict) -> bool:
        """Return True if the action is approved, False if denied."""
        if self._decision_fn is not None:
            return bool(self._decision_fn(tool_name, arguments))

        print("\n" + "=" * 50)
        print("HUMAN APPROVAL REQUIRED")
        print("=" * 50)
        print(f"Tool: {tool_name}")
        print("Arguments:")
        for key, value in arguments.items():
            print(f"  {key}: {value}")
        print("=" * 50)

        answer = input("Approve this action? [y/n]: ").strip().lower()
        return answer in ("y", "yes")
