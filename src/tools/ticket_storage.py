import json
import os
from typing import Any, Dict, List


class TicketStorage:
    """Handles JSON-based persistence for support tickets."""

    def __init__(self, storage_path: str = "data/tickets.json"):
        self.storage_path = storage_path

    def save_ticket(self, ticket_data: Dict[str, Any]) -> None:
        """Appends a new ticket record to the storage file."""
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        tickets = self.get_all_tickets()
        tickets.append(ticket_data)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2)

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Retrieves all stored tickets from disk."""
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []