"""Operações idempotentes e decisões de confirmação no banco de domínio."""

import json
import sqlite3
from uuid import uuid4

from aurora.storage import Storage, encode


class Conflict(Exception):
    """Confirmação inexistente, alheia ou já respondida."""


class Operations:
    def __init__(self, store: Storage):
        self.store = store

    def prepare(self, session, invocation, agent, call, action, args):
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT * FROM confirmacoes WHERE session_id=? AND invocation_id=? AND tool_call_id=?",
                (session, invocation, call),
            ).fetchone()
            if row:
                if (
                    row["argumentos_json"] != encode(args)
                    or row["acao"] != action
                    or row["agente"] != agent
                ):
                    raise ValueError("Correlação de confirmação divergente")
                return dict(row)
            public_id = str(uuid4())
            db.execute(
                "INSERT INTO confirmacoes(id,session_id,invocation_id,agente,tool_call_id,acao,argumentos_json) VALUES (?,?,?,?,?,?,?)",
                (public_id, session, invocation, agent, call, action, encode(args)),
            )
            return dict(
                db.execute(
                    "SELECT * FROM confirmacoes WHERE id=?", (public_id,)
                ).fetchone()
            )

    def correlate(self, session, invocation, agent, original, confirmation_id):
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT * FROM confirmacoes WHERE session_id=? AND invocation_id=? AND tool_call_id=?",
                (session, invocation, original["id"]),
            ).fetchone()
            if not row or row["agente"] != agent or row["acao"] != original["name"]:
                raise ValueError("Evento de confirmação sem correlação")
            if row["confirmation_call_id"] not in (None, confirmation_id):
                raise ValueError("Chamada de confirmação divergente")
            db.execute(
                "UPDATE confirmacoes SET confirmation_call_id=? WHERE id=?",
                (confirmation_id, row["id"]),
            )

    def pending(self, session):
        rows = self.store.query(
            "SELECT * FROM confirmacoes WHERE session_id=? AND status='pendente' AND confirmation_call_id IS NOT NULL ORDER BY rowid",
            (session,),
        )
        return [
            {
                "id": r["id"],
                "acao": r["acao"],
                "detalhes": json.loads(r["argumentos_json"]),
            }
            for r in rows
        ]

    def unresolved(self, session):
        return self.store.query(
            "SELECT * FROM confirmacoes WHERE session_id=? AND status='respondida' ORDER BY rowid",
            (session,),
        )

    def decide(self, session, public_id, decision):
        with self.store.transaction() as db:
            count = db.execute(
                "UPDATE confirmacoes SET status='respondida',decisao=? WHERE id=? AND session_id=? AND status='pendente' AND confirmation_call_id IS NOT NULL",
                (int(decision), public_id, session),
            ).rowcount
            if not count:
                raise Conflict()
            return dict(
                db.execute(
                    "SELECT * FROM confirmacoes WHERE id=?", (public_id,)
                ).fetchone()
            )

    def get(self, public_id):
        return self.store.query("SELECT * FROM confirmacoes WHERE id=?", (public_id,))[
            0
        ]

    def execute(
        self,
        session,
        apartment,
        invocation,
        agent,
        call,
        action,
        args,
        confirmation=None,
    ):
        op_id = encode([session, invocation, call])
        encoded = encode({"acao": action, "detalhes": args})
        with self.store.transaction() as db:
            old = db.execute("SELECT * FROM operacoes WHERE id=?", (op_id,)).fetchone()
            if old:
                if old["argumentos_json"] != encoded:
                    raise ValueError("Argumentos da operação divergentes")
                return json.loads(old["resultado_json"])
            row = None
            if confirmation is not None:
                row = db.execute(
                    "SELECT * FROM confirmacoes WHERE session_id=? AND invocation_id=? AND tool_call_id=?",
                    (session, invocation, call),
                ).fetchone()
                if (
                    not row
                    or row["status"] != "respondida"
                    or row["agente"] != agent
                    or row["argumentos_json"] != encode(args)
                    or row["acao"] != action
                    or bool(row["decisao"]) != confirmation.confirmed
                ):
                    raise ValueError("Decisão não autorizada ou correlação divergente")
            if row and not row["decisao"]:
                result = {"status": "negada", "acao": action}
            else:
                # O serviço também impõe a confirmação; a tool não é o único controle.
                if action == "reservar":
                    area = db.execute(
                        "SELECT taxa_centavos FROM areas WHERE id=?", (args["area"],)
                    ).fetchone()
                    if not area or (area["taxa_centavos"] > 0 and row is None):
                        raise ValueError("Reserva exige confirmação persistida")
                if action == "autorizar" and row is None:
                    raise ValueError("Visita exige confirmação persistida")
                db.execute(
                    "INSERT INTO operacoes VALUES (?,?,?,?,?)",
                    (op_id, session, call, encoded, "{}"),
                )
                result = self._effect(db, op_id, apartment, action, args)
            if not db.execute(
                "SELECT 1 FROM operacoes WHERE id=?", (op_id,)
            ).fetchone():
                db.execute(
                    "INSERT INTO operacoes VALUES (?,?,?,?,?)",
                    (op_id, session, call, encoded, encode(result)),
                )
            else:
                db.execute(
                    "UPDATE operacoes SET resultado_json=? WHERE id=?",
                    (encode(result), op_id),
                )
            if row:
                status = (
                    "conflito"
                    if result["status"] == "indisponivel"
                    else result["status"]
                )
                db.execute(
                    "UPDATE confirmacoes SET status=?,resultado_json=? WHERE id=?",
                    (status, encode(result), row["id"]),
                )
            return result

    def _effect(self, db, op_id, apartment, action, args):
        if action == "reservar":
            while True:
                code = "RSV-" + uuid4().hex.upper()
                if db.execute(
                    "INSERT OR IGNORE INTO codigos_emitidos VALUES (?)", (code,)
                ).rowcount:
                    break
            try:
                db.execute(
                    "INSERT INTO reservas VALUES (?,?,?,?,'ativa',?)",
                    (code, apartment, args["area"], args["data"], op_id),
                )
            except sqlite3.IntegrityError as exc:
                if "reservas.area, reservas.data" not in str(exc):
                    raise
                return {
                    "status": "indisponivel",
                    "area": args["area"],
                    "data": args["data"],
                }
            return {
                "status": "executada",
                "codigo": code,
                "area": args["area"],
                "data": args["data"],
            }
        if action == "cancelar":
            if args.get("codigo"):
                rows = db.execute(
                    "SELECT codigo FROM reservas WHERE apartamento=? AND codigo=? AND status='ativa'",
                    (apartment, args["codigo"]),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT codigo FROM reservas WHERE apartamento=? AND area=? AND data=? AND status='ativa'",
                    (apartment, args["area"], args["data"]),
                ).fetchall()
            if not rows:
                return {
                    "status": "nao_encontrada",
                    "mensagem": "Reserva própria não encontrada.",
                }
            db.execute(
                "UPDATE reservas SET status='cancelada' WHERE codigo=? AND apartamento=?",
                (rows[0]["codigo"], apartment),
            )
            return {
                "status": "executada",
                "codigo": rows[0]["codigo"],
                "acao": "cancelar",
            }
        if action == "autorizar":
            db.execute(
                "INSERT INTO visitantes VALUES (?,?,?,?,?)",
                (str(uuid4()), apartment, args["nome"], args["data"], op_id),
            )
            return {"status": "executada", "nome": args["nome"], "data": args["data"]}
        raise ValueError("Ação desconhecida")
