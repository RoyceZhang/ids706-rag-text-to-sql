"""Read-only SQL execution against live Supabase Postgres."""
import psycopg
import sqlparse
import streamlit as st


def read_only_connection():
    return psycopg.connect(
        host=st.secrets["db_host"],
        port=int(st.secrets.get("db_port", 5432)),
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        dbname=st.secrets.get("db_name", "postgres"),
        sslmode="require",
        connect_timeout=10,
    )


def run_select(query):
    """Execute one read-only SELECT/WITH query, returning column names and rows."""
    statements = sqlparse.parse(query.strip())
    if len(statements) != 1 or statements[0].get_type() != "SELECT":
        raise ValueError("Enter exactly one SELECT query (WITH ... SELECT is allowed).")

    with read_only_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("SET LOCAL statement_timeout = '5000ms'")
            cur.execute(query)
            if cur.description is None:
                raise ValueError("The query did not return a result table.")
            columns = [item.name for item in cur.description]
            rows = cur.fetchmany(101)
            return columns, rows[:100], len(rows) > 100
