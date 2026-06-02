import sqlite3
import re
from database import get_connection

# Keywords that should never be allowed (safety layer)
BLOCKED_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "REPLACE"]

def check_sql_safety(sql: str) -> tuple[bool, str]:
    """
    Returns (is_safe, reason).
    Blocks any destructive SQL operations.
    """
    sql_upper = sql.upper()
    for keyword in BLOCKED_KEYWORDS:
        # Use word boundary check to avoid false positives
        if re.search(rf"\b{keyword}\b", sql_upper):
            return False, f"Blocked keyword detected: {keyword}. Only SELECT queries are allowed."
    return True, "OK"

def validate_sql_syntax(sql: str) -> tuple[bool, str]:
    """
    Validates SQL by using SQLite's EXPLAIN to dry-run without executing.
    Returns (is_valid, error_message).
    """
    conn = get_connection()
    try:
        conn.execute(f"EXPLAIN {sql}")
        conn.close()
        return True, "Valid"
    except sqlite3.Error as e:
        conn.close()
        return False, str(e)

def execute_sql(sql: str) -> tuple[bool, list, list, str]:
    """
    Executes the SQL and returns (success, columns, rows, error).
    Limits results to 50 rows max.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(50)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        return True, columns, rows, ""
    except sqlite3.Error as e:
        conn.close()
        return False, [], [], str(e)

def format_results_as_text(columns: list, rows: list) -> str:
    """Format query results as readable text for LLM interpretation."""
    if not rows:
        return "Query returned no results."
    
    lines = [" | ".join(columns)]
    lines.append("-" * len(lines[0]))
    for row in rows[:10]:  # show max 10 in text summary
        lines.append(" | ".join(str(v) for v in row))
    
    if len(rows) > 10:
        lines.append(f"... and {len(rows) - 10} more rows")
    
    return "\n".join(lines)
