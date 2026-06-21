#!/usr/bin/env python3
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from tools.dashboard_logger import log_change, log_marketing_fact


@pytest.fixture
def temp_db():
    """Sets up a temporary SQLite database with required tables."""
    fd, path = tempfile.mkstemp(suffix=".db")
    db_path = Path(path)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables matching models.py
    cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            billing_type TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            manager_id INTEGER,
            vat_type TEXT,
            vat_rate REAL,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE changelog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            reason TEXT,
            expected_effect TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE marketing_fact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            source_id INTEGER NOT NULL,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            spend REAL DEFAULT 0.0,
            leads_primary INTEGER DEFAULT 0,
            leads_qualified INTEGER DEFAULT 0,
            cpl REAL DEFAULT 0.0,
            cpl_qualified REAL DEFAULT 0.0,
            ctr REAL DEFAULT 0.0,
            cpc REAL DEFAULT 0.0,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(source_id) REFERENCES sources(id)
        )
    """)
    conn.commit()
    conn.close()

    yield db_path

    # Teardown
    os.close(fd)
    if db_path.exists():
        db_path.unlink()
    os.environ.pop("DATABASE_URL", None)


def test_log_change(temp_db):
    # Log a change for 'Test Project'
    log_change(
        project_name="Test Project",
        description="Changed SEO meta tags",
        reason="Improve search ranking",
        expected_effect="Organic CTR increase by 5%",
        change_date="2026-06-21",
    )

    # Verify connection and data
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check client & project auto-generation
    cursor.execute("SELECT * FROM projects WHERE name = ?", ("Test Project",))
    project = cursor.fetchone()
    assert project is not None
    assert project["name"] == "Test Project"

    # Check changelog record
    cursor.execute("SELECT * FROM changelog WHERE project_id = ?", (project["id"],))
    change = cursor.fetchone()
    assert change is not None
    assert change["description"] == "Changed SEO meta tags"
    assert change["reason"] == "Improve search ranking"
    assert change["expected_effect"] == "Organic CTR increase by 5%"
    assert change["date"] == "2026-06-21"

    conn.close()


def test_log_marketing_fact(temp_db):
    # Log marketing metrics
    log_marketing_fact(
        project_name="Test Project",
        source_name="seo",
        impressions=1000,
        clicks=100,
        spend=500.0,
        leads_primary=10,
        leads_qualified=5,
        fact_date="2026-06-21",
    )

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check fact record
    cursor.execute("SELECT * FROM marketing_fact")
    fact = cursor.fetchone()
    assert fact is not None
    assert fact["impressions"] == 1000
    assert fact["clicks"] == 100
    assert fact["spend"] == 500.0
    assert fact["leads_primary"] == 10
    assert fact["leads_qualified"] == 5
    assert fact["ctr"] == 10.0  # (100/1000)*100
    assert fact["cpc"] == 5.0  # 500/100
    assert fact["cpl"] == 50.0  # 500/10
    assert fact["cpl_qualified"] == 100.0  # 500/5
    assert fact["date"] == "2026-06-21"

    # Test update (upsert) behavior
    log_marketing_fact(
        project_name="Test Project",
        source_name="seo",
        impressions=2000,
        clicks=250,
        spend=1000.0,
        leads_primary=20,
        leads_qualified=10,
        fact_date="2026-06-21",
    )

    cursor.execute("SELECT COUNT(*) as cnt FROM marketing_fact")
    assert cursor.fetchone()["cnt"] == 1

    cursor.execute("SELECT * FROM marketing_fact")
    updated_fact = cursor.fetchone()
    assert updated_fact["impressions"] == 2000
    assert updated_fact["clicks"] == 250
    assert updated_fact["spend"] == 1000.0
    assert updated_fact["ctr"] == 12.5  # (250/2000)*100
    assert updated_fact["cpc"] == 4.0  # 1000/250

    conn.close()


def test_log_change_retry_on_lock(temp_db):
    import threading
    import time

    lock_acquired = threading.Event()
    release_lock = threading.Event()

    def lock_and_wait():
        conn = sqlite3.connect(temp_db)
        conn.execute("BEGIN EXCLUSIVE TRANSACTION;")
        conn.execute(
            "INSERT INTO clients (name, status) VALUES (?, ?)",
            ("Locked Client", "active"),
        )
        lock_acquired.set()
        release_lock.wait()
        conn.rollback()
        conn.close()

    t = threading.Thread(target=lock_and_wait)
    t.daemon = True
    t.start()

    lock_acquired.wait()

    def unlock_after_delay():
        time.sleep(0.4)
        release_lock.set()

    t_unlock = threading.Thread(target=unlock_after_delay)
    t_unlock.start()

    # Call log_change. It should hit the lock, retry, and succeed after the lock is released.
    log_change(
        project_name="Retry Project",
        description="Testing retry logic",
        change_date="2026-06-21",
    )

    t_unlock.join()
    t.join()

    # Verify that the change was successfully written after retry
    conn2 = sqlite3.connect(temp_db)
    cursor = conn2.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM changelog WHERE description = 'Testing retry logic'"
    )
    count = cursor.fetchone()[0]
    conn2.close()

    assert count == 1
