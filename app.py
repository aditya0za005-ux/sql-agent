import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

from database import setup_database
from graph import run_agent
from memory import ConversationMemory

# Page Config
 

st.set_page_config(
    page_title="SQL Agent",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling

st.markdown("""
<style>
    /* Dark theme base */
    .stApp { background-color: #0f1117; color: #e0e0e0; }
    
    /* Input box */
    .stTextInput > div > div > input {
        background-color: #1e2130;
        color: #e0e0e0;
        border: 1px solid #3a3f55;
        border-radius: 8px;
    }

    /* SQL code block */
    .sql-box {
        background: #1a1f2e;
        border-left: 3px solid #4f8ef7;
        border-radius: 6px;
        padding: 12px 16px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #a8d8f0;
        margin: 8px 0;
        white-space: pre-wrap;
    }

    /* Answer box */
    .answer-box {
        background: #151b2d;
        border: 1px solid #2d3550;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }

    /* Status badges */
    .badge-success {
        background: #1a3a2a;
        color: #4caf82;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-error {
        background: #3a1a1a;
        color: #e05555;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-retry {
        background: #2d2a1a;
        color: #e0a830;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #13161f;
    }

    /* Buttons */
    .stButton > button {
        background: #2a3555;
        color: #e0e0e0;
        border: 1px solid #3a4870;
        border-radius: 8px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background: #3a4a72;
        border-color: #4f8ef7;
    }

    h1, h2, h3 { color: #c8d8ff; }
    .stDataFrame { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# Init

setup_database()

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory(max_turns=5)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar

with st.sidebar:
    st.markdown("## 🗄️ SQL Agent")
    st.markdown("*Autonomous Text-to-SQL with LangGraph*")
    st.divider()

    st.markdown("### 📊 Available Tables")
    tables_info = {
        "customers": "👤 Customer profiles",
        "products": "📦 Product catalog",
        "orders": "🛒 Order records",
        "order_items": "🔗 Order line items",
        "employees": "👔 Employee data"
    }
    for table, desc in tables_info.items():
        st.markdown(f"`{table}` — {desc}")

    st.divider()

    st.markdown("### 💡 Try These")
    example_questions = [
        "Show top 5 customers by total order value",
        "Which products are low in stock?",
        "Revenue by product category",
        "Show all orders from customers in Pune",
        "Average salary by department",
        "Which customer placed the most orders?",
    ]
    for q in example_questions:
        if st.button(q, key=f"ex_{q[:20]}", use_container_width=True):
            st.session_state.example_input = q

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.memory.clear()
        st.rerun()

    st.markdown("### ⚙️ Stack")
    st.markdown("""
    - **LLM**: Llama 3.3 70B (Groq)
    - **Orchestration**: LangGraph
    - **RAG**: FAISS + HuggingFace
    - **DB**: SQLite
    - **Safety**: Query validation layer
    """)

# Main Area

st.markdown("# 🗄️ Autonomous SQL Agent")
st.markdown("Ask questions in plain English. The agent generates, validates, and executes SQL automatically.")
st.divider()

# Chat History

for turn in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(turn["question"])

    with st.chat_message("assistant"):
        # SQL
        with st.expander("📝 Generated SQL", expanded=False):
            st.markdown(f'<div class="sql-box">{turn["sql"]}</div>', unsafe_allow_html=True)

        # Status badge
        if turn["retries"] > 0:
            st.markdown(f'<span class="badge-retry">⚠️ Self-corrected ({turn["retries"]} retries)</span>', unsafe_allow_html=True)
        elif turn["success"]:
            st.markdown('<span class="badge-success">✅ Executed successfully</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-error">❌ Query failed</span>', unsafe_allow_html=True)

        # Answer
        st.markdown(turn["answer"])

        # Results table
        if turn["columns"] and turn["rows"]:
            with st.expander(f"📊 Raw Results ({len(turn['rows'])} rows)", expanded=False):
                df = pd.DataFrame(turn["rows"], columns=turn["columns"])
                st.dataframe(df, use_container_width=True)

# Input

# Handle example button clicks
default_input = st.session_state.pop("example_input", "")

question = st.chat_input("Ask anything about your data...")

# Use example if button was clicked
if default_input and not question:
    question = default_input

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing query..."):
            context = st.session_state.memory.get_context_string()
            result = run_agent(question, conversation_context=context)

        sql = result.get("sql_query", "")
        answer = result.get("final_answer", "Something went wrong.")
        columns = result.get("columns", [])
        rows = result.get("rows", [])
        retries = result.get("retry_count", 0)
        success = bool(rows) or ("no results" in answer.lower())

        # SQL expander
        with st.expander("📝 Generated SQL", expanded=True):
            st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

        # Status
        if retries > 0:
            st.markdown(f'<span class="badge-retry">⚠️ Self-corrected ({retries} retries)</span>', unsafe_allow_html=True)
        elif sql:
            st.markdown('<span class="badge-success">✅ Executed successfully</span>', unsafe_allow_html=True)

        # Answer
        st.markdown(answer)

        # Table
        if columns and rows:
            with st.expander(f"📊 Raw Results ({len(rows)} rows)", expanded=True):
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, use_container_width=True)

        # Save to memory
        st.session_state.memory.add_turn(question, answer, sql)
        st.session_state.chat_history.append({
            "question": question,
            "sql": sql,
            "answer": answer,
            "columns": columns,
            "rows": rows,
            "retries": retries,
            "success": bool(sql)
        })
