"""IDS 706 SQL Quiz: live PostgreSQL queries and Supabase Auth."""
import httpx
import pandas as pd
import streamlit as st
from supabase import create_client
from db import run_select
from rag import retrieve_context, generate_sql

st.set_page_config(page_title="IDS 706 SQL Quiz", page_icon="🗄️", layout="wide")
st.title("🗄️ SQL Quiz — Online Store")
st.caption("5 questions · 4 points each · 20 points total")


def auth_client():
    # Create a fresh client for each execution; do not cache user auth across sessions.
    return create_client(st.secrets["supabase_url"], st.secrets["supabase_publishable_key"])


def verified_user():
    token = st.session_state.get("access_token")
    if not token:
        return None
    try:
        result = auth_client().auth.get_user(token)
        return result.user
    except Exception:
        st.session_state.pop("access_token", None)
        return None


def load_questions():
    cols, rows, _ = run_select(
        "SELECT question_id, title, prompt, points, expected_sql, expected_result "
        "FROM public.quiz_questions ORDER BY question_id"
    )
    return [dict(zip(cols, row)) for row in rows]


def save_answer(user_id, token, question_id, sql_answer):
    url = st.secrets["supabase_url"].rstrip("/") + "/rest/v1/quiz_answers?on_conflict=user_id,question_id"
    headers = {
        "apikey": st.secrets["supabase_publishable_key"],
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    payload = [{"user_id": str(user_id), "question_id": question_id, "sql_answer": sql_answer}]
    response = httpx.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()


def load_saved_answers(token, user_id):
    url = st.secrets["supabase_url"].rstrip("/") + "/rest/v1/quiz_answers"
    headers = {
        "apikey": st.secrets["supabase_publishable_key"],
        "Authorization": "Bearer " + token,
    }
    response = httpx.get(
        url,
        headers=headers,
        params={"select": "question_id,sql_answer", "user_id": "eq." + str(user_id)},
        timeout=15,
    )
    response.raise_for_status()
    return {item["question_id"]: item["sql_answer"] for item in response.json()}

st.divider()
st.header("RAG-Powered Text-to-SQL")

question = st.text_input(
    "Ask a question about the store database",
    key="rag_question",
)

if st.button("Generate SQL", type="primary", key="rag_generate"):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        try:
            context = retrieve_context(question)
            sql = generate_sql(
                question,
                context,
                st.secrets["openai_api_key"],
            )
            st.session_state["rag_context"] = context
            st.session_state["rag_sql"] = sql
        except Exception as exc:
            st.error(f"Could not generate SQL: {exc}")

if st.session_state.get("rag_context"):
    with st.expander("Retrieved context"):
        for document in st.session_state["rag_context"]:
            st.write(document)

if st.session_state.get("rag_sql"):
    st.code(st.session_state["rag_sql"], language="sql")

user = verified_user()
if user is None:
    st.info("Please sign in or create an account to run SQL and save quiz answers.")
    tab_login, tab_signup = st.tabs(["Sign in", "Sign up"])
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            try:
                result = auth_client().auth.sign_in_with_password({"email": email, "password": password})
                if result.session is None:
                    st.error("No session received. Check your email verification status.")
                else:
                    st.session_state["access_token"] = result.session.access_token
                    st.rerun()
            except Exception as exc:
                st.error(f"Sign-in failed: {exc}")
    with tab_signup:
        with st.form("signup_form"):
            email_new = st.text_input("Email", key="signup_email")
            password_new = st.text_input("Password (at least 6 characters)", type="password", key="signup_password")
            create_account = st.form_submit_button("Create account")
        if create_account:
            try:
                result = auth_client().auth.sign_up({"email": email_new, "password": password_new})
                if result.session:
                    st.session_state["access_token"] = result.session.access_token
                    st.rerun()
                else:
                    st.success("Account created. Verify your email, then sign in.")
            except Exception as exc:
                st.error(f"Sign-up failed: {exc}")
    st.stop()  # Authentication gate: no database query or save from signed-out users.

with st.sidebar:
    st.success(f"Signed in: {user.email}")
    if st.button("Sign out"):
        st.session_state.pop("access_token", None)
        st.rerun()

try:
    questions = load_questions()
    if not questions:
        st.error("No questions found in public.quiz_questions.")
        st.stop()
    saved = load_saved_answers(st.session_state["access_token"], user.id)
except Exception as exc:
    st.error(f"Database setup/connection error: {exc}")
    st.stop()

selected_id = st.selectbox(
    "Choose a question",
    options=[int(q["question_id"]) for q in questions],
    format_func=lambda n: next(f"Q{n}: {q['title']} ({q['points']} points)" for q in questions if q["question_id"] == n),
)
question = next(q for q in questions if q["question_id"] == selected_id)
st.subheader(f"Question {selected_id} — {question['title']}")
st.write(question["prompt"])
with st.expander("Hint: expected SQL and result"):
    st.code(question["expected_sql"], language="sql")
    st.write(question["expected_result"])

sql = st.text_area(
    "Write a SQL query",
    value=saved.get(selected_id, "SELECT * FROM public.customers ORDER BY customer_id;" if selected_id == 1 else ""),
    height=175,
    key=f"answer_q{selected_id}",
)
col_run, col_save = st.columns(2)
with col_run:
    run_clicked = st.button("▶ Run Query", type="primary", use_container_width=True)
with col_save:
    save_clicked = st.button("💾 Save Answer", use_container_width=True)

if run_clicked:
    # Revalidate the session before executing SQL.
    if verified_user() is None:
        st.error("Session expired. Sign in again.")
        st.stop()
    try:
        cols, rows, truncated = run_select(sql)
        st.success(f"Query succeeded: showing {len(rows)} row(s).")
        st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
        if truncated:
            st.warning("Only the first 100 rows are shown.")
    except Exception as exc:
        st.error(f"Query failed: {exc}")
if save_clicked:
    if verified_user() is None:
        st.error("Session expired. Sign in again.")
        st.stop()
    try:
        save_answer(user.id, st.session_state["access_token"], selected_id, sql)
        st.success("Your SQL answer was saved.")
    except Exception as exc:
        st.error(f"Could not save answer: {exc}")
