# IDS 706 — SQL Quiz with Supabase

Live quiz URL: **ADD AFTER DEPLOYMENT**

A 20-point SQL quiz with five questions about online store sales. Users sign in with Supabase Auth, run read-only SQL against a hosted PostgreSQL database, and save answers into a row-level-secured table.

## Setup
1. Create the five tables and seed data from Step 1.
2. Run `sql/reader_role.sql` in Supabase SQL Editor **after replacing** its placeholder with a new unique password. Never commit that modified SQL.
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`; fill in your Supabase Project URL and publishable/anon key and **Session pooler** database host, username and quiz_reader password.
4. Use Python 3.11 or 3.12; `python -m pip install -r requirements.txt`.
5. Run `python -m streamlit run app.py`.
6. In Supabase Authentication settings, enable Email sign-ups and decide whether email confirmation is required. Verify email when configured.

## Security
- SQL is restricted to a single parsed SELECT statement and a database transaction marked READ ONLY; the database connection uses a dedicated SELECT-only account.
- Supabase Auth user is verified on the server. Signed-out visitors cannot run SQL or save answers.
- Saves use the user's bearer access token so database RLS is applied to quiz_answers.
- Never commit `.streamlit/secrets.toml`, `.env`, passwords, or access tokens.

## Next steps
- Add a GitHub Actions workflow using GitHub Secrets and verify a green run (Step 3).
- Deploy to Streamlit Community Cloud and configure app secrets, then paste the live URL above (Step 4).
