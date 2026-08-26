"""
Usa o Claude para filtrar, resumir e classificar as notícias brutas
nas categorias definidas em config.CATEGORIES.
"""
import json
import anthropic

from config import ANTHROPIC_API_KEY, CATEGORIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-6"  # ajuste para o modelo que preferir


def _build_feedback_block(feedback: dict | None) -> str:
    if not feedback:
        return ""

    liked = feedback.get("liked_titles") or []
    disliked = feedback.get("disliked_titles") or []
    source_scores = feedback.get("source_scores") or {}

    if not liked and not disliked and not source_scores:
        return ""

    lines = ["\nPreferências aprendidas com o feedback da equipe (like/dislike no dashboard):"]
    if liked:
        lines.append("- Notícias com estilo/tema PARECIDO com estas foram bem avaliadas no passado:")
        lines += [f'  * "{t}"' for t in liked]
    if disliked:
        lines.append("- Notícias com estilo/tema PARECIDO com estas foram mal avaliadas -- evite esse tipo:")
        lines += [f'  * "{t}"' for t in disliked]
    if source_scores:
        lines.append("- Desempenho histórico por fonte (curtidas x descurtidas):")
        for source, scores in source_scores.items():
            lines.append(f'  * {source}: {scores.get("like", 0)} likes, {scores.get("dislike", 0)} dislikes')
        lines.append("  Dê leve preferência a fontes com histórico melhor, mas não exclua uma fonte só por poucos dislikes.")

    return "\n".join(lines) + "\n"


def build_prompt(raw_news: list[dict], feedback: dict | None = None) -> str:
    categories_desc = "\n".join(
        f'- "{key}" ({title}): selecione até {qty} notícia(s), as mais relevantes'
        for key, title, _icon, qty in CATEGORIES
    )

    news_block = "\n".join(
        f'[{i}] fonte: {item["source"]} | título: {item["title"]} | resumo: {item["summary"][:300]} | link: {item["link"]}'
        for i, item in enumerate(raw_news)
    )

    feedback_block = _build_feedback_block(feedback)

    return f"""Você é o analista responsável pelo morning call de mercado de um family office brasileiro.

Abaixo está uma lista de notícias brutas coletadas de RSS feeds. Sua tarefa:
1. Selecione apenas as notícias relevantes para investidores (câmbio, juros, bolsa, commodities, crédito privado, imóveis, macro internacional).
2. Classifique cada notícia escolhida em UMA das categorias abaixo, respeitando o limite de itens por categoria:
{categories_desc}
3. Para cada notícia escolhida, escreva um resumo curto e direto (máximo 20 palavras), em português, focado no que importa para quem investe.
4. Ignore notícias irrelevantes, duplicadas ou puramente promocionais.
5. Se não houver notícia relevante o suficiente para preencher uma categoria, deixe a lista dela mais curta -- não invente conteúdo.
{feedback_block}
Notícias brutas:
{news_block}

Responda APENAS com um JSON válido, sem nenhum texto adicional, no formato:
{{
  "cambio_juros": [{{"title": "...", "source": "...", "link": "..."}}],
  "bolsa": [...],
  "commodities": [...],
  "internacional": [...],
  "credito_privado": [...],
  "imoveis": [...]
}}
"""


def summarize_and_classify(raw_news: list[dict], feedback: dict | None = None) -> dict:
    prompt = build_prompt(raw_news, feedback)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("[erro] resposta da IA não é um JSON válido:")
        print(text)
        return {key: [] for key, _title, _icon, _qty in CATEGORIES}


if __name__ == "__main__":
    from collect_news import fetch_raw_news

    raw = fetch_raw_news()
    result = summarize_and_classify(raw)
    print(json.dumps(result, indent=2, ensure_ascii=False))
