from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from graph import run_agent
from database import setup_database

setup_database()

app = FastAPI(
    title="SQL Agent API",
    description="Autonomous Text-to-SQL Agent using LangGraph",
    version="1.0"
)


class QueryRequest(BaseModel):
    question: str
    conversation_context: str = ""


@app.get("/")
def root():
    return {
        "message": "SQL Agent API Running"
    }


@app.post("/query")
def query_agent(request: QueryRequest):
    result = run_agent(
        request.question,
        conversation_context=request.conversation_context
    )

    return {
        "question": request.question,
        "answer": result.get("final_answer"),
        "sql": result.get("sql_query"),
        "columns": result.get("columns", []),
        "rows": result.get("rows", []),
        "retry_count": result.get("retry_count", 0)
    }
