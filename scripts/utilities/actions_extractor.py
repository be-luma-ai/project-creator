# utilities/meta_actions.py

from typing import List, Optional, Union

def extract_action_value(actions: Optional[List[dict]], action_type: str) -> float:
    """
    Extracts the numeric value of a specific action type from the actions list 
    returned by Meta Ads API (e.g., "purchase", "link_click").

    Args:
        actions (Optional[List[dict]]): List of action dictionaries, or None.
        action_type (str): The action type to extract.

    Returns:
        float: The value associated with the action type, or 0 if not found.
    """
    if not actions:
        return 0.0

    for action in actions:
        if action.get("action_type") == action_type:
            try:
                return float(action.get("value", 0))
            except (ValueError, TypeError):
                return 0.0

    return 0.0