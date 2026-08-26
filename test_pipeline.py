"""
Script de teste: roda a coleta + classificação + geração do HTML com dados
REAIS, mas sem publicar no GitHub Pages nem enviar e-mail. Útil para validar
o dashboard completo antes de configurar essas duas últimas etapas.

Uso: python test_pipeline.py
Depois, abra dist/index.html no navegador.
"""
from collect_news import fetch_raw_news, fetch_market_data
from classify_offline import classify_offline
from generate_dashboard import generate_html

print("1/3 -> coletando notícias e dados de mercado...")
raw_news = fetch_raw_news()
market_data = fetch_market_data()
print(f"    {len(raw_news)} notícias brutas coletadas")

print("2/3 -> classificando notícias por palavra-chave...")
news = classify_offline(raw_news)

print("3/3 -> gerando dashboard HTML...")
path, _html = generate_html(news, market_data)
print(f"    gerado em {path} -- abra esse arquivo no navegador para conferir")
