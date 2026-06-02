from typing import List, Dict

class ConversationMemory:
    """
    Simple in-memory conversation history.
    Keeps last N turns for LLM context.
    """
    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.history: List[Dict] = []

    def add_turn(self, user_msg: str, assistant_msg: str, sql: str = ""):
        self.history.append({
            "user": user_msg,
            "assistant": assistant_msg,
            "sql": sql
        })
        # Keep only last N turns
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def get_context_string(self) -> str:
        if not self.history:
            return "No previous conversation."
        
        lines = []
        for turn in self.history:
            lines.append(f"User: {turn['user']}")
            if turn['sql']:
                lines.append(f"SQL used: {turn['sql']}")
            lines.append(f"Assistant: {turn['assistant'][:200]}...")  # truncate long answers
        
        return "\n".join(lines)

    def clear(self):
        self.history = []
