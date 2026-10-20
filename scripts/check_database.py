
"""Check the Supabase database using the read-only role."""

import os
import psycopg


def main():
    required = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [key for key in required if not os.environ.get(key)]

    if missing:
        raise RuntimeError(f"Missing secrets: {missing}")

    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
        sslmode="require",
        connect_timeout=15,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")

            expected = {
                "customers": 8,
                "products": 6,
                "orders": 15,
            }

            for table, count in expected.items():
                cur.execute(f"SELECT COUNT(*) FROM public.{table}")
                actual = cur.fetchone()[0]
                assert actual == count
                print(f"PASS: {table} has {actual} rows")

            cur.execute(
                "SELECT COUNT(*), SUM(points) "
                "FROM public.quiz_questions"
            )
            questions, points = cur.fetchone()
            assert questions == 5
            assert points == 20
            print("PASS: 5 questions, 20 points")

            cur.execute(
                "SELECT has_table_privilege("
                "current_user, 'public.orders', 'INSERT')"
            )
            assert cur.fetchone()[0] is False
            print("PASS: Reader cannot insert orders")

    print("SUCCESS: Connected to Supabase!")


if __name__ == "__main__":
    main()
