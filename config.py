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
    ("commodities", "Commodities", "ti-droplet", 5),
    ("cripto", "Cripto", "ti-currency-bitcoin", 5),
    ("internacional", "Internacional", "ti-world", 5),
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
]

# --- Indicadores de mercado (tickers Yahoo Finance) ---
MARKET_TICKERS = {
    "USD/BRL": "BRL=X",
    "Ibovespa": "^BVSP",
    "Petróleo (Brent)": "BZ=F",
}

# --- Publicação (GitHub Pages) ---
# URL pública onde o dashboard fica hospedado, ex: https://SEU-USUARIO.github.io/morning-call/
DASHBOARD_PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL", "")

OUTPUT_HTML_PATH = os.getenv("OUTPUT_HTML_PATH", "./docs/index.html")
