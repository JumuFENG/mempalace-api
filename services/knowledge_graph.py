"""Knowledge Graph service - Temporal entity relationships via SQLite."""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from core.config import settings


class KGService:
    def __init__(self):
        self.db_path = str(settings.kg_path)
        self._ensure_db()

    def _ensure_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS triples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject INTEGER NOT NULL,
                predicate TEXT NOT NULL,
                object INTEGER NOT NULL,
                valid_from TEXT,
                valid_to TEXT,
                FOREIGN KEY (subject) REFERENCES entities(id),
                FOREIGN KEY (object) REFERENCES entities(id),
                UNIQUE(subject, predicate, object)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_triples_predicate ON triples(predicate)")
        conn.commit()
        conn.close()

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _entity_id(self, name: str, create: bool = True) -> Optional[int]:
        conn = self._conn()
        cur = conn.execute("SELECT id FROM entities WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            conn.close()
            return row[0]
        if create:
            cur = conn.execute("INSERT INTO entities (name) VALUES (?)", (name,))
            conn.commit()
            entity_id = cur.lastrowid
            conn.close()
            return entity_id
        conn.close()
        return None

    def add_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        valid_from: Optional[str] = None,
    ) -> bool:
        s_id = self._entity_id(subject)
        o_id = self._entity_id(obj)
        if s_id is None or o_id is None:
            return False

        conn = self._conn()
        try:
            conn.execute("""
                INSERT INTO triples (subject, predicate, object, valid_from)
                VALUES (?, ?, ?, ?)
            """, (s_id, predicate, o_id, valid_from or datetime.utcnow().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def query_entity(
        self,
        name: str,
        direction: str = "both",
        as_of: Optional[str] = None,
    ) -> dict:
        eid = self._entity_id(name, create=False)
        if eid is None:
            return {"entity": name, "triples": []}

        conn = self._conn()
        if direction == "outgoing":
            query = """
                SELECT t.predicate, e.name, t.valid_from, t.valid_to
                FROM triples t JOIN entities e ON t.object = e.id
                WHERE t.subject = ? AND (t.valid_to IS NULL OR t.valid_to > ?)
                ORDER BY t.valid_from DESC
            """
            params = (eid, as_of or datetime.utcnow().isoformat())
        elif direction == "incoming":
            query = """
                SELECT t.predicate, s.name, t.valid_from, t.valid_to
                FROM triples t JOIN entities s ON t.subject = s.id
                WHERE t.object = ? AND (t.valid_to IS NULL OR t.valid_to > ?)
                ORDER BY t.valid_from DESC
            """
            params = (eid, as_of or datetime.utcnow().isoformat())
        else:
            out_query = """
                SELECT t.predicate, e.name, t.valid_from, t.valid_to, 'out'
                FROM triples t JOIN entities e ON t.object = e.id
                WHERE t.subject = ? AND (t.valid_to IS NULL OR t.valid_to > ?)
            """
            in_query = """
                SELECT t.predicate, s.name, t.valid_from, t.valid_to, 'in'
                FROM triples t JOIN entities s ON t.subject = s.id
                WHERE t.object = ? AND (t.valid_to IS NULL OR t.valid_to > ?)
            """
            out_results = conn.execute(out_query, (eid, as_of or datetime.utcnow().isoformat())).fetchall()
            in_results = conn.execute(in_query, (eid, as_of or datetime.utcnow().isoformat())).fetchall()
            conn.close()

            triples = []
            for row in out_results + in_results:
                triples.append({
                    "predicate": row[0],
                    "object": row[1],
                    "valid_from": row[2],
                    "valid_to": row[3],
                    "direction": row[4],
                })
            return {"entity": name, "triples": triples}

        results = conn.execute(query, params).fetchall()
        conn.close()

        triples = []
        for row in results:
            triples.append({
                "predicate": row[0],
                "object": row[1],
                "valid_from": row[2],
                "valid_to": row[3],
            })
        return {"entity": name, "triples": triples}

    def invalidate(
        self,
        subject: str,
        predicate: str,
        obj: str,
        ended: Optional[str] = None,
    ) -> bool:
        s_id = self._entity_id(subject, create=False)
        o_id = self._entity_id(obj, create=False)
        if s_id is None or o_id is None:
            return False

        conn = self._conn()
        conn.execute("""
            UPDATE triples SET valid_to = ?
            WHERE subject = ? AND predicate = ? AND object = ? AND valid_to IS NULL
        """, (ended or datetime.utcnow().isoformat(), s_id, predicate, o_id))
        conn.commit()
        affected = conn.total_changes > 0
        conn.close()
        return affected

    def timeline(self, entity_name: Optional[str] = None) -> list[dict]:
        conn = self._conn()
        if entity_name:
            eid = self._entity_id(entity_name, create=False)
            if eid is None:
                conn.close()
                return []
            query = """
                SELECT s.name, t.predicate, o.name, t.valid_from, t.valid_to
                FROM triples t
                JOIN entities s ON t.subject = s.id
                JOIN entities o ON t.object = o.id
                WHERE t.subject = ? OR t.object = ?
                ORDER BY t.valid_from ASC
            """
            results = conn.execute(query, (eid, eid)).fetchall()
        else:
            query = """
                SELECT s.name, t.predicate, o.name, t.valid_from, t.valid_to
                FROM triples t
                JOIN entities s ON t.subject = s.id
                JOIN entities o ON t.object = o.id
                ORDER BY t.valid_from ASC
            """
            results = conn.execute(query).fetchall()
        conn.close()

        return [
            {
                "subject": row[0],
                "predicate": row[1],
                "object": row[2],
                "valid_from": row[3],
                "valid_to": row[4],
            }
            for row in results
        ]

    def stats(self) -> dict:
        conn = self._conn()
        entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        triples = conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
        current = conn.execute("SELECT COUNT(*) FROM triples WHERE valid_to IS NULL").fetchone()[0]
        predicates = [r[0] for r in conn.execute(
            "SELECT DISTINCT predicate FROM triples ORDER BY predicate"
        ).fetchall()]
        conn.close()
        return {
            "entities": entities,
            "triples": triples,
            "current_facts": current,
            "predicates": predicates,
        }


kg_service = KGService()
