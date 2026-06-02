from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from database import get_table_metadata

# Business-level descriptions for each table
TABLE_DESCRIPTIONS = {
    "customers": "Contains customer information including name, email, city, country, and signup date. Use for customer-related queries, filtering by location, or counting users.",
    "products": "Contains product catalog with name, category, price, and stock. Use for product queries, price filters, inventory checks, or category analysis.",
    "orders": "Contains orders placed by customers with order date, status (pending/shipped/completed), and total amount. Use for sales analysis, revenue calculations, or order status queries.",
    "order_items": "Junction table linking orders to products. Contains quantity and unit price. Use for detailed sales breakdown, product popularity, or revenue per product.",
    "employees": "Contains employee records with department, salary, hire date, and manager relationship. Use for HR analytics, salary queries, department headcount."
}

_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    metadata = get_table_metadata()

    docs = []
    for table_name, info in metadata.items():
        col_names = [col["name"] for col in info["columns"]]
        description = TABLE_DESCRIPTIONS.get(table_name, "")

        content = f"""
Table: {table_name}
Description: {description}
Columns: {', '.join(col_names)}
Sample data: {info['sample_rows'][:1]}
        """.strip()

        docs.append(Document(
            page_content=content,
            metadata={"table": table_name}
        ))

    _vector_store = FAISS.from_documents(docs, embeddings)
    return _vector_store

def retrieve_relevant_schema(question: str, k: int = 3) -> str:
    """Retrieve top-k relevant table schemas for a given question."""
    store = get_vector_store()
    results = store.similarity_search(question, k=k)
    return "\n\n".join([doc.page_content for doc in results])
