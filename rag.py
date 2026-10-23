from functools import lru_cache
import chromadb
from openai import OpenAI

KNOWLEDGE_DOCS = [
    """
    Schema: public.customers
    Columns: customer_id, name, city.
    Stores customer information.
    """,
    """
    Schema: public.products
    Columns: product_id, product_name, category, price.
    Stores product catalog information.
    """,
    """
    Schema: public.orders
    Columns: order_id, customer_id, product_id, quantity, unit_price, order_date.
    Each order row references a customer and a product.
    orders.customer_id joins customers.customer_id.
    orders.product_id joins products.product_id.
    """,
    """
    Question: Retrieve all customers ordered by customer ID.
    SQL: SELECT * FROM public.customers ORDER BY customer_id;
    """,
    """
    Question: Find products with prices greater than 100.
    SQL: SELECT * FROM public.products WHERE price > 100;
    """,
    """
    Question: Count orders placed by each customer.
    SQL: SELECT customer_id, COUNT(*) AS order_count
         FROM public.orders
         GROUP BY customer_id;
    """,
    """
    Question: Show each order ID with the customer's name.
    SQL: SELECT o.order_id, c.name
         FROM public.orders AS o
         JOIN public.customers AS c
           ON o.customer_id = c.customer_id;
    """,
    """
    Question: Compute total sales revenue per product, highest to lowest.
    SQL: SELECT product_id, SUM(quantity * unit_price) AS revenue
         FROM public.orders
         GROUP BY product_id
         ORDER BY revenue DESC, product_id;
    """,
]

@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name="sql_quiz_knowledge",
        metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(
        ids=[f"doc-{i}" for i in range(len(KNOWLEDGE_DOCS))],
        documents=KNOWLEDGE_DOCS,
    )
    return collection


def retrieve_context(question: str, n_results: int = 3) -> list[str]:
    collection = get_collection()
    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, collection.count()),
    )
    return results["documents"][0]

def generate_sql(
    question: str,
    retrieved_context: list[str],
    api_key: str,
) -> str:
    client = OpenAI(api_key=api_key)
    context_text = "\n\n".join(retrieved_context)

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=(
            "Generate one PostgreSQL SELECT query using only the provided "
            "schema and context. Return only SQL, without markdown or explanation."
        ),
        input=(
            f"Question:\n{question}\n\n"
            f"Retrieved context:\n{context_text}"
        ),
    )

    return response.output_text.strip()


if __name__ == "__main__":
    question = "How can I calculate total sales revenue for each product?"
    for i, document in enumerate(retrieve_context(question), start=1):
        print(f"\n--- Retrieved document {i} ---\n{document}")