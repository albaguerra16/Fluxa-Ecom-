"""SQLite para historial de sesiones Fluxa (análisis + creatives)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "fluxa.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT    NOT NULL,
            producto  TEXT    NOT NULL,
            modulo    TEXT    NOT NULL,
            datos     TEXT    NOT NULL
        );
        """)


def guardar(producto: str, modulo: str, datos: dict) -> int:
    init_db()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO sesiones (fecha, producto, modulo, datos) VALUES (?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), producto, modulo, json.dumps(datos, ensure_ascii=False)),
        )
        return cur.lastrowid


def listar(modulo: str | None = None, limite: int = 50) -> list[dict]:
    init_db()
    with _conn() as con:
        if modulo:
            rows = con.execute(
                "SELECT * FROM sesiones WHERE modulo=? ORDER BY fecha DESC LIMIT ?",
                (modulo, limite),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM sesiones ORDER BY fecha DESC LIMIT ?", (limite,)
            ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["datos"] = json.loads(d["datos"])
        result.append(d)
    return result


def eliminar(session_id: int) -> None:
    init_db()
    with _conn() as con:
        con.execute("DELETE FROM sesiones WHERE id=?", (session_id,))
