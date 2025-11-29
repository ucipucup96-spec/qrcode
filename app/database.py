import os
import sqlite3
from typing import Iterable, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)


CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS sticker_sizes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        width REAL NOT NULL,
        height REAL NOT NULL,
        margin_x REAL NOT NULL,
        margin_y REAL NOT NULL,
        rows INTEGER NOT NULL,
        cols INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        sticker_size_id INTEGER NOT NULL,
        count INTEGER NOT NULL,
        FOREIGN KEY (sticker_size_id) REFERENCES sticker_sizes(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS serials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER NOT NULL,
        serial TEXT NOT NULL,
        FOREIGN KEY (batch_id) REFERENCES batches(id)
    );
    """,
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    for statement in CREATE_TABLES_SQL:
        cur.executescript(statement)
    conn.commit()
    conn.close()


def fetch_sticker_sizes() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, width, height, margin_x, margin_y, rows, cols FROM sticker_sizes ORDER BY id"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_sticker_size(
    name: str,
    width: float,
    height: float,
    margin_x: float,
    margin_y: float,
    rows: int,
    cols: int,
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sticker_sizes (name, width, height, margin_x, margin_y, rows, cols)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, width, height, margin_x, margin_y, rows, cols),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_sticker_size(
    sticker_id: int,
    name: str,
    width: float,
    height: float,
    margin_x: float,
    margin_y: float,
    rows: int,
    cols: int,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE sticker_sizes
        SET name = ?, width = ?, height = ?, margin_x = ?, margin_y = ?, rows = ?, cols = ?
        WHERE id = ?
        """,
        (name, width, height, margin_x, margin_y, rows, cols, sticker_id),
    )
    conn.commit()
    conn.close()


def delete_sticker_size(sticker_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sticker_sizes WHERE id = ?", (sticker_id,))
    conn.commit()
    conn.close()


def insert_batch(name: str, created_at: str, sticker_size_id: int, count: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO batches (name, created_at, sticker_size_id, count)
        VALUES (?, ?, ?, ?)
        """,
        (name, created_at, sticker_size_id, count),
    )
    batch_id = cur.lastrowid
    conn.commit()
    conn.close()
    return batch_id


def insert_serials(batch_id: int, serials: Iterable[str]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO serials (batch_id, serial) VALUES (?, ?)",
        [(batch_id, serial) for serial in serials],
    )
    conn.commit()
    conn.close()


def fetch_batches() -> List[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.id, b.name, b.created_at, b.count, s.name AS sticker_name
        FROM batches b
        LEFT JOIN sticker_sizes s ON b.sticker_size_id = s.id
        ORDER BY b.created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_batch(batch_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT b.id, b.name, b.created_at, b.count, b.sticker_size_id, s.name AS sticker_name,
               s.width, s.height, s.margin_x, s.margin_y, s.rows, s.cols
        FROM batches b
        LEFT JOIN sticker_sizes s ON b.sticker_size_id = s.id
        WHERE b.id = ?
        """,
        (batch_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def fetch_serials(batch_id: int) -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT serial FROM serials WHERE batch_id = ? ORDER BY id", (batch_id,))
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


DEFAULT_STICKERS = [
    ("1in x 1in", 25.4, 25.4, 5.0, 5.0, 8, 3),
    ("2in x 1in", 50.8, 25.4, 5.0, 5.0, 8, 2),
    ("65 x 25mm", 65.0, 25.0, 3.0, 3.0, 9, 3),
]


def seed_sticker_sizes() -> None:
    if fetch_sticker_sizes():
        return
    for sticker in DEFAULT_STICKERS:
        insert_sticker_size(*sticker)
