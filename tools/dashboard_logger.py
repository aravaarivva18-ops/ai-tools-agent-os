#!/usr/bin/env python3
"""
Dashboard logger utility to record events and marketing facts
from business modules directly into dashboard.db.
"""

import os
import random
import sqlite3
import time
from datetime import date
from pathlib import Path


def get_db_path() -> Path:
    """Finds the dashboard.db path dynamically."""
    # Check env var first
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        # Strip sqlite:///
        clean_path = db_url.replace("sqlite:///", "", 1)
        return Path(clean_path).resolve()

    # Look in dashboard-hand-on-pulse/
    root_dir = Path(__file__).resolve().parent.parent
    mvp_db = root_dir / "dashboard-hand-on-pulse" / "dashboard.db"
    if mvp_db.exists():
        return mvp_db

    # Fallback to root
    return root_dir / "dashboard.db"


def _get_connection():
    db_path = get_db_path()
    # Use 30.0s timeout and check_same_thread=False for Streamlit concurrent execution
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable Write-Ahead Logging (WAL) for better write concurrency
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS healer_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT NOT NULL,
                test_file TEXT NOT NULL,
                target_file TEXT,
                error_category TEXT,
                iterations INTEGER DEFAULT 1,
                status TEXT CHECK(status IN ('healed', 'failed', 'stealth_stop')),
                time_saved_min INTEGER DEFAULT 0
            );
        """)
        conn.commit()
    except Exception:
        pass
    return conn


def log_healer_event(
    session_id: str,
    test_file: str,
    target_file: str | None = None,
    error_category: str | None = None,
    iterations: int = 1,
    status: str = "healed",
    time_saved_min: int = 0,
) -> None:
    """Logs test healer execution statistics to the healer_log table with retry logic."""
    max_attempts = 5
    for attempt in range(max_attempts):
        conn = None
        try:
            conn = _get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO healer_log (session_id, test_file, target_file, error_category, iterations, status, time_saved_min)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, test_file, target_file, error_category, iterations, status, time_saved_min),
            )
            conn.commit()
            print(f"Logged healer event for '{test_file}' successfully.")
            return
        except sqlite3.OperationalError as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
            if "locked" in str(e).lower() and attempt < max_attempts - 1:
                sleep_time = 0.1 * (2**attempt) + random.uniform(0.01, 0.05)
                print(
                    f"Database locked, retrying in {sleep_time:.3f}s (attempt {attempt + 1}/{max_attempts})..."
                )
                time.sleep(sleep_time)
            else:
                print(f"Error logging healer event: {e}")
                raise e
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
            print(f"Error logging healer event: {e}")
            raise e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass



def _get_or_create_project_id(conn, project_name: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
    row = cursor.fetchone()
    if row:
        return row["id"]

    # Fallback: get first project in DB
    cursor.execute("SELECT id FROM projects LIMIT 1")
    row = cursor.fetchone()
    if row:
        return row["id"]

    # Create default project and client if empty
    cursor.execute("SELECT id FROM clients LIMIT 1")
    client_row = cursor.fetchone()
    if client_row:
        client_id = client_row["id"]
    else:
        cursor.execute(
            "INSERT INTO clients (name, status, billing_type) VALUES (?, ?, ?)",
            ("Default Client", "active", "fixed"),
        )
        client_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO projects (client_id, name, vat_type, vat_rate) VALUES (?, ?, ?, ?)",
        (client_id, project_name, "with_vat", 0.20),
    )
    return cursor.lastrowid


def _get_or_create_source_id(conn, source_name: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sources WHERE name = ?", (source_name,))
    row = cursor.fetchone()
    if row:
        return row["id"]

    cursor.execute("INSERT INTO sources (name) VALUES (?)", (source_name,))
    return cursor.lastrowid


def log_change(
    project_name: str,
    description: str,
    reason: str | None = None,
    expected_effect: str | None = None,
    change_date: str | None = None,
) -> None:
    """Logs a system, SEO, or marketing change event to the changelog table with retry logic."""
    if not change_date:
        change_date = date.today().isoformat()

    max_attempts = 5
    for attempt in range(max_attempts):
        conn = None
        try:
            conn = _get_connection()
            project_id = _get_or_create_project_id(conn, project_name)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO changelog (date, project_id, description, reason, expected_effect)
                VALUES (?, ?, ?, ?, ?)
                """,
                (change_date, project_id, description, reason, expected_effect),
            )
            conn.commit()
            print(f"Logged change for '{project_name}' successfully.")
            return
        except sqlite3.OperationalError as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
            if "locked" in str(e).lower() and attempt < max_attempts - 1:
                sleep_time = 0.1 * (2**attempt) + random.uniform(0.01, 0.05)
                print(
                    f"Database locked, retrying in {sleep_time:.3f}s (attempt {attempt + 1}/{max_attempts})..."
                )
                time.sleep(sleep_time)
            else:
                print(f"Error logging change: {e}")
                raise e
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
            print(f"Error logging change: {e}")
            raise e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


def log_marketing_fact(
    project_name: str,
    source_name: str,
    impressions: int,
    clicks: int,
    spend: float,
    leads_primary: int,
    leads_qualified: int,
    fact_date: str | None = None,
) -> None:
    """Logs daily marketing metrics to the marketing_fact table with retry logic."""
    if not fact_date:
        fact_date = date.today().isoformat()

    # Calculate metrics
    ctr = (clicks / impressions * 100.0) if impressions > 0 else 0.0
    cpc = (spend / clicks) if clicks > 0 else 0.0
    cpl = (spend / leads_primary) if leads_primary > 0 else 0.0
    cpl_qualified = (spend / leads_qualified) if leads_qualified > 0 else 0.0

    max_attempts = 5
    for attempt in range(max_attempts):
        conn = None
        try:
            conn = _get_connection()
            project_id = _get_or_create_project_id(conn, project_name)
            source_id = _get_or_create_source_id(conn, source_name)
            cursor = conn.cursor()

            # Check if record already exists for this date, project and source
            cursor.execute(
                """
                SELECT id FROM marketing_fact
                WHERE date = ? AND project_id = ? AND source_id = ?
                """,
                (fact_date, project_id, source_id),
            )
            row = cursor.fetchone()

            if row:
                # Update
                cursor.execute(
                    """
                    UPDATE marketing_fact
                    SET impressions = ?, clicks = ?, spend = ?,
                        leads_primary = ?, leads_qualified = ?,
                        ctr = ?, cpc = ?, cpl = ?, cpl_qualified = ?
                    WHERE id = ?
                    """,
                    (
                        impressions,
                        clicks,
                        spend,
                        leads_primary,
                        leads_qualified,
                        ctr,
                        cpc,
                        cpl,
                        cpl_qualified,
                        row["id"],
                    ),
                )
            else:
                # Insert
                cursor.execute(
                    """
                    INSERT INTO marketing_fact
                    (date, project_id, source_id, impressions, clicks, spend,
                     leads_primary, leads_qualified, ctr, cpc, cpl, cpl_qualified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fact_date,
                        project_id,
                        source_id,
                        impressions,
                        clicks,
                        spend,
                        leads_primary,
                        leads_qualified,
                        ctr,
                        cpc,
                        cpl,
                        cpl_qualified,
                    ),
                )

            conn.commit()
            print(
                f"Logged marketing fact for project '{project_name}' source '{source_name}' successfully."
            )
            return
        except sqlite3.OperationalError as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
            if "locked" in str(e).lower() and attempt < max_attempts - 1:
                sleep_time = 0.1 * (2**attempt) + random.uniform(0.01, 0.05)
                print(
                    f"Database locked, retrying in {sleep_time:.3f}s (attempt {attempt + 1}/{max_attempts})..."
                )
                time.sleep(sleep_time)
            else:
                print(f"Error logging marketing fact: {e}")
                raise e
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
            print(f"Error logging marketing fact: {e}")
            raise e
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
