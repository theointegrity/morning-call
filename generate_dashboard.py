"""
Gera o arquivo HTML final do dashboard a partir do template Jinja2.
"""
import hashlib
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from jinja2 import Environment, FileSystemLoader

from config import CATEGORIES, OUTPUT_HTML_PATH, FEEDBACK_WEBAPP_URL
from agenda import get_upcoming_events

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _format_market(market_raw: dict) -> dict:
    """Formata os valores de mercado para exibição (ex: casas decimais, moeda)."""
    formatted = {}
    for label, m in market_raw.items():
        value = m.get("value")
        if value is None:
            display = "indisponível"
        elif label == "Selic":
            display = f"{value:.2f}%"
        elif label == "USD/BRL":
            display = f"{value:.2f}"
        elif label == "Ibovespa":
            display = f"{value:,.0f}".replace(",", ".")
        elif label == "Petróleo (Brent)":
            display = f"US$ {value:.2f}"
        else:
            display = str(value)
        formatted[label] = {"display_value": display, "change_pct": m.get("change_pct")}
    return formatted


def _add_ids(news: dict) -> dict:
    """Gera um id estável (hash) por notícia, usado para registrar o feedback."""
    for items in news.values():
        for item in items:
            raw = f"{item.get('title', '')}|{item.get('link', '')}"
            item["id"] = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return news


def generate_html(news: dict, market_raw: dict) -> str:
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("dashboard_template.html")

    now = datetime.now(BRASILIA_TZ)
    formatted_date = f"{DIAS[now.weekday()].capitalize()}, {now.day} de {MESES[now.month - 1]} de {now.year}"
    formatted_time = now.strftime("%H:%M")

    upcoming_events = [
        {"date": ev["date"].strftime("%d/%m"), "label": ev["label"]}
        for ev in get_upcoming_events()
    ]

    html = template.render(
        news=_add_ids(news),
        market=_format_market(market_raw),
        categories=CATEGORIES,
        formatted_date=formatted_date,
        formatted_time=formatted_time,
        feedback_webapp_url=FEEDBACK_WEBAPP_URL,
        upcoming_events=upcoming_events,
    )

    os.makedirs(os.path.dirname(OUTPUT_HTML_PATH), exist_ok=True)
    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    return OUTPUT_HTML_PATH, html


if __name__ == "__main__":
    # teste rápido com dados fictícios
    fake_news = {"cambio_juros": [{"title": "Exemplo de notícia", "source": "Teste", "link": "https://example.com", "id": "abc123"}]}
    fake_market = {"USD/BRL": {"value": 5.42, "change_pct": 0.4}}
    path, _html = generate_html(fake_news, fake_market)
    print(f"Gerado em {path}")
