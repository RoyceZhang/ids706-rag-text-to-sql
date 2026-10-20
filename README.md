# IDS 706 — SQL Quiz with Supabase

A live, 20-point SQL quiz built with **Streamlit**, **Supabase PostgreSQL**, **Supabase Auth**, and **GitHub Actions** for the IDS 706 Week 7 Major Assignment.

## Live application and repository

- **Take the quiz:** https://ids706-sql-quiz-royce-zhang.streamlit.app/
- **GitHub repository:** https://github.com/RoyceZhang/ids706-sql-quiz
- **GitHub Actions:** https://github.com/RoyceZhang/ids706-sql-quiz/actions

The application uses a hosted PostgreSQL database, not a local SQLite file or hard-coded result table. A signed-in student can select a question, write SQL, execute it against the live database, inspect returned rows, and save an answer. A signed-out visitor is shown the sign-in/sign-up screen and cannot access the query or save controls.

## How to take the quiz (student/TA instructions)

1. Open the **live quiz URL** above.
2. Choose **Sign up** if you need an account, or **Sign in** if you already have one. Sign-up uses an email address and password through Supabase Auth. If email confirmation is enabled, confirm your email before signing in. For grading, the TA may use an existing confirmed account or register and verify an account.
3. After signing in, use **Choose a question** to select Question 1–5.
4. Read the prompt and write your SQL in **Write a SQL query**. You can expand **Hint: expected SQL and result** to see a reference query and the expected output description.
5. Press **Run Query** to execute your SQL on the hosted PostgreSQL database. The result is displayed as a table. Successful SELECT queries display up to 100 rows.
6. Press **Save Answer** to save your SQL text under your authenticated account. Answers are stored in `public.quiz_answers`, with one saved answer per user per question (saving again updates it).
7. Use **Sign out** in the sidebar when finished.

**Quick grader test:** After signing in, select Question 1 and run:

```sql
SELECT * FROM public.customers ORDER BY customer_id;
```

It should return **8 customer rows**. Then choose Question 5 and run:

```sql
SELECT product_id,
       SUM(quantity * unit_price) AS revenue
FROM public.orders
GROUP BY product_id
ORDER BY revenue DESC, product_id;
```

The expected result has **6 rows**, with product 1 generating `1798.00` in revenue. Click **Save Answer** to verify persistence. Finally, sign out and confirm that running/saving SQL is unavailable.

## Quiz contents (20 points)

| # | Topic | Student task | Points |
|---|---|---|---:|
| 1 | Basic SELECT | Retrieve all customers ordered by customer ID. | 4 |
| 2 | WHERE filtering | Find products with prices greater than 100. | 4 |
| 3 | GROUP BY | Count orders placed by each customer. | 4 |
| 4 | JOIN | Show each order ID with the customer's name. | 4 |
| 5 | Aggregation and sorting | Compute total sales revenue per product, highest to lowest. | 4 |
| | **Total** | | **20** |

Each question is stored in `public.quiz_questions`, including its title, prompt, point value, reference SQL (`expected_sql`), and expected-result description (`expected_result`). The in-app hint can be expanded for these details. Students are assessed on the **result set**, not exact SQL wording.

## Architecture and database

**Architecture:** Browser → Streamlit application (`app.py`) → Supabase Auth for authentication; authenticated application actions → hosted PostgreSQL for read-only query execution (`db.py`), and Supabase REST API for saving answers subject to Row Level Security (RLS).

Supabase hosts a PostgreSQL database with these tables:

| Table | Important columns | Purpose |
|---|---|---|
| `public.customers` | `customer_id`, `name`, `city` | Sample customer data (8 rows) |
| `public.products` | `product_id`, `product_name`, `category`, `price` | Sample product catalog (6 rows) |
| `public.orders` | `order_id`, `customer_id`, `product_id`, `quantity`, `unit_price`, `order_date` | Sample purchases (15 rows) |
| `public.quiz_questions` | `question_id`, `title`, `prompt`, `points`, `expected_sql`, `expected_result` | The 5 quiz questions |
| `public.quiz_answers` | `answer_id`, `user_id`, `question_id`, `sql_answer`, `updated_at` | Saved answers, scoped to the signed-in user |

`orders.customer_id` references `customers.customer_id`, and `orders.product_id` references `products.product_id`. `quiz_answers.user_id` references Supabase Auth's `auth.users(id)` and `quiz_answers.question_id` references `quiz_questions.question_id`.

The sample dataset and quiz questions were created in Supabase SQL Editor. The application queries the hosted database in real time. For a new Supabase project, provision the five tables and sample rows before running the app; this repository's `sql/reader_role.sql` sets up the restricted querying role **after** the tables have been created. The initial schema and seed dataset were provisioned in the hosted project and are not automatically created by the Streamlit app.

## Authentication and query security

- **Supabase Auth** provides email/password registration and sign-in. `app.py` verifies the access token server-side via `auth.get_user` and stops before displaying quiz/query/save features for unauthenticated visitors. It rechecks authentication when **Run Query** or **Save Answer** is clicked.
- SQL execution uses the dedicated **`quiz_reader`** PostgreSQL role, with `SELECT` access to the sample data and quiz questions, not an administrative database account. Role setup is in `sql/reader_role.sql`.
- `db.py` accepts one parsed `SELECT` statement (including supported `WITH ... SELECT` statements), sets the transaction **READ ONLY**, applies a **5-second statement timeout**, and returns at most **100 rows** to the UI. These checks supplement PostgreSQL permissions; they do not grant students write access.
- Saving answers uses the signed-in user's bearer token through the Supabase REST API. RLS on `public.quiz_answers` restricts access to the corresponding `auth.uid()`; users can save/read their own answers, not other users' answers.
- Database connections use the Supabase **Session pooler on port 5432** with **`sslmode=require`**.
- Passwords and tokens belong in local/hosted secrets, **never in source control**. The real `.streamlit/secrets.toml`, `.env`, and Python virtual environment are excluded by `.gitignore`.

## Run locally

**Prerequisites:** Python 3.11+ and access to the provisioned Supabase project.

```bash
git clone https://github.com/RoyceZhang/ids706-sql-quiz.git
cd ids706-sql-quiz
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
python -m pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` locally (do not commit it):

```toml
supabase_url = "https://YOUR_PROJECT_REF.supabase.co"
supabase_publishable_key = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
db_host = "YOUR_SESSION_POOLER_HOST"
db_port = 5432
db_user = "quiz_reader.YOUR_PROJECT_REF"
db_password = "YOUR_PRIVATE_READER_PASSWORD"
db_name = "postgres"
```

Find the Supabase Project URL and publishable key in the Supabase dashboard. For PostgreSQL credentials, use **Connect → Connection string → Session pooler** (not Direct connection). `db_user` is the dedicated read-only role with the project reference suffix. The reader role can be set up using `sql/reader_role.sql` in Supabase SQL Editor; **replace the password placeholder privately before executing**, and do not commit a modified copy containing the real password.

Start the app:

```bash
python -m streamlit run app.py
```

Open `http://localhost:8501`, create or sign in to a confirmed Supabase Auth account, and run a quiz query.

## GitHub Actions and GitHub Secrets

The workflow `.github/workflows/database-check.yml` runs on **push** and supports manual execution with **workflow_dispatch**. It uses Python 3.11, installs `psycopg`, and executes `scripts/check_database.py` against hosted Supabase PostgreSQL.

Create these **repository secrets** under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| `DB_HOST` | Supabase Session pooler hostname |
| `DB_USER` | Read-only database username, including the project reference suffix |
| `DB_PASSWORD` | Password for the read-only database role |

The workflow supplies `DB_PORT=5432` and `DB_NAME=postgres` without embedding any password. The script checks the live database connection, validates 8 customers / 6 products / 15 orders, confirms 5 questions totaling 20 points, and verifies that the reader lacks `INSERT` privileges on the orders table. Any failed assertion causes the workflow to fail.

**CI evidence:** See the successful **Database Check** run on the [Actions page](https://github.com/RoyceZhang/ids706-sql-quiz/actions). GitHub Secrets are referenced in the workflow as `${{ secrets.DB_HOST }}`, `${{ secrets.DB_USER }}`, and `${{ secrets.DB_PASSWORD }}`; their values are not stored in the workflow file.

## Cloud deployment

The hosted quiz runs on **Streamlit Community Cloud**, deployed from the `main` branch with `app.py` as its entry point. The deployed application uses Streamlit Cloud's encrypted **App settings → Secrets** for the same keys as the local `.streamlit/secrets.toml`; these settings are separate from GitHub Actions repository secrets.

After deployment or credential rotation, confirm the public URL opens, a confirmed user can sign in, **Run Query** produces live rows, **Save Answer** persists to Supabase, and signed-out visitors cannot perform either operation. If changing the reader password, update local secrets, Streamlit Cloud secrets, and the GitHub `DB_PASSWORD` secret.

## Project files

```text
ids706-sql-quiz/
├── .github/workflows/database-check.yml  # CI database check
├── .streamlit/secrets.toml.example        # Safe configuration template
├── scripts/check_database.py              # CI assertions against PostgreSQL
├── sql/reader_role.sql                     # Restricted database role setup
├── app.py                                  # Streamlit UI, Auth and answer saving
├── db.py                                   # Read-only SQL execution
├── requirements.txt                        # Python dependencies
├── .gitignore                              # Excludes real secrets and .venv
└── README.md                               # This guide
```

## Troubleshooting

- **Email not confirmed:** Confirm the registration email (or ask the project administrator to confirm a test account) before signing in.
- **Database connection failed:** Check the Session pooler host, port `5432`, username suffix, current reader password, and SSL requirement. Check that the reader role exists and has `SELECT` permissions and RLS read policies for the quiz tables.
- **Save Answer failed:** Verify the Supabase URL/key, valid user session, and RLS policies for `quiz_answers`.
- **GitHub Actions failed with missing secrets:** Add `DB_HOST`, `DB_USER`, and `DB_PASSWORD` in the repository Actions secrets, then re-run the workflow.

---

**Assignment:** IDS 706 · Week 7 Major Assignment: Build a SQL Quiz with Supabase  
**Submitted repository:** https://github.com/RoyceZhang/ids706-sql-quiz
