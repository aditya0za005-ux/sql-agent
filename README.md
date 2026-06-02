<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/de903d50-64d5-4cf0-9239-e6b92c5626e1" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f65dbc3d-d685-4102-a6de-f363b36953a4" />

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/19855583-dc08-423e-9ba3-d7b9be4d0e35" />
# 🗄️ Autonomous Text-to-SQL Agent

An intelligent multi-agent system that converts natural language questions into SQL queries using LangGraph for workflow orchestration, FAISS for schema-aware retrieval, and Llama 3.3 70B via Groq for reasoning.

## Features

- **Schema-Aware RAG** — FAISS vector store retrieves only relevant tables for each question instead of dumping the entire schema to the LLM
- **Self-Correcting Workflow** — If SQL fails validation or execution, a repair agent automatically fixes it (up to 2 retries)
- **Query Safety Layer** — Blocks all destructive operations (DROP, DELETE, UPDATE, etc.)
- **Conversational Memory** — Remembers last 5 turns so follow-up questions work correctly
- **Result Explanation** — LLM explains why specific tables/joins were used, making output trustworthy

## Architecture

```
User Question
     ↓
Schema Retrieval Node  ← RAG: FAISS retrieves relevant tables
     ↓
SQL Generation Node    ← LLM generates SQL with schema context
     ↓
Validation Node        ← Safety check + SQLite syntax validation
     ↓ (fail)          ↓ (pass)
Repair Node ←←←    Execution Node
     ↓ (retry)         ↓ (fail → repair)
                   Answer Generation Node
                       ↓
                   Final Response
```

## Tech Stack

| Component | Tool |
|-----------|------|
| LLM | Llama 3.3 70B via Groq |
| Orchestration | LangGraph |
| Schema RAG | FAISS + HuggingFace Embeddings |
| Database | SQLite |
| Frontend | Streamlit |
| Memory | In-memory conversation history |

## Setup

```bash
git clone <repo>
cd text2sql

pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

streamlit run app.py
```

## Sample Questions to Try

- "Show top 5 customers by total order value"
- "Which products are low in stock?"  
- "Revenue by product category"
- "Show all completed orders from customers in Pune"
- "Average salary by department"
- "Which customer placed the most orders?"
- "Show employees and their managers"

## Project Structure

```
text2sql/
├── app.py           # Streamlit UI
├── graph.py         # LangGraph agent workflow
├── database.py      # SQLite setup + schema discovery
├── vector_store.py  # FAISS schema RAG
├── tools.py         # SQL validator, safety, executor
├── memory.py        # Conversation history
├── requirements.txt
└── data/
    └── company.db   # Auto-generated SQLite database
```

## Resume Description

> Developed an autonomous Text-to-SQL multi-agent system using LangGraph and LangChain with schema-aware RAG retrieval (FAISS), self-correcting SQL workflows with automatic error recovery, query safety validation, and conversational memory. Built on Llama 3.3 70B via Groq with a Streamlit frontend.
