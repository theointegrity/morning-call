"""
Configurações centrais do Morning Call - Integrity.
Todas as chaves e listas sensíveis vêm de variáveis de ambiente (.env).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Chaves de API ---
# Só é necessária se SUMMARIZATION_MODE = "ai"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Modo de resumo/classificação das notícias ---
# "offline" (padrão): classifica por palavras-chave, sem custo de API
# "ai": usa a API da Anthropic para resumir e classificar com mais qualidade
SUMMARIZATION_MODE = os.getenv("SUMMARIZATION_MODE", "offline")

# --- E-mail (Gmail via SMTP + senha de app) ---
RECIPIENTS = [e.strip() for e in os.getenv("RECIPIENTS", "").split(",") if e.strip()]
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "theo@integritywm.com.br")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# --- Feedback (like/dislike) ---
# URL do Web App do Google Apps Script (ver apps_script/feedback_webapp.gs)
FEEDBACK_WEBAPP_URL = os.getenv("FEEDBACK_WEBAPP_URL", "")

# --- Categorias e quantidade de notícias por categoria ---
# (chave interna, título exibido, ícone Tabler, quantidade de itens)
CATEGORIES = [
    ("cambio_juros", "Câmbio e juros", "ti-building-bank", 5),
    ("bolsa", "Bolsa", "ti-chart-line", 5),
    ("empresas", "Empresas", "ti-briefcase", 5),
    ("commodities", "Commodities", "ti-droplet", 5),
    ("cripto", "Cripto", "ti-currency-bitcoin", 5),
    ("internacional", "Internacional", "ti-world", 5),
    ("politica_fiscal", "Política e fiscal", "ti-building-bank-2", 5),
    ("credito_privado", "Crédito privado", "ti-file-invoice", 5),
    ("fundos", "Fundos", "ti-chart-donut", 5),
    ("imoveis", "Imóveis", "ti-building-skyscraper", 5),
]

# --- Janela de coleta de notícias (horas para trás) ---
# Aumentei em relação ao padrão inicial (20h) porque com poucas fontes,
# uma janela curta deixa categorias mais nichadas (cripto, crédito privado,
# fundos, imóveis) vazias com frequência.
NEWS_HOURS_BACK = int(os.getenv("NEWS_HOURS_BACK", "36"))

# --- Fontes de notícias (RSS) ---
# Adicione/ajuste feeds livremente. As 3 últimas foram adicionadas para
# cobrir melhor cripto, fundos e crédito privado -- teste cada uma abrindo
# a URL no navegador (deve aparecer um XML) e remova/troque se alguma não
# retornar conteúdo.
RSS_FEEDS = [
    {"name": "Valor Econômico", "url": "https://valor.globo.com/rss/home/"},
    {"name": "InfoMoney", "url": "https://www.infomoney.com.br/feed/"},
    {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-sectors=business-finance"},
    {"name": "Investing.com Brasil", "url": "https://br.investing.com/rss/news.rss"},
    {"name": "Money Times", "url": "https://www.moneytimes.com.br/feed/"},
    {"name": "Suno Notícias", "url": "https://www.suno.com.br/noticias/feed/"},
    {"name": "Cointelegraph Brasil", "url": "https://cointelegraph.com.br/rss"},
    {"name": "Poder360", "url": "https://www.poder360.com.br/feed/"},
]

# --- Indicadores de mercado (tickers Yahoo Finance) ---
MARKET_TICKERS = {
    "USD/BRL": "BRL=X",
    "Ibovespa": "^BVSP",
    "Petróleo (Brent)": "BZ=F",
    "Bitcoin (USD)": "BTC-USD",
    "HASH11": "HASH11.SA",
}

# --- Publicação (GitHub Pages) ---
# URL pública onde o dashboard fica hospedado, ex: https://SEU-USUARIO.github.io/morning-call/
DASHBOARD_PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL", "")

OUTPUT_HTML_PATH = os.getenv("OUTPUT_HTML_PATH", "./docs/index.html")

# --- Agenda de eventos econômicos conhecidos com antecedência ---
# Datas oficiais (Copom: Banco Central; FOMC: Federal Reserve). Como não
# existe uma API gratuita e confiável de calendário econômico completo,
# mantemos aqui manualmente as datas já divulgadas oficialmente pelos
# bancos centrais. Atualize esta lista quando os próximos calendários
# anuais forem divulgados (geralmente no fim do ano anterior).
AGENDA_EVENTS = [
    # Copom 2026 (decisão da Selic no 2º dia de cada reunião)
    {"date": "2026-01-28", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-03-18", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-04-29", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-06-17", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-08-05", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-09-16", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-11-04", "label": "Decisão do Copom (Selic)"},
    {"date": "2026-12-09", "label": "Decisão do Copom (Selic)"},
    # Copom 2027 (decisão da Selic no 2º dia de cada reunião)
    {"date": "2027-01-27", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-03-17", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-04-28", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-06-16", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-08-04", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-09-22", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-10-27", "label": "Decisão do Copom (Selic)"},
    {"date": "2027-12-08", "label": "Decisão do Copom (Selic)"},
    # FOMC 2026 (decisão de juros dos EUA no 2º dia de cada reunião)
    {"date": "2026-01-28", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-03-18", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-04-29", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-06-17", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-07-29", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-09-16", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-10-28", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2026-12-09", "label": "Decisão do FOMC (juros dos EUA)"},
    # FOMC 2027 (decisão de juros dos EUA no 2º dia de cada reunião)
    {"date": "2027-01-27", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-03-17", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-04-28", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-06-09", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-07-28", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-09-15", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-10-27", "label": "Decisão do FOMC (juros dos EUA)"},
    {"date": "2027-12-08", "label": "Decisão do FOMC (juros dos EUA)"},
]
