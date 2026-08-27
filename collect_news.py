"""
Coleta notícias (RSS) e indicadores de mercado.
Saída: dict bruto que será passado para o módulo de resumo/classificação por IA.
"""
import feedparser
import yfinance as yf
from datetime import datetime, timedelta, timezone

from config import RSS_FEEDS, MARKET_TICKERS, NEWS_HOURS_BACK


def fetch_raw_news(hours_back: int = None) -> list[dict]:
    """Puxa itens recentes de todos os feeds RSS configurados."""
    hours_back = hours_back if hours_back is not None else NEWS_HOURS_BACK
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    items = []

    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            published = _parse_date(entry)
            if published and published < cutoff:
                continue
            items.append({
                "source": feed["name"],
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "").strip(),
                "link": entry.get("link", ""),
                "published": published.isoformat() if published else None,
            })

    return items


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch_market_data() -> dict:
    """Pega preço atual e variação percentual do dia para cada ticker configurado."""
    data = {}
    for label, ticker in MARKET_TICKERS.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) < 2:
                print(f"[aviso] {label} ({ticker}): histórico insuficiente "
                      f"({len(hist)} dia(s) retornado(s)) -- ticker pode estar "
                      f"errado, deslistado, ou sem negociação recente")
                continue
            prev_close = hist["Close"].iloc[-2]
            last = hist["Close"].iloc[-1]
            change_pct = ((last - prev_close) / prev_close) * 100
            data[label] = {"value": round(float(last), 2), "change_pct": round(float(change_pct), 2)}
        except Exception as e:
            print(f"[aviso] falha ao buscar {label} ({ticker}): {e}")

    # Selic não vem do Yahoo Finance -- puxa direto da API do Banco Central
    data["Selic"] = fetch_selic()
    # DI29 não tem API gratuita -- usamos a Selic esperada 2029 (Focus/BCB)
    data["Selic esperada 2029 (Focus)"] = fetch_selic_esperada_2029()
    return data


def fetch_selic() -> dict:
    import requests
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        valor = float(resp.json()[0]["valor"])
        return {"value": valor, "change_pct": None}
    except Exception as e:
        print(f"[aviso] falha ao buscar Selic: {e}")
        return {"value": None, "change_pct": None}


def fetch_selic_esperada_2029() -> dict:
    """
    Busca a expectativa de mercado (pesquisa Focus, Banco Central) para a
    Selic no fim de 2029 -- usada como referência de juros de longo prazo,
    já que não existe fonte gratuita e estável para a curva DI/Tesouro
    (ver README/histórico de conversa para mais contexto).

    IMPORTANTE: isso é uma EXPECTATIVA/pesquisa de opinião entre
    economistas (mediana Focus), não um preço de mercado negociado --
    por isso o rótulo no dashboard deixa isso explícito ("Focus").
    """
    import requests

    url = (
        "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
        "ExpectativasMercadoAnuais"
        "?$top=1"
        "&$filter=Indicador%20eq%20'Selic'%20and%20DataReferencia%20eq%20'2029'"
        "&$orderby=Data%20desc"
        "&$format=json"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        values = resp.json().get("value", [])
        if not values:
            print("[aviso] Selic esperada 2029 (Focus) não retornou nenhum dado")
            return {"value": None, "change_pct": None}
        mediana = values[0].get("Mediana")
        return {"value": float(mediana), "change_pct": None}
    except Exception as e:
        print(f"[aviso] falha ao buscar Selic esperada 2029 (Focus): {e}")
        return {"value": None, "change_pct": None}


if __name__ == "__main__":
    news = fetch_raw_news()
    print(f"{len(news)} notícias coletadas")
    market = fetch_market_data()
    print(market)
