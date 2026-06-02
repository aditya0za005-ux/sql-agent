from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from vector_store import retrieve_relevant_schema
from tools import check_sql_safety, validate_sql_syntax, execute_sql, format_results_as_text
from database import get_full_schema

import os

# ─────────────────────────────────────────────
# State Definition
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    user_question: str
    conversation_context: str
    relevant_schema: str
    sql_query: str
    sql_valid: bool
    sql_error: str
    retry_count: int
    columns: list
    rows: list
    final_answer: str
    error_message: str

# ─────────────────────────────────────────────
# LLM Setup
# ─────────────────────────────────────────────

def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

# ─────────────────────────────────────────────
# Node Functions
# ─────────────────────────────────────────────

def schema_retrieval_node(state: AgentState) -> AgentState:
    """RAG: Retrieve only relevant table schemas for this question."""
    relevant = retrieve_relevant_schema(state["user_question"], k=3)
    return {**state, "relevant_schema": relevant}


def sql_generation_node(state: AgentState) -> AgentState:
    """Generate SQL using LLM with relevant schema + conversation context."""
    llm = get_llm()

    system_prompt = """You are an expert SQL assistant for a SQLite database.
Your job is to convert natural language questions into correct SQLite SQL queries.

Rules:
- Output ONLY the raw SQL query, nothing else. No explanation, no markdown, no backticks.
- Use only SELECT statements.
- Always use proper JOINs when combining tables.
- Use table aliases for clarity.
- For date comparisons use SQLite date functions.
- If the question is about "top N", use ORDER BY + LIMIT.
- Use lowercase column and table names exactly as shown in the schema.
"""

    user_prompt = f"""Database Schema (relevant tables):
{state['relevant_schema']}

Previous conversation:
{state['conversation_context']}

Current question: {state['user_question']}

Write the SQL query:"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    sql = response.content.strip().strip("```sql").strip("```").strip()
    return {**state, "sql_query": sql, "sql_error": "", "sql_valid": False}


def validation_node(state: AgentState) -> AgentState:
    """Check SQL safety + syntax validity."""
    sql = state["sql_query"]

    # Safety check first
    is_safe, reason = check_sql_safety(sql)
    if not is_safe:
        return {**state, "sql_valid": False, "sql_error": reason}

    # Syntax validation
    is_valid, error = validate_sql_syntax(sql)
    return {**state, "sql_valid": is_valid, "sql_error": error if not is_valid else ""}


def execution_node(state: AgentState) -> AgentState:
    """Execute validated SQL query."""
    success, columns, rows, error = execute_sql(state["sql_query"])
    if not success:
        return {**state, "sql_valid": False, "sql_error": error, "columns": [], "rows": []}
    return {**state, "columns": columns, "rows": rows}


def repair_node(state: AgentState) -> AgentState:
    """
    Error recovery: ask LLM to fix the broken SQL.
    Uses full schema here for maximum context.
    """
    llm = get_llm()
    full_schema = get_full_schema()

    prompt = f"""The following SQL query failed with this error:

SQL: {state['sql_query']}
Error: {state['sql_error']}

Full database schema:
{full_schema}

Fix the SQL query. Output ONLY the corrected SQL, nothing else."""

    response = llm.invoke([HumanMessage(content=prompt)])
    fixed_sql = response.content.strip().strip("```sql").strip("```").strip()

    return {
        **state,
        "sql_query": fixed_sql,
        "sql_error": "",
        "sql_valid": False,
        "retry_count": state.get("retry_count", 0) + 1
    }


def answer_generation_node(state: AgentState) -> AgentState:
    """Convert raw SQL results into a human-readable answer with explanation."""
    llm = get_llm()

    results_text = format_results_as_text(state["columns"], state["rows"])

    prompt = f"""The user asked: "{state['user_question']}"

I ran this SQL query:
{state['sql_query']}

Results:
{results_text}

Now give a clear, helpful answer to the user's question based on these results.
Also briefly explain which tables were used and why.
Keep it concise but complete."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "final_answer": response.content}


def error_answer_node(state: AgentState) -> AgentState:
    """Generate a graceful error message if all retries fail."""
    answer = f"I wasn't able to generate a valid SQL query for your question after multiple attempts.\n\nLast error: {state['sql_error']}\n\nTry rephrasing your question or being more specific about which data you need."
    return {**state, "final_answer": answer}


# ─────────────────────────────────────────────
# Routing Logic
# ─────────────────────────────────────────────

def should_retry_or_fail(state: AgentState) -> str:
    """After validation/execution failure, retry up to 2 times."""
    if state.get("retry_count", 0) >= 2:
        return "error_answer"
    return "repair"


def after_repair(state: AgentState) -> str:
    return "validate"


# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_schema", schema_retrieval_node)
    graph.add_node("generate_sql", sql_generation_node)
    graph.add_node("validate", validation_node)
    graph.add_node("execute", execution_node)
    graph.add_node("repair", repair_node)
    graph.add_node("generate_answer", answer_generation_node)
    graph.add_node("error_answer", error_answer_node)

    graph.set_entry_point("retrieve_schema")

    graph.add_edge("retrieve_schema", "generate_sql")
    graph.add_edge("generate_sql", "validate")

    graph.add_conditional_edges(
        "validate",
        lambda s: "execute" if s["sql_valid"] else should_retry_or_fail(s),
        {"execute": "execute", "repair": "repair", "error_answer": "error_answer"}
    )

    graph.add_conditional_edges(
        "execute",
        lambda s: "generate_answer" if s["sql_valid"] else should_retry_or_fail(s),
        {"generate_answer": "generate_answer", "repair": "repair", "error_answer": "error_answer"}
    )

    graph.add_edge("repair", "validate")
    graph.add_edge("generate_answer", END)
    graph.add_edge("error_answer", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agent(question: str, conversation_context: str = "") -> dict:
    """Main entry point. Returns final state with answer, SQL, and results."""
    graph = get_graph()

    initial_state: AgentState = {
        "user_question": question,
        "conversation_context": conversation_context,
        "relevant_schema": "",
        "sql_query": "",
        "sql_valid": False,
        "sql_error": "",
        "retry_count": 0,
        "columns": [],
        "rows": [],
        "final_answer": "",
        "error_message": ""
    }

    result = graph.invoke(initial_state)
    return result
