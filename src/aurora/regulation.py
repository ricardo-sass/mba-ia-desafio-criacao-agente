"""Índice lexical local: seleciona assunto antes de selecionar artigos."""

import re
import unicodedata
from pathlib import Path


def normalize(value):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value.lower())
        if not unicodedata.combining(c)
    )


TOPICS = {
    "I": ["disposicoes gerais", "administracao", "sindico", "locacao", "temporada"],
    "II": ["direitos", "deveres"],
    "III": ["silencio", "barulho", "ruido", "sossego"],
    "IV": ["piscina", "nadar", "natacao"],
    "V": ["academia", "brinquedoteca", "playground"],
    "VI": ["salao", "churrasqueira", "quadra"],
    "VII": ["portaria", "seguranca", "visitante", "entrega", "entregador"],
    "VIII": ["animal", "animais", "cachorro", "gato", "pet"],
    "IX": ["mudanca", "mudancas"],
    "X": ["obra", "obras", "reforma"],
    "XI": ["garagem", "veiculo", "carro", "vaga", "estacionamento"],
    "XII": ["lixo", "reciclagem", "residuo", "coleta"],
    "XIII": ["infracao", "infracoes", "penalidade", "multa", "advertencia"],
    "XIV": ["disposicoes finais", "vigencia"],
}
STOP = set(
    "a o as os de da do das dos e em no na nos nas um uma qual quais que como para por ate funciona horario horarios regras sobre pode posso quero saber".split()
)


class Regulation:
    def __init__(self, path: Path):
        self.chapters = {}
        sections = re.split(
            r"^## Capítulo ([IVX]+): (.+)$", path.read_text(), flags=re.M
        )
        for i in range(1, len(sections), 3):
            number, title, body = sections[i : i + 3]
            articles = re.split(r"(?=^\*\*Art\. \d+)", body, flags=re.M)
            self.chapters[number] = [
                {
                    "capitulo": f"{number}: {title}",
                    "artigo": int(
                        match.group(1) if (match := re.search(r"Art\. (\d+)", a)) else 0
                    ),
                    "texto": a.strip(),
                }
                for a in articles
                if re.search(r"^\*\*Art\. \d+", a)
            ]

    def search(self, question):
        q = normalize(question)
        if re.search(r"(inteir|integral|complet|todos os (capitulos|artigos))", q):
            return {"orientacao": "Escolha um assunto específico do regulamento."}
        selected = [
            k
            for k, words in TOPICS.items()
            if any(re.search(r"\b" + re.escape(w) + r"\w*\b", q) for w in words)
        ]
        if not selected:
            return {
                "orientacao": "Informe o assunto ou a área para consultar o regulamento."
            }
        terms = set(re.findall(r"\w+", q)) - STOP
        results: list[dict] = []
        for chapter in selected:
            articles = self.chapters[chapter]
            # Horários da piscina estão concentrados no artigo 22.
            if chapter == "IV" and any(
                w in q
                for w in ("hora", "domingo", "feriado", "funciona", "fecha", "abre")
            ):
                results.extend(a for a in articles if a["artigo"] == 22)
                continue
            topic_terms = {normalize(w) for w in TOPICS[chapter]}
            specific = terms - topic_terms
            ranked = [
                (len(specific & set(re.findall(r"\w+", normalize(a["texto"])))), a)
                for a in articles
            ]
            ranked.sort(key=lambda pair: pair[0], reverse=True)
            if ranked and ranked[0][0] > 0:
                results.extend(a for score, a in ranked[:2] if score > 0)
            elif not specific:
                return {
                    "orientacao": "Qual regra sobre esse assunto você deseja consultar?"
                }
        return (
            {"trechos": results}
            if results
            else {"informacao": "Informação não encontrada para essa pergunta."}
        )
