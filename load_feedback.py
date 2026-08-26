"""
Carrega o histórico de likes/dislikes registrado na planilha (via Apps Script)
e monta um resumo de preferências que é injetado no prompt de resumo/classificação.

Isso NÃO é um modelo treinado — é uma heurística baseada em histórico que
orienta o Claude a repetir o que a equipe gostou e evitar o que não gostou.
"""
import requests
from collections import defaultdict

from config import FEEDBACK_WEBAPP_URL

EMPTY_SUMMARY = {"liked_titles": [], "disliked_titles": [], "source_scores": {}}


def load_feedback_summary(max_examples: int = 8) -> dict:
    if not FEEDBACK_WEBAPP_URL:
        return EMPTY_SUMMARY

    try:
        resp = requests.get(FEEDBACK_WEBAPP_URL, params={"action": "read"}, timeout=10)
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        print(f"[aviso] falha ao carregar feedback: {e}")
        return EMPTY_SUMMARY

    liked = [r["title"] for r in rows if r.get("vote") == "like" and r.get("title")]
    disliked = [r["title"] for r in rows if r.get("vote") == "dislike" and r.get("title")]

    source_scores = defaultdict(lambda: {"like": 0, "dislike": 0})
    for r in rows:
        vote = r.get("vote")
        if vote in ("like", "dislike"):
            source_scores[r.get("source", "desconhecida")][vote] += 1

    return {
        "liked_titles": liked[-max_examples:],
        "disliked_titles": disliked[-max_examples:],
        "source_scores": dict(source_scores),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(load_feedback_summary(), indent=2, ensure_ascii=False))
