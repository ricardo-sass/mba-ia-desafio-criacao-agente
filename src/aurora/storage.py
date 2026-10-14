"""SQLite de domínio: transações curtas e invariantes no armazenamento."""

import json
import sqlite3
import time
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

SCHEMA = """
CREATE TABLE IF NOT EXISTS apartamentos(numero TEXT PRIMARY KEY, morador TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS areas(id TEXT PRIMARY KEY, nome TEXT NOT NULL, taxa_centavos INTEGER NOT NULL CHECK(taxa_centavos>=0));
CREATE TABLE IF NOT EXISTS codigos_emitidos(codigo TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS vinculos_sessao(session_id TEXT PRIMARY KEY, apartamento TEXT NOT NULL REFERENCES apartamentos(numero), adk_user_id TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS vinculo_imutavel BEFORE UPDATE ON vinculos_sessao BEGIN SELECT RAISE(ABORT, 'Vínculo imutável'); END;
CREATE TABLE IF NOT EXISTS operacoes(id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES vinculos_sessao(session_id), tool_call_id TEXT NOT NULL, argumentos_json TEXT NOT NULL, resultado_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reservas(codigo TEXT PRIMARY KEY REFERENCES codigos_emitidos(codigo), apartamento TEXT NOT NULL REFERENCES apartamentos(numero), area TEXT NOT NULL REFERENCES areas(id), data TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ativa','cancelada')), operacao_id TEXT UNIQUE REFERENCES operacoes(id));
CREATE UNIQUE INDEX IF NOT EXISTS reservas_area_data_ativa ON reservas(area,data) WHERE status='ativa';
CREATE TABLE IF NOT EXISTS visitantes(id TEXT PRIMARY KEY, apartamento TEXT NOT NULL REFERENCES apartamentos(numero), nome TEXT NOT NULL, data TEXT NOT NULL, operacao_id TEXT UNIQUE REFERENCES operacoes(id));
CREATE TABLE IF NOT EXISTS confirmacoes(id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES vinculos_sessao(session_id), invocation_id TEXT NOT NULL, agente TEXT NOT NULL, tool_call_id TEXT NOT NULL, confirmation_call_id TEXT, acao TEXT NOT NULL, argumentos_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente','respondida','executada','negada','conflito')), decisao INTEGER CHECK(decisao IN (0,1)), resultado_json TEXT, UNIQUE(session_id,invocation_id,tool_call_id));
CREATE TRIGGER IF NOT EXISTS confirmacao_imutavel BEFORE UPDATE OF session_id,invocation_id,agente,tool_call_id,acao,argumentos_json ON confirmacoes BEGIN SELECT RAISE(ABORT, 'Argumentos imutáveis'); END;
"""


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Storage:
    def __init__(self, folder: Path, seeds: Path | None = None):
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / "condominio.sqlite3"
        self.seeds = seeds or Path(__file__).resolve().parents[2] / "dados"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(SCHEMA)
        with self.transaction() as db:
            if not db.execute("SELECT 1 FROM apartamentos LIMIT 1").fetchone():
                self._seed(db)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=5000")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connect() as db:
            for attempt in range(3):
                try:
                    db.execute("BEGIN IMMEDIATE")
                    break
                except sqlite3.OperationalError as exc:
                    if "locked" not in str(exc).lower() or attempt == 2:
                        raise
                    time.sleep(0.05 * (attempt + 1))
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def _seed(self, db):
        def read(name):
            return json.loads(
                (self.seeds / f"{name}.json").read_text(), parse_float=Decimal
            )

        for a in read("apartamentos"):
            db.execute(
                "INSERT OR IGNORE INTO apartamentos VALUES (?,?)",
                (a["numero"], a["morador"]),
            )
        for a in read("areas"):
            db.execute(
                "INSERT OR IGNORE INTO areas VALUES (?,?,?)",
                (a["id"], a["nome"], int(Decimal(a["taxa"]) * 100)),
            )
        for r in read("reservas"):
            db.execute(
                "INSERT OR IGNORE INTO codigos_emitidos VALUES (?)", (r["codigo"],)
            )
            db.execute(
                "INSERT INTO reservas VALUES (?,?,?,?,'ativa',NULL)",
                (r["codigo"], r["apartamento"], r["area"], r["data"]),
            )
        for v in read("visitantes"):
            db.execute(
                "INSERT INTO visitantes VALUES (?,?,?,?,NULL)",
                (str(uuid4()), v["apartamento"], v["nome"], v["data"]),
            )

    def reset(self):
        with self.transaction() as db:
            for table in (
                "reservas",
                "visitantes",
                "confirmacoes",
                "operacoes",
                "vinculos_sessao",
            ):
                db.execute(f"DELETE FROM {table}")
            self._seed(db)

    def query(self, sql, args=()):
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, args)]

    def apartment(self, number):
        return bool(self.query("SELECT 1 FROM apartamentos WHERE numero=?", (number,)))

    def bind(self, session_id, apartment, user_id):
        with self.transaction() as db:
            db.execute(
                "INSERT INTO vinculos_sessao VALUES (?,?,?)",
                (session_id, apartment, user_id),
            )

    def binding(self, session_id):
        rows = self.query(
            "SELECT * FROM vinculos_sessao WHERE session_id=?", (session_id,)
        )
        return rows[0] if rows else None

    def reservations(self, apartment):
        return self.query(
            "SELECT codigo,area,data FROM reservas WHERE apartamento=? AND status='ativa' ORDER BY data,codigo",
            (apartment,),
        )

    def visitors(self, apartment):
        return self.query(
            "SELECT nome,data FROM visitantes WHERE apartamento=? ORDER BY data,nome,id",
            (apartment,),
        )

    def areas(self):
        return self.query("SELECT * FROM areas ORDER BY id")

    def area(self, area):
        rows = self.query("SELECT * FROM areas WHERE id=?", (area,))
        return rows[0] if rows else None

    def available(self, area, day):
        return not self.query(
            "SELECT 1 FROM reservas WHERE area=? AND data=? AND status='ativa'",
            (area, day),
        )
