"""
RAG Engine -- SQLite FTS5-based retrieval voor bedrijfs-FAQ.
Lichter dan ChromaDB, built-in Python sqlite3, perfect voor Pi 5.
"""
import sqlite3
import json
import re
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger("stay4s.whatsapp")

DB_PATH = os.environ.get("RAG_DB_PATH", "/home/Miesdevries/stay4s-whatsapp/faq.db")

STOP_WORDS = {
    "wat", "zijn", "jullie", "de", "het", "een", "en", "van", "in", "op",
    "te", "is", "aan", "met", "voor", "die", "dat", "hier", "daar", "ook",
    "niet", "maar", "hoe", "waar", "wanneer", "wie", "kan", "kun", "heb",
    "hebt", "hebben", "zal", "zou", "moet", "wil", "wilt", "ik", "jij", "u",
    "we", "wij", "ze", "zij", "dit", "die", "toen", "nu", "al", "er", "toch",
}


class RAGEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                doc_type TEXT DEFAULT 'faq',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
            USING fts5(
                title, content, source,
                content='documents',
                content_rowid='id'
            )
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ai
            AFTER INSERT ON documents
            BEGIN
                INSERT INTO documents_fts(rowid, title, content, source)
                VALUES (new.id, new.title, new.content, new.source);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ad
            AFTER DELETE ON documents
            BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, content, source)
                VALUES('delete', old.id, old.title, old.content, old.source);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_au
            AFTER UPDATE ON documents
            BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, content, source)
                VALUES('delete', old.id, old.title, old.content, old.source);
                INSERT INTO documents_fts(rowid, title, content, source)
                VALUES (new.id, new.title, new.content, new.source);
            END
        """)
        conn.commit()
        conn.close()
        logger.info(f"RAG database initialized at {self.db_path}")

    def add_document(self, title: str, content: str, source: str, doc_type: str = "faq") -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO documents (title, content, source, doc_type) VALUES (?, ?, ?, ?)",
            (title, content, source, doc_type)
        )
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added document #{doc_id}: {title}")
        return doc_id

    def search(self, query: str, limit: int = 3) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        clean_words = re.sub(r"[^a-zA-Z0-9\s]", " ", query).split()
        if not clean_words:
            return []

        meaningful = [w for w in clean_words if w.lower() not in STOP_WORDS]
        if not meaningful:
            meaningful = clean_words[:3]

        fts_query = " OR ".join([w + "*" for w in meaningful[:5]])

        try:
            results = conn.execute("""
                SELECT
                    d.id, d.title, d.content, d.source, d.doc_type,
                    bm25(documents_fts) as score
                FROM documents_fts
                JOIN documents d ON d.id = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY score ASC
                LIMIT ?
            """, (fts_query, limit)).fetchall()
        except Exception as e:
            logger.error(f"FTS5 search error: {e}, query: {fts_query}")
            conn.close()
            return []

        docs = []
        for row in results:
            docs.append({
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "source": row["source"],
                "doc_type": row["doc_type"],
                "score": abs(row["score"])
            })

        conn.close()
        return docs

    def get_context(self, query: str, max_chars: int = 1500) -> tuple:
        results = self.search(query, limit=3)
        if not results:
            return "", []

        context_parts = []
        sources = []
        total_chars = 0

        for doc in results:
            content_len = len(doc["content"])
            if total_chars + content_len > max_chars:
                break
            context_parts.append("Bron: " + doc["title"] + "\n" + doc["content"])
            sources.append({"title": doc["title"], "source": doc["source"], "score": doc["score"]})
            total_chars += content_len

        context = "\n\n---\n\n".join(context_parts) if context_parts else ""
        return context, sources

    def list_all(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, title, source, doc_type, created_at FROM documents ORDER BY id").fetchall()
        docs = [dict(row) for row in rows]
        conn.close()
        return docs

    def delete_document(self, doc_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        conn.close()
        return count