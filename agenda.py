"""
Calcula os próximos eventos da agenda econômica conhecida (ver
config.AGENDA_EVENTS). Não é um calendário automático/dinâmico -- é uma
lista mantida manualmente com datas já oficialmente divulgadas pelos
bancos centrais, atualizada quando novos calendários anuais saem.
"""
from datetime import datetime, date
from zoneinfo import ZoneInfo

from config import AGENDA_EVENTS

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


def get_upcoming_events(limit: int = 3) -> list[dict]:
    """Retorna os próximos eventos (a partir de hoje, inclusive), ordenados por data."""
    today = datetime.now(BRASILIA_TZ).date()

    upcoming = []
    for ev in AGENDA_EVENTS:
        ev_date = datetime.strptime(ev["date"], "%Y-%m-%d").date()
        if ev_date >= today:
            upcoming.append({"date": ev_date, "label": ev["label"]})

    upcoming.sort(key=lambda e: e["date"])
    return upcoming[:limit]


if __name__ == "__main__":
    for ev in get_upcoming_events():
        print(ev["date"].strftime("%d/%m/%Y"), "-", ev["label"])
