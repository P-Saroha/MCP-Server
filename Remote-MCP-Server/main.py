from fastmcp import FastMCP
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


init_db()


@mcp.tool()
def add_expense(date: str,
                amount: float,
                category: str,
                subcategory: str = "",
                note: str = ""):
    """Add a new expense."""

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO expenses
            (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, amount, category, subcategory, note)
        )

        return {
            "status": "success",
            "expense_id": cur.lastrowid
        }


@mcp.tool()
def list_expenses(start_date: str, end_date: str):
    """List expenses between two dates."""

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
            """,
            (start_date, end_date)
        )

        cols = [d[0] for d in cur.description]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]


@mcp.tool()
def summarize(start_date: str,
              end_date: str,
              category: str = None):
    """Summarize expenses by category."""

    with sqlite3.connect(DB_PATH) as conn:

        query = """
            SELECT category,
                   SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """

        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += """
            GROUP BY category
            ORDER BY total_amount DESC
        """

        cur = conn.execute(query, params)

        cols = [d[0] for d in cur.description]

        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]


@mcp.resource("expense://categories")
def categories():
    """Available categories."""

    if not os.path.exists(CATEGORIES_PATH):
        return json.dumps(
            {
                "message": "categories.json not found",
                "categories": []
            },
            indent=2
        )

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    mcp.run()